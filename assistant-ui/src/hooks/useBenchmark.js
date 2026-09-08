import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Hook for managing benchmark execution and results.
 * Polls status during active benchmark runs.
 */
export function useBenchmark() {
  const [status, setStatus] = useState({
    running: false,
    progress: 0,
    total_steps: 0,
    current_step: 0,
    current_backend: '',
    current_prompt: '',
    results: [],
    error: null,
  });
  const [historicalResults, setHistoricalResults] = useState([]);
  const pollRef = useRef(null);

  // Start benchmark
  const runBenchmark = useCallback(async () => {
    try {
      const r = await fetch('http://localhost:5000/api/benchmark/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_tokens: 150 }),
      });
      if (r.ok) {
        // Start polling for progress
        startPolling();
      }
    } catch (e) {
      console.error('Benchmark start failed:', e);
    }
  }, []);

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch('http://localhost:5000/api/benchmark/status');
        if (r.ok) {
          const d = await r.json();
          setStatus(d);
          if (!d.running && d.progress >= 100) {
            clearInterval(pollRef.current);
            pollRef.current = null;
            // Fetch final results from DB
            fetchResults();
          }
        }
      } catch (_) { }
    }, 1000);
  };

  const fetchResults = async () => {
    try {
      const r = await fetch('http://localhost:5000/api/benchmark/results');
      if (r.ok) {
        const d = await r.json();
        setHistoricalResults(d.results || []);
      }
    } catch (_) { }
  };

  // Load historical results on mount
  useEffect(() => {
    fetchResults();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const exportCSV = useCallback(() => {
    window.open('http://localhost:5000/api/benchmark/export', '_blank');
  }, []);

  return { status, historicalResults, runBenchmark, exportCSV };
}
