import React, { useState, useEffect } from 'react';
import { api } from './api';
import Navbar from './components/Navbar';
import LoginView from './components/LoginView';
import DashboardView from './pages/DashboardView';
import NotebooksView from './pages/NotebooksView';
import StudyView from './pages/StudyView';
import QuizView from './pages/QuizView';
import ProgressView from './pages/ProgressView';
import RevisionView from './pages/RevisionView';

export default function App() {
  // Auth state
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('adhyay_user');
    return saved ? JSON.parse(saved) : null;
  });

  // Notebooks state
  const [notebooks, setNotebooks] = useState([]);
  const [activeNotebookId, setActiveNotebookId] = useState(() => {
    const saved = localStorage.getItem('adhyay_active_nb');
    return saved ? Number(saved) : null;
  });

  // Navigation tab
  const [activeTab, setActiveTab] = useState('dashboard');
  const [navigationParams, setNavigationParams] = useState({});

  useEffect(() => {
    if (user?.id) {
      loadNotebooks(user.id);
    }
  }, [user?.id]);

  useEffect(() => {
    if (activeNotebookId) {
      localStorage.setItem('adhyay_active_nb', activeNotebookId);
    }
  }, [activeNotebookId]);

  async function loadNotebooks(userId) {
    try {
      const data = await api.getNotebooks(userId);
      setNotebooks(data.notebooks || []);
      if (data.notebooks?.length) {
        if (!activeNotebookId || !data.notebooks.some(n => n.id === activeNotebookId)) {
          setActiveNotebookId(data.notebooks[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    }
  }

  function handleLoginSuccess(userData) {
    setUser(userData);
    localStorage.setItem('adhyay_user', JSON.stringify(userData));
    loadNotebooks(userData.id);
  }

  function handleLogout() {
    setUser(null);
    localStorage.removeItem('adhyay_user');
    localStorage.removeItem('adhyay_active_nb');
    setActiveNotebookId(null);
  }

  function handleNavigate(tabId, params = {}) {
    setActiveTab(tabId);
    setNavigationParams(params);
  }

  if (!user) {
    return <LoginView onLoginSuccess={handleLoginSuccess} />;
  }

  const activeNotebook = notebooks.find(n => n.id === activeNotebookId) || notebooks[0];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#FBFBFA' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        notebooks={notebooks}
        activeNotebookId={activeNotebookId}
        setActiveNotebookId={setActiveNotebookId}
        user={user}
        onLogout={handleLogout}
      />

      <main className="app-container">
        {activeTab === 'dashboard' && (
          <DashboardView
            notebooks={notebooks}
            activeNotebook={activeNotebook}
            setActiveNotebookId={setActiveNotebookId}
            user={user}
            onNavigate={handleNavigate}
          />
        )}

        {activeTab === 'notebooks' && (
          <NotebooksView
            notebooks={notebooks}
            activeNotebook={activeNotebook}
            setActiveNotebookId={setActiveNotebookId}
            user={user}
            onRefreshNotebooks={() => loadNotebooks(user.id)}
          />
        )}

        {activeTab === 'study' && (
          <StudyView
            activeNotebook={activeNotebook}
            user={user}
            initialTopicId={navigationParams.topicId}
            onNavigateToQuiz={(tid) => handleNavigate('quiz', { topicId: tid })}
          />
        )}

        {activeTab === 'quiz' && (
          <QuizView
            activeNotebook={activeNotebook}
            user={user}
            initialTopicId={navigationParams.topicId}
          />
        )}

        {activeTab === 'progress' && (
          <ProgressView
            activeNotebook={activeNotebook}
            user={user}
            onNavigate={handleNavigate}
          />
        )}

        {activeTab === 'revision' && (
          <RevisionView
            activeNotebook={activeNotebook}
            user={user}
          />
        )}
      </main>
    </div>
  );
}
