import json
from datetime import datetime
from database import get_connection

# --- User & Authentication ---
def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, password, created_at FROM users WHERE email = ?", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and user.get("password") == password.strip():
        return {"id": user["id"], "email": user["email"], "name": user["name"]}
    return None

def register_user(email, name, password):
    email_clean = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return None # already exists

    cursor.execute("""
    INSERT INTO users (email, name, password)
    VALUES (?, ?, ?)
    """, (email_clean, name.strip(), password.strip()))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "email": email_clean, "name": name.strip()}

def get_default_user():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name FROM users ORDER BY id ASC LIMIT 1")
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (email, name, password) VALUES ('student@adhyay.edu', 'Adhyay Student', 'student123')")
        conn.commit()
        cursor.execute("SELECT id, email, name FROM users ORDER BY id ASC LIMIT 1")
        user = cursor.fetchone()
    conn.close()
    return dict(user)

# --- Notebooks ---
def get_notebooks(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notebooks WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_notebook(notebook_id):
    if not notebook_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notebooks WHERE id = ?", (notebook_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_notebook(user_id, subject_name, description=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO notebooks (user_id, subject_name, description)
    VALUES (?, ?, ?)
    """, (user_id, subject_name, description))
    conn.commit()
    nb_id = cursor.lastrowid
    conn.close()
    return nb_id

def delete_notebook(notebook_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notebooks WHERE id = ?", (notebook_id,))
    conn.commit()
    conn.close()

# --- Notes ---
def save_note(notebook_id, filename, raw_text, page_count=1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO notes (notebook_id, filename, raw_text, page_count)
    VALUES (?, ?, ?, ?)
    """, (notebook_id, filename, raw_text, page_count))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id

def get_notes(notebook_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE notebook_id = ? ORDER BY uploaded_at DESC", (notebook_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Topics ---
def get_topics(notebook_id):
    if not notebook_id:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM topics 
    WHERE notebook_id = ? 
    ORDER BY order_index ASC, id ASC
    """, (notebook_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_topic(topic_id):
    if not topic_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_topic(notebook_id, name, summary="", order_index=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO topics (notebook_id, name, summary, order_index)
    VALUES (?, ?, ?, ?)
    """, (notebook_id, name, summary, order_index))
    conn.commit()
    topic_id = cursor.lastrowid
    conn.close()
    return topic_id

def update_topic_summary(topic_id, summary):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE topics SET summary = ? WHERE id = ?", (summary, topic_id))
    conn.commit()
    conn.close()

# --- Prerequisites ---
def save_prerequisite(topic_id, prereq_topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO topic_prereqs (topic_id, prereq_topic_id)
    VALUES (?, ?)
    """, (topic_id, prereq_topic_id))
    conn.commit()
    conn.close()

def get_prerequisites_for_notebook(notebook_id):
    if not notebook_id:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.topic_id, t1.name AS topic_name, p.prereq_topic_id, t2.name AS prereq_name
    FROM topic_prereqs p
    JOIN topics t1 ON p.topic_id = t1.id
    JOIN topics t2 ON p.prereq_topic_id = t2.id
    WHERE t1.notebook_id = ?
    """, (notebook_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Quiz Questions ---
def save_quiz_question(topic_id, question, options, correct_answer, explanation=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO quiz_questions (topic_id, question, options_json, correct_answer, explanation)
    VALUES (?, ?, ?, ?, ?)
    """, (topic_id, question, json.dumps(options), correct_answer, explanation))
    conn.commit()
    q_id = cursor.lastrowid
    conn.close()
    return q_id

def get_quiz_questions_by_topic(topic_id):
    if not topic_id:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quiz_questions WHERE topic_id = ?", (topic_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d['options'] = json.loads(d['options_json'])
        res.append(d)
    return res

def get_all_quiz_questions_for_notebook(notebook_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT q.*, t.name AS topic_name 
    FROM quiz_questions q
    JOIN topics t ON q.topic_id = t.id
    WHERE t.notebook_id = ?
    """, (notebook_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d['options'] = json.loads(d['options_json'])
        res.append(d)
    return res

# --- Quiz Attempts ---
def record_quiz_attempt(user_id, question_id, topic_id, user_answer, is_correct, confidence):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO quiz_attempts (user_id, question_id, topic_id, user_answer, is_correct, confidence, attempted_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, question_id, topic_id, user_answer, 1 if is_correct else 0, confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    att_id = cursor.lastrowid
    conn.close()
    return att_id

def get_quiz_attempts(user_id, topic_id=None, limit=30):
    conn = get_connection()
    cursor = conn.cursor()
    if topic_id:
        cursor.execute("""
        SELECT a.*, q.question, q.correct_answer, t.name as topic_name
        FROM quiz_attempts a
        JOIN quiz_questions q ON a.question_id = q.id
        JOIN topics t ON a.topic_id = t.id
        WHERE a.user_id = ? AND a.topic_id = ?
        ORDER BY a.attempted_at DESC
        LIMIT ?
        """, (user_id, topic_id, limit))
    else:
        cursor.execute("""
        SELECT a.*, q.question, q.correct_answer, t.name as topic_name
        FROM quiz_attempts a
        JOIN quiz_questions q ON a.question_id = q.id
        JOIN topics t ON a.topic_id = t.id
        WHERE a.user_id = ?
        ORDER BY a.attempted_at DESC
        LIMIT ?
        """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Mastery ---
def get_mastery_scores(user_id, notebook_id):
    if not notebook_id:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.id AS topic_id, t.name AS topic_name, t.order_index,
           COALESCE(m.score, 50.0) AS score,
           m.last_reviewed_at
    FROM topics t
    LEFT JOIN mastery m ON t.id = m.topic_id AND m.user_id = ?
    WHERE t.notebook_id = ?
    ORDER BY t.order_index ASC, t.id ASC
    """, (user_id, notebook_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_topic_mastery(user_id, topic_id):
    if not topic_id:
        return {"score": 50.0, "last_reviewed_at": None}
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT score, last_reviewed_at FROM mastery WHERE user_id = ? AND topic_id = ?", (user_id, topic_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"score": 50.0, "last_reviewed_at": None}

def set_topic_mastery(user_id, topic_id, score, reviewed_at=None):
    if reviewed_at is None:
        reviewed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO mastery (user_id, topic_id, score, last_reviewed_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, topic_id) DO UPDATE SET
        score = excluded.score,
        last_reviewed_at = excluded.last_reviewed_at
    """, (user_id, topic_id, score, reviewed_at))
    conn.commit()
    conn.close()
