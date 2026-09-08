import React, { useState, useEffect } from 'react';
import { api } from '../api';
import MasteryBar from '../components/MasteryBar';

export default function DashboardView({
  notebooks,
  activeNotebook,
  setActiveNotebookId,
  user,
  onNavigate
}) {
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (activeNotebook?.id) {
      loadProgress(activeNotebook.id);
    }
  }, [activeNotebook?.id]);

  async function loadProgress(nbId) {
    setLoading(true);
    try {
      const data = await api.getProgress(nbId, user.id);
      setProgressData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (!activeNotebook) {
    return <div className="card">Please select or create a subject notebook.</div>;
  }

  const topics = progressData?.topics || [];
  const recs = progressData?.recommendations || [];
  const avgMastery = topics.length
    ? Math.round(topics.reduce((acc, t) => acc + (t.effective_score || 0), 0) / topics.length)
    : 0;
  const weakTopics = topics.filter(t => (t.effective_score || 0) < 65);
  const topRec = recs[0];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.85rem', marginBottom: '0.2rem' }}>📖 {activeNotebook.subject_name}</h1>
        <p className="subdued">{activeNotebook.description || 'Continuous cognitive tracking and structured mastery.'}</p>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ padding: '1.2rem' }}>
          <span className="subdued" style={{ fontSize: '0.85rem' }}>Overall Subject Mastery</span>
          <h2 style={{ fontSize: '1.8rem', color: '#0D9488', margin: '0.3rem 0 0 0' }}>{avgMastery}%</h2>
        </div>
        <div className="card" style={{ padding: '1.2rem' }}>
          <span className="subdued" style={{ fontSize: '0.85rem' }}>Total Topics Organized</span>
          <h2 style={{ fontSize: '1.8rem', color: '#1E293B', margin: '0.3rem 0 0 0' }}>{topics.length}</h2>
        </div>
        <div className="card" style={{ padding: '1.2rem' }}>
          <span className="subdued" style={{ fontSize: '0.85rem' }}>Focus Areas Needed</span>
          <h2 style={{ fontSize: '1.8rem', color: weakTopics.length ? '#EF4444' : '#10B981', margin: '0.3rem 0 0 0' }}>
            {weakTopics.length}
          </h2>
        </div>
        <div className="card" style={{ padding: '1.2rem' }}>
          <span className="subdued" style={{ fontSize: '0.85rem' }}>Top Recommendation</span>
          <h3 style={{ fontSize: '1.2rem', color: '#0F172A', margin: '0.4rem 0 0 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {topRec ? topRec.topic_name : 'All Clear'}
          </h3>
        </div>
      </div>

      {/* Hero Recommendation Card: "What Should I Study Next?" */}
      {topRec && (
        <div className={topRec.effective_score < 50 ? 'weak-hero-card' : 'hero-card'}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span className={`badge ${topRec.effective_score < 50 ? 'badge-critical' : 'badge-progress'}`}>
              🎯 What Should I Study Next?
            </span>
            <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#1E293B' }}>
              Mastery: {Math.round(topRec.effective_score)}%
            </span>
          </div>

          <h3 style={{ marginTop: '0.6rem', marginBottom: '0.3rem', fontSize: '1.3rem' }}>
            Start with: <strong>{topRec.topic_name}</strong>
          </h3>

          <p style={{ color: '#334155', fontSize: '0.98rem', marginBottom: '1rem' }}>
            <strong>Pedagogical Reason:</strong> {topRec.primary_reason}
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => onNavigate('study', { topicId: topRec.topic_id })}
              className="btn btn-primary"
            >
              📝 Study Concept Notes
            </button>
            <button
              onClick={() => onNavigate('quiz', { topicId: topRec.topic_id })}
              className="btn"
              style={{ fontWeight: 600 }}
            >
              🎯 Take Adaptive Quiz
            </button>
          </div>
        </div>
      )}

      {/* Simultaneous Multi-Notebook Shelf */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', margin: 0 }}>📚 Your Subject Notebooks</h3>
            <span className="subdued">All notebooks coexist simultaneously. Click any subject to switch context:</span>
          </div>
          <button onClick={() => onNavigate('notebooks')} className="btn" style={{ fontSize: '0.85rem' }}>
            ➕ Manage Notebooks
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          {notebooks.map(nb => {
            const isActive = nb.id === activeNotebook.id;
            return (
              <div
                key={nb.id}
                onClick={() => !isActive && setActiveNotebookId(nb.id)}
                style={{
                  background: isActive ? '#F0FDFA' : '#FFFFFF',
                  border: isActive ? '2px solid #0D9488' : '1px solid #E2E8F0',
                  borderRadius: '12px',
                  padding: '1.2rem',
                  cursor: isActive ? 'default' : 'pointer',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: '#0F172A' }}>{nb.subject_name}</h4>
                  {isActive && <span className="badge badge-mastered">ACTIVE</span>}
                </div>
                <p style={{ fontSize: '0.85rem', color: '#64748B', margin: '0 0 0.75rem 0' }}>
                  {nb.topic_count || 0} topics • Avg Mastery: {nb.average_mastery || 0}%
                </p>
                {!isActive && (
                  <button className="btn" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                    Switch to this Subject
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Focus Areas & Cognitive Health */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '1.15rem', marginBottom: '0.4rem' }}>📊 Your Focus Areas & Knowledge Health</h3>
          <p className="subdued" style={{ marginBottom: '1.2rem' }}>Updated dynamically after every quiz attempt with confidence updates and decay.</p>

          {loading ? (
            <p className="subdued">Loading knowledge health...</p>
          ) : topics.length ? (
            topics.map(t => (
              <MasteryBar
                key={t.topic_id}
                score={t.effective_score}
                topicName={t.topic_name}
                decayInfo={t.decay_info}
              />
            ))
          ) : (
            <p className="subdued">No topics found. Upload lecture notes to begin.</p>
          )}
        </div>

        <div className="card" style={{ background: '#F8FAFC' }}>
          <h4 style={{ fontSize: '1.05rem', marginBottom: '0.6rem' }}>🧠 Cognitive Tracking Model</h4>
          <p style={{ fontSize: '0.9rem', color: '#475569', marginBottom: '0.8rem' }}>
            Unlike generic quiz apps, Adhyay pairs <strong>accuracy with confidence</strong>:
          </p>
          <ul style={{ fontSize: '0.85rem', color: '#334155', paddingLeft: '1.2rem', lineHeight: '1.6' }}>
            <li><strong>Correct + Confident:</strong> Strong mastery (+15%)</li>
            <li><strong>Correct + Guessed:</strong> Minimal update (+2%)</li>
            <li><strong>Wrong + Confident:</strong> Critical misconception penalty (-18%)</li>
            <li><strong>Decay:</strong> Stale topics lose retention over time (-1.5%/day)</li>
          </ul>
          <p style={{ fontSize: '0.82rem', color: '#64748B', marginTop: '0.8rem' }}>
            Prerequisite graph relationships ensure foundational concepts are reinforced first.
          </p>
        </div>
      </div>
    </div>
  );
}
