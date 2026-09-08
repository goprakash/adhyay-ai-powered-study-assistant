import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import MasteryBar from '../components/MasteryBar';

export default function StudyView({
  activeNotebook,
  user,
  initialTopicId,
  onNavigateToQuiz
}) {
  const [topics, setTopics] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState(initialTopicId || null);
  const [topicDetail, setTopicDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  // Chatbot State
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [botTyping, setBotTyping] = useState(false);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    if (activeNotebook?.id) {
      loadTopics(activeNotebook.id);
    }
  }, [activeNotebook?.id]);

  useEffect(() => {
    if (selectedTopicId) {
      loadTopicDetail(selectedTopicId);
      // Reset chat greeting for the selected topic
      setChatMessages([
        { role: 'assistant', content: `Hello ${user?.name || 'there'}! I am your Adhyay tutor for this topic. Ask me any question, request a code example, or click one of the quick prompts below!` }
      ]);
    }
  }, [selectedTopicId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, botTyping]);

  async function loadTopics(nbId) {
    try {
      const data = await api.getTopics(nbId, user.id);
      setTopics(data.topics || []);
      if (data.topics?.length) {
        if (!selectedTopicId || !data.topics.some(t => t.id === selectedTopicId)) {
          setSelectedTopicId(data.topics[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function loadTopicDetail(topicId) {
    setLoadingDetail(true);
    try {
      const data = await api.getTopicDetail(topicId, user.id);
      setTopicDetail(data.topic);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetail(false);
    }
  }

  async function handleRegenerateSummary() {
    if (!selectedTopicId) return;
    setRegenerating(true);
    try {
      const res = await api.regenerateSummary(selectedTopicId);
      setTopicDetail(prev => ({ ...prev, summary: res.summary }));
    } catch (err) {
      alert(err.message || 'Error regenerating summary');
    } finally {
      setRegenerating(false);
    }
  }

  async function sendMessage(textToSend) {
    const query = textToSend || chatInput;
    if (!query.trim() || !selectedTopicId) return;

    const userMsg = { role: 'user', content: query };
    const updatedMessages = [...chatMessages, userMsg];
    setChatMessages(updatedMessages);
    setChatInput('');
    setBotTyping(true);

    try {
      const res = await api.sendTopicChat(selectedTopicId, query, updatedMessages);
      setChatMessages(prev => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error responding to your question.' }]);
    } finally {
      setBotTyping(false);
    }
  }

  if (!topics.length) {
    return (
      <div className="card">
        <h3>No topics found for {activeNotebook?.subject_name}</h3>
        <p className="subdued">Please upload notes in the Notebooks tab to generate structured topics.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Top Header & Topic Selector */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.2rem' }}>📝 Study & Concepts</h1>
          <p className="subdued">{activeNotebook?.subject_name} — Structured notes and grounded conversational AI tutor.</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <select
            value={selectedTopicId || ''}
            onChange={(e) => setSelectedTopicId(Number(e.target.value))}
            style={{ fontWeight: 600, minWidth: '220px' }}
          >
            {topics.map(t => (
              <option key={t.id} value={t.id}>📖 {t.name}</option>
            ))}
          </select>

          <button
            onClick={() => onNavigateToQuiz(selectedTopicId)}
            className="btn btn-primary"
            style={{ whiteSpace: 'nowrap' }}
          >
            🎯 Quiz on this Topic
          </button>
        </div>
      </div>

      {/* Mastery Status for this Topic */}
      {topicDetail && (
        <div style={{ marginBottom: '1.25rem' }}>
          <MasteryBar
            score={topicDetail.effective_score}
            topicName={`${topicDetail.name} Mastery`}
            decayInfo={topicDetail.decay_info}
          />
        </div>
      )}

      {/* Split Screen: Left = Structured Summary, Right = Working Grounded Chatbot */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: STRUCTURED SUMMARY */}
        <div className="card" style={{ minHeight: '600px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.2rem', margin: 0 }}>📘 Structured Summary</h3>
            <button
              onClick={handleRegenerateSummary}
              className="btn"
              disabled={regenerating}
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}
            >
              {regenerating ? 'Updating...' : '✨ Refresh AI Summary'}
            </button>
          </div>

          {loadingDetail ? (
            <p className="subdued">Loading concept notes...</p>
          ) : (
            <div className="prose" style={{ fontSize: '0.94rem', lineHeight: '1.65', color: '#334155' }}>
              <pre style={{
                whiteSpace: 'pre-wrap',
                fontFamily: 'inherit',
                background: 'transparent',
                color: 'inherit',
                padding: 0,
                fontSize: '0.94rem'
              }}>
                {topicDetail?.summary || 'No summary available for this concept.'}
              </pre>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: WORKING GROUNDED AI TUTOR */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '640px' }}>
          <div style={{ marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1.15rem', margin: 0 }}>💬 Grounded AI Tutor: {topicDetail?.name}</h3>
            <span className="subdued" style={{ fontSize: '0.82rem' }}>Answers strictly grounded in your lecture notes.</span>
          </div>

          {/* Quick Prompts Chips */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', marginBottom: '0.8rem' }}>
            <button
              onClick={() => sendMessage(`Show a clear code example for ${topicDetail?.name}`)}
              className="btn"
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.5rem', textAlign: 'left' }}
            >
              💡 Show Code Example
            </button>
            <button
              onClick={() => sendMessage(`What is the difference between ${topicDetail?.name} and related concepts?`)}
              className="btn"
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.5rem', textAlign: 'left' }}
            >
              ⚖️ Key Differences / vs
            </button>
            <button
              onClick={() => sendMessage(`What are the core rules and constraints for ${topicDetail?.name}?`)}
              className="btn"
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.5rem', textAlign: 'left' }}
            >
              ⚙️ Core Rules & Syntax
            </button>
            <button
              onClick={() => sendMessage(`What are the most common exam traps for ${topicDetail?.name}?`)}
              className="btn"
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.5rem', textAlign: 'left' }}
            >
              ⚠️ Common Exam Traps
            </button>
          </div>

          {/* Chat Messages Log */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '0.5rem',
            border: '1px solid #F1F5F9',
            borderRadius: '10px',
            backgroundColor: '#F8FAFC',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
            marginBottom: '0.8rem'
          }}>
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}
              >
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              </div>
            ))}
            {botTyping && (
              <div className="chat-bubble-bot" style={{ fontStyle: 'italic', color: '#64748B' }}>
                Adhyay tutor is thinking...
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Input Bar */}
          <form
            onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
            style={{ display: 'flex', gap: '0.5rem' }}
          >
            <input
              type="text"
              placeholder={`Ask anything about ${topicDetail?.name || 'this topic'}...`}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              style={{ flex: 1 }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!chatInput.trim() || botTyping}
            >
              Send
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
