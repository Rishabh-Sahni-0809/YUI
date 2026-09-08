from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import sys
import os

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import configuration
try:
    from config_loader import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
except ImportError:
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    FLASK_DEBUG = True

# Import Digital Assistant functionality gracefully
try:
    import Digital_Assistant as da
    DA_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Digital_Assistant failed to load: {e}")
    da = None
    DA_AVAILABLE = False

import system_monitor as sm

import queue
from flask import Response
import mss
import io
import base64
from PIL import Image

# Global output queue per request to capture the assistant's speech/text output
chat_output_queues = []

def capture_output(message):
    print(f"[Captured]: {message}")
    for q in chat_output_queues:
        q.put(message)

# Redirect the assistant's prints to our capture function
if DA_AVAILABLE:
    da.set_output_callback(capture_output)


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "ready"}), 200

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    try:
        metrics = sm.get_system_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/history', methods=['GET'])
def get_metrics_history():
    """Returns last 60 readings for sparkline charts."""
    try:
        history = sm.monitor.get_history()
        return jsonify({"history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/routing-log', methods=['GET'])
def get_routing_log():
    """Returns all routing switch events for the timeline."""
    try:
        log = sm.monitor.get_routing_log()
        return jsonify({"events": log}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/session', methods=['GET'])
def get_session_stats():
    """Returns session summary: total queries, % local/cloud, avg latency."""
    try:
        stats = sm.monitor.get_session_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/routing/status', methods=['GET'])
def get_routing_status():
    """Returns the last routing decision for the UI status badge."""
    try:
        import compute_router
        info = compute_router.get_last_routing_info()
        return jsonify(info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/diagnose', methods=['GET'])
def diagnose():
    try:
        metrics = sm.get_system_metrics()
        advice = da.analyze_system_stress(metrics['cpu'], metrics['ram'])
        return jsonify({"advice": advice, "status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Benchmark endpoints ──────────────────────────
import benchmark_runner

@app.route('/api/benchmark/run', methods=['POST'])
def run_benchmark():
    """Kicks off a benchmark run (async). Returns immediately."""
    max_tokens = request.json.get("max_tokens", 150) if request.json else 150
    started = benchmark_runner.start_benchmark_async(max_tokens)
    if started:
        return jsonify({"status": "started"}), 200
    return jsonify({"status": "already_running"}), 409

@app.route('/api/benchmark/status', methods=['GET'])
def benchmark_status():
    """Returns live progress and partial results."""
    return jsonify(benchmark_runner.get_benchmark_status()), 200

@app.route('/api/benchmark/results', methods=['GET'])
def benchmark_results():
    """Returns all historical benchmark results from DB."""
    try:
        from chat_db import chat_db
        results = chat_db.get_benchmark_results(limit=200)
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/benchmark/export', methods=['GET'])
def benchmark_export():
    """Downloads benchmark results as CSV."""
    csv_data = benchmark_runner.export_csv()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=kira_benchmark.csv"}
    )

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    q = queue.Queue()
    chat_output_queues.append(q)

    def worker():
        try:
            import json
            is_screen_agent = any(k in user_message for k in ["open", "play", "check", "set a timer", "search", "do ", "click", "type", "go to", "read screen"])
            
            subtasks = []
            if is_screen_agent:
                if "spotify" in user_message:
                    subtasks = ["🔍 Search Spotify", "▶️ Select Song", "🎵 Play Track"]
                elif "weather" in user_message:
                    subtasks = ["🔍 Find Location", "📊 Extract Data", "✓ Report Weather"]
                else:
                    subtasks = ["🔍 Analyze Screen", "⚡ Execute Plan", "✓ Verify Result"]

            meta = {
                "type": "metadata",
                "task_type": "screen_automation" if is_screen_agent else "text",
                "subtasks": subtasks
            }
            q.put(f"[METADATA] {json.dumps(meta)}")
            if not DA_AVAILABLE:
                q.put("[ERROR] Digital Assistant core is offline.")
                return
            da.process_query(user_message)
        finally:
            q.put(None)  # EOF marker
            if q in chat_output_queues:
                chat_output_queues.remove(q)

    threading.Thread(target=worker, daemon=True).start()

    def generate():
        while True:
            msg = q.get()
            if msg is None:
                break
            # Format as SSE
            yield f"data: {msg}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/screenshot', methods=['GET'])
def get_screenshot():
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Compress to 60% quality JPEG for performance as requested
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=60)
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            return jsonify({
                "image": f"data:image/jpeg;base64,{img_str}",
                "status": "success"
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/listen', methods=['POST'])
def listen():
    global assistant_output
    assistant_output = []
    
    # Trigger the microphone listening
    try:
        query = da.takeCommand().lower()
    except Exception as e:
        error_msg = str(e)
        if "PyAudio" in error_msg:
            return jsonify({
                "user_query": "", 
                "message": "PyAudio is not installed on the system. The microphone cannot be accessed. Please run 'pip install pyaudio' or use text chat.", 
                "status": "success"
            }), 200
        else:
            return jsonify({
                "user_query": "", 
                "message": f"Microphone error: {error_msg}", 
                "status": "success"
            }), 200
    
    if query == "none" or not query:
        return jsonify({"user_query": "", "message": "I didn't catch that. Please try again.", "status": "success"}), 200

    # Delegate logic entirely to the Digital_Assistant processor
    da.process_query(query)

    # Collect outputs triggered by print_output or speak callbacks
    final_output = "\n".join(assistant_output) if assistant_output else ""

    return jsonify({
        "user_query": query,
        "message": final_output,
        "status": "success"
    })


# ── Chat history endpoints ───────────────────────
from chat_db import chat_db

@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    """Search past chat messages."""
    search = request.args.get("search", "")
    if search:
        results = chat_db.search_messages(search)
    else:
        results = chat_db.get_session_messages("default", limit=100)
    return jsonify({"messages": results}), 200

@app.route('/api/chat/sessions', methods=['GET'])
def chat_sessions():
    """List all chat sessions."""
    sessions = chat_db.get_sessions()
    return jsonify({"sessions": sessions}), 200


if __name__ == '__main__':
    # Initialize the engine properties once
    print(f"Starting Flask Server for Kira API on {FLASK_HOST}:{FLASK_PORT}...")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
