import React from 'react';

export default function MasteryBar({ score = 50, topicName, decayInfo }) {
  const clampedScore = Math.max(0, Math.min(100, Math.round(score)));
  
  let color = '#10B981'; // green
  let status = '🟢 Mastered';
  if (clampedScore < 50) {
    color = '#EF4444'; // red
    status = '🔴 Critical Focus';
  } else if (clampedScore < 65) {
    color = '#F59E0B'; // amber/orange
    status = '🟠 Needs Review';
  } else if (clampedScore < 80) {
    color = '#6366F1'; // blue/indigo
    status = '🟡 Reinforcing';
  }

  return (
    <div style={{ marginBottom: '0.85rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontWeight: 500, fontSize: '0.95rem' }}>{topicName}</span>
          {decayInfo?.is_decayed && (
            <span className="badge badge-warning" title={`Score decayed by ${decayInfo.decay_amount}% over ${decayInfo.days_elapsed} days`}>
              ⏳ Stale (-{decayInfo.decay_amount}%)
            </span>
          )}
        </div>
        <span style={{ fontWeight: 600, fontSize: '0.92rem', color }}>
          {clampedScore}% <span style={{ fontWeight: 400, fontSize: '0.8rem', color: '#64748B' }}>({status})</span>
        </span>
      </div>
      <div className="meter-container">
        <div className="meter-fill" style={{ width: `${clampedScore}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}
