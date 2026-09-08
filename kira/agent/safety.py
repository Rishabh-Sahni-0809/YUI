# ── Safety layer — block dangerous actions ───────────────────
BLOCKED_COMMANDS = [
    "rm -rf", "format", "del /f", "shutdown /s", "shutdown /r",
    "taskkill /f /im", "reg delete", "cipher /w", "diskpart",
    "powershell -enc", "cmd /c del",
]
BLOCKED_HOTKEYS  = ["alt+f4", "ctrl+alt+del"]
BLOCKED_APPS     = ["powershell", "regedit", "diskpart"]

def is_safe_step(action: str, target: str, value: str) -> tuple[bool, str]:
    """Returns (is_safe, reason). Block dangerous operations."""
    v_low = value.lower()
    t_low = target.lower()
    if action == "hotkey":
        for bh in BLOCKED_HOTKEYS:
            if bh in v_low:
                return False, f"Blocked hotkey: {value}"
    if action == "type":
        for bc in BLOCKED_COMMANDS:
            if bc in v_low:
                return False, f"Blocked command in type: {value}"
    if action in ("click", "hotkey", "type"):
        for ba in BLOCKED_APPS:
            if ba in v_low or ba in t_low:
                return False, f"Blocked app reference: {value or target}"
    return True, ""
