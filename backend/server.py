from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import io

import database
import models
import mastery_engine
import recommendation_engine
import pdf_processor
import ai_service

# Initialize DB and seed demo data
database.init_db()
database.seed_demo_data(force=False)

app = FastAPI(title="Adhyay AI API", version="2.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- PYDANTIC SCHEMAS -----------------
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class CreateNotebookRequest(BaseModel):
    user_id: int
    subject_name: str
    description: Optional[str] = ""

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class QuizAttemptRequest(BaseModel):
    user_id: int
    question_id: int
    topic_id: int
    user_answer: str
    confidence: str # 'Guessed', 'Somewhat Sure', 'Confident'

class ExplainMistakeRequest(BaseModel):
    topic_id: int
    question: str
    student_answer: str
    correct_answer: str

# ----------------- HEALTH -----------------
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Adhyay API", "version": "2.0"}

# ----------------- AUTHENTICATION -----------------
@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = models.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"user": user}

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    user = models.register_user(req.email, req.name, req.password)
    if not user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    # Create initial starter notebook
    models.create_notebook(user["id"], "My First Notebook", "Personal study material and lecture notes.")
    return {"user": user}

# ----------------- NOTEBOOKS -----------------
@app.get("/api/notebooks")
def list_notebooks(user_id: int = 1):
    notebooks = models.get_notebooks(user_id)
    enriched = []
    for nb in notebooks:
        topics = models.get_topics(nb["id"])
        scores = models.get_mastery_scores(user_id, nb["id"])
        avg_score = sum(t["score"] for t in scores) / len(scores) if scores else 0.0
        enriched.append({
            **nb,
            "topic_count": len(topics),
            "average_mastery": round(avg_score, 1)
        })
    return {"notebooks": enriched}

@app.post("/api/notebooks")
def create_notebook(req: CreateNotebookRequest):
    nb_id = models.create_notebook(req.user_id, req.subject_name, req.description)
    nb = models.get_notebook(nb_id)
    return {"notebook": nb}

@app.delete("/api/notebooks/{nb_id}")
def delete_notebook(nb_id: int):
    models.delete_notebook(nb_id)
    return {"success": True}

# ----------------- NOTES & PDF UPLOAD -----------------
@app.get("/api/notebooks/{nb_id}/notes")
def list_notes(nb_id: int):
    notes = models.get_notes(nb_id)
    return {"notes": notes}

@app.post("/api/notebooks/{nb_id}/upload-notes")
async def upload_notes(
    nb_id: int,
    user_id: int = Form(...),
    file: UploadFile = File(...)
):
    nb = models.get_notebook(nb_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found.")

    file_bytes = await file.read()
    if file.filename.endswith(".pdf"):
        extracted = pdf_processor.extract_text_from_pdf(file_bytes)
    else:
        text_content = file_bytes.decode("utf-8", errors="ignore")
        extracted = {"raw_text": text_content, "page_count": 1}

    raw_text = extracted.get("raw_text", "")
    if len(raw_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Could not extract readable text from document.")

    # Save note
    note_id = models.save_note(nb_id, file.filename, raw_text, page_count=extracted.get("page_count", 1))

    # Extract topics via AI
    topics = ai_service.extract_topics_from_notes(raw_text, subject_name=nb["subject_name"])
    
    topic_map = {}
    created_topics = []
    for idx, t in enumerate(topics):
        t_id = models.save_topic(nb_id, t["name"], summary=t.get("summary", ""), order_index=idx + 1)
        topic_map[t["name"]] = t_id
        models.set_topic_mastery(user_id, t_id, 50.0)
        created_topics.append({"id": t_id, "name": t["name"], "summary": t.get("summary", "")})

    # Save prerequisites
    for t in topics:
        prereq = t.get("prereq")
        if prereq and prereq in topic_map:
            models.save_prerequisite(topic_map[t["name"]], topic_map[prereq])

    return {
        "success": True,
        "note_id": note_id,
        "page_count": extracted.get("page_count", 1),
        "topics": created_topics
    }

# ----------------- TOPICS & STUDY -----------------
@app.get("/api/notebooks/{nb_id}/topics")
def get_topics(nb_id: int, user_id: int = 1):
    topics = models.get_topics(nb_id)
    result = []
    for t in topics:
        mastery = models.get_topic_mastery(user_id, t["id"])
        decay = mastery_engine.calculate_decay(mastery["score"], mastery["last_reviewed_at"])
        health = mastery_engine.classify_topic_health(decay["effective_score"])
        result.append({
            **t,
            "raw_score": mastery["score"],
            "effective_score": decay["effective_score"],
            "decay_info": decay,
            "health": health
        })
    return {"topics": result}

@app.get("/api/topics/{topic_id}")
def get_topic_detail(topic_id: int, user_id: int = 1):
    t = models.get_topic(topic_id)
    if not t:
        raise HTTPException(status_code=404, detail="Topic not found.")
    mastery = models.get_topic_mastery(user_id, topic_id)
    decay = mastery_engine.calculate_decay(mastery["score"], mastery["last_reviewed_at"])
    health = mastery_engine.classify_topic_health(decay["effective_score"])
    return {
        "topic": {
            **t,
            "raw_score": mastery["score"],
            "effective_score": decay["effective_score"],
            "decay_info": decay,
            "health": health
        }
    }

@app.post("/api/topics/{topic_id}/summary/regenerate")
def regenerate_summary(topic_id: int):
    t = models.get_topic(topic_id)
    if not t:
        raise HTTPException(status_code=404, detail="Topic not found.")
    notes = models.get_notes(t["notebook_id"])
    context = "\n".join([n["raw_text"] for n in notes])
    new_summary = ai_service.generate_topic_summary(t["name"], context)
    models.update_topic_summary(topic_id, new_summary)
    return {"summary": new_summary}

@app.post("/api/topics/{topic_id}/chat")
def topic_chat(topic_id: int, req: ChatRequest):
    t = models.get_topic(topic_id)
    if not t:
        raise HTTPException(status_code=404, detail="Topic not found.")
    notes = models.get_notes(t["notebook_id"])
    context = f"{t.get('summary', '')}\n" + "\n".join([n["raw_text"] for n in notes])
    reply = ai_service.chat_with_topic(
        topic_name=t["name"],
        notes_context=context,
        chat_history=req.history or [],
        user_message=req.message
    )
    return {"reply": reply}

# ----------------- QUIZZES & ADAPTIVE EVALUATION -----------------
@app.get("/api/topics/{topic_id}/quiz")
def get_topic_quiz(topic_id: int):
    questions = models.get_quiz_questions_by_topic(topic_id)
    return {"questions": questions}

@app.post("/api/topics/{topic_id}/quiz/generate")
def generate_quiz(topic_id: int):
    t = models.get_topic(topic_id)
    if not t:
        raise HTTPException(status_code=404, detail="Topic not found.")
    notes = models.get_notes(t["notebook_id"])
    context = f"{t.get('summary', '')}\n" + "\n".join([n["raw_text"] for n in notes])
    generated = ai_service.generate_quiz_questions(t["name"], context, num_questions=3)
    saved = []
    for q in generated:
        qid = models.save_quiz_question(topic_id, q["question"], q["options"], q["correct_answer"], q.get("explanation", ""))
        saved.append({"id": qid, **q})
    return {"questions": saved}

@app.post("/api/quiz/attempt")
def record_attempt(req: QuizAttemptRequest):
    topic = models.get_topic(req.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    # Find the question
    questions = models.get_quiz_questions_by_topic(req.topic_id)
    q = next((item for item in questions if item["id"] == req.question_id), None)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found.")

    is_correct = (req.user_answer.strip() == q["correct_answer"].strip())
    
    # Calculate score update with confidence
    mastery = models.get_topic_mastery(req.user_id, req.topic_id)
    old_score = mastery["score"]
    new_score = mastery_engine.calculate_new_mastery(old_score, is_correct, req.confidence)
    delta = round(new_score - old_score, 1)

    # Persist attempt & mastery
    models.record_quiz_attempt(req.user_id, req.question_id, req.topic_id, req.user_answer, is_correct, req.confidence)
    models.set_topic_mastery(req.user_id, req.topic_id, new_score)

    return {
        "is_correct": is_correct,
        "correct_answer": q["correct_answer"],
        "explanation": q.get("explanation", ""),
        "old_score": old_score,
        "new_score": new_score,
        "delta": delta,
        "confidence": req.confidence
    }

@app.post("/api/quiz/explain-mistake")
def explain_mistake_endpoint(req: ExplainMistakeRequest):
    topic = models.get_topic(req.topic_id)
    notes = models.get_notes(topic["notebook_id"]) if topic else []
    context = "\n".join([n["raw_text"] for n in notes])
    diagnostic = ai_service.explain_mistake(
        topic_name=topic["name"] if topic else "Concept",
        question=req.question,
        student_answer=req.student_answer,
        correct_answer=req.correct_answer,
        notes_context=f"{topic.get('summary', '') if topic else ''}\n{context}"
    )
    return {"diagnostic": diagnostic}

# ----------------- PROGRESS, KNOWLEDGE GRAPH & RECOMMENDATIONS -----------------
@app.get("/api/notebooks/{nb_id}/progress")
def get_progress(nb_id: int, user_id: int = 1):
    topics = models.get_mastery_scores(user_id, nb_id)
    prereqs = models.get_prerequisites_for_notebook(nb_id)
    recommendations = recommendation_engine.get_study_recommendations(user_id, nb_id, topics, prereqs)
    
    # Enriched topic list with health classification
    topic_cards = []
    for t in topics:
        decay = mastery_engine.calculate_decay(t["score"], t["last_reviewed_at"])
        health = mastery_engine.classify_topic_health(decay["effective_score"])
        topic_cards.append({
            "topic_id": t["topic_id"],
            "topic_name": t["topic_name"],
            "raw_score": t["score"],
            "effective_score": decay["effective_score"],
            "last_reviewed_at": t["last_reviewed_at"],
            "decay_info": decay,
            "health": health
        })

    attempts = models.get_quiz_attempts(user_id, limit=20)

    return {
        "topics": topic_cards,
        "prerequisites": prereqs,
        "recommendations": recommendations,
        "recent_attempts": attempts
    }

# ----------------- REVISION TOOLS (FLASHCARDS & CHEAT-SHEET) -----------------
@app.post("/api/topics/{topic_id}/flashcards")
def get_flashcards(topic_id: int):
    t = models.get_topic(topic_id)
    if not t:
        raise HTTPException(status_code=404, detail="Topic not found.")
    notes = models.get_notes(t["notebook_id"])
    context = f"{t.get('summary', '')}\n" + "\n".join([n["raw_text"] for n in notes])
    cards = ai_service.generate_flashcards(t["name"], context, count=3)
    return {"flashcards": cards}

@app.post("/api/notebooks/{nb_id}/cheat-sheet")
def get_cheat_sheet(nb_id: int, user_id: int = 1):
    nb = models.get_notebook(nb_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found.")
    topics = models.get_mastery_scores(user_id, nb_id)
    weak_data = []
    for t in topics:
        t_obj = models.get_topic(t["topic_id"])
        weak_data.append({
            "name": t["topic_name"],
            "score": t["score"],
            "summary": t_obj.get("summary", "") if t_obj else ""
        })
    weak_data.sort(key=lambda x: x["score"])
    sheet = ai_service.generate_exam_cheat_sheet(nb["subject_name"], weak_data[:4])
    return {"cheat_sheet": sheet}
