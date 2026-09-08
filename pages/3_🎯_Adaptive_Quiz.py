import streamlit as st
import models
import ai_service
import mastery_engine
from components.styles import get_custom_css
from components.ui_cards import render_header, render_mastery_bar

st.set_page_config(page_title="Adaptive Quiz — Adhyay", page_icon="🎯", layout="wide")
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
topics = models.get_topics(active_nb_id)

if not topics:
    st.info(f"No topics found in '{active_nb['subject_name']}'. Upload lecture notes in the Notebooks tab to begin.")
    st.stop()

render_header(
    f"🎯 Adaptive Concept Quiz — {active_nb['subject_name']}",
    "Adhyay pairs questions with confidence tagging to identify misconceptions and update your mastery."
)

# Topic Selector
topic_options = {t["id"]: t["name"] for t in topics}
default_idx = 0
if "quiz_topic_id" in st.session_state and st.session_state["quiz_topic_id"] in topic_options:
    default_idx = list(topic_options.keys()).index(st.session_state["quiz_topic_id"])

col_sel, col_stat = st.columns([2, 1])
with col_sel:
    selected_topic_id = st.selectbox(
        "Select Concept to Quiz:",
        options=list(topic_options.keys()),
        format_func=lambda x: f"🎯 {topic_options[x]}",
        index=default_idx
    )
    st.session_state["quiz_topic_id"] = selected_topic_id

current_topic = models.get_topic(selected_topic_id)
mastery_record = models.get_topic_mastery(user_id, selected_topic_id)
current_score = mastery_record["score"]

with col_stat:
    st.write("")
    render_mastery_bar(current_score, topic_name=f"{current_topic['name']} Mastery")

st.divider()

# Load questions
questions = models.get_quiz_questions_by_topic(selected_topic_id)

# If no questions exist, generate them
if not questions:
    st.info(f"No questions saved yet for '{current_topic['name']}'.")
    if st.button("✨ Generate AI Questions", type="primary"):
        with st.spinner("Drafting questions based on course notes..."):
            notes = models.get_notes(active_nb_id)
            context_text = "\n".join([n["raw_text"] for n in notes])
            generated = ai_service.generate_quiz_questions(
                current_topic["name"],
                f"{current_topic.get('summary', '')}\n{context_text}",
                num_questions=3
            )
            for q in generated:
                models.save_quiz_question(
                    current_topic["id"],
                    q["question"],
                    q["options"],
                    q["correct_answer"],
                    q.get("explanation", "")
                )
            st.success("Questions generated!")
            st.rerun()
    st.stop()

# Session State for Question Index
q_idx_key = f"quiz_q_idx_{user_id}_{selected_topic_id}"
if q_idx_key not in st.session_state:
    st.session_state[q_idx_key] = 0

current_q_idx = st.session_state[q_idx_key] % len(questions)
q_item = questions[current_q_idx]

# Question Card
st.markdown(f"#### Question {current_q_idx + 1} of {len(questions)}")
st.markdown(f"""
<div class="adhyay-card" style="font-size: 1.15rem; font-weight: 500; border-left: 4px solid #3B82F6;">
    {q_item['question']}
</div>
""", unsafe_allow_html=True)

# Quiz Form
form_key = f"quiz_form_{q_item['id']}_{current_q_idx}"
with st.form(key=form_key):
    st.markdown("**Your Answer:**")
    selected_option = st.radio("Choose option:", options=q_item["options"], label_visibility="collapsed")

    st.write("")
    st.markdown("**How confident are you in this answer?**")
    st.caption("Adhyay uses confidence to detect false mastery or deep misconceptions.")
    
    confidence = st.select_slider(
        "Confidence Level:",
        options=["Guessed", "Somewhat Sure", "Confident"],
        value="Somewhat Sure"
    )

    submitted = st.form_submit_button("Submit & Evaluate", type="primary")

if submitted:
    is_correct = (selected_option.strip() == q_item["correct_answer"].strip())
    new_score = mastery_engine.calculate_new_mastery(current_score, is_correct, confidence)
    delta = round(new_score - current_score, 1)

    models.record_quiz_attempt(
        user_id=user_id,
        question_id=q_item["id"],
        topic_id=selected_topic_id,
        user_answer=selected_option,
        is_correct=is_correct,
        confidence=confidence
    )
    models.set_topic_mastery(user_id, selected_topic_id, new_score)

    st.session_state["last_submission"] = {
        "q_id": q_item["id"],
        "is_correct": is_correct,
        "selected_option": selected_option,
        "correct_answer": q_item["correct_answer"],
        "confidence": confidence,
        "old_score": current_score,
        "new_score": new_score,
        "delta": delta,
        "topic_name": current_topic["name"],
        "question_text": q_item["question"],
        "explanation": q_item.get("explanation", "")
    }

# Immediate Diagnostic Feedback
if "last_submission" in st.session_state and st.session_state["last_submission"]["q_id"] == q_item["id"]:
    res = st.session_state["last_submission"]
    
    if res["is_correct"]:
        st.markdown(f"""
        <div class="adhyay-card" style="background-color: #F0FDF4; border: 1.5px solid #86EFAC;">
            <h4 style="color: #166534; margin: 0 0 6px 0;">✅ Correct! ({res['confidence']})</h4>
            <p style="margin: 0; color: #14532D; font-size: 0.95rem;">
                Your answer: <strong>{res['selected_option']}</strong><br>
                Mastery updated: <strong>{res['old_score']:.0f}% → {res['new_score']:.0f}%</strong> ({'+' if res['delta'] >= 0 else ''}{res['delta']}%)
            </p>
            <p style="margin-top: 6px; font-size: 0.9rem; color: #166534;">{res['explanation']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        misconception_badge = "🚨 Misconception Alert" if res["confidence"] == "Confident" else "Weak Area Flagged"
        st.markdown(f"""
        <div class="adhyay-card" style="background-color: #FEF2F2; border: 1.5px solid #FCA5A5;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #991B1B; margin: 0;">❌ Incorrect ({res['confidence']})</h4>
                <span class="badge-pill badge-critical">{misconception_badge}</span>
            </div>
            <p style="margin: 8px 0 0 0; color: #7F1D1D; font-size: 0.95rem;">
                You selected: <strong>{res['selected_option']}</strong><br>
                Correct answer: <strong>{res['correct_answer']}</strong><br>
                Mastery adjusted: <strong>{res['old_score']:.0f}% → {res['new_score']:.0f}%</strong> ({res['delta']}%)
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("💡 Explain My Mistake (Cognitive Diagnostic)", expanded=True):
            with st.spinner("Analyzing why this happened..."):
                notes = models.get_notes(active_nb_id)
                context_text = "\n".join([n["raw_text"] for n in notes])
                diagnostic = ai_service.explain_mistake(
                    topic_name=res["topic_name"],
                    question=res["question_text"],
                    student_answer=res["selected_option"],
                    correct_answer=res["correct_answer"],
                    notes_context=f"{current_topic.get('summary', '')}\n{context_text}"
                )
                st.markdown(diagnostic)

    col_nav1, _ = st.columns([1, 4])
    with col_nav1:
        if st.button("Next Question ➡️"):
            st.session_state[q_idx_key] = (current_q_idx + 1) % len(questions)
            del st.session_state["last_submission"]
            st.rerun()

st.divider()

# Attempt History
st.markdown("##### 📜 Recent Attempts on this Topic")
recent_attempts = models.get_quiz_attempts(user_id, topic_id=selected_topic_id, limit=5)
if recent_attempts:
    for att in recent_attempts:
        status_icon = "✅" if att["is_correct"] else "❌"
        st.markdown(f"- {status_icon} **{att['attempted_at'][11:16]}**: Answered *'{att['user_answer']}'* ({att['confidence']})")
else:
    st.caption("No past attempts recorded yet.")
