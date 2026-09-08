import React from 'react';

export default function Navbar({
  activeTab,
  setActiveTab,
  notebooks = [],
  activeNotebookId,
  setActiveNotebookId,
  user,
  onLogout
}) {
  return (
    <header style={{
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid #E2E8F0',
      position: 'sticky',
      top: 0,
      zIndex: 40,
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.02)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0.75rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.8rem'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            backgroundColor: '#0D9488',
            color: '#FFFFFF',
            width: '36px',
            height: '36px',
            borderRadius: '9px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem',
            fontWeight: 700
          }}>
            📖
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: '#0F172A', lineHeight: 1.1 }}>Adhyay</h2>
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Personalized AI Study Assistant</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
          {[
            { id: 'dashboard', label: '🏠 Dashboard' },
            { id: 'notebooks', label: '📚 Notebooks' },
            { id: 'study', label: '📝 Study Topics' },
            { id: 'quiz', label: '🎯 Adaptive Quiz' },
            { id: 'progress', label: '📊 Progress & Plan' },
            { id: 'revision', label: '⚡ Revision Tools' },
          ].map(tab => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '0.45rem 0.85rem',
                  borderRadius: '8px',
                  fontSize: '0.88rem',
                  fontWeight: isActive ? 600 : 500,
                  border: 'none',
                  backgroundColor: isActive ? '#F0FDFA' : 'transparent',
                  color: isActive ? '#0D9488' : '#475569',
                  transition: 'all 0.15s ease'
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Right Section: Active Subject Switcher & Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {notebooks.length > 0 && (
            <select
              value={activeNotebookId || ''}
              onChange={(e) => setActiveNotebookId(Number(e.target.value))}
              style={{
                width: 'auto',
                padding: '0.4rem 0.75rem',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: '#0D9488',
                backgroundColor: '#F0FDFA',
                borderColor: '#CCFBF1',
                borderRadius: '8px'
              }}
            >
              {notebooks.map(nb => (
                <option key={nb.id} value={nb.id}>
                  📖 {nb.subject_name}
                </option>
              ))}
            </select>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.82rem', color: '#475569', fontWeight: 500 }}>
              👤 {user?.name || 'Student'}
            </span>
            <button
              onClick={onLogout}
              className="btn"
              style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
              title="Sign Out"
            >
              🚪 Sign Out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}