import React, { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, AreaChart, Area, Cell,
} from 'recharts';
import { useBenchmark } from '../../hooks/useBenchmark';
import './BenchmarkDashboard.css';

const BACKEND_COLORS = {
  local_ollama: '#00c9a7',
  cloud_groq:   '#6366f1',
  cloud_gemini:  '#f59e0b',
};

const BACKEND_LABELS = {
  local_ollama: 'Local (Ollama)',
  cloud_groq:   'Cloud (Groq)',
  cloud_gemini:  'Cloud (Gemini)',
};

const STATE_COLORS = {
  green:  '#22c55e',
  yellow: '#eab308',
  red:    '#ef4444',
};

export default function BenchmarkDashboard({ metrics, metricsHistory }) {
  const { status, historicalResults, runBenchmark, exportCSV } = useBenchmark();
  const { current, history } = metrics || {};

  // Prepare sparkline data
  const cpuSparkline = (history || []).map((h, i) => ({ i, cpu: h.cpu }));
  const ramSparkline = (history || []).map((h, i) => ({ i, ram: h.ram }));

  // Aggregate benchmark results for comparison chart
  const latencyComparison = useMemo(() => {
    if (!status.results?.length && !historicalResults?.length) return [];
    const data = status.results?.length ? status.results : historicalResults;

    const byBackend = {};
    data.forEach(r => {
      if (!byBackend[r.backend]) {
        byBackend[r.backend] = { latencies: [], tps: [] };
      }
      if (r.latency_ms > 0) {
        byBackend[r.backend].latencies.push(r.latency_ms);
        byBackend[r.backend].tps.push(r.tokens_per_sec);
      }
    });

    return Object.entries(byBackend).map(([backend, vals]) => ({
      backend: BACKEND_LABELS[backend] || backend,
      key: backend,
      avgLatency: vals.latencies.length
        ? Math.round(vals.latencies.reduce((a, b) => a + b, 0) / vals.latencies.length)
        : 0,
      avgTPS: vals.tps.length
        ? Math.round(vals.tps.reduce((a, b) => a + b, 0) / vals.tps.length * 10) / 10
        : 0,
    }));
  }, [status.results, historicalResults]);

  // Build per-prompt comparison table
  const promptTable = useMemo(() => {
    const data = status.results?.length ? status.results : historicalResults;
    if (!data?.length) return [];
    const byPrompt = {};
    data.forEach(r => {
      if (!byPrompt[r.prompt_id]) byPrompt[r.prompt_id] = { text: r.prompt_text, backends: {} };
      byPrompt[r.prompt_id].backends[r.backend] = {
        latency: Math.round(r.latency_ms),
        tps: r.tokens_per_sec,
      };
    });
    return Object.values(byPrompt);
  }, [status.results, historicalResults]);

  const cpuState = current?.state || 'green';

  return (
    <div className="benchmark-dashboard">
      {/* ── Header ─────────────────────────────── */}
      <div className="bench-header">
        <div className="bench-header-left">
          <h2>⚡ Performance Dashboard</h2>
          <span className="bench-subtitle">OpenVINO INT8 · Live System Metrics · Inference Benchmarks</span>
        </div>
        <div className="bench-header-actions">
          <button
            className={`bench-btn bench-btn-primary ${status.running ? 'disabled' : ''}`}
            onClick={runBenchmark}
            disabled={status.running}
          >
            {status.running ? `Running... ${status.progress}%` : '▶ Run Benchmark'}
          </button>
          <button className="bench-btn bench-btn-secondary" onClick={exportCSV}>
            ↓ Export CSV
          </button>
        </div>
      </div>

      {/* ── Progress bar (when running) ─────────── */}
      {status.running && (
        <div className="bench-progress-bar">
          <div className="bench-progress-fill" style={{ width: `${status.progress}%` }} />
          <span className="bench-progress-label">
            Step {status.current_step}/{status.total_steps} · {status.current_backend} · {status.current_prompt}
          </span>
        </div>
      )}

      {/* ── Top row: Live gauges ────────────────── */}
      <div className="bench-grid-2">
        {/* CPU Gauge */}
        <div className="bench-card">
          <div className="bench-card-header">
            <span>CPU Usage</span>
            <span className={`state-badge state-${cpuState}`}>
              {cpuState.toUpperCase()}
            </span>
          </div>
          <div className="gauge-row">
            <div className="circular-gauge">
              <svg viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="50" fill="none" stroke="var(--bg-elevated)" strokeWidth="10" />
                <circle
                  cx="60" cy="60" r="50" fill="none"
                  stroke={STATE_COLORS[cpuState]}
                  strokeWidth="10"
                  strokeDasharray={`${(current?.cpu || 0) * 3.14} 314`}
                  strokeLinecap="round"
                  transform="rotate(-90 60 60)"
                  style={{ transition: 'stroke-dasharray 0.5s ease' }}
                />
                <text x="60" y="65" textAnchor="middle" className="gauge-text">
                  {Math.round(current?.cpu || 0)}%
                </text>
              </svg>
            </div>
            <div className="sparkline-container">
              <ResponsiveContainer width="100%" height={60}>
                <AreaChart data={cpuSparkline}>
                  <Area
                    type="monotone" dataKey="cpu"
                    stroke={STATE_COLORS[cpuState]} fill={STATE_COLORS[cpuState]}
                    fillOpacity={0.15} strokeWidth={1.5} dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
              <span className="sparkline-label">Last 60 readings</span>
            </div>
          </div>
          {/* Per-core bars */}
          {current?.cpu_per_core?.length > 0 && (
            <div className="core-bars">
              {current.cpu_per_core.map((val, i) => (
                <div key={i} className="core-bar-item">
                  <div className="core-bar-track">
                    <div
                      className="core-bar-fill"
                      style={{
                        width: `${val}%`,
                        background: val > 75 ? STATE_COLORS.red : val > 50 ? STATE_COLORS.yellow : STATE_COLORS.green,
                      }}
                    />
                  </div>
                  <span className="core-label">C{i}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* RAM Gauge */}
        <div className="bench-card">
          <div className="bench-card-header">
            <span>RAM Usage</span>
            <span className="ram-detail">
              {current?.ram_used_gb || 0} / {current?.ram_total_gb || 0} GB
            </span>
          </div>
          <div className="gauge-row">
            <div className="circular-gauge">
              <svg viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="50" fill="none" stroke="var(--bg-elevated)" strokeWidth="10" />
                <circle
                  cx="60" cy="60" r="50" fill="none"
                  stroke={current?.ram_percent > 75 ? STATE_COLORS.red : current?.ram_percent > 50 ? STATE_COLORS.yellow : STATE_COLORS.green}
                  strokeWidth="10"
                  strokeDasharray={`${(current?.ram || current?.ram_percent || 0) * 3.14} 314`}
                  strokeLinecap="round"
                  transform="rotate(-90 60 60)"
                  style={{ transition: 'stroke-dasharray 0.5s ease' }}
                />
                <text x="60" y="65" textAnchor="middle" className="gauge-text">
                  {Math.round(current?.ram || 0)}%
                </text>
              </svg>
            </div>
            <div className="sparkline-container">
              <ResponsiveContainer width="100%" height={60}>
                <AreaChart data={ramSparkline}>
                  <Area
                    type="monotone" dataKey="ram"
                    stroke="#8b5cf6" fill="#8b5cf6"
                    fillOpacity={0.15} strokeWidth={1.5} dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
              <span className="sparkline-label">Last 60 readings</span>
            </div>
          </div>
          <div className="ram-bar-track">
            <div
              className="ram-bar-fill"
              style={{ width: `${current?.ram || 0}%` }}
            />
            <span className="ram-bar-label">
              {current?.ram_available_gb || 0} GB available
            </span>
          </div>
        </div>
      </div>

      {/* ── Middle row: Latency comparison + Session stats ── */}
      <div className="bench-grid-2">
        {/* Latency comparison bar chart */}
        <div className="bench-card">
          <div className="bench-card-header">
            <span>Avg Latency by Backend (ms)</span>
          </div>
          {latencyComparison.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={latencyComparison} layout="vertical">
                <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
                <YAxis type="category" dataKey="backend" width={120} stroke="var(--text-muted)" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="avgLatency" radius={[0, 6, 6, 0]}>
                  {latencyComparison.map((entry, i) => (
                    <Cell key={i} fill={BACKEND_COLORS[entry.key] || '#666'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="bench-empty">Run a benchmark to see latency comparison</div>
          )}
        </div>

        {/* Tokens per second chart */}
        <div className="bench-card">
          <div className="bench-card-header">
            <span>Tokens / Second by Backend</span>
          </div>
          {latencyComparison.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={latencyComparison} layout="vertical">
                <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
                <YAxis type="category" dataKey="backend" width={120} stroke="var(--text-muted)" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="avgTPS" radius={[0, 6, 6, 0]}>
                  {latencyComparison.map((entry, i) => (
                    <Cell key={i} fill={BACKEND_COLORS[entry.key] || '#666'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="bench-empty">Run a benchmark to see throughput comparison</div>
          )}
        </div>
      </div>

      {/* ── Bottom: Prompt comparison table ─────── */}
      {promptTable.length > 0 && (
        <div className="bench-card bench-card-wide">
          <div className="bench-card-header">
            <span>Per-Prompt Results</span>
          </div>
          <div className="bench-table-wrapper">
            <table className="bench-table">
              <thead>
                <tr>
                  <th>Prompt</th>
                  <th>Local (ms)</th>
                  <th>Groq (ms)</th>
                  <th>Gemini (ms)</th>
                </tr>
              </thead>
              <tbody>
                {promptTable.map((row, i) => (
                  <tr key={i}>
                    <td className="prompt-cell">{row.text?.substring(0, 60)}...</td>
                    <td className="latency-cell local">
                      {row.backends.local_ollama?.latency ?? '—'}
                    </td>
                    <td className="latency-cell cloud">
                      {row.backends.cloud_groq?.latency ?? '—'}
                    </td>
                    <td className="latency-cell cloud">
                      {row.backends.cloud_gemini?.latency ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
