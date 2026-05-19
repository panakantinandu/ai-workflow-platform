import React from 'react';

export default function StatCard({ label, value, icon, accent, flash }) {
  return (
    <div className={`stat-card ${flash ? 'stat-flash' : ''}`} style={{ '--acc': accent }}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-info">
        <span className="stat-val">{value}</span>
        <span className="stat-lbl">{label}</span>
      </div>
      <div className="stat-glow" />
    </div>
  );
}
