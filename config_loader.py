# ─────────────────────────────────────────────────
#  KIRA — Centralised Configuration Loader
#  Loads config.yaml + .env once, exposes as module-level dict.
#  Every other module imports from here instead of
#  hardcoding values.
# ─────────────────────────────────────────────────
import os
import yaml
from pathlib import Path

# ── Load .env if python-dotenv is available ──────
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # dotenv not installed — rely on OS env vars

# ── Load config.yaml ─────────────────────────────
_CONFIG_PATH = Path(__file__).parent / "config.yaml"

def _load_yaml() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

_cfg = _load_yaml()

# ── Convenience accessors ────────────────────────

# Model settings
MODEL_OLLAMA       = _cfg.get("model", {}).get("ollama_model", "phi")
MODEL_OLLAMA_URL   = _cfg.get("model", {}).get("ollama_url", "http://localhost:11434")
MODEL_OV_DIR       = _cfg.get("model", {}).get("openvino_model_dir", "./omniparser_ov")
MODEL_MAX_TOKENS   = _cfg.get("model", {}).get("max_tokens", 200)
MODEL_TEMPERATURE  = _cfg.get("model", {}).get("temperature", 0.2)
MODEL_CONTEXT_LEN  = _cfg.get("model", {}).get("context_length", 4096)

# Threshold settings
THRESH_GREEN_MAX   = _cfg.get("thresholds", {}).get("green_max", 50)
THRESH_YELLOW_MAX  = _cfg.get("thresholds", {}).get("yellow_max", 75)
THRESH_RED_MIN     = _cfg.get("thresholds", {}).get("red_min", 75)

# Monitor settings
MONITOR_POLL_MS    = _cfg.get("monitor", {}).get("poll_interval_ms", 500)
MONITOR_HISTORY    = _cfg.get("monitor", {}).get("history_size", 60)

# Conversation settings
CONV_CONTEXT_N     = _cfg.get("conversation", {}).get("context_messages", 10)
CONV_SYSTEM_PROMPT = _cfg.get("conversation", {}).get("system_prompt",
    "You are Kira, a helpful AI assistant.")

# Cloud settings
CLOUD_GROQ_MODEL   = _cfg.get("cloud", {}).get("groq_model", "groq/compound")
CLOUD_GEMINI_MODEL = _cfg.get("cloud", {}).get("gemini_model", "gemini-3.6-flash")
CLOUD_GROQ_TIMEOUT = _cfg.get("cloud", {}).get("groq_timeout", 10)
CLOUD_GEMINI_TIMEOUT = _cfg.get("cloud", {}).get("gemini_timeout", 15)

# Paths
TESSERACT_PATH     = _cfg.get("paths", {}).get("tesseract_path", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
ALARM_SOUND_PATH   = _cfg.get("paths", {}).get("alarm_sound_path", "C:\\Users\\hp\\Music\\Ashes Remain - On My Own.mp3")

# Flags
ENABLE_TTS                = _cfg.get("flags", {}).get("enable_tts", True)
ENABLE_SPEECH             = _cfg.get("flags", {}).get("enable_speech_input", True)
ENABLE_DESKTOP            = _cfg.get("flags", {}).get("enable_desktop_automation", True)

# Flask settings
FLASK_HOST         = _cfg.get("flask", {}).get("host", "0.0.0.0")
FLASK_PORT         = _cfg.get("flask", {}).get("port", 5000)
FLASK_DEBUG        = _cfg.get("flask", {}).get("debug", False)

# API keys (from .env or OS environment)
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")
WOLFRAMALPHA_ID    = os.getenv("WOLFRAMALPHA_APP_ID")
ELEVENLABS_KEY     = os.getenv("ELEVENLABS_API_KEY")

def get_threshold_state(cpu: float, ram: float) -> str:
    """Returns 'green', 'yellow', or 'red' based on configured thresholds."""
    worst = max(cpu, ram)
    if worst >= THRESH_RED_MIN:
        return "red"
    elif worst >= THRESH_GREEN_MAX:
        return "yellow"
    return "green"

def should_route_to_cloud(cpu: float, ram: float) -> bool:
    """True when system load is at RED threshold and cloud keys are available."""
    return (get_threshold_state(cpu, ram) == "red"
            and bool(GROQ_API_KEY or GEMINI_API_KEY))
