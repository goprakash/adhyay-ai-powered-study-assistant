import streamlit as st
import models
from mastery_engine import calculate_decay, classify_topic_health
from recommendation_engine import get_study_recommendations
from components.styles import get_custom_css
from components.ui_cards import render_header, render_mastery_bar, render_recommendation_card

st.set_page_config(page_title="Progress & Plan — Adhyay", page_icon="📊", layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Authentication Guard
if "authenticated_user" not in st.session_state or st.session_state["authenticated_user"] is None:
    st.warning("Please sign in on the Home page first.")
    if st.button("👉 Go to Sign In"):
        st.switch_page("app.py")
    st.stop()

current_user = st.session_state["authenticated_user"]
user_id = current_user["id"]

active_nb_id = st.session_state.get("active_notebook_id")
if not active_nb_id:
    user_notebooks = models.get_notebooks(user_id)
    if user_notebooks:
        active_nb_id = user_notebooks[0]["id"]
        st.session_state["active_notebook_id"] = active_nb_id
    else:
        st.warning("Please create a subject notebook first.")
        st.stop()

active_nb = models.get_notebook(active_nb_id)
topics_mastery = models.get_mastery_scores(user_id, active_nb_id)
prereqs = models.get_prerequisites_for_notebook(active_nb_id)

render_header(
    f"📊 Analytics & Study Recommendations — {active_nb['subject_name']}",
    "Cognitive tracking, time-based decay, and prerequisite graph analysis."
)

tab_rec, tab_breakdown, tab_graph, tab_history = st.tabs([
    "🎯 What Should I Study Next?",
    "📈 Knowledge Health & Decay",
    "🌳 Prerequisite Knowledge Graph",
    "📜 Attempt History & Misconceptions"
])

# ==========================================
# TAB 1: WHAT SHOULD I STUDY NEXT?
# ==========================================
with tab_rec:
    st.subheader("🎯 Personalized 'What Should I Study Next?' Engine")
    st.markdown("""
    Adhyay doesn't just show low scores — it determines **which concept will unblock downstream understanding**
    by traversing your prerequisite dependency graph.
    """)

    recommendations = get_study_recommendations(user_id, active_nb_id, topics_mastery, prereqs)
    
    if not recommendations:
        st.info("No study recommendations available yet.")
    else:
        for idx, rec in enumerate(recommendations, start=1):
            col_card, col_action = st.columns([4, 1.2])
            with col_card:
                render_recommendation_card(rec, index=idx)
            with col_action:
                st.write("")
                st.write("")
                if st.button(f"Study {rec['topic_name']}", key=f"rec_study_{rec['topic_id']}", use_container_width=True):
                    st.session_state["study_topic_id"] = rec["topic_id"]
                    st.switch_page("pages/2_📝_Study_Topics.py")
                if st.button(f"Quiz {rec['topic_name']}", key=f"rec_quiz_{rec['topic_id']}", use_container_width=True):
                    st.session_state["quiz_topic_id"] = rec["topic_id"]
                    st.switch_page("pages/3_🎯_Adaptive_Quiz.py")

# ==========================================
# TAB 2: KNOWLEDGE HEALTH & DECAY
# ==========================================
with tab_breakdown:
    st.subheader("📈 Detailed Topic Mastery & Retention Decay")
    st.caption("Inactive concepts experience time decay simulating natural memory loss.")

    col1, col2 = st.columns([3, 2])
    with col1:
        for t in topics_mastery:
            decay_info = calculate_decay(t["score"], t["last_reviewed_at"])
            render_mastery_bar(decay_info["effective_score"], topic_name=t["topic_name"], decay_info=decay_info)
            if decay_info["is_decayed"]:
                st.caption(f"⚠️ Raw score: {t['score']:.0f}% | Decayed by {decay_info['decay_amount']:.0f}% ({decay_info['days_elapsed']} days inactive)")
            st.write("")

    with col2:
        st.markdown("#### Knowledge Health Summary")
        counts = {"Critical (<50%)": 0, "Needs Review (50-65%)": 0, "Reinforcing (65-80%)": 0, "Mastered (>80%)": 0}
        for t in topics_mastery:
            d = calculate_decay(t["score"], t["last_reviewed_at"])
            s = d["effective_score"]
            if s < 50: counts["Critical (<50%)"] += 1
            elif s < 65: counts["Needs Review (50-65%)"] += 1
            elif s < 80: counts["Reinforcing (65-80%)"] += 1
            else: counts["Mastered (>80%)"] += 1

        st.write(f"- 🔴 **Critical Focus:** {counts['Critical (<50%)']} topics")
        st.write(f"- 🟠 **Needs Review:** {counts['Needs Review (50-65%)']} topics")
        st.write(f"- 🟡 **Reinforcing:** {counts['Reinforcing (65-80%)']} topics")
        st.write(f"- 🟢 **Mastered:** {counts['Mastered (>80%)']} topics")

# ==========================================
# TAB 3: PREREQUISITE GRAPH
# ==========================================
with tab_graph:
    st.subheader("🌳 Prerequisite Knowledge Graph")
    if prereqs:
        st.markdown("##### Direct Dependencies:")
        for p in prereqs:
            st.markdown(f"- **{p['prereq_name']}** ➔ *prerequisite for* ➔ **{p['topic_name']}**")
    else:
        st.info("No prerequisites defined for this notebook yet.")

# ==========================================
# TAB 4: ATTEMPT HISTORY
# ==========================================
with tab_history:
    st.subheader("📜 Recent Quiz Attempts")
    attempts = models.get_quiz_attempts(user_id, limit=25)
    
    if attempts:
        misconceptions = [a for a in attempts if not a["is_correct"] and a["confidence"] == "Confident"]
        if misconceptions:
            st.error(f"🚨 You have {len(misconceptions)} critical misconception(s) on record.")

        for a in attempts[:15]:
            status = "✅ Correct" if a["is_correct"] else "❌ Incorrect"
            mis_tag = " (🚨 False Confidence!)" if not a["is_correct"] and a["confidence"] == "Confident" else ""
            st.markdown(f"- **{a['topic_name']}** | {status} | Answer: *'{a['user_answer']}'* ({a['confidence']}){mis_tag} | *{a['attempted_at']}*")
    else:
        st.info("No quiz attempts recorded yet.")
