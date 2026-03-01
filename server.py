from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import sys
import os

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import Digital Assistant functionality
import Digital_Assistant as da
import system_monitor as sm

# Global output buffer to capture the assistant's speech/text output
assistant_output = []

def capture_output(message):
    global assistant_output
    assistant_output.append(message)
    print(f"[Captured]: {message}")

# Redirect the assistant's prints to our capture function
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

@app.route('/api/diagnose', methods=['GET'])
def diagnose():
    try:
        metrics = sm.get_system_metrics()
        advice = da.analyze_system_stress(metrics['cpu'], metrics['ram'])
        return jsonify({"advice": advice, "status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    global assistant_output
    assistant_output = []  # Clear previous output
    
    data = request.json
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Delegate logic entirely to the Digital_Assistant processor
    da.process_query(user_message)

    # Collect outputs triggered by print_output or speak callbacks
    final_output = "\n".join(assistant_output) if assistant_output else ""

    return jsonify({
        "message": final_output,
        "status": "success"
    })


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


if __name__ == '__main__':
    # Initialize the engine properties once
    print("Starting Flask Server for Digital Dave API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
