import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function RevisionView({
  activeNotebook,
  user
}) {
  const [topics, setTopics] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [activeTab, setActiveTab] = useState('flashcards'); // 'flashcards', 'cheatsheet'

  // Flashcards state
  const [flashcards, setFlashcards] = useState([]);
  const [cardIndex, setCardIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [loadingCards, setLoadingCards] = useState(false);

  // Cheat-Sheet state
  const [cheatSheetText, setCheatSheetText] = useState('');
  const [loadingSheet, setLoadingSheet] = useState(false);

  useEffect(() => {
    if (activeNotebook?.id) {
      loadTopics(activeNotebook.id);
    }
  }, [activeNotebook?.id]);

  useEffect(() => {
    if (selectedTopicId) {
      loadFlashcards(selectedTopicId);
    }
  }, [selectedTopicId]);

  async function loadTopics(nbId) {
    try {
      const data = await api.getTopics(nbId, user.id);
      setTopics(data.topics || []);
      if (data.topics?.length) {
        setSelectedTopicId(data.topics[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function loadFlashcards(topicId) {
    setLoadingCards(true);
    setRevealed(false);
    setCardIndex(0);
    try {
      const res = await api.getFlashcards(topicId);
      setFlashcards(res.flashcards || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCards(false);
    }
  }

  async function handleGenerateCheatSheet() {
    if (!activeNotebook?.id) return;
    setLoadingSheet(true);
    try {
      const res = await api.getCheatSheet(activeNotebook.id, user.id);
      setCheatSheetText(res.cheat_sheet || '');
    } catch (err) {
      alert(err.message || 'Error generating cheat sheet');
    } finally {
      setLoadingSheet(false);
    }
  }

  function handleDownloadCheatSheet() {
    const blob = new Blob([cheatSheetText], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeNotebook.subject_name.replace(/\s+/g, '_')}_Exam_CheatSheet.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const curCard = flashcards[cardIndex];

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.85rem', marginBottom: '0.2rem' }}>⚡ Quick Revision Tools</h1>
        <p className="subdued">{activeNotebook?.subject_name} — Active recall flashcards and targeted Exam Cheat-Sheets.</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '0.5rem' }}>
        <button
          onClick={() => setActiveTab('flashcards')}
          className="btn"
          style={{
            fontWeight: activeTab === 'flashcards' ? 600 : 500,
            backgroundColor: activeTab === 'flashcards' ? '#0D9488' : '#FFFFFF',
            color: activeTab === 'flashcards' ? '#FFFFFF' : '#334155',
            borderColor: activeTab === 'flashcards' ? '#0D9488' : '#CBD5E1'
          }}
        >
          🗂️ Concept Flashcards
        </button>
        <button
          onClick={() => setActiveTab('cheatsheet')}
          className="btn"
          style={{
            fontWeight: activeTab === 'cheatsheet' ? 600 : 500,
            backgroundColor: activeTab === 'cheatsheet' ? '#0D9488' : '#FFFFFF',
            color: activeTab === 'cheatsheet' ? '#FFFFFF' : '#334155',
            borderColor: activeTab === 'cheatsheet' ? '#0D9488' : '#CBD5E1'
          }}
        >
          📝 Personalized Exam Cheat-Sheet
        </button>
      </div>

      {/* FLASHCARDS */}
      {activeTab === 'flashcards' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Filter by Concept:</span>
            <select
              value={selectedTopicId || ''}
              onChange={(e) => setSelectedTopicId(Number(e.target.value))}
              style={{ width: 'auto', fontWeight: 600 }}
            >
              {topics.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>

          {loadingCards ? (
            <div className="card"><p className="subdued">Loading flashcards...</p></div>
          ) : !flashcards.length ? (
            <div className="card"><p className="subdued">No flashcards available for this topic.</p></div>
          ) : (
            <div>
              <div style={{ textAlign: 'center', fontWeight: 600, color: '#64748B', fontSize: '0.9rem' }}>
                Card {cardIndex + 1} of {flashcards.length}
              </div>

              {/* Flashcard Box */}
              <div
                className="flashcard-box"
                onClick={() => setRevealed(!revealed)}
                style={{
                  cursor: 'pointer',
                  borderColor: revealed ? '#0D9488' : '#CBD5E1',
                  backgroundColor: revealed ? '#F0FDFA' : '#FFFFFF',
                  transition: 'all 0.2s ease'
                }}
              >
                {!revealed ? (
                  <>
                    <span style={{ fontSize: '0.8rem', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Concept Question
                    </span>
                    <h3 style={{ margin: '1rem 0', color: '#1E293B', fontWeight: 600, fontSize: '1.25rem' }}>
                      {curCard?.question}
                    </h3>
                    <span style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
                      Click to reveal answer
                    </span>
                  </>
                ) : (
                  <>
                    <span style={{ fontSize: '0.8rem', color: '#0D9488', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                      Answer
                    </span>
                    <h3 style={{ margin: '1rem 0', color: '#0F172A', fontWeight: 600, fontSize: '1.2rem' }}>
                      {curCard?.answer}
                    </h3>
                    <span style={{ fontSize: '0.82rem', color: '#64748B' }}>
                      Q: {curCard?.question}
                    </span>
                  </>
                )}
              </div>

              {/* Controls */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
                <button
                  onClick={() => { setCardIndex(prev => Math.max(0, prev - 1)); setRevealed(false); }}
                  disabled={cardIndex === 0}
                  className="btn"
                >
                  ⬅️ Previous
                </button>
                <button
                  onClick={() => setRevealed(!revealed)}
                  className="btn btn-primary"
                  style={{ minWidth: '150px' }}
                >
                  {revealed ? '🔄 Hide Answer' : '👁️ Reveal Answer'}
                </button>
                <button
                  onClick={() => { setCardIndex(prev => Math.min(flashcards.length - 1, prev + 1)); setRevealed(false); }}
                  disabled={cardIndex >= flashcards.length - 1}
                  className="btn"
                >
                  Next ➡️
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* EXAM CHEAT-SHEET */}
      {activeTab === 'cheatsheet' && (
        <div>
          <div className="card">
            <h3 style={{ fontSize: '1.15rem', marginBottom: '0.4rem' }}>Personalized Revision Sheet</h3>
            <p className="subdued" style={{ marginBottom: '1.2rem' }}>
              Adhyay generates a concise revision sheet that prioritizes your **weakest concepts** first.
            </p>

            <button
              onClick={handleGenerateCheatSheet}
              className="btn btn-primary"
              disabled={loadingSheet}
              style={{ width: '100%', padding: '0.75rem', marginBottom: '1rem' }}
            >
              {loadingSheet ? 'Compiling high-yield revision points...' : '⚡ Generate Focused Exam Cheat-Sheet'}
            </button>

            {cheatSheetText && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
                  <button onClick={handleDownloadCheatSheet} className="btn" style={{ fontSize: '0.85rem' }}>
                    📥 Download Markdown Cheat-Sheet
                  </button>
                </div>
                <div style={{
                  padding: '1.5rem',
                  background: '#F8FAFC',
                  borderRadius: '10px',
                  border: '1px solid #E2E8F0',
                  whiteSpace: 'pre-wrap',
                  fontSize: '0.94rem',
                  lineHeight: '1.65'
                }}>
                  {cheatSheetText}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
