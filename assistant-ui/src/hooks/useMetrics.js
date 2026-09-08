import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Enhanced metrics hook with:
 *  - 500ms polling (matches spec)
 *  - Rolling history buffer (60 readings)
 *  - Per-core CPU data
 *  - RAM details (used/total/available)
 *  - Threshold state (green/yellow/red)
 *  - Routing status polling
 */
export function useMetrics() {
  const [current, setCurrent] = useState({
    cpu: 0, ram: 0, gpu: 0, state: 'green',
    cpu_per_core: [], ram_used_gb: 0, ram_total_gb: 0, ram_available_gb: 0,
  });
  const [history, setHistory] = useState([]);
  const [routingStatus, setRoutingStatus] = useState({
    backend: 'unknown', latency_ms: 0, reason: 'Initializing...'
  });

  const pollRef = useRef(null);
  const routingPollRef = useRef(null);

  useEffect(() => {
    // Fast metrics poll (500ms)
    const tick = async () => {
      try {
        const r = await fetch("http://localhost:5000/api/metrics");
        if (r.ok) {
          const d = await r.json();
          setCurrent({
            cpu: d.cpu || 0,
            ram: d.ram || 0,
            gpu: d.gpu || 0,
            state: d.state || 'green',
            cpu_per_core: d.cpu_per_core || [],
            ram_used_gb: d.ram_used_gb || 0,
            ram_total_gb: d.ram_total_gb || 0,
            ram_available_gb: d.ram_available_gb || 0,
          });

          // Build local history buffer
          setHistory(prev => {
            const next = [...prev, {
              cpu: d.cpu || 0,
              ram: d.ram || 0,
              timestamp: d.timestamp || new Date().toISOString(),
            }];
            // Keep last 60
            return next.length > 60 ? next.slice(-60) : next;
          });
        }
      } catch (_) { }
    };

    tick();
    pollRef.current = setInterval(tick, 500);
    return () => clearInterval(pollRef.current);
  }, []);

  useEffect(() => {
    // Routing status poll (every 2s — less frequent)
    const tickRouting = async () => {
      try {
        const r = await fetch("http://localhost:5000/api/routing/status");
        if (r.ok) {
          const d = await r.json();
          setRoutingStatus(d);
        }
      } catch (_) { }
    };

    tickRouting();
    routingPollRef.current = setInterval(tickRouting, 2000);
    return () => clearInterval(routingPollRef.current);
  }, []);

  return { current, history, routingStatus };
}
