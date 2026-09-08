import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function NotebooksView({
  notebooks,
  activeNotebook,
  setActiveNotebookId,
  user,
  onRefreshNotebooks
}) {
  const [activeSubTab, setActiveSubTab] = useState('list'); // 'list', 'upload', 'create'
  const [notes, setNotes] = useState([]);
  const [loadingNotes, setLoadingNotes] = useState(false);

  // Upload state
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadError, setUploadError] = useState('');

  // Create state
  const [newSubject, setNewSubject] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (activeNotebook?.id) {
      loadNotes(activeNotebook.id);
    }
  }, [activeNotebook?.id]);

  async function loadNotes(nbId) {
    setLoadingNotes(true);
    try {
      const data = await api.getNotes(nbId);
      setNotes(data.notes || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingNotes(false);
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file || !activeNotebook) return;
    setUploading(true);
    setUploadMessage('1/3 Parsing document with pdfplumber...');
    setUploadError('');

    try {
      setUploadMessage('2/3 Identifying concepts and building prerequisite graph...');
      const res = await api.uploadNotes(activeNotebook.id, user.id, file);
      setUploadMessage(`🎉 Successfully extracted ${res.topics?.length || 0} topics from ${file.name}!`);
      setFile(null);
      loadNotes(activeNotebook.id);
      onRefreshNotebooks();
    } catch (err) {
      setUploadError(err.message || 'Failed to process document');
    } finally {
      setUploading(false);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!newSubject.trim()) return;
    setCreating(true);
    try {
      const res = await api.createNotebook(user.id, newSubject.trim(), newDesc.trim());
      setNewSubject('');
      setNewDesc('');
      await onRefreshNotebooks();
      if (res.notebook?.id) {
        setActiveNotebookId(res.notebook.id);
      }
      setActiveSubTab('list');
    } catch (err) {
      alert(err.message || 'Error creating notebook');
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(nbId, e) {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this subject notebook?')) return;
    try {
      await api.deleteNotebook(nbId);
      onRefreshNotebooks();
    } catch (err) {
      alert(err.message || 'Error deleting');
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.85rem', marginBottom: '0.2rem' }}>📚 Subject Notebooks & Lecture Notes</h1>
        <p className="subdued">Manage multiple courses simultaneously, upload PDF notes, and inspect extracted material.</p>
      </div>

      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '0.5rem' }}>
        {[
          { id: 'list', label: '📖 All Notebooks' },
          { id: 'upload', label: '📤 Upload Notes to Active Subject' },
          { id: 'create', label: '➕ Create New Subject' },
        ].map(st => (
          <button
            key={st.id}
            onClick={() => setActiveSubTab(st.id)}
            className="btn"
            style={{
              fontWeight: activeSubTab === st.id ? 600 : 500,
              backgroundColor: activeSubTab === st.id ? '#0D9488' : '#FFFFFF',
              color: activeSubTab === st.id ? '#FFFFFF' : '#334155',
              borderColor: activeSubTab === st.id ? '#0D9488' : '#CBD5E1'
            }}
          >
            {st.label}
          </button>
        ))}
      </div>

      {/* TAB 1: ALL NOTEBOOKS */}
      {activeSubTab === 'list' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {notebooks.map(nb => {
            const isActive = nb.id === activeNotebook?.id;
            return (
              <div
                key={nb.id}
                className="card"
                style={{
                  border: isActive ? '2px solid #0D9488' : '1px solid #E2E8F0',
                  backgroundColor: isActive ? '#F0FDFA' : '#FFFFFF',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <h3 style={{ fontSize: '1.25rem', margin: 0 }}>{nb.subject_name}</h3>
                    {isActive && <span className="badge badge-mastered">CURRENT ACTIVE</span>}
                  </div>
                  <p style={{ color: '#475569', fontSize: '0.92rem', marginBottom: '0.8rem' }}>
                    {nb.description || 'Course study notes and concept units.'}
                  </p>
                  <div style={{ fontSize: '0.82rem', color: '#64748B', marginBottom: '1rem' }}>
                    <span>🧠 <strong>{nb.topic_count || 0}</strong> topics</span> &nbsp;•&nbsp; 
                    <span>📊 Avg Mastery: <strong>{nb.average_mastery || 0}%</strong></span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.8rem' }}>
                  {!isActive && (
                    <button
                      onClick={() => setActiveNotebookId(nb.id)}
                      className="btn btn-primary"
                      style={{ flex: 1, fontSize: '0.85rem' }}
                    >
                      Set as Active
                    </button>
                  )}
                  {notebooks.length > 1 && (
                    <button
                      onClick={(e) => handleDelete(nb.id, e)}
                      className="btn"
                      style={{ color: '#EF4444', borderColor: '#FECDD3' }}
                      title="Delete notebook"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB 2: UPLOAD NOTES */}
      {activeSubTab === 'upload' && (
        <div style={{ maxWidth: '700px' }}>
          <div className="card">
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.4rem' }}>
              Upload Notes for <strong>{activeNotebook?.subject_name}</strong>
            </h3>

            {uploadMessage && (
              <div style={{ background: '#F0FDF4', color: '#166534', padding: '0.8rem', borderRadius: '8px', marginBottom: '1rem' }}>
                {uploadMessage}
              </div>
            )}
            {uploadError && (
              <div style={{ background: '#FEF2F2', color: '#991B1B', padding: '0.8rem', borderRadius: '8px', marginBottom: '1rem' }}>
                {uploadError}
              </div>
            )}

            <form onSubmit={handleUpload}>
              <div style={{
                border: '2px dashed #CBD5E1',
                borderRadius: '12px',
                padding: '2rem',
                textAlign: 'center',
                backgroundColor: '#F8FAFC',
                marginBottom: '1.25rem'
              }}>
                <input
                  type="file"
                  accept=".pdf,.txt"
                  id="pdf_file_input"
                  onChange={(e) => setFile(e.target.files[0])}
                  style={{ display: 'none' }}
                />
                <label htmlFor="pdf_file_input" style={{ cursor: 'pointer', display: 'block' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📄</div>
                  <strong style={{ color: '#0D9488' }}>Click to select PDF notes</strong> or drag and drop
                  <p style={{ fontSize: '0.8rem', color: '#94A3B8', marginTop: '0.2rem' }}>PDF or TXT files supported</p>
                </label>
                {file && (
                  <div style={{ marginTop: '0.75rem', fontWeight: 600, color: '#1E293B' }}>
                    Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </div>
                )}
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={!file || uploading}
                style={{ width: '100%', padding: '0.75rem' }}
              >
                {uploading ? 'Processing with pdfplumber & AI...' : '🚀 Process Notes & Extract Topics'}
              </button>
            </form>
          </div>

          {/* Uploaded Documents List */}
          <div className="card">
            <h4 style={{ marginBottom: '0.8rem' }}>📁 Uploaded Documents in this Notebook</h4>
            {loadingNotes ? (
              <p className="subdued">Loading documents...</p>
            ) : notes.length ? (
              notes.map(n => (
                <div key={n.id} style={{ padding: '0.75rem', borderBottom: '1px solid #F1F5F9' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>📄 {n.filename}</div>
                  <div style={{ fontSize: '0.8rem', color: '#64748B' }}>
                    {n.page_count} page(s) • Uploaded {n.uploaded_at?.slice(0, 10)}
                  </div>
                </div>
              ))
            ) : (
              <p className="subdued">No documents uploaded yet for this subject.</p>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: CREATE NOTEBOOK */}
      {activeSubTab === 'create' && (
        <div style={{ maxWidth: '600px' }}>
          <div className="card">
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.4rem' }}>➕ Create a New Subject Notebook</h3>
            <p className="subdued" style={{ marginBottom: '1.25rem' }}>
              Add a new subject to study simultaneously alongside your existing courses.
            </p>

            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem' }}>
                  Subject Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Operating Systems"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem' }}>
                  Course Description (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Key syllabus areas, professor, or semester..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={creating}
                style={{ width: '100%', padding: '0.75rem' }}
              >
                {creating ? 'Creating...' : 'Create Notebook'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
