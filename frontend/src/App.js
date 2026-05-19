import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import TaskDetail from './components/TaskDetail';
import StatCard from './components/StatCard';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const REFRESH_MS = 5000;
const LIMIT = 20;

function parseResultQuick(raw) {
  if (!raw) return null;
  if (typeof raw === 'object') return raw;
  try {
    const p = JSON.parse(raw);
    return typeof p === 'string' ? JSON.parse(p) : p;
  } catch { return null; }
}

function statusCls(s) {
  const v = (s || '').toLowerCase();
  if (v === 'completed') return 'status-completed';
  if (v === 'failed')    return 'status-failed';
  if (v === 'running')   return 'status-running';
  return 'status-queued';
}

function formatDate(d) {
  if (!d) return '—';
  const dt = new Date(d);
  return isNaN(dt) ? d : dt.toLocaleString();
}

function ScorePill({ score }) {
  if (score == null) return <span className="score-nil">—</span>;
  const n = Number(score);
  const c = n >= 70 ? 'pill-green' : n < 60 ? 'pill-red' : 'pill-yellow';
  return <span className={`score-pill ${c}`}>{n}</span>;
}

function PulseDot({ color = '#10b981' }) {
  return <span className="pulse-wrap"><span className="pulse-ring" style={{ '--pc': color }} /><span className="pulse-core" style={{ background: color }} /></span>;
}

const FILTERS = ['all', 'completed', 'failed', 'queued'];

export default function App() {
  const [tasks,      setTasks]      = useState([]);
  const [totalTasks, setTotalTasks] = useState(0);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);
  const [selected,   setSelected]   = useState(null);
  const [filter,     setFilter]     = useState('all');
  const [refreshing, setRefreshing] = useState(false);
  const [lastAt,     setLastAt]     = useState(null);
  const [page,       setPage]       = useState(0);

  const fetchTasks = useCallback((silent = false) => {
    if (!silent) setRefreshing(true);
    axios.get(`${API_URL}/tasks?skip=${page * LIMIT}&limit=${LIMIT}`)
      .then(r => {
        setTasks(r.data.items || []);
        setTotalTasks(r.data.total || 0);
        setError(null);
        setLoading(false);
        setLastAt(new Date());
        if (!silent) setTimeout(() => setRefreshing(false), 500);
      })
      .catch(e => {
        const msg = e.message || 'API unreachable';
        setError(msg);
        toast.error(`Connection failed: ${msg}`);
        setLoading(false);
        setRefreshing(false);
      });
  }, [page]);

  useEffect(() => {
    fetchTasks();
    const t = setInterval(() => fetchTasks(true), REFRESH_MS);
    return () => clearInterval(t);
  }, [fetchTasks]);

  useEffect(() => {
    if (!selected) return;
    const u = tasks.find(t => t.id === selected.id);
    if (u) setSelected(u);
  }, [tasks]); // eslint-disable-line

  const stats = useMemo(() => {
    const completed = tasks.filter(t => t.status?.toLowerCase() === 'completed').length;
    const failed    = tasks.filter(t => t.status?.toLowerCase() === 'failed').length;
    const queued    = tasks.filter(t => t.status?.toLowerCase() === 'queued').length;
    const scores    = tasks
      .map(t => parseResultQuick(t.result)?.evaluation?.score)
      .filter(s => s != null)
      .map(Number);
    const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;
    return { total: totalTasks, completed, failed, queued, avg };
  }, [tasks, totalTasks]);

  const visible = useMemo(() =>
    filter === 'all' ? tasks : tasks.filter(t => (t.status || '').toLowerCase() === filter),
    [tasks, filter]);

  if (loading && tasks.length === 0) return (
    <div className="splash">
      <div className="splash-logo">⬡</div>
      <div className="splash-bars">
        {[0,1,2,3,4].map(i => <div key={i} className="splash-bar" style={{ '--i': i }} />)}
      </div>
      <p className="splash-txt">Connecting to task engine…</p>
    </div>
  );

  if (error && tasks.length === 0) return (
    <div className="splash splash-err">
      <div className="splash-err-icon">⚡</div>
      <h2>Connection Failed</h2>
      <p>{error}</p>
      <button className="retry-btn" onClick={() => fetchTasks()}>↺ Retry</button>
    </div>
  );

  return (
    <div className="app">
      <Toaster position="top-right" toastOptions={{ style: { background: '#1e293b', color: '#f8fafc' } }} />

      {/* ── Header ── */}
      <header className="app-header">
        <div className="hdr-left">
          <div className="logo">
            <span className="logo-hex">⬡</span>
            <span className="logo-name">AI<span className="logo-accent">Flow</span></span>
          </div>
          <span className="hdr-sep" />
          <span className="hdr-sub">Task Monitor</span>
        </div>
        <div className="hdr-right">
          <div className={`live-badge ${refreshing ? 'live-spin' : ''}`}>
            <PulseDot />
            <span>Live</span>
            {lastAt && <span className="live-time">{lastAt.toLocaleTimeString()}</span>}
          </div>
        </div>
      </header>

      {/* ── Stats ── */}
      <div className="stats-row">
        <StatCard label="Total (All time)" value={stats.total} icon="📋" accent="#6366f1" />
        <StatCard label="Completed (Page)" value={stats.completed} icon="✓"  accent="#10b981" />
        <StatCard label="Failed (Page)"    value={stats.failed}    icon="✕"  accent="#ef4444" flash={stats.failed > 0} />
        <StatCard label="Queued (Page)"    value={stats.queued}    icon="⏳" accent="#f59e0b" />
        <StatCard label="Avg Score (Page)" value={stats.avg ?? '—'} icon="★" accent="#00d4ff" />
      </div>

      {/* ── Filters ── */}
      <div className="filter-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {FILTERS.map(f => (
            <button
              key={f}
              className={`filter-pill ${filter === f ? 'pill-active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              <span className="pill-cnt">
                {f === 'all' ? tasks.length : tasks.filter(t => (t.status||'').toLowerCase() === f).length}
              </span>
            </button>
          ))}
        </div>
        <div className="pagination-controls" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button 
            disabled={page === 0} 
            onClick={() => setPage(p => Math.max(0, p - 1))}
            className="retry-btn" style={{ padding: '4px 12px', marginTop: 0 }}
          >
            ← Prev
          </button>
          <span style={{ fontSize: '12px', color: '#64748b' }}>Page {page + 1}</span>
          <button 
            disabled={(page + 1) * LIMIT >= totalTasks}
            onClick={() => setPage(p => p + 1)}
            className="retry-btn" style={{ padding: '4px 12px', marginTop: 0 }}
          >
            Next →
          </button>
        </div>
      </div>

      {/* ── Body ── */}
      <main className="app-body">
        <motion.section 
          className={`table-section ${selected ? 'tbl-shrink' : ''}`}
          layout
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        >
          <div className="tbl-wrap">
            <table className="task-table">
              <thead>
                <tr>
                  <th>ID</th><th>Task Type</th><th>Status</th><th>Score</th><th>Created</th>
                </tr>
              </thead>
              <motion.tbody layout>
                <AnimatePresence>
                  {visible.length === 0
                    ? <motion.tr key="empty" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}><td colSpan={5} className="tbl-empty">No tasks match this filter.</td></motion.tr>
                    : visible.map((task, i) => {
                        const res   = parseResultQuick(task.result);
                        const score = res?.evaluation?.score ?? res?.evaluation_score ?? null;
                        const isFail = (task.status||'').toLowerCase() === 'failed';
                        return (
                          <motion.tr
                            key={task.id}
                            layout
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            transition={{ duration: 0.2, delay: i * 0.03 }}
                            className={`task-row ${isFail ? 'row-fail' : ''} ${selected?.id === task.id ? 'row-active' : ''}`}
                            onClick={() => setSelected(selected?.id === task.id ? null : task)}
                            style={{ cursor: 'pointer' }}
                          >
                            <td><span className="task-id">#{task.id}</span></td>
                            <td><span className="type-chip">{task.task_type ?? '—'}</span></td>
                            <td>
                              <span className={`status-badge ${statusCls(task.status)}`}>
                                <span className="s-dot" />
                                {task.status ?? '—'}
                              </span>
                            </td>
                            <td><ScorePill score={score} /></td>
                            <td className="date-cell">{formatDate(task.created_at)}</td>
                          </motion.tr>
                        );
                      })
                  }
                </AnimatePresence>
              </motion.tbody>
            </table>
          </div>
        </motion.section>

        <AnimatePresence>
          {selected && (
            <TaskDetail task={selected} onClose={() => setSelected(null)} />
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
