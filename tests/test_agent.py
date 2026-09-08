import pytest
from kira.agent.safety import is_safe_step

def test_safety_check_blocks_format():
    is_safe, reason = is_safe_step("type", "", "format c:")
    assert not is_safe
    assert "Blocked command" in reason

def test_safety_check_allows_normal_typing():
    is_safe, reason = is_safe_step("type", "", "hello world")
    assert is_safe

def test_safety_check_blocks_powershell():
    is_safe, reason = is_safe_step("hotkey", "powershell", "win+r")
    assert not is_safe
    assert "Blocked app" in reason
