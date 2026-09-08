import streamlit as st
import models
import ai_service
from components.styles import get_custom_css
from components.ui_cards import render_header, render_mastery_bar
from mastery_engine import calculate_decay

st.set_page_config(page_title="Study Topics — Adhyay", page_icon="📝", layout="wide")
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
        st.warning("No notebooks found. Please create one on the Home or Notebooks page.")
        st.stop()

active_nb = models.get_notebook(active_nb_id)
topics = models.get_topics(active_nb_id)

if not topics:
    st.info(f"No topics available in '{active_nb['subject_name']}' yet. Upload notes in the Notebooks tab to begin!")
    st.stop()

render_header(
    f"📝 Study Concepts — {active_nb['subject_name']}",
    "Structured study summaries and grounded AI dialogue scoped exclusively to your lecture notes."
)

# Topic Selector
topic_names = {t["id"]: t["name"] for t in topics}
default_idx = 0
if "study_topic_id" in st.session_state and st.session_state["study_topic_id"] in topic_names:
    default_idx = list(topic_names.keys()).index(st.session_state["study_topic_id"])

selected_topic_id = st.selectbox(
    "Choose Concept to Study:",
    options=list(topic_names.keys()),
    format_func=lambda x: f"📖 {topic_names[x]}",
    index=default_idx
)
st.session_state["study_topic_id"] = selected_topic_id

current_topic = models.get_topic(selected_topic_id)
mastery_info = models.get_topic_mastery(user_id, selected_topic_id)
decay_info = calculate_decay(mastery_info["score"], mastery_info["last_reviewed_at"])

# Top Status Row
col_stat_l, col_stat_r = st.columns([3, 1])
with col_stat_l:
    render_mastery_bar(decay_info["effective_score"], topic_name=f"Mastery in {current_topic['name']}", decay_info=decay_info)
with col_stat_r:
    st.write("")
    if st.button("🎯 Quiz on this Topic", type="primary", use_container_width=True):
        st.session_state["quiz_topic_id"] = selected_topic_id
        st.switch_page("pages/3_🎯_Adaptive_Quiz.py")

st.divider()

# Layout: Split Screen (Left: Study Summary, Right: Working AI Chatbot)
col_summary, col_chat = st.columns([1.1, 1])

# ==========================================
# LEFT: STRUCTURED SUMMARY
# ==========================================
with col_summary:
    st.markdown("#### 📘 Concept Summary")
    st.caption("Definition, rules, code/conceptual example, and pitfalls.")

    summary_text = current_topic.get("summary")
    if not summary_text or len(summary_text.strip()) < 20:
        with st.spinner("Compiling summary from notes..."):
            notes = models.get_notes(active_nb_id)
            context_text = "\n".join([n["raw_text"] for n in notes])
            summary_text = ai_service.generate_topic_summary(current_topic["name"], context_text)
            models.update_topic_summary(current_topic["id"], summary_text)

    st.markdown(f"""
    <div class="adhyay-card" style="font-size: 0.95rem; line-height: 1.6;">
    {summary_text}
    </div>
    """, unsafe_allow_html=True)

    if st.button("✨ Regenerate Summary"):
        with st.spinner("Refreshing summary..."):
            notes = models.get_notes(active_nb_id)
            context_text = "\n".join([n["raw_text"] for n in notes])
            new_sum = ai_service.generate_topic_summary(current_topic["name"], context_text)
            models.update_topic_summary(current_topic["id"], new_sum)
            st.success("Summary updated!")
            st.rerun()

# ==========================================
# RIGHT: WORKING GROUNDED CHATBOT
# ==========================================
with col_chat:
    st.markdown(f"#### 💬 Grounded AI Tutor: {current_topic['name']}")
    st.caption("Ask questions, request code examples, or clarify confusing concepts.")

    # Unique chat history key per user and topic
    chat_key = f"chat_history_{user_id}_{selected_topic_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": f"Hello {current_user['name']}! I am your Adhyay tutor for **{current_topic['name']}**. Ask me anything about this concept or click one of the quick prompts below!"}
        ]

    # Quick Suggestion Chips
    st.markdown("**Quick Prompts:**")
    qc1, qc2 = st.columns(2)
    prompt_to_send = None

    with qc1:
        if st.button("💡 Show a code example", use_container_width=True, key="qp_ex"):
            prompt_to_send = f"Can you show a clear, commented code example for {current_topic['name']}?"
        if st.button("⚖️ Key differences / vs", use_container_width=True, key="qp_diff"):
            prompt_to_send = f"What is the key difference between {current_topic['name']} and related concepts?"
    with qc2:
        if st.button("⚙️ What are the core rules?", use_container_width=True, key="qp_rules"):
            prompt_to_send = f"What are the essential rules and constraints for {current_topic['name']}?"
        if st.button("⚠️ Common exam traps", use_container_width=True, key="qp_traps"):
            prompt_to_send = f"What are common pitfalls or exam mistakes regarding {current_topic['name']}?"

    # Chat Container
    chat_box = st.container(height=380)
    with chat_box:
        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Handle manual chat input
    user_typed = st.chat_input(f"Ask about {current_topic['name']}...")
    if user_typed:
        prompt_to_send = user_typed

    # Process message if triggered by input or chip
    if prompt_to_send:
        # Append and display user message
        st.session_state[chat_key].append({"role": "user", "content": prompt_to_send})

        # Generate intelligent grounded bot reply
        notes = models.get_notes(active_nb_id)
        context_text = "\n".join([n["raw_text"] for n in notes])
        
        bot_response = ai_service.chat_with_topic(
            topic_name=current_topic["name"],
            notes_context=f"{current_topic.get('summary', '')}\n{context_text}",
            chat_history=st.session_state[chat_key],
            user_message=prompt_to_send
        )

        st.session_state[chat_key].append({"role": "assistant", "content": bot_response})
        st.rerun()

    if len(st.session_state[chat_key]) > 1:
        if st.button("🧹 Clear Chat History", key="clr_chat"):
            st.session_state[chat_key] = [
                {"role": "assistant", "content": f"Chat reset. How can I help you study **{current_topic['name']}**?"}
            ]
            st.rerun()
