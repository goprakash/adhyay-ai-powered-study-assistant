import streamlit as st
import models
import pdf_processor
import ai_service
from components.styles import get_custom_css
from components.ui_cards import render_header

st.set_page_config(page_title="My Notebooks & PDF Upload — Adhyay", page_icon="📖", layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Authentication Guard
if "authenticated_user" not in st.session_state or st.session_state["authenticated_user"] is None:
    st.warning("Please sign in on the Home page first to access your notebooks.")
    if st.button("👉 Go to Sign In"):
        st.switch_page("app.py")
    st.stop()

current_user = st.session_state["authenticated_user"]
user_id = current_user["id"]

render_header("📖 Subject Notebooks & Lecture Notes", "Manage your course subjects simultaneously and upload lecture notes.")

notebooks = models.get_notebooks(user_id)
if "active_notebook_id" not in st.session_state or not any(nb["id"] == st.session_state["active_notebook_id"] for nb in notebooks):
    st.session_state["active_notebook_id"] = notebooks[0]["id"] if notebooks else None

active_nb_id = st.session_state["active_notebook_id"]
active_nb = models.get_notebook(active_nb_id)

tab_manage, tab_upload, tab_create = st.tabs(["📚 All Notebooks", "📤 Upload Notes to Active Subject", "➕ Create New Subject"])

# ==========================================
# TAB 1: ALL NOTEBOOKS (Multi-Notebook Shelf)
# ==========================================
with tab_manage:
    st.markdown("##### 📚 Your Coexisting Subject Notebooks")
    st.caption("You can maintain as many subjects as you like simultaneously. Each has its own notes, topics, and mastery graph.")

    if not notebooks:
        st.info("No notebooks created yet. Create your first subject in the tab above!")
    else:
        for nb in notebooks:
            is_active = (nb["id"] == active_nb_id)
            card_border = "2px solid #0D9488" if is_active else "1px solid #E2E8F0"
            card_bg = "#F0FDFA" if is_active else "#FFFFFF"
            active_badge = "<span class='badge-pill badge-mastered'>CURRENT ACTIVE</span>" if is_active else ""

            nb_topics = models.get_topics(nb["id"])
            nb_notes = models.get_notes(nb["id"])

            st.markdown(f"""
            <div class="adhyay-card" style="border: {card_border}; background-color: {card_bg};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 1.25rem;">{nb['subject_name']}</h3>
                    {active_badge}
                </div>
                <p style="margin: 6px 0 10px 0; color: #475569; font-size: 0.95rem;">{nb['description'] or 'Course notebook'}</p>
                <div style="font-size: 0.85rem; color: #64748B;">
                    <span>📁 <strong>{len(nb_notes)}</strong> note document(s)</span> &nbsp;|&nbsp; 
                    <span>🧠 <strong>{len(nb_topics)}</strong> topics extracted</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_btn1, col_btn2, _ = st.columns([1.5, 1, 4])
            with col_btn1:
                if not is_active:
                    if st.button(f"Switch Active Context to {nb['subject_name']}", key=f"set_act_{nb['id']}"):
                        st.session_state["active_notebook_id"] = nb["id"]
                        st.rerun()
            with col_btn2:
                if len(notebooks) > 1:
                    if st.button("🗑️ Delete", key=f"del_nb_{nb['id']}"):
                        models.delete_notebook(nb["id"])
                        st.session_state["active_notebook_id"] = None
                        st.rerun()

# ==========================================
# TAB 2: UPLOAD & EXTRACT NOTES
# ==========================================
with tab_upload:
    if not active_nb:
        st.warning("Please select or create a subject notebook first.")
    else:
        st.markdown(f"### Current Active Subject: **{active_nb['subject_name']}**")
        
        # Existing Notes in this Notebook
        existing_notes = models.get_notes(active_nb["id"])
        if existing_notes:
            st.markdown("##### 📁 Uploaded Notes for this Subject:")
            for note in existing_notes:
                with st.expander(f"📄 {note['filename']} ({note['page_count']} pages)"):
                    st.text_area("Note Text Preview", note["raw_text"][:2000] + ("..." if len(note["raw_text"]) > 2000 else ""), height=160, disabled=True, key=f"note_prev_{note['id']}")
        else:
            st.info("No lecture notes uploaded yet for this subject. Upload your PDF below.")

        st.divider()

        # PDF Upload
        st.markdown("##### 📥 Upload PDF Notes")
        st.caption("Adhyay uses **pdfplumber** to extract clean text and identify topics.")

        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf", "txt"], help="Upload lecture notes or textbook chapters.")
        if uploaded_file:
            st.success(f"Selected: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
            
            if st.button("🚀 Process Notes & Extract Topics with AI", type="primary"):
                with st.spinner("Extracting text with pdfplumber..."):
                    if uploaded_file.name.endswith(".pdf"):
                        extracted_data = pdf_processor.extract_text_from_pdf(uploaded_file.read())
                    else:
                        text_content = uploaded_file.read().decode("utf-8", errors="ignore")
                        extracted_data = {"raw_text": text_content, "pages": [{"page_number": 1, "text": text_content}], "page_count": 1}

                if not extracted_data.get("raw_text") or len(extracted_data.get("raw_text").strip()) < 20:
                    st.error("Could not read text from this file. Please verify it contains selectable text.")
                else:
                    st.success(f"Extracted {len(extracted_data['raw_text'])} characters from {extracted_data['page_count']} page(s)!")
                    
                    # Save raw note
                    models.save_note(
                        active_nb["id"],
                        uploaded_file.name,
                        extracted_data["raw_text"],
                        page_count=extracted_data["page_count"]
                    )

                    with st.spinner("Analyzing topics and prerequisite graph..."):
                        topics = ai_service.extract_topics_from_notes(
                            extracted_data["raw_text"],
                            subject_name=active_nb["subject_name"]
                        )

                    with st.spinner("Saving topics and initializing cognitive mastery tracking..."):
                        topic_name_to_id = {}
                        for idx, t in enumerate(topics):
                            t_id = models.save_topic(
                                active_nb["id"],
                                name=t["name"],
                                summary=t.get("summary", ""),
                                order_index=idx + 1
                            )
                            topic_name_to_id[t["name"]] = t_id
                            models.set_topic_mastery(user_id, t_id, 50.0)

                        for t in topics:
                            prereq_name = t.get("prereq")
                            if prereq_name and prereq_name in topic_name_to_id:
                                models.save_prerequisite(topic_name_to_id[t["name"]], topic_name_to_id[prereq_name])

                    st.balloons()
                    st.success(f"Extracted and configured {len(topics)} topics for '{active_nb['subject_name']}'!")
                    st.rerun()

# ==========================================
# TAB 3: CREATE NEW NOTEBOOK
# ==========================================
with tab_create:
    st.markdown("##### ➕ Create a New Subject Notebook")
    st.caption("Add a new subject to study alongside your existing notebooks.")

    with st.form("create_notebook_form"):
        subject_name = st.text_input("Subject Name", placeholder="e.g. Operating Systems")
        description = st.text_area("Description / Syllabus", placeholder="Brief description of the course...")
        submitted = st.form_submit_button("Create Notebook", type="primary")

        if submitted:
            if not subject_name.strip():
                st.error("Please enter a subject name.")
            else:
                new_id = models.create_notebook(user_id, subject_name.strip(), description.strip())
                st.session_state["active_notebook_id"] = new_id
                st.success(f"Notebook '{subject_name}' created!")
                st.rerun()
