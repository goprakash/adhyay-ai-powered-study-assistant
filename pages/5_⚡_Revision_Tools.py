import streamlit as st
import models
import ai_service
from components.styles import get_custom_css
from components.ui_cards import render_header

st.set_page_config(page_title="Revision Tools — Adhyay", page_icon="⚡", layout="wide")
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
topics_mastery = models.get_mastery_scores(user_id, active_nb_id)

render_header(
    f"⚡ Revision Tools — {active_nb['subject_name']}",
    "Interactive flashcards and targeted Exam Cheat-Sheets focused on your weak concepts."
)

tab_flashcards, tab_cheatsheet = st.tabs(["🗂️ Interactive Flashcards", "📝 Personalized Exam Cheat-Sheet"])

# ==========================================
# TAB 1: FLASHCARDS
# ==========================================
with tab_flashcards:
    st.subheader("🗂️ Active Recall Flashcards")

    col_filter1, col_filter2 = st.columns([2, 2])
    with col_filter1:
        flashcard_mode = st.radio(
            "Flashcard Scope:",
            ["Weak Topics Only (Recommended)", "All Topics in Subject", "Select Specific Topic"],
            horizontal=True
        )

    selected_topic_id = None
    if flashcard_mode == "Select Specific Topic":
        with col_filter2:
            topic_dict = {t["id"]: t["name"] for t in topics}
            selected_topic_id = st.selectbox("Choose Topic:", options=list(topic_dict.keys()), format_func=lambda x: topic_dict[x])

    target_topics = []
    if flashcard_mode == "Weak Topics Only (Recommended)":
        weak_ids = [t["topic_id"] for t in topics_mastery if t["score"] < 65.0]
        target_topics = [t for t in topics if t["id"] in weak_ids]
        if not target_topics and topics:
            target_topics = topics[:3]
    elif flashcard_mode == "All Topics in Subject":
        target_topics = topics
    else:
        target_topics = [t for t in topics if t["id"] == selected_topic_id]

    if not target_topics:
        st.info("No topics found for this selection.")
    else:
        fc_key = f"flashcards_{user_id}_{active_nb_id}_{flashcard_mode}_{selected_topic_id}"
        if fc_key not in st.session_state:
            with st.spinner("Generating flashcards..."):
                cards = []
                for t in target_topics:
                    cards.extend(ai_service.generate_flashcards(t["name"], t.get("summary", ""), count=2))
                st.session_state[fc_key] = cards
                st.session_state[f"{fc_key}_idx"] = 0
                st.session_state[f"{fc_key}_revealed"] = False

        cards = st.session_state.get(fc_key, [])
        cur_idx = st.session_state.get(f"{fc_key}_idx", 0)
        is_revealed = st.session_state.get(f"{fc_key}_revealed", False)

        if not cards:
            st.info("No flashcards available. Click Regenerate below.")
        else:
            cur_card = cards[cur_idx % len(cards)]
            st.markdown(f"**Card {cur_idx + 1} of {len(cards)}**")

            if not is_revealed:
                st.markdown(f"""
                <div class="flashcard-box" style="background-color: #FFFFFF; border: 2px solid #E2E8F0;">
                    <span style="font-size: 0.85rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Concept Question</span>
                    <h3 style="margin-top: 0.8rem; color: #1E293B; font-weight: 500;">{cur_card['question']}</h3>
                    <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 1rem;">Click 'Reveal Answer' below to check your recall</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="flashcard-box" style="background-color: #F8FAFC; border: 2px solid #0D9488;">
                    <span style="font-size: 0.85rem; color: #0D9488; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Answer & Concept</span>
                    <h3 style="margin-top: 0.8rem; color: #0F172A; font-weight: 600;">{cur_card['answer']}</h3>
                    <p style="color: #64748B; font-size: 0.9rem; margin-top: 1rem;">Q: {cur_card['question']}</p>
                </div>
                """, unsafe_allow_html=True)

            c_prev, c_flip, c_next, c_regen = st.columns([1, 1.5, 1, 1.5])
            with c_prev:
                if st.button("⬅️ Previous", disabled=(cur_idx == 0)):
                    st.session_state[f"{fc_key}_idx"] = max(0, cur_idx - 1)
                    st.session_state[f"{fc_key}_revealed"] = False
                    st.rerun()

            with c_flip:
                flip_label = "👁️ Reveal Answer" if not is_revealed else "🔄 Hide Answer"
                if st.button(flip_label, type="primary", use_container_width=True):
                    st.session_state[f"{fc_key}_revealed"] = not is_revealed
                    st.rerun()

            with c_next:
                if st.button("Next ➡️", disabled=(cur_idx >= len(cards) - 1)):
                    st.session_state[f"{fc_key}_idx"] = cur_idx + 1
                    st.session_state[f"{fc_key}_revealed"] = False
                    st.rerun()

            with c_regen:
                if st.button("✨ Regenerate Cards"):
                    del st.session_state[fc_key]
                    st.rerun()

# ==========================================
# TAB 2: EXAM CHEAT-SHEET
# ==========================================
with tab_cheatsheet:
    st.subheader("📝 Personalized Exam Cheat-Sheet")
    st.markdown("Generates a compact revision sheet prioritized around your weakest concepts.")

    sheet_key = f"cheatsheet_{user_id}_{active_nb_id}"
    if st.button("⚡ Generate Focused Exam Cheat-Sheet", type="primary"):
        with st.spinner("Compiling cheat-sheet for weak areas..."):
            weak_topics_data = []
            for t in topics_mastery:
                t_obj = models.get_topic(t["topic_id"])
                weak_topics_data.append({
                    "name": t["topic_name"],
                    "score": t["score"],
                    "summary": t_obj.get("summary", "") if t_obj else ""
                })
            weak_topics_data.sort(key=lambda x: x["score"])

            cheat_sheet_content = ai_service.generate_exam_cheat_sheet(
                active_nb["subject_name"],
                weak_topics_data[:4]
            )
            st.session_state[sheet_key] = cheat_sheet_content

    if sheet_key in st.session_state:
        sheet_text = st.session_state[sheet_key]
        st.markdown(f"""
        <div class="adhyay-card" style="background-color: #FFFFFF; font-size: 0.95rem;">
            {sheet_text}
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="📥 Download Cheat-Sheet (Markdown)",
            data=sheet_text,
            file_name=f"{active_nb['subject_name'].replace(' ', '_')}_CheatSheet.md",
            mime="text/markdown"
        )
