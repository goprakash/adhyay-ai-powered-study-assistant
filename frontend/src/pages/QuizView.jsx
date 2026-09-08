import React, { useState, useEffect } from 'react';
import { api } from '../api';
import MasteryBar from '../components/MasteryBar';

export default function QuizView({
  activeNotebook,
  user,
  initialTopicId
}) {
  const [topics, setTopics] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState(initialTopicId || null);
  const [topicDetail, setTopicDetail] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // Form State
  const [selectedOption, setSelectedOption] = useState('');
  const [confidence, setConfidence] = useState('Somewhat Sure'); // 'Guessed', 'Somewhat Sure', 'Confident'
  const [submitting, setSubmitting] = useState(false);
  const [lastSubmission, setLastSubmission] = useState(null);

  // Explain Mistake State
  const [explaining, setExplaining] = useState(false);
  const [diagnosticText, setDiagnosticText] = useState('');

  useEffect(() => {
    if (activeNotebook?.id) {
      loadTopics(activeNotebook.id);
    }
  }, [activeNotebook?.id]);

  useEffect(() => {
    if (selectedTopicId) {
      loadTopicData(selectedTopicId);
    }
  }, [selectedTopicId]);

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

  async function loadTopicData(topicId) {
    setLoadingQuestions(true);
    setLastSubmission(null);
    setDiagnosticText('');
    setSelectedOption('');
    try {
      const [tData, qData] = await Promise.all([
        api.getTopicDetail(topicId, user.id),
        api.getTopicQuiz(topicId)
      ]);
      setTopicDetail(tData.topic);
      setQuestions(qData.questions || []);
      setCurrentQIndex(0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingQuestions(false);
    }
  }

  async function handleGenerateQuestions() {
    if (!selectedTopicId) return;
    setLoadingQuestions(true);
    try {
      const data = await api.generateQuiz(selectedTopicId);
      setQuestions(data.questions || []);
      setCurrentQIndex(0);
    } catch (err) {
      alert(err.message || 'Failed to generate questions');
    } finally {
      setLoadingQuestions(false);
    }
  }

  async function handleSubmitAttempt(e) {
    e.preventDefault();
    if (!selectedOption) return;
    const curQ = questions[currentQIndex];
    if (!curQ) return;

    setSubmitting(true);
    try {
      const res = await api.submitQuizAttempt({
        user_id: user.id,
        question_id: curQ.id,
        topic_id: selectedTopicId,
        user_answer: selectedOption,
        confidence: confidence
      });

      setLastSubmission(res);

      // Update topic mastery score locally
      setTopicDetail(prev => ({
        ...prev,
        effective_score: res.new_score
      }));

      // If wrong, automatically fetch cognitive diagnostic
      if (!res.is_correct) {
        fetchDiagnostic(curQ.question, selectedOption, res.correct_answer);
      }
    } catch (err) {
      alert(err.message || 'Error evaluating attempt');
    } finally {
      setSubmitting(false);
    }
  }

  async function fetchDiagnostic(qText, studentAns, correctAns) {
    setExplaining(true);
    try {
      const data = await api.explainMistake({
        topic_id: selectedTopicId,
        question: qText,
        student_answer: studentAns,
        correct_answer: correctAns
      });
      setDiagnosticText(data.diagnostic);
    } catch (err) {
      setDiagnosticText('Could not load detailed diagnostic.');
    } finally {
      setExplaining(false);
    }
  }

  function handleNextQuestion() {
    setSelectedOption('');
    setLastSubmission(null);
    setDiagnosticText('');
    setCurrentQIndex(prev => (prev + 1) % questions.length);
  }

  const curQ = questions[currentQIndex];

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.2rem' }}>🎯 Adaptive Concept Quiz</h1>
          <p className="subdued">{activeNotebook?.subject_name} — Confidence-weighted learning & cognitive diagnostics.</p>
        </div>

        <select
          value={selectedTopicId || ''}
          onChange={(e) => setSelectedTopicId(Number(e.target.value))}
          style={{ fontWeight: 600, minWidth: '220px' }}
        >
          {topics.map(t => (
            <option key={t.id} value={t.id}>🎯 {t.name}</option>
          ))}
        </select>
      </div>

      {topicDetail && (
        <div style={{ marginBottom: '1.5rem' }}>
          <MasteryBar
            score={topicDetail.effective_score}
            topicName={`${topicDetail.name} Mastery`}
            decayInfo={topicDetail.decay_info}
          />
        </div>
      )}

      {loadingQuestions ? (
        <div className="card"><p className="subdued">Loading quiz questions...</p></div>
      ) : !questions.length ? (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }}>
          <h3>No questions saved yet for {topicDetail?.name}</h3>
          <p className="subdued" style={{ marginBottom: '1.2rem' }}>
            Generate adaptive multiple-choice questions grounded in your course notes.
          </p>
          <button onClick={handleGenerateQuestions} className="btn btn-primary">
            ✨ Generate AI Quiz Questions
          </button>
        </div>
      ) : (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
            <span style={{ fontWeight: 600, color: '#64748B', fontSize: '0.9rem' }}>
              Question {currentQIndex + 1} of {questions.length}
            </span>
          </div>

          {/* Question Box */}
          <div className="card" style={{ borderLeft: '4px solid #3B82F6', fontSize: '1.15rem', fontWeight: 500 }}>
            {curQ.question}
          </div>

          {/* Form */}
          <form onSubmit={handleSubmitAttempt} className="card">
            <div style={{ marginBottom: '1.5rem' }}>
              <span style={{ display: 'block', fontWeight: 600, marginBottom: '0.8rem', color: '#1E293B' }}>
                Select Your Answer:
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {curQ.options.map((opt, idx) => {
                  const isChecked = selectedOption === opt;
                  return (
                    <label
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        padding: '0.85rem 1rem',
                        borderRadius: '10px',
                        border: isChecked ? '2px solid #0D9488' : '1px solid #E2E8F0',
                        background: isChecked ? '#F0FDFA' : '#FFFFFF',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <input
                        type="radio"
                        name="quiz_option"
                        value={opt}
                        checked={isChecked}
                        onChange={() => setSelectedOption(opt)}
                        disabled={!!lastSubmission}
                        style={{ width: 'auto' }}
                      />
                      <span style={{ fontSize: '0.95rem', color: '#1E293B', fontWeight: isChecked ? 600 : 400 }}>
                        {opt}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Confidence Selector */}
            <div style={{ marginBottom: '1.5rem', background: '#F8FAFC', padding: '1rem', borderRadius: '10px' }}>
              <span style={{ display: 'block', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.3rem', color: '#1E293B' }}>
                How confident are you in this answer?
              </span>
              <span className="subdued" style={{ fontSize: '0.82rem', display: 'block', marginBottom: '0.6rem' }}>
                High confidence on a wrong answer flags a critical misconception.
              </span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {['Guessed', 'Somewhat Sure', 'Confident'].map(lvl => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setConfidence(lvl)}
                    disabled={!!lastSubmission}
                    className="btn"
                    style={{
                      flex: 1,
                      backgroundColor: confidence === lvl ? '#0D9488' : '#FFFFFF',
                      color: confidence === lvl ? '#FFFFFF' : '#334155',
                      borderColor: confidence === lvl ? '#0D9488' : '#CBD5E1',
                      fontWeight: confidence === lvl ? 600 : 500
                    }}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>

            {!lastSubmission ? (
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!selectedOption || submitting}
                style={{ width: '100%', padding: '0.75rem' }}
              >
                {submitting ? 'Evaluating...' : 'Submit & Evaluate'}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleNextQuestion}
                className="btn btn-primary"
                style={{ width: '100%', padding: '0.75rem' }}
              >
                Next Question ➡️
              </button>
            )}
          </form>

          {/* Submission Result Feedback */}
          {lastSubmission && (
            <div>
              {lastSubmission.is_correct ? (
                <div className="card" style={{ background: '#F0FDF4', border: '1.5px solid #86EFAC' }}>
                  <h4 style={{ color: '#166534', margin: '0 0 4px 0' }}>✅ Correct! ({lastSubmission.confidence})</h4>
                  <p style={{ color: '#14532D', fontSize: '0.92rem', margin: 0 }}>
                    Mastery updated: <strong>{Math.round(lastSubmission.old_score)}% → {Math.round(lastSubmission.new_score)}%</strong> (+{lastSubmission.delta}%)
                  </p>
                  <p style={{ color: '#166534', fontSize: '0.88rem', marginTop: '6px' }}>
                    {lastSubmission.explanation}
                  </p>
                </div>
              ) : (
                <div>
                  <div className="card" style={{ background: '#FEF2F2', border: '1.5px solid #FCA5A5' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <h4 style={{ color: '#991B1B', margin: 0 }}>❌ Incorrect ({lastSubmission.confidence})</h4>
                      <span className="badge badge-critical">
                        {lastSubmission.confidence === 'Confident' ? '🚨 Critical Misconception' : 'Weak Concept'}
                      </span>
                    </div>
                    <p style={{ color: '#7F1D1D', fontSize: '0.92rem', margin: 0 }}>
                      You selected: <strong>{selectedOption}</strong><br />
                      Correct answer: <strong>{lastSubmission.correct_answer}</strong><br />
                      Mastery adjusted: <strong>{Math.round(lastSubmission.old_score)}% → {Math.round(lastSubmission.new_score)}%</strong> ({lastSubmission.delta}%)
                    </p>
                  </div>

                  {/* "Explain My Mistake" Card */}
                  <div className="card" style={{ borderLeft: '5px solid #EF4444' }}>
                    <h4 style={{ fontSize: '1.05rem', color: '#991B1B', marginBottom: '0.6rem' }}>
                      💡 Explain My Mistake (Cognitive Diagnostic)
                    </h4>
                    {explaining ? (
                      <p className="subdued">Analyzing conceptual misconception using lecture notes...</p>
                    ) : (
                      <div className="prose" style={{ fontSize: '0.92rem', lineHeight: '1.6' }}>
                        <pre style={{
                          whiteSpace: 'pre-wrap',
                          fontFamily: 'inherit',
                          background: 'transparent',
                          color: 'inherit',
                          padding: 0
                        }}>
                          {diagnosticText}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
