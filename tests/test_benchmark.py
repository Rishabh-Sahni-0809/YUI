import pytest
from benchmark_runner import benchmark_state, BENCHMARK_PROMPTS

def test_benchmark_prompts_loaded():
    assert len(BENCHMARK_PROMPTS) > 0

def test_benchmark_state_initialization():
    assert benchmark_state.running == False
    assert benchmark_state.progress == 0
    assert len(benchmark_state.results) == 0
