import streamlit as st
import os
from database import init_db, seed_demo_data
import models
from mastery_engine import calculate_decay, classify_topic_health
from recommendation_engine import get_study_recommendations
from components.styles import get_custom_css
from components.ui_cards import render_header, render_mastery_bar, render_recommendation_card

# 1. Page Configuration
st.set_page_config(
    page_title="Adhyay — Personalized AI Study Assistant",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply calm aesthetic styling
st.markdown(get_custom_css(), unsafe_allow_html=True)

# 2. Database Initialization
init_db()
seed_demo_data(force=False)

# =============================================================================
# AUTHENTICATION CHECK & LOGIN PAGE
# =============================================================================
if "authenticated_user" not in st.session_state or st.session_state["authenticated_user"] is None:
    # Render Calm, Peaceful Login / Welcome Screen
    col_l, col_center, col_r = st.columns([1, 2.2, 1])
    with col_center:
        st.write("")
        st.write("")
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h1 style="font-size: 2.2rem; margin-bottom: 0.3rem;">📖 Adhyay</h1>
            <p style="color: #64748B; font-size: 1.05rem;">Personalized AI Study Assistant</p>
            <p style="color: #94A3B8; font-size: 0.9rem; max-width: 480px; margin: 0 auto;">
                A calm, distraction-free study space that turns your lecture notes into structured mastery through adaptive quizzes and cognitive tracking.
            </p>
        </div>
        """, unsafe_allow_html=True)

        auth_tab_login, auth_tab_register = st.tabs(["🔑 Sign In", "✨ Create Account"])

        with auth_tab_login:
            st.markdown("##### Sign in to your study notebook")
            with st.form("login_form"):
                login_email = st.text_input("Email Address", value="student@adhyay.edu")
                login_password = st.text_input("Password", value="student123", type="password")
                submitted_login = st.form_submit_button("Sign In to Adhyay", type="primary", use_container_width=True)

                if submitted_login:
                    user = models.authenticate_user(login_email, login_password)
                    if user:
                        st.session_state["authenticated_user"] = user
                        st.success(f"Welcome back, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password. You can also use the 1-click Demo Login below.")

            st.write("")
            # 1-Click Demo Login
            if st.button("🚀 1-Click Demo Student Sign-In", use_container_width=True):
                user = models.get_default_user()
                st.session_state["authenticated_user"] = user
                st.success(f"Signed in as {user['name']}!")
                st.rerun()

        with auth_tab_register:
            st.markdown("##### New to Adhyay? Create a free account")
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", placeholder="e.g. Priya Patel")
                reg_email = st.text_input("Email Address", placeholder="e.g. priya@university.edu")
                reg_password = st.text_input("Create Password", type="password")
                submitted_reg = st.form_submit_button("Create My Account", type="primary", use_container_width=True)

                if submitted_reg:
                    if not reg_email or not reg_name or not reg_password:
                        st.error("Please fill in all fields.")
                    else:
                        new_user = models.register_user(reg_email, reg_name, reg_password)
                        if new_user:
                            # Create an initial starter notebook for this new user
                            models.create_notebook(new_user["id"], "My First Notebook", "General lecture notes and study material.")
                            st.session_state["authenticated_user"] = new_user
                            st.success(f"Account created! Welcome, {new_user['name']}!")
                            st.rerun()
                        else:
                            st.error("An account with this email already exists. Please sign in.")

    # Stop rendering the rest of the application until authenticated
    st.stop()

# =============================================================================
# AUTHENTICATED USER SESSION SETUP
# =============================================================================
current_user = st.session_state["authenticated_user"]
user_id = current_user["id"]

# Load all notebooks belonging to this user
user_notebooks = models.get_notebooks(user_id)

# If user has no notebook, create default one
if not user_notebooks:
    models.create_notebook(user_id, "Java Programming (OOP)", "Core OOP concepts and polymorphism.")
    user_notebooks = models.get_notebooks(user_id)

if "active_notebook_id" not in st.session_state or not any(nb["id"] == st.session_state["active_notebook_id"] for nb in user_notebooks):
    st.session_state["active_notebook_id"] = user_notebooks[0]["id"]

active_nb_id = st.session_state["active_notebook_id"]
active_nb = models.get_notebook(active_nb_id)

# =============================================================================
# SIDEBAR CONTROLS (Clean, no API key input)
# =============================================================================
with st.sidebar:
    st.markdown("### 📖 Adhyay")
    st.caption("Personalized AI Study Assistant")

    # User Profile Pill
    st.markdown(f"""
    <div class="user-pill">
        <strong>👤 {current_user['name']}</strong><br>
        <span style="font-size: 0.8rem; color: #64748B;">{current_user['email']}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["authenticated_user"] = None
        st.session_state["active_notebook_id"] = None
        st.rerun()

    st.divider()

    # Active Notebook Selection
    st.markdown("##### 📚 Active Subject")
    nb_dict = {nb["id"]: nb["subject_name"] for nb in user_notebooks}
    selected_nb_id = st.selectbox(
        "Current Subject:",
        options=list(nb_dict.keys()),
        format_func=lambda x: nb_dict.get(x, "Select"),
        index=list(nb_dict.keys()).index(active_nb_id) if active_nb_id in nb_dict else 0,
        label_visibility="collapsed"
    )
    if selected_nb_id != st.session_state["active_notebook_id"]:
        st.session_state["active_notebook_id"] = selected_nb_id
        st.rerun()

    st.write("")
    if st.button("➕ Add New Subject", use_container_width=True):
        st.switch_page("pages/1_📖_Notebooks.py")

    st.divider()
    if st.button("🔄 Reset Demo Data"):
        seed_demo_data(force=True)
        st.success("Sample notebooks refreshed!")
        st.rerun()

# =============================================================================
# MAIN DASHBOARD CONTENT
# =============================================================================
# 1. MULTI-NOTEBOOK SHELF (Simultaneous Notebooks Demonstration)
st.markdown("### 📚 Your Subject Notebooks")

nb_cols = st.columns(min(3, max(1, len(user_notebooks))))
for idx, nb in enumerate(user_notebooks):
    col_target = nb_cols[idx % len(nb_cols)]
    with col_target:
        is_active = (nb["id"] == active_nb_id)
        card_border = "2px solid #0D9488" if is_active else "1px solid #E2E8F0"
        card_bg = "#F0FDFA" if is_active else "#FFFFFF"
        active_badge = "<span class='badge-pill badge-mastered'>ACTIVE</span>" if is_active else ""
        
        nb_topics = models.get_topics(nb["id"])
        st.markdown(f"""
        <div class="notebook-shelf-card" style="border: {card_border}; background-color: {card_bg};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <h4 style="margin: 0; font-size: 1.05rem;">{nb['subject_name']}</h4>
                {active_badge}
            </div>
            <p style="font-size: 0.85rem; color: #64748B; margin: 0 0 8px 0;">{len(nb_topics)} topics organized</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not is_active:
            if st.button(f"Switch to {nb['subject_name']}", key=f"switch_nb_{nb['id']}", use_container_width=True):
                st.session_state["active_notebook_id"] = nb["id"]
                st.rerun()
st.divider()

# Header
st.markdown(f"# 📖 {active_nb['subject_name']}")
st.markdown(f"<p class='subdued-text'>{active_nb['description'] or 'Structured study workspace.'}</p>", unsafe_allow_html=True)

# Fetch Topics, Mastery & Recommendations
topics_mastery = models.get_mastery_scores(user_id, active_nb["id"])
prereqs = models.get_prerequisites_for_notebook(active_nb["id"])
recommendations = get_study_recommendations(user_id, active_nb["id"], topics_mastery, prereqs)

# Top Metrics Row
avg_mastery = sum(t["score"] for t in topics_mastery) / len(topics_mastery) if topics_mastery else 0
weak_topics = [t for t in topics_mastery if t["score"] < 65.0]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Subject Mastery", f"{avg_mastery:.1f}%")
with col2:
    st.metric("Total Topics", len(topics_mastery))
with col3:
    st.metric("Focus Areas Needed", len(weak_topics), delta=f"-{len(weak_topics)}" if weak_topics else None, delta_color="inverse")
with col4:
    top_rec = recommendations[0]["topic_name"] if recommendations else "All clear"
    st.metric("Top Recommendation", top_rec)

st.write("")


# 2. PERSONALIZED "WHAT SHOULD I STUDY NEXT?" HERO CARD
if recommendations:
    top = recommendations[0]
    is_critical = top["effective_score"] < 50
    card_class = "adhyay-weak-card" if is_critical else "adhyay-hero-card"
    accent_border = "#EF4444" if is_critical else "#10B981"
    
    st.markdown(f"""
    <div class="{card_class}" style="border-left: 6px solid {accent_border};">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span class="badge-pill {'badge-critical' if is_critical else 'badge-progress'}">🎯 What Should I Study Next?</span>
            <span style="font-weight: 700; font-size: 1.2rem; color: #1E293B;">Mastery: {top['effective_score']:.0f}%</span>
        </div>
        <h3 style="margin-top: 0.6rem; margin-bottom: 0.4rem; color: #0F172A;">Recommended: <strong>{top['topic_name']}</strong></h3>
        <p style="color: #334155; font-size: 1.02rem; margin-bottom: 0.5rem;">
            <strong>Why:</strong> {top['primary_reason']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2, _ = st.columns([1.5, 1.5, 3])
    with col_btn1:
        if st.button("📝 Study Concept Notes", use_container_width=True):
            st.session_state["study_topic_id"] = top["topic_id"]
            st.switch_page("pages/2_📝_Study_Topics.py")
    with col_btn2:
        if st.button("🎯 Take Adaptive Quiz", use_container_width=True):
            st.session_state["quiz_topic_id"] = top["topic_id"]
            st.switch_page("pages/3_🎯_Adaptive_Quiz.py")

st.divider()

# 3. TOPIC MASTERY BREAKDOWN (Your Focus Areas)
st.markdown("### 📊 Your Focus Areas & Knowledge Health")
st.caption("Confidence-weighted scoring with time-decay tracking to surface stale concepts.")

col_left, col_right = st.columns([3, 2])

with col_left:
    for t in topics_mastery:
        decay_info = calculate_decay(t["score"], t["last_reviewed_at"])
        render_mastery_bar(decay_info["effective_score"], topic_name=t["topic_name"], decay_info=decay_info)
        st.write("")

with col_right:
    st.markdown("""
    <div class="adhyay-card">
        <h4 style="margin-top: 0;">🧠 How Adhyay Tracks Learning</h4>
        <p style="font-size: 0.9rem; color: #475569;">Unlike simple quiz apps, Adhyay factors in <strong>confidence & forgetting decay</strong>:</p>
        <ul style="font-size: 0.85rem; color: #334155; padding-left: 1.2rem;">
            <li><strong>Correct + Confident:</strong> Strong mastery (+15%)</li>
            <li><strong>Correct + Guessed:</strong> Modest update (+2%)</li>
            <li><strong>Wrong + Confident:</strong> Critical misconception (-18%)</li>
            <li><strong>Decay:</strong> Stale topics lose retention over time</li>
        </ul>
        <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 0;">Prerequisite relationships prioritize foundational concepts first.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 4. LEARNING LOOP NAVIGATION GRID
st.markdown("### 🔄 Continuous Learning Loop")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div class="adhyay-card">
        <h4>1. 📖 Notes & Topics</h4>
        <p style="font-size: 0.85rem; color: #64748B;">Upload PDFs and extract structured topics via pdfplumber and Gemini.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Manage Notes", key="loop_notes", use_container_width=True):
        st.switch_page("pages/1_📖_Notebooks.py")

with c2:
    st.markdown("""
    <div class="adhyay-card">
        <h4>2. 📝 Structured Study</h4>
        <p style="font-size: 0.85rem; color: #64748B;">Read clear summaries, rules, examples, and chat scoped to your notes.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Study Topics", key="loop_study", use_container_width=True):
        st.switch_page("pages/2_📝_Study_Topics.py")

with c3:
    st.markdown("""
    <div class="adhyay-card">
        <h4>3. 🎯 Adaptive Quiz</h4>
        <p style="font-size: 0.85rem; color: #64748B;">Take MCQs with confidence ratings and get 'Explain My Mistake' diagnostics.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Take Quiz", key="loop_quiz", use_container_width=True):
        st.switch_page("pages/3_🎯_Adaptive_Quiz.py")

with c4:
    st.markdown("""
    <div class="adhyay-card">
        <h4>4. ⚡ Quick Revision</h4>
        <p style="font-size: 0.85rem; color: #64748B;">Flip flashcards or generate a focused Exam Cheat-Sheet for weak areas.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Revision Tools", key="loop_rev", use_container_width=True):
        st.switch_page("pages/5_⚡_Revision_Tools.py")
