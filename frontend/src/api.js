const API_BASE = '/api';

export const api = {
  // Auth
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  },

  async register(name, email, password) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  // Notebooks
  async getNotebooks(userId = 1) {
    const res = await fetch(`${API_BASE}/notebooks?user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to load notebooks');
    return res.json();
  },

  async createNotebook(userId, subjectName, description) {
    const res = await fetch(`${API_BASE}/notebooks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, subject_name: subjectName, description })
    });
    if (!res.ok) throw new Error('Failed to create notebook');
    return res.json();
  },

  async deleteNotebook(nbId) {
    const res = await fetch(`${API_BASE}/notebooks/${nbId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete notebook');
    return res.json();
  },

  // Notes & PDF Upload
  async getNotes(nbId) {
    const res = await fetch(`${API_BASE}/notebooks/${nbId}/notes`);
    if (!res.ok) throw new Error('Failed to load notes');
    return res.json();
  },

  async uploadNotes(nbId, userId, file) {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/notebooks/${nbId}/upload-notes`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to process notes');
    }
    return res.json();
  },

  // Topics & Study
  async getTopics(nbId, userId = 1) {
    const res = await fetch(`${API_BASE}/notebooks/${nbId}/topics?user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to load topics');
    return res.json();
  },

  async getTopicDetail(topicId, userId = 1) {
    const res = await fetch(`${API_BASE}/topics/${topicId}?user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to load topic');
    return res.json();
  },

  async regenerateSummary(topicId) {
    const res = await fetch(`${API_BASE}/topics/${topicId}/summary/regenerate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to regenerate summary');
    return res.json();
  },

  async sendTopicChat(topicId, message, history = []) {
    const res = await fetch(`${API_BASE}/topics/${topicId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history })
    });
    if (!res.ok) throw new Error('Failed to send message');
    return res.json();
  },

  // Quiz
  async getTopicQuiz(topicId) {
    const res = await fetch(`${API_BASE}/topics/${topicId}/quiz`);
    if (!res.ok) throw new Error('Failed to load quiz');
    return res.json();
  },

  async generateQuiz(topicId) {
    const res = await fetch(`${API_BASE}/topics/${topicId}/quiz/generate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to generate quiz');
    return res.json();
  },

  async submitQuizAttempt(payload) {
    const res = await fetch(`${API_BASE}/quiz/attempt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to evaluate attempt');
    return res.json();
  },

  async explainMistake(payload) {
    const res = await fetch(`${API_BASE}/quiz/explain-mistake`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to get mistake explanation');
    return res.json();
  },

  // Progress & Recommendations
  async getProgress(nbId, userId = 1) {
    const res = await fetch(`${API_BASE}/notebooks/${nbId}/progress?user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to load progress');
    return res.json();
  },

  // Revision
  async getFlashcards(topicId) {
    const res = await fetch(`${API_BASE}/topics/${topicId}/flashcards`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to load flashcards');
    return res.json();
  },

  async getCheatSheet(nbId, userId = 1) {
    const res = await fetch(`${API_BASE}/notebooks/${nbId}/cheat-sheet?user_id=${userId}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to load cheat sheet');
    return res.json();
  }
};