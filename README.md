# 📖 Adhyay — Personalized AI Study Assistant (React + FastAPI)

**Adhyay** is an intelligent, calm, and adaptive study companion designed to help students master subjects from their own lecture notes.

Instead of a simple "chat-with-PDF" tool, Adhyay implements a **continuous cognitive learning loop**:
$$\text{Upload Notes} \longrightarrow \text{Understand Topics} \longrightarrow \text{Take Quiz} \longrightarrow \text{Analyze Mistakes} \longrightarrow \text{Track Mastery \& Decay} \longrightarrow \text{Recommend Next Study Topic}$$

---

## 📂 Project File Stack

```text
adhyay/
├── backend/
│   ├── server.py               # FastAPI application with complete REST endpoints
│   ├── database.py             # SQLite schema, multi-notebook seeding & migrations
│   ├── models.py               # Relational data access layer & user authentication
│   ├── mastery_engine.py       # Confidence-based scoring formula & forgetting decay
│   ├── recommendation_engine.py# Prerequisite graph solver & "What to Study Next"
│   ├── pdf_processor.py        # PDF text parsing via pdfplumber
│   ├── ai_service.py           # Gemini API client & intelligent conversational tutor
│   ├── sample_data/            # Sample notes and PDF generator
│   └── adhyay.db               # SQLite database
├── frontend/                   # Modern React SPA (Vite + React)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js          # API proxy to FastAPI
│   └── src/
│       ├── main.jsx
│       ├── App.jsx             # Main router, auth state & active notebook context
│       ├── api.js              # Centralized API fetcher
│       ├── index.css           # Calm, paper-like study notebook stylesheet
│       ├── components/
│       │   ├── Navbar.jsx      # Navigation header with subject switcher & user badge
│       │   ├── LoginView.jsx   # Peaceful Sign-in & Register screen with 1-click Demo Login
│       │   └── MasteryBar.jsx  # Visual progress meter with decay badge
│       └── pages/
│           ├── DashboardView.jsx # Hero recommendation, Focus Areas, Simultaneous Notebooks
│           ├── NotebooksView.jsx # Multi-notebook cards grid & PDF drag-and-drop upload
│           ├── StudyView.jsx     # Structured summaries & grounded AI chat with quick prompts
│           ├── QuizView.jsx      # Confidence-tagged MCQs & "Explain My Mistake" diagnostic
│           ├── ProgressView.jsx  # Knowledge health, decay tracking & prerequisite graph
│           └── RevisionView.jsx  # Flip flashcards & personalized Exam Cheat-Sheet
└── run_adhyay.sh               # Turnkey launcher script (starts both backend & frontend)
```

---

## 🚀 How to Access the Program

### Currently Running
Both the FastAPI backend and React frontend are running live:
👉 **[http://localhost:5173](http://localhost:5173)** (Frontend)
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)** (FastAPI Interactive Swagger Docs)

### Running in the Future
To launch both services simultaneously:
```bash
cd /Users/gopikaprakash/Documents/adhyay
./run_adhyay.sh
```

---

## 🌟 Core Features Implemented

1. **Peaceful Login & Registration**: Clean sign-in with a **1-click Demo Student Sign-In** button (`student@adhyay.edu` / `student123`).
2. **Simultaneous Multi-Notebooks**: Manage and toggle between multiple subjects simultaneously (pre-seeded with *Java OOP*, *Data Structures*, and *Digital Logic*).
3. **PDF Text Extraction**: Uses `pdfplumber` to extract clean page-by-page lecture notes.
4. **Structured Summaries & Grounded AI Chat**: Structured cards (Definition, Rules, Code Example, Pitfalls) and a working AI tutor with quick suggestion chips.
5. **Confidence-Weighted Quizzes**: Tests accuracy and certainty ($+15\%$ for Correct+Confident, $-18\%$ for Wrong+Confident misconception penalty).
6. **"Explain My Mistake"**: Analyzes student error, diagnoses conceptual misconception, quotes course notes, and provides memory heuristics.
7. **Time-Based Mastery Decay**: Models natural forgetting curve for inactive topics.
8. **Prerequisite Graph & "What to Study Next"**: Prioritizes foundational blockers before downstream concepts.
9. **Interactive Revision**: Flip-card flashcards and downloadable Exam Cheat-Sheets.
# adhyay-ai-powered-study-assistant
