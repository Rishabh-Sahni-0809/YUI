# ─────────────────────────────────────────────────
#  KIRA — Benchmark Runner
#
#  Runs standardised prompts across all available
#  backends and records performance metrics for
#  the Intel pitch dashboard.
# ─────────────────────────────────────────────────
import time
import threading
import datetime
import json

from chat_db import chat_db
import system_monitor as sm

try:
    from config_loader import (
        MODEL_OLLAMA, MODEL_OLLAMA_URL, MODEL_MAX_TOKENS, MODEL_TEMPERATURE,
        GROQ_API_KEY, GEMINI_API_KEY,
        CLOUD_GROQ_MODEL, CLOUD_GEMINI_MODEL,
        CLOUD_GROQ_TIMEOUT, CLOUD_GEMINI_TIMEOUT,
    )
except ImportError:
    import os
    MODEL_OLLAMA = "phi"
    MODEL_OLLAMA_URL = "http://localhost:11434"
    MODEL_MAX_TOKENS = 200
    MODEL_TEMPERATURE = 0.2
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    CLOUD_GROQ_MODEL = "groq/compound"
    CLOUD_GEMINI_MODEL = "gemini-3.6-flash"
    CLOUD_GROQ_TIMEOUT = 10
    CLOUD_GEMINI_TIMEOUT = 15

import requests

# ── Standard benchmark prompts ───────────────────
BENCHMARK_PROMPTS = [
    {
        "id": 1,
        "text": "What is the capital of France?",
        "category": "simple_fact",
    },
    {
        "id": 2,
        "text": "Explain the difference between a list and a tuple in Python in 2 sentences.",
        "category": "short_explanation",
    },
    {
        "id": 3,
        "text": "Write a Python function to check if a number is prime.",
        "category": "code_generation",
    },
    {
        "id": 4,
        "text": "Summarize the key benefits of edge AI computing for consumer devices.",
        "category": "summarization",
    },
    {
        "id": 5,
        "text": "Given CPU usage at 92% and RAM at 78%, what should a system do to optimize performance? List 3 actions.",
        "category": "reasoning",
    },
]

# ── Backend execution wrappers ───────────────────

def _run_ollama(prompt: str, max_tokens: int) -> tuple:
    """Returns (response_text, latency_ms, token_count)."""
    url = f"{MODEL_OLLAMA_URL}/api/generate"
    data = {
        "model": MODEL_OLLAMA,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": MODEL_TEMPERATURE,
        }
    }
    t0 = time.perf_counter()
    try:
        res = requests.post(url, json=data, timeout=60)
        res.raise_for_status()
        latency = (time.perf_counter() - t0) * 1000
        body = res.json()
        text = body.get("response", "")
        # Ollama provides eval_count (tokens generated)
        tokens = body.get("eval_count", len(text.split()))
        return text, latency, tokens
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        return f"[ERROR] {e}", latency, 0


def _run_groq(prompt: str, max_tokens: int) -> tuple:
    """Returns (response_text, latency_ms, token_count)."""
    if not GROQ_API_KEY:
        return "[SKIP] No Groq API key", 0, 0

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": CLOUD_GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    t0 = time.perf_counter()
    try:
        res = requests.post(url, json=data, headers=headers, timeout=CLOUD_GROQ_TIMEOUT)
        res.raise_for_status()
        latency = (time.perf_counter() - t0) * 1000
        body = res.json()
        text = body["choices"][0]["message"]["content"]
        tokens = body.get("usage", {}).get("completion_tokens", len(text.split()))
        return text, latency, tokens
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        return f"[ERROR] {e}", latency, 0


def _run_gemini(prompt: str, max_tokens: int) -> tuple:
    """Returns (response_text, latency_ms, token_count)."""
    if not GEMINI_API_KEY:
        return "[SKIP] No Gemini API key", 0, 0

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{CLOUD_GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens}
    }
    t0 = time.perf_counter()
    try:
        res = requests.post(url, json=data, headers=headers, timeout=CLOUD_GEMINI_TIMEOUT)
        res.raise_for_status()
        latency = (time.perf_counter() - t0) * 1000
        body = res.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        tokens = len(text.split())  # Gemini doesn't always return token count
        return text, latency, tokens
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        return f"[ERROR] {e}", latency, 0


# ── Available backends ───────────────────────────
BACKENDS = {
    "local_ollama": _run_ollama,
    "cloud_groq": _run_groq,
    "cloud_gemini": _run_gemini,
}


# ── Benchmark state (for polling progress) ───────
class BenchmarkState:
    def __init__(self):
        self.running = False
        self.progress = 0        # 0-100
        self.total_steps = 0
        self.current_step = 0
        self.current_backend = ""
        self.current_prompt = ""
        self.results = []        # live results as they come in
        self.error = None

    def to_dict(self):
        return {
            "running": self.running,
            "progress": self.progress,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "current_backend": self.current_backend,
            "current_prompt": self.current_prompt,
            "results": self.results,
            "error": self.error,
        }

benchmark_state = BenchmarkState()


def run_benchmark(max_tokens: int = 150):
    """
    Runs all 5 benchmark prompts on all available backends.
    Updates benchmark_state in real time for frontend polling.
    Saves results to SQLite.
    """
    global benchmark_state

    if benchmark_state.running:
        return  # Don't start duplicate runs

    # Determine which backends are available
    available = ["local_ollama"]
    if GROQ_API_KEY:
        available.append("cloud_groq")
    if GEMINI_API_KEY:
        available.append("cloud_gemini")

    prompts = BENCHMARK_PROMPTS
    total = len(prompts) * len(available)

    benchmark_state.running = True
    benchmark_state.progress = 0
    benchmark_state.total_steps = total
    benchmark_state.current_step = 0
    benchmark_state.results = []
    benchmark_state.error = None

    # Warmup for local model (avoids cold start penalty in benchmark)
    if "local_ollama" in available:
        benchmark_state.current_backend = "local_ollama"
        benchmark_state.current_prompt = "[Warmup] Initializing model..."
        _run_ollama("Hello", 10)

    step = 0
    for prompt in prompts:
        for backend_name in available:
            step += 1
            benchmark_state.current_step = step
            benchmark_state.current_backend = backend_name
            benchmark_state.current_prompt = prompt["text"][:50]
            benchmark_state.progress = int((step / total) * 100)

            runner = BACKENDS[backend_name]
            response, latency_ms, tokens = runner(prompt["text"], max_tokens)

            tokens_per_sec = (tokens / (latency_ms / 1000.0)) if latency_ms > 0 and tokens > 0 else 0.0

            # Capture system snapshot
            sys_metrics = sm.get_system_metrics()
            
            result = {
                "prompt_id": prompt["id"],
                "prompt_text": prompt["text"],
                "category": prompt["category"],
                "backend": backend_name,
                "latency_ms": round(latency_ms, 1),
                "tokens_out": tokens,
                "tokens_per_sec": round(tokens_per_sec, 1),
                "response_preview": response[:200] if response else "",
                "cpu": sys_metrics.get("cpu", 0),
                "ram": sys_metrics.get("ram", 0),
            }
            benchmark_state.results.append(result)

            # Persist to DB
            try:
                chat_db.save_benchmark(
                    prompt_id=prompt["id"],
                    prompt_text=prompt["text"],
                    backend=backend_name,
                    latency_ms=latency_ms,
                    tokens_out=tokens,
                    tokens_per_sec=tokens_per_sec,
                    response=response[:500] if response else "",
                )
            except Exception as e:
                print(f"[BENCH] DB save error: {e}")

    benchmark_state.running = False
    benchmark_state.progress = 100
    print(f"[BENCH] Complete. {len(benchmark_state.results)} results recorded.")


def start_benchmark_async(max_tokens: int = 150):
    """Starts benchmark in a background thread. Returns immediately."""
    if benchmark_state.running:
        return False
    t = threading.Thread(target=run_benchmark, args=(max_tokens,), daemon=True)
    t.start()
    return True


def get_benchmark_status() -> dict:
    return benchmark_state.to_dict()


def export_csv() -> str:
    return chat_db.export_benchmarks_csv()
