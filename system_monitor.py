# ─────────────────────────────────────────────────
#  KIRA — System Monitor (Upgraded)
#
#  Changes from original:
#    - Background polling thread at configurable interval
#    - Per-core CPU stats
#    - Detailed RAM (used / total / available)
#    - Three threshold states: GREEN / YELLOW / RED
#    - Rolling buffer of last N readings for sparkline
#    - Structured routing event log with timestamps
# ─────────────────────────────────────────────────
import psutil
import time
import threading
import datetime
from collections import deque

# Import config — graceful fallback if config_loader isn't ready
try:
    from config_loader import (
        THRESH_GREEN_MAX, THRESH_YELLOW_MAX, THRESH_RED_MIN,
        MONITOR_POLL_MS, MONITOR_HISTORY, get_threshold_state,
    )
except ImportError:
    THRESH_GREEN_MAX = 50
    THRESH_YELLOW_MAX = 75
    THRESH_RED_MIN = 75
    MONITOR_POLL_MS = 500
    MONITOR_HISTORY = 60
    def get_threshold_state(cpu, ram):
        worst = max(cpu, ram)
        if worst >= 75: return "red"
        if worst >= 50: return "yellow"
        return "green"


class SystemMonitor:
    """
    Background-polling system monitor.

    - Polls CPU (aggregate + per-core) and RAM every MONITOR_POLL_MS ms
    - Maintains a rolling history buffer for sparkline charts
    - Logs routing switch events with timestamps
    """

    def __init__(self):
        self._history = deque(maxlen=MONITOR_HISTORY)
        self._routing_log = deque(maxlen=200)  # last 200 routing events
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        # Latest snapshot (thread-safe via _lock)
        self._latest = {
            "cpu": 0.0,
            "cpu_per_core": [],
            "ram_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "ram_available_gb": 0.0,
            "state": "green",       # green / yellow / red
            "timestamp": None,
        }

        # Initialise psutil CPU timing baseline
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

        # Start background polling
        self.start()

    # ── Background thread ────────────────────────
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _poll_loop(self):
        interval = MONITOR_POLL_MS / 1000.0
        while self._running:
            self._take_reading()
            time.sleep(interval)

    def _take_reading(self):
        cpu_agg = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_percent(interval=None, percpu=True)
        ram = psutil.virtual_memory()
        state = get_threshold_state(cpu_agg, ram.percent)
        now = datetime.datetime.now().isoformat()

        snapshot = {
            "cpu": round(cpu_agg, 1),
            "cpu_per_core": [round(c, 1) for c in cpu_cores],
            "ram_percent": round(ram.percent, 1),
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "ram_available_gb": round(ram.available / (1024**3), 2),
            "state": state,
            "timestamp": now,
        }

        with self._lock:
            self._latest = snapshot
            self._history.append(snapshot)

    # ── Public API ───────────────────────────────

    def get_current(self) -> dict:
        """Returns the latest metrics snapshot."""
        with self._lock:
            return dict(self._latest)

    def get_history(self) -> list:
        """Returns the last N readings for sparkline charts."""
        with self._lock:
            return list(self._history)

    def get_threshold_state(self) -> str:
        """Returns 'green', 'yellow', or 'red'."""
        with self._lock:
            return self._latest["state"]

    def is_system_stressed(self) -> bool:
        """Returns True if CPU or RAM is at RED threshold."""
        return self.get_threshold_state() == "red"

    # ── Routing event log ────────────────────────

    def log_routing_event(self, backend: str, cpu: float, ram: float,
                          latency_ms: float = 0, reason: str = ""):
        """Log a routing decision for the timeline display."""
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "backend": backend,
            "cpu": round(cpu, 1),
            "ram": round(ram, 1),
            "latency_ms": round(latency_ms, 1),
            "reason": reason,
        }
        with self._lock:
            self._routing_log.append(event)

    def get_routing_log(self) -> list:
        """Returns all logged routing events."""
        with self._lock:
            return list(self._routing_log)

    # ── Session stats (for benchmark summary) ────

    def get_session_stats(self) -> dict:
        """Aggregate stats from routing log."""
        with self._lock:
            log = list(self._routing_log)

        if not log:
            return {
                "total_queries": 0,
                "local_pct": 0,
                "cloud_pct": 0,
                "avg_latency_local_ms": 0,
                "avg_latency_cloud_ms": 0,
            }

        total = len(log)
        local_events = [e for e in log if "local" in e["backend"]]
        cloud_events = [e for e in log if "cloud" in e["backend"] or "groq" in e["backend"] or "gemini" in e["backend"]]

        avg_local = (sum(e["latency_ms"] for e in local_events) / len(local_events)) if local_events else 0
        avg_cloud = (sum(e["latency_ms"] for e in cloud_events) / len(cloud_events)) if cloud_events else 0

        return {
            "total_queries": total,
            "local_count": len(local_events),
            "cloud_count": len(cloud_events),
            "local_pct": round(len(local_events) / total * 100, 1),
            "cloud_pct": round(len(cloud_events) / total * 100, 1),
            "avg_latency_local_ms": round(avg_local, 1),
            "avg_latency_cloud_ms": round(avg_cloud, 1),
        }


# ── Singleton ────────────────────────────────────
monitor = SystemMonitor()


# ── Backward-compat shim ────────────────────────
# Other modules that do `import system_monitor as sm; sm.get_system_metrics()`
# will keep working.
def get_system_metrics() -> dict:
    """Legacy-compatible function returning the same shape as before."""
    m = monitor.get_current()
    return {
        "cpu": m["cpu"],
        "ram": m["ram_percent"],
        "gpu": 0,
        "state": m["state"],
        "cpu_per_core": m["cpu_per_core"],
        "ram_used_gb": m["ram_used_gb"],
        "ram_total_gb": m["ram_total_gb"],
        "ram_available_gb": m["ram_available_gb"],
        "status": m["state"],
        "is_emergency": m["state"] == "red",
        "timestamp": m["timestamp"],
    }


if __name__ == "__main__":
    print("Testing System Monitor (upgraded)...")
    print(f"Poll interval: {MONITOR_POLL_MS}ms | History size: {MONITOR_HISTORY}")
    time.sleep(1)  # Let a couple readings accumulate
    for _ in range(5):
        m = monitor.get_current()
        print(f"  CPU: {m['cpu']}% ({len(m['cpu_per_core'])} cores) | "
              f"RAM: {m['ram_percent']}% ({m['ram_used_gb']}/{m['ram_total_gb']} GB) | "
              f"State: {m['state'].upper()}")
        time.sleep(1)
    print(f"\nHistory buffer: {len(monitor.get_history())} readings")
