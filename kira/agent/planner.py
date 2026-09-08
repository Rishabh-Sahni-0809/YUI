import re
import json
import compute_router

class AgentStep:
    """One step in the agent's execution plan."""
    def __init__(self, action: str, target: str = "", value: str = ""):
        self.action  = action   # "click"|"type"|"hotkey"|"scroll"|"wait"|"verify"|"done"
        self.target  = target   # element label or SoM number
        self.value   = value    # text to type, hotkey, expected screen text for verify
        self.success = None

    def __repr__(self):
        return f"AgentStep({self.action}, target={self.target!r}, value={self.value!r})"

def _S(action, target="", value=""):
    return AgentStep(action, target, value)

def parse_llm_plan(response_text: str) -> list[AgentStep]:
    steps = []
    for line in response_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(?:-\s*)?\[(.*?)\]\s*(?:(?:target|t)=([^,]*))?(?:,?\s*(?:value|v)=([^\]]*))?', line)
        if m:
            action = m.group(1).strip().lower()
            target = m.group(2).strip() if m.group(2) else ""
            value  = m.group(3).strip() if m.group(3) else ""
            
            # Simple cleanup for quotes
            target = target.strip('\'"')
            value = value.strip('\'"')
            
            steps.append(_S(action, target, value))
    return steps

def plan_task(goal: str) -> list[AgentStep]:
    """
    Rule-based instant planner for common tasks — zero LLM, zero latency.
    """
    g = goal.lower().strip()

    m = re.match(r'open (\w[\w\s]*?) and type (.+)', g)
    if m:
        app   = m.group(1).strip()
        text  = m.group(2).strip()
        return [
            _S("hotkey", value="win"),
            _S("wait",   value="0.5"),
            _S("type",   value=app),
            _S("wait",   value="0.8"),
            _S("hotkey", value="enter"),
            _S("wait",   value="1.5"),
            _S("type",   value=text),
            _S("done"),
        ]

    m = re.match(r'open (\w[\w\s]*?) and (?:go to|open|navigate to) (.+)', g)
    if m:
        app = m.group(1).strip()
        url = m.group(2).strip()
        if not url.startswith("http"):
            url = "https://" + url
        return [
            _S("hotkey", value="win"),
            _S("wait",   value="0.5"),
            _S("type",   value=app),
            _S("wait",   value="0.8"),
            _S("hotkey", value="enter"),
            _S("wait",   value="2"),
            _S("hotkey", value="ctrl+l"),
            _S("type",   value=url),
            _S("hotkey", value="enter"),
            _S("done"),
        ]

    m = re.match(r'^open spotify(?: app)? and play (.+)$', g)
    if m:
        song = m.group(1).strip()
        return [
            _S("hotkey", value="win"),
            _S("wait",   value="0.5"),
            _S("type",   value="spotify"),
            _S("wait",   value="0.8"),
            _S("hotkey", value="enter"),
            _S("wait",   value="4"),
            _S("hotkey", value="ctrl+l"),
            _S("type",   value=song),
            _S("wait",   value="1.5"),
            _S("hotkey", value="enter"),
            _S("wait",   value="1.5"),
            _S("hotkey", value="tab"),
            _S("wait",   value="0.2"),
            _S("hotkey", value="down"),
            _S("wait",   value="0.2"),
            _S("hotkey", value="enter"),
            _S("done"),
        ]

    m = re.match(r'^(?:check|what is the) weather(?: in (.+))?', g)
    if m:
        location = m.group(1).strip() if m.group(1) else ""
        query = f"weather {location}".strip()
        return [
            _S("hotkey", value="win"),
            _S("wait",   value="0.5"),
            _S("type",   value="chrome"),
            _S("hotkey", value="enter"),
            _S("wait",   value="2"),
            _S("hotkey", value="ctrl+l"),
            _S("type",   value=f"https://www.google.com/search?q={query}"),
            _S("hotkey", value="enter"),
            _S("done"),
        ]

    m = re.match(r'^(?:open|check) (?:my )?(?:email|gmail)', g)
    if m:
        return [
            _S("hotkey", value="win"),
            _S("wait",   value="0.5"),
            _S("type",   value="chrome"),
            _S("hotkey", value="enter"),
            _S("wait",   value="2"),
            _S("hotkey", value="ctrl+l"),
            _S("type",   value="https://mail.google.com"),
            _S("hotkey", value="enter"),
            _S("done"),
        ]

    m = re.match(r'^set a timer for (\d+) (minutes?|hours?|seconds?)', g)
    if m:
        duration = m.group(1)
        unit = m.group(2)
        return [
            _S("hotkey", value="win"),
            _S("wait",   value="0.5"),
            _S("type",   value="chrome"),
            _S("hotkey", value="enter"),
            _S("wait",   value="2"),
            _S("hotkey", value="ctrl+l"),
            _S("type",   value=f"https://www.google.com/search?q=timer+{duration}+{unit}"),
            _S("hotkey", value="enter"),
            _S("done"),
        ]

    m = re.match(r'^search (?:google )?for (?!.* and )(.+)$', g)
    if m:
        query = m.group(1).strip()
        return [
            _S("hotkey", value="win"),
            _S("wait",   value="0.5"),
            _S("type",   value="chrome"),
            _S("hotkey", value="enter"),
            _S("wait",   value="2"),
            _S("hotkey", value="ctrl+l"),
            _S("type",   value=f"https://www.google.com/search?q={query}"),
            _S("hotkey", value="enter"),
            _S("done"),
        ]

    m = re.match(r'^open (?!.* and )(.+)$', g)
    if m:
        app = m.group(1).strip()
        DIRECT = {
            "notepad":     "notepad.exe",
            "calculator":  "calc.exe",
            "paint":       "mspaint.exe",
            "file explorer": "explorer.exe",
            "task manager":  "taskmgr.exe",
            "cmd":         "cmd.exe",
            "command prompt": "cmd.exe",
        }
        if app in DIRECT:
            return [
                _S("hotkey", value="win+r"),
                _S("wait",   value="0.5"),
                _S("type",   value=DIRECT[app]),
                _S("hotkey", value="enter"),
                _S("done"),
            ]
        else:
            return [
                _S("hotkey", value="win"),
                _S("wait",   value="0.5"),
                _S("type",   value=app),
                _S("wait",   value="0.8"),
                _S("hotkey", value="enter"),
                _S("done"),
            ]

    # LLM fallback
    sys_prompt = (
        "You are an agent that generates a sequence of GUI automation steps to achieve a goal.\n"
        "Output ONLY the steps, one per line.\n"
        "Available actions: [click], [type], [hotkey], [scroll], [wait], [done]\n"
        "Format: [action] t=target, v=value\n"
        "Example:\n"
        "[hotkey] v=win\n"
        "[type] v=chrome\n"
        "[hotkey] v=enter\n"
        "[done]\n"
        f"\nGoal: {goal}"
    )
    
    try:
        response = compute_router.route_query(sys_prompt, max_tokens=150)
        return parse_llm_plan(response)
    except Exception as e:
        print(f"[PLANNER] LLM fallback failed: {e}")
        return []
