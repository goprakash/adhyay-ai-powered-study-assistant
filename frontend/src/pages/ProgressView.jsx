import React, { useState, useEffect } from 'react';
import { api } from '../api';
import MasteryBar from '../components/MasteryBar';

export default function ProgressView({
  activeNotebook,
  user,
  onNavigate
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('recs'); // 'recs', 'health', 'graph', 'history'

  useEffect(() => {
    if (activeNotebook?.id) {
      loadProgress(activeNotebook.id);
    }
  }, [activeNotebook?.id]);

  async function loadProgress(nbId) {
    setLoading(true);
    try {
      const res = await api.getProgress(nbId, user.id);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="card"><p className="subdued">Loading learning analytics...</p></div>;
  }

  const recs = data?.recommendations || [];
  const topics = data?.topics || [];
  const prereqs = data?.prerequisites || [];

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.85rem', marginBottom: '0.2rem' }}>📊 Analytics & Study Recommendations</h1>
        <p className="subdued">{activeNotebook?.subject_name} — Cognitive modeling, memory decay, and prerequisite traversal.</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '0.5rem' }}>
        {[
          { id: 'recs', label: 'What to Study Next' },
          { id: 'health', label: 'Knowledge Health & Decay' },
          { id: 'graph', label: 'Prerequisite Graph' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className="btn"
            style={{
              fontWeight: activeTab === t.id ? 600 : 500,
              backgroundColor: activeTab === t.id ? '#0D9488' : '#FFFFFF',
              color: activeTab === t.id ? '#FFFFFF' : '#334155',
              borderColor: activeTab === t.id ? '#0D9488' : '#CBD5E1'
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB 1: RECOMMENDATIONS */}
      {activeTab === 'recs' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p className="subdued">
            Adhyay recommends targeted revision from topics you have actually answered incorrectly.
          </p>

          {recs.map((rec, idx) => {
            const isCritical = rec.effective_score < 50;
            const borderCol = isCritical ? '#EF4444' : rec.effective_score < 65 ? '#F59E0B' : '#10B981';
            return (
              <div
                key={rec.topic_id}
                className="card"
                style={{
                  borderLeft: `5px solid ${borderCol}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '1rem'
                }}
              >
                <div style={{ flex: 1, minWidth: '260px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.15rem' }}>#{idx + 1}. {rec.topic_name}</h3>
                    <span style={{ fontWeight: 700, fontSize: '1.05rem', color: borderCol }}>
                      {Math.round(rec.effective_score)}%
                    </span>
                  </div>
                  <p style={{ margin: '0 0 0.4rem 0', color: '#334155', fontSize: '0.92rem' }}>
                    <strong>Why study this:</strong> {rec.primary_reason}
                  </p>
                  {rec.downstream_weak?.length > 0 && (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: '#DC2626' }}>
                      ⚠️ <strong>Prerequisite blocker:</strong> Essential for {rec.downstream_weak.join(', ')}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => onNavigate('study', { topicId: rec.topic_id })}
                    className="btn btn-primary"
                    style={{ fontSize: '0.85rem' }}
                  >
                    Study Concept
                  </button>
                  <button
                    onClick={() => onNavigate('quiz', { topicId: rec.topic_id })}
                    className="btn"
                    style={{ fontSize: '0.85rem' }}
                  >
                    Take Quiz
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB 2: HEALTH & DECAY */}
      {activeTab === 'health' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '1.5rem' }}>
          <div className="card">
            <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem' }}>Concept Retention Health</h3>
            {topics.map(t => (
              <MasteryBar
                key={t.topic_id}
                score={t.effective_score}
                topicName={t.topic_name}
                decayInfo={t.decay_info}
              />
            ))}
          </div>

          <div className="card">
            <h4 style={{ marginBottom: '0.8rem' }}>Focus Distribution</h4>
            <ul style={{ listStyle: 'none', lineHeight: '2', fontSize: '0.9rem' }}>
              <li>🔴 <strong>Critical Focus (&lt;50%):</strong> {topics.filter(t => t.effective_score < 50).length} topics</li>
              <li>🟠 <strong>Needs Review (50-65%):</strong> {topics.filter(t => t.effective_score >= 50 && t.effective_score < 65).length} topics</li>
              <li>🟡 <strong>Reinforcing (65-80%):</strong> {topics.filter(t => t.effective_score >= 65 && t.effective_score < 80).length} topics</li>
              <li>🟢 <strong>Mastered (&gt;80%):</strong> {topics.filter(t => t.effective_score >= 80).length} topics</li>
            </ul>
          </div>
        </div>
      )}

      {/* TAB 3: PREREQUISITE GRAPH */}
      {activeTab === 'graph' && (
        <div className="card">
          <h3 style={{ fontSize: '1.15rem', marginBottom: '0.6rem' }}>Prerequisite Relationships</h3>
          <p className="subdued" style={{ marginBottom: '1rem' }}>
            Downstream concepts require upstream foundations. Fixing prerequisites first yields faster mastery.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {prereqs.length ? (
              prereqs.map((p, idx) => (
                <div key={idx} style={{ padding: '0.75rem 1rem', background: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontWeight: 600, color: '#0F172A' }}>{p.prereq_name}</span>
                  <span style={{ color: '#0D9488' }}>➔ prerequisite for ➔</span>
                  <span style={{ fontWeight: 600, color: '#0F172A' }}>{p.topic_name}</span>
                </div>
              ))
            ) : (
              <p className="subdued">No prerequisites defined for this notebook.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
