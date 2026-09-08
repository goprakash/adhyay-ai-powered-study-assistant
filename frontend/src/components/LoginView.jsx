import React, { useState } from 'react';
import { api } from '../api';

export default function LoginView({ onLoginSuccess }) {
  const [tab, setTab] = useState('login'); // 'login' or 'register'
  const [email, setEmail] = useState('student@adhyay.edu');
  const [password, setPassword] = useState('student123');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e) {
    if (e) e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.login(email, password);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.register(name, email, password);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  function handleDemoLogin() {
    setEmail('student@adhyay.edu');
    setPassword('student123');
    api.login('student@adhyay.edu', 'student123')
      .then(data => onLoginSuccess(data.user))
      .catch(err => setError(err.message));
  }

  return (
    <div style={{
      minHeight: '85vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 1rem'
    }}>
      <div style={{
        maxWidth: '460px',
        width: '100%',
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: '16px',
        padding: '2.5rem',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '1.8rem' }}>
          <div style={{
            fontSize: '2.5rem',
            width: '64px',
            height: '64px',
            lineHeight: '64px',
            margin: '0 auto 0.8rem auto',
            background: '#F0FDFA',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            📖
          </div>
          <h1 style={{ fontSize: '1.8rem', color: '#0F172A', marginBottom: '0.2rem' }}>Adhyay</h1>
          <p style={{ color: '#64748B', fontSize: '0.95rem' }}>Personalized AI Study Assistant</p>
          <p style={{ color: '#94A3B8', fontSize: '0.85rem', marginTop: '0.4rem' }}>
            A calm, distraction-free study space turning lecture notes into cognitive mastery.
          </p>
        </div>

        {/* Tab switch */}
        <div style={{
          display: 'flex',
          background: '#F1F5F9',
          borderRadius: '10px',
          padding: '4px',
          marginBottom: '1.5rem'
        }}>
          <button
            onClick={() => { setTab('login'); setError(''); }}
            style={{
              flex: 1,
              padding: '0.5rem',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontWeight: tab === 'login' ? 600 : 500,
              background: tab === 'login' ? '#FFFFFF' : 'transparent',
              color: tab === 'login' ? '#0F172A' : '#64748B',
              border: 'none',
              boxShadow: tab === 'login' ? '0 1px 3px rgba(0,0,0,0.05)' : 'none'
            }}
          >
            Sign In
          </button>
          <button
            onClick={() => { setTab('register'); setError(''); }}
            style={{
              flex: 1,
              padding: '0.5rem',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontWeight: tab === 'register' ? 600 : 500,
              background: tab === 'register' ? '#FFFFFF' : 'transparent',
              color: tab === 'register' ? '#0F172A' : '#64748B',
              border: 'none',
              boxShadow: tab === 'register' ? '0 1px 3px rgba(0,0,0,0.05)' : 'none'
            }}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div style={{
            backgroundColor: '#FEE2E2',
            color: '#991B1B',
            padding: '0.65rem 0.85rem',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}

        {tab === 'login' ? (
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: '#475569' }}>
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div style={{ marginBottom: '1.4rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: '#475569' }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In to Adhyay'}
            </button>

            <div style={{ margin: '1.5rem 0', textAlign: 'center', borderTop: '1px solid #E2E8F0', position: 'relative' }}>
              <span style={{
                position: 'absolute',
                top: '-0.7rem',
                left: '50%',
                transform: 'translateX(-50%)',
                background: '#FFFFFF',
                padding: '0 0.8rem',
                fontSize: '0.78rem',
                color: '#94A3B8'
              }}>
                OR
              </span>
            </div>

            <button
              type="button"
              onClick={handleDemoLogin}
              className="btn"
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: '#F8FAFC',
                border: '1.5px dashed #0D9488',
                color: '#0D9488',
                fontWeight: 600
              }}
            >
              🚀 1-Click Demo Student Sign-In
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegister}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: '#475569' }}>
                Full Name
              </label>
              <input
                type="text"
                placeholder="e.g. Maya Sen"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: '#475569' }}>
                Email Address
              </label>
              <input
                type="email"
                placeholder="e.g. maya@univ.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div style={{ marginBottom: '1.4rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: '#475569' }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Creating account...' : 'Create My Account'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
