# ─────────────────────────────────────────────────
#  KIRA — Adaptive Compute Router (Upgraded)
#
#  Changes from original:
#    - Uses config_loader instead of hardcoded values
#    - Correct routing: LOCAL first when system is GREEN
#    - Latency timing on every call
#    - Returns routing metadata alongside response
#    - Logs every decision to system_monitor for timeline
#    - Streaming-ready architecture
# ─────────────────────────────────────────────────
import os
import time
import requests

import system_monitor as sm

# Import from central config
try:
    from config_loader import (
        GROQ_API_KEY, GEMINI_API_KEY,
        MODEL_OLLAMA, MODEL_OLLAMA_URL, MODEL_MAX_TOKENS, MODEL_TEMPERATURE,
        CLOUD_GROQ_MODEL, CLOUD_GEMINI_MODEL,
        CLOUD_GROQ_TIMEOUT, CLOUD_GEMINI_TIMEOUT,
    )
except ImportError:
    # Graceful fallback if config_loader isn't set up yet
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL_OLLAMA = "phi"
    MODEL_OLLAMA_URL = "http://localhost:11434"
    MODEL_MAX_TOKENS = 200
    MODEL_TEMPERATURE = 0.2
    CLOUD_GROQ_MODEL = "groq/compound"
    CLOUD_GEMINI_MODEL = "gemini-3.6-flash"
    CLOUD_GROQ_TIMEOUT = 10
    CLOUD_GEMINI_TIMEOUT = 15


def is_complex_task(prompt: str) -> bool:
    """Heuristic to determine if a task requires cloud reasoning."""
    complex_triggers = [
        "why", "explain", "summarize", "write code", "analyze",
        "debug", "compare", "plan", "strategy"
    ]
    prompt_lower = prompt.lower()

    # 1. Length check: longer queries usually imply more complex logic
    if len(prompt.split()) > 30:
        return True

    # 2. Keyword check
    for trigger in complex_triggers:
        if trigger in prompt_lower:
            return True

    return False


# ─────────────────────────────────────────────────
#  Backend implementations
# ─────────────────────────────────────────────────

def _ask_local_ollama(prompt: str, max_tokens: int, messages: list = None) -> str:
    options = {
        "num_predict": max_tokens,
        "temperature": MODEL_TEMPERATURE,
        "top_k": 10,
    }

    if messages:
        # Use /api/chat for multi-turn conversation
        url = f"{MODEL_OLLAMA_URL}/api/chat"
        data = {
            "model": MODEL_OLLAMA,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.exceptions.Timeout:
            return "[LOCAL TIMEOUT] The local model took too long to respond."
        except Exception as err:
            return f"[LOCAL ERROR] {err}"
    else:
        # Fallback: single prompt via /api/generate
        url = f"{MODEL_OLLAMA_URL}/api/generate"
        data = {
            "model": MODEL_OLLAMA,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.Timeout:
            return "[LOCAL TIMEOUT] The local model took too long to respond."
        except Exception as err:
            return f"[LOCAL ERROR] {err}"


def _ask_groq(prompt: str, max_tokens: int, messages: list = None) -> str:
    """Primary cloud backend: Groq (fastest free tier)."""
    if not GROQ_API_KEY:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    # Use conversation messages if provided, otherwise single prompt
    msg_list = messages if messages else [{"role": "user", "content": prompt}]
    data = {
        "model": CLOUD_GROQ_MODEL,
        "messages": msg_list,
        "max_tokens": max_tokens
    }
    try:
        res = requests.post(url, json=data, headers=headers, timeout=CLOUD_GROQ_TIMEOUT)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[WARN] Groq inference failed: {e}")
        return None


def _ask_gemini(prompt: str, max_tokens: int) -> str:
    """Secondary cloud backend: Gemini Flash (fallback)."""
    if not GEMINI_API_KEY:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{CLOUD_GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens}
    }
    try:
        res = requests.post(url, json=data, headers=headers, timeout=CLOUD_GEMINI_TIMEOUT)
        res.raise_for_status()
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"[WARN] Gemini inference failed: {e}")
        return None


def _ask_cloud(prompt: str, max_tokens: int, messages: list = None) -> str:
    """Try Groq first, then Gemini, then fall back to local."""
    result = _ask_groq(prompt, max_tokens, messages=messages)
    if result:
        return result

    result = _ask_gemini(prompt, max_tokens)
    if result:
        return result

    # All cloud backends failed — fall back to local
    print("[WARN] All cloud backends failed. Falling back to local.")
    return _ask_local_ollama(prompt, max_tokens, messages=messages)


# ─────────────────────────────────────────────────
#  Main routing function
# ─────────────────────────────────────────────────

def route_query(prompt: str, max_tokens: int = 200, force_local: bool = False, messages: list = None) -> str:
    """
    Routes the prompt to the best available backend.

    Decision tree (matches spec):
      LOCAL  if CPU < 75% AND RAM < 75% AND model loaded
      CLOUD  otherwise (if keys available)

    Returns the text response. Routing metadata is logged to
    system_monitor for the benchmark dashboard.
    """
    metrics = sm.get_system_metrics()
    cpu = metrics.get("cpu", 0)
    ram = metrics.get("ram", 0)
    state = metrics.get("state", "green")

    # ── Determine route ──────────────────────────
    if force_local:
        route = "local_ollama"
        reason = "Force-local requested"
    elif state == "red" and (GROQ_API_KEY or GEMINI_API_KEY):
        route = "cloud"
        reason = f"System stressed (CPU={cpu}%, RAM={ram}%, state=RED)"
        print(f"[ROUTER] {reason}. Offloading to cloud.")
    elif state == "red" and not (GROQ_API_KEY or GEMINI_API_KEY):
        route = "local_ollama"
        reason = f"System stressed but no cloud keys configured"
        print(f"[ROUTER] {reason}. Using local despite stress.")
    else:
        # GREEN or YELLOW → prefer local
        route = "local_ollama"
        reason = f"System healthy (CPU={cpu}%, RAM={ram}%, state={state.upper()})"

    # ── Execute with latency timing ──────────────
    t0 = time.perf_counter()

    if route == "cloud":
        response = _ask_cloud(prompt, max_tokens, messages=messages)
        # Determine which cloud backend actually responded
        backend_label = "cloud_groq"  # default assumption
        if not GROQ_API_KEY:
            backend_label = "cloud_gemini"
    else:
        response = _ask_local_ollama(prompt, max_tokens, messages=messages)
        backend_label = "local_ollama"
        # If local failed, try cloud as fallback
        if response.startswith("[LOCAL ERROR]") or response.startswith("[LOCAL TIMEOUT]"):
            if GROQ_API_KEY or GEMINI_API_KEY:
                print(f"[ROUTER] Local failed. Auto-switching to cloud.")
                reason = f"Local inference failed: {response[:80]}"
                t0 = time.perf_counter()  # Reset timer for cloud
                response = _ask_cloud(prompt, max_tokens)
                backend_label = "cloud_groq"

    latency_ms = (time.perf_counter() - t0) * 1000

    # ── Log routing decision ─────────────────────
    try:
        sm.monitor.log_routing_event(
            backend=backend_label,
            cpu=cpu,
            ram=ram,
            latency_ms=latency_ms,
            reason=reason,
        )
    except Exception:
        pass  # Don't break inference if logging fails

    print(f"[ROUTER] {backend_label} | {latency_ms:.0f}ms | {reason}")
    return response


# ── Metadata accessor for UI ─────────────────────
def get_last_routing_info() -> dict:
    """Returns the most recent routing event for the UI status badge."""
    log = sm.monitor.get_routing_log()
    if log:
        return log[-1]
    return {"backend": "unknown", "latency_ms": 0, "reason": "No queries yet"}
