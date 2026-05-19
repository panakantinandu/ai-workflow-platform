import React, { useEffect, useRef } from 'react';

function formatDate(d) {
  if (!d) return '—';
  const dt = new Date(d);
  return isNaN(dt) ? d : dt.toLocaleString();
}

function formatType(t) {
  if (!t) return '—';
  return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function parseResult(raw) {
  if (raw === null || raw === undefined) return null;
  if (typeof raw === 'object') return raw;
  try {
    const p = JSON.parse(raw);
    return typeof p === 'string' ? JSON.parse(p) : p;
  } catch { return undefined; }
}

/* ── Canvas score gauge ── */
function ScoreGauge({ score }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c || score == null) return;
    const ctx = c.getContext('2d');
    const W = c.width, H = c.height;
    const cx = W / 2, cy = H * 0.72, r = W * 0.36;
    const start = Math.PI, end = 2 * Math.PI;
    const arc = start + (score / 100) * Math.PI;
    const color = score >= 70 ? '#10b981' : score < 60 ? '#ef4444' : '#f59e0b';

    ctx.clearRect(0, 0, W, H);

    // track
    ctx.beginPath();
    ctx.arc(cx, cy, r, start, end);
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 14;
    ctx.lineCap = 'round';
    ctx.stroke();

    // glow behind fill
    ctx.shadowBlur = 18;
    ctx.shadowColor = color;

    // fill
    const g = ctx.createLinearGradient(cx - r, cy, cx + r, cy);
    g.addColorStop(0, color + '70');
    g.addColorStop(1, color);
    ctx.beginPath();
    ctx.arc(cx, cy, r, start, arc);
    ctx.strokeStyle = g;
    ctx.lineWidth = 14;
    ctx.lineCap = 'round';
    ctx.stroke();
    ctx.shadowBlur = 0;

    // score number
    ctx.fillStyle = '#f1f5f9';
    ctx.font = `bold ${W * 0.24}px -apple-system,sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(score, cx, cy - 6);

    // label
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.font = `${W * 0.085}px -apple-system,sans-serif`;
    ctx.fillText('SCORE', cx, cy + 20);
  }, [score]);

  if (score == null) return null;
  return <canvas ref={ref} width={180} height={110} className="gauge-canvas" />;
}

function SeverityBadge({ sev }) {
  if (!sev) return null;
  const map = { high: ['sev-h', '🔴'], medium: ['sev-m', '🟡'], low: ['sev-l', '🟢'] };
  const [cls, icon] = map[(sev || '').toLowerCase()] || ['sev-x', '⚪'];
  return <span className={`sev-badge ${cls}`}>{icon} {sev}</span>;
}

function Section({ title, children }) {
  return (
    <div className="det-section">
      <div className="det-sec-hdr">
        <span className="det-sec-title">{title}</span>
        <div className="det-sec-line" />
      </div>
      <div className="det-sec-body">{children}</div>
    </div>
  );
}

function Row({ label, value, mono }) {
  if (value == null || value === '') return null;
  return (
    <div className="det-row">
      <span className="det-lbl">{label}</span>
      <span className={`det-val ${mono ? 'mono' : ''}`}>{String(value)}</span>
    </div>
  );
}

function StatusChip({ status }) {
  const map = {
    completed: 'dsc-green',
    failed:    'dsc-red',
    queued:    'dsc-yellow',
    running:   'dsc-blue',
  };
  const cls = map[(status || '').toLowerCase()] || '';
  return (
    <span className={`det-status-chip ${cls}`}>
      <span className="s-dot" />{status}
    </span>
  );
}

export default function TaskDetail({ task, onClose }) {
  const result = parseResult(task.result);
  const analysis   = result?.analysis ?? {};
  const rootCause  = analysis.root_cause ?? analysis.rootCause ?? null;
  const severity   = analysis.severity ?? null;
  const rec        = result?.recommendation ?? null;
  const evalObj    = result?.evaluation ?? {};
  const score      = evalObj.score ?? result?.evaluation_score ?? result?.score ?? null;
  const confidence = evalObj.confidence ?? null;
  const issues     = evalObj.issues ?? [];

  const knownKeys = new Set(['analysis','recommendation','evaluation','evaluation_score','score']);
  const extra = result ? Object.entries(result).filter(([k]) => !knownKeys.has(k)) : [];

  return (
    <div className="task-detail">

      {/* ── Detail header ── */}
      <div className="det-header">
        <div className="det-title-row">
          <div className="det-id">Task <span className="det-id-num">#{task.id}</span></div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="det-badges">
          <StatusChip status={task.status} />
          <span className="det-type-tag">{formatType(task.task_type)}</span>
        </div>
        <div className="det-created">
          <span className="det-clock">🕐</span>{formatDate(task.created_at)}
        </div>
      </div>

      {/* ── Score gauge ── */}
      {score != null && (
        <div className="gauge-section">
          <ScoreGauge score={Number(score)} />
          {confidence && (
            <div className="confidence-row">
              <span className="conf-lbl">Confidence</span>
              <span className={`conf-badge ${confidence.toLowerCase() === 'high' ? 'conf-h' : 'conf-m'}`}>
                {confidence}
              </span>
            </div>
          )}
        </div>
      )}

      {/* ── Parse error ── */}
      {result === undefined && (
        <Section title="Result">
          <p className="parse-err">⚠ Could not parse JSON result.</p>
          <pre className="raw-pre">{task.result}</pre>
        </Section>
      )}

      {/* ── No result ── */}
      {result === null && (
        <Section title="Result">
          <p className="no-data">No result data available yet.</p>
        </Section>
      )}

      {/* ── Full result ── */}
      {result && result !== undefined && (
        <>
          {(rootCause || severity) && (
            <Section title="Analysis">
              {severity && (
                <div className="det-row">
                  <span className="det-lbl">Severity</span>
                  <SeverityBadge sev={severity} />
                </div>
              )}
              {rootCause && (
                <div className="det-row root-row">
                  <span className="det-lbl">Root Cause</span>
                  <span className="root-text">{rootCause}</span>
                </div>
              )}
              {Object.entries(analysis)
                .filter(([k]) => !['root_cause','rootCause','severity'].includes(k))
                .map(([k, v]) => (
                  <Row key={k} label={k} value={typeof v === 'object' ? JSON.stringify(v) : v} />
                ))}
            </Section>
          )}

          {rec && (
            <Section title="Recommendation">
              <div className="rec-box">
                <span className="rec-icon">💡</span>
                <p className="rec-text">{rec}</p>
              </div>
            </Section>
          )}

          {issues.length > 0 && (
            <Section title="Issues">
              {issues.map((iss, i) => (
                <div key={i} className="issue-row">
                  <span className="issue-dot" />{String(iss)}
                </div>
              ))}
            </Section>
          )}

          {extra.length > 0 && (
            <Section title="Other Data">
              {extra.map(([k, v]) => (
                <Row key={k} label={k} value={typeof v === 'object' ? JSON.stringify(v, null, 2) : v} mono />
              ))}
            </Section>
          )}
        </>
      )}
    </div>
  );
}
