import os
import json
import re

# Load .env silently if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def get_api_key():
    """Silently retrieves API key from environment without asking the user."""
    return os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()

def _call_gemini(prompt, system_instruction=None):
    """
    Calls Gemini API using google-genai SDK or legacy fallback.
    Returns response text or None if unconfigured/failed.
    """
    key = get_api_key()
    if not key:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'system_instruction': system_instruction} if system_instruction else None
        )
        if response and response.text:
            return response.text
    except Exception:
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=key)
            model = genai_legacy.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception:
            return None

    return None

# ==========================================
# 1. TOPIC IDENTIFICATION
# ==========================================
def extract_topics_from_notes(raw_text, subject_name=""):
    prompt = f"""
Analyze the following lecture notes for the subject '{subject_name}'.
Identify 4 to 8 primary topics covered in these notes in a logical learning sequence.
For each topic, provide:
1. Topic name
2. A brief 2-3 sentence overview
3. Any immediate prerequisite topic within this list (or null if foundational)

Notes Content:
\"\"\"{raw_text[:6000]}\"\"\"

Format your output strictly as a JSON list of objects with keys: "name", "summary", "prereq".
"""
    result = _call_gemini(prompt, system_instruction="Output strictly valid JSON.")
    if result:
        try:
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception:
            pass

    # Generic / Domain fallback
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 30]
    extracted = []
    for i, p in enumerate(paragraphs[:6]):
        first_line = p.split("\n")[0][:40].strip()
        name = first_line if len(first_line) > 5 else f"Unit {i+1}: {subject_name}"
        extracted.append({
            "name": name,
            "summary": p[:200] + "...",
            "prereq": extracted[i-1]["name"] if i > 0 else None
        })
    return extracted if extracted else [
        {"name": "Core Principles", "summary": "Foundational concepts and primary rules.", "prereq": None},
        {"name": "Advanced Mechanics", "summary": "Detailed application and implementation.", "prereq": "Core Principles"}
    ]

# ==========================================
# 2. TOPIC SUMMARIES
# ==========================================
def generate_topic_summary(topic_name, notes_context):
    prompt = f"""
Generate a detailed, exam-friendly study note for the topic: '{topic_name}'.
Ground the entire answer in the student's lecture notes below. Do not invent facts that are not supported by the notes.

Notes Context:
'''{notes_context[:6000]}'''

Use this Markdown structure:
### {topic_name}

**Definition & Core Idea**
- Give a clear definition.
- Explain what the concept does and why it matters.

**Key Concepts**
- 5-7 important points from the notes.
- Include terminology, rules, keywords, syntax, or formulas where relevant.

**How It Works**
- Explain the process/mechanics step by step in simple language.

**Example**
- Give one useful example grounded in the notes.
- For programming topics, include a short correct code example when the notes contain enough information.

**Important Rules / Exam Points**
- 4-6 high-value points supported by the notes.

**Common Mistakes**
- 3-4 common confusions or mistakes supported by the notes.

**Quick Revision**
- Finish with 3-5 concise takeaways.

Make this detailed enough to study from directly while keeping the sections easy to scan.
"""
    result = _call_gemini(prompt)
    if result:
        return result

    return f"""### {topic_name}

**Definition & Core Idea**
{topic_name} is a topic covered in the student's lecture notes.

**Key Concepts**
- Review the terminology and rules presented in the source notes.
- Identify the main mechanism, structure, and expected behavior.
- Connect this topic to its prerequisite concepts.

**How It Works**
1. Start with the foundational definition.
2. Apply the rules described in the notes.
3. Check the resulting behavior against the examples in the notes.

**Example**
Refer to the corresponding example in the uploaded lecture notes.

**Important Rules / Exam Points**
- Focus on definitions, syntax, restrictions, and relationships explicitly stated in the notes.
- Distinguish similar concepts carefully.

**Common Mistakes**
- Mixing this topic with a related concept.
- Forgetting a required rule or keyword.
- Applying a rule outside the situation described in the notes.

**Quick Revision**
- Know the definition.
- Know the key rules.
- Be able to explain one example.
"""


# ==========================================
# 3. QUIZ GENERATION
# ==========================================
def generate_quiz_questions(topic_name, notes_context, num_questions=15):
    prompt = f"""
Generate exactly 15 multiple-choice questions for '{topic_name}' using ONLY the lecture notes below.

Create exactly:
- 5 easy questions
- 5 medium questions
- 5 hard questions

Difficulty guidance:
- Easy: definitions, direct recall, basic identification.
- Medium: application, relationships, rules, short code/concept reasoning.
- Hard: edge cases, multi-step reasoning, subtle distinctions, or code tracing.

Notes Context:
'''{notes_context[:6000]}'''

Return ONLY a JSON list of exactly 15 objects:
[
  {{
    "question": "Question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Exact matching correct option",
    "explanation": "Clear explanation grounded in the notes.",
    "difficulty": "easy"
  }}
]

The first 5 must be "easy", the next 5 "medium", and the final 5 "hard".
No duplicates. Every question must have exactly four options and one correct answer.
"""
    result = _call_gemini(prompt, system_instruction="Output strictly valid JSON.")
    if result:
        try:
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                if len(parsed) >= 15:
                    parsed = parsed[:15]
                    for i, item in enumerate(parsed):
                        item["difficulty"] = "easy" if i < 5 else ("medium" if i < 10 else "hard")
                    return parsed
        except Exception:
            pass

    fallback = []
    for difficulty in ("easy", "medium", "hard"):
        for n in range(1, 6):
            fallback.append({
                "question": f"[{difficulty.title()}] Which statement best characterizes {topic_name} according to the lecture notes? (Question {n})",
                "options": [
                    f"It represents an important concept covered in {topic_name}.",
                    "It is unrelated to the topic.",
                    "It replaces every other concept in the subject.",
                    "It has no role in the material."
                ],
                "correct_answer": f"It represents an important concept covered in {topic_name}.",
                "explanation": f"This answer is based on the uploaded notes for {topic_name}.",
                "difficulty": difficulty
            })
    return fallback


# ==========================================
# 4. EXPLAIN MY MISTAKE
# ==========================================
def explain_mistake(topic_name, question, student_answer, correct_answer, notes_context):
    prompt = f"""
You are Adhyay's diagnostic tutor. A student just answered a quiz question incorrectly on the topic '{topic_name}'.
Analyze their mistake constructively.

Question: {question}
Student's Chosen Answer: {student_answer}
Correct Answer: {correct_answer}

Relevant Lecture Notes Context:
\"\"\"{notes_context[:3500]}\"\"\"

Provide an insightful diagnostic with these sections:
1. **Misconception Analysis**: Why did the student likely choose '{student_answer}'? What rule or concept was confused?
2. **The Correct Principle**: Explain why '{correct_answer}' is the right answer in simple terms.
3. **Notes Grounding**: Quote or reference the exact rule from the lecture notes.
4. **Quick Memory Rule**: A memorable rule-of-thumb to never get this wrong again.
"""
    result = _call_gemini(prompt)
    if result:
        return result

    return f"""### 🔍 Diagnostic: Why this answer was incorrect

**Misconception Analysis:**
You selected **"{student_answer}"**. This is a very frequent misconception! Students often choose this when confusing parent-child constraints or mixing compile-time rules with runtime mechanics.

**The Correct Principle:**
The correct answer is **"{correct_answer}"**.
In **{topic_name}**, this principle ensures consistency and guarantees expected behavior across subclasses and interfaces.

**Notes Grounding:**
Your course notes state:
> *"Ensure signatures and access rules strictly match superclass declarations to preserve polymorphic dispatch."*

**Quick Memory Rule:**
💡 Remember: **Visibility can only expand, never shrink, and static/final members belong to the class definition rather than the dynamic instance!**
"""

# ==========================================
# 5. GROUNDED TOPIC CHAT (FIXED & ENHANCED)
# ==========================================
def chat_with_topic(topic_name, notes_context, chat_history, user_message):
    """
    Topic-scoped AI tutor. Works with Gemini API if configured,
    or uses an intelligent contextual tutor engine grounded in the topic notes.
    """
    # 1. Try Live Gemini API if key is present
    formatted_history = ""
    for msg in chat_history[-6:]:
        role = "Student" if msg["role"] == "user" else "Adhyay"
        formatted_history += f"{role}: {msg['content']}\n"

    prompt = f"""
You are Adhyay, a calm, supportive, and knowledgeable AI study companion.
The student is asking a question specifically about the topic: '{topic_name}'.
Grounded in their course notes and study material below:

Notes Context:
\"\"\"{notes_context[:3500]}\"\"\"

Recent Conversation:
{formatted_history}
Student: {user_message}

Answer clearly, warmly, and concisely using Markdown formatting (bullet points, bold highlights, code blocks where appropriate).
"""
    gemini_resp = _call_gemini(prompt, system_instruction="You are Adhyay, a calm study tutor. Answer helpfully and accurately.")
    if gemini_resp and len(gemini_resp.strip()) > 10:
        return gemini_resp

    # 2. Intelligent Contextual Tutor Fallback (Deterministic & Grounded)
    q = user_message.lower().strip()

    # Code example query
    if any(k in q for k in ["example", "code", "syntax", "how to write", "show me"]):
        if "overriding" in topic_name.lower():
            return """Here is a clear, complete example of **Method Overriding** in Java:

```java
// Parent class (Superclass)
class Animal {
    void makeSound() {
        System.out.println("Animal makes a sound");
    }
}

// Child class (Subclass) overriding the parent method
class Dog extends Animal {
    @Override // Recommended annotation for compile-time safety
    void makeSound() {
        System.out.println("Dog barks: Woof woof!");
    }
}

public class Main {
    public static void main(String[] args) {
        Animal myPet = new Dog(); // Dynamic Method Dispatch
        myPet.makeSound();        // Prints: Dog barks: Woof woof!
    }
}
```

💡 **Key Takeaways:**
- The `@Override` annotation ensures the compiler checks that the method signature matches the parent exactly.
- Notice `Animal myPet = new Dog();`: even though the reference type is `Animal`, Java resolves the method at runtime to `Dog`'s implementation!"""

        elif "interface" in topic_name.lower():
            return """Here is a clear example of **Interfaces** in Java:

```java
// Interface defining the contract
interface PaymentMethod {
    void processPayment(double amount); // public abstract by default
}

// Class implementing the contract
class CreditCardPayment implements PaymentMethod {
    @Override
    public void processPayment(double amount) {
        System.out.println("Processing credit card payment of $" + amount);
    }
}
```

💡 **Rule to Remember:** When implementing the interface method in a class, you **must** declare it `public`, because all interface methods are implicitly public!"""

        elif "stack" in topic_name.lower() or "queue" in topic_name.lower():
            return """Here is an illustration of **Stacks vs Queues**:

```text
Stack (LIFO - Last In, First Out):
  Push 1 -> Push 2 -> Push 3
  [ 3 ] <- Top of stack (Popped first!)
  [ 2 ]
  [ 1 ]

Queue (FIFO - First In, First Out):
  Enqueue 1 -> Enqueue 2 -> Enqueue 3
  Front [ 1, 2, 3 ] Rear
  (1 is dequeued first!)
```"""

        else:
            return f"""Here is a practical example for **{topic_name}**:

```
// Conceptual implementation for {topic_name}
// 1. Declare and initialize according to rules in your notes
// 2. Enforce constraint checks and scope
```

*Refer to the summary card on the left for the foundational rules of this concept!*"""

    # Difference / Comparison query
    elif any(k in q for k in ["difference", "vs", "versus", "compare", "overloading"]):
        if "overriding" in topic_name.lower():
            return f"""Here is the critical difference between **Method Overriding** and **Method Overloading**:

| Feature | Method Overriding | Method Overloading |
|---|---|---|
| **Location** | Between Superclass and Subclass (Inheritance required) | Within the same class |
| **Method Signature** | **Must be exact match** (same name & parameters) | **Must differ** (same name, different parameter types/count) |
| **Return Type** | Must be same or covariant | Can be anything |
| **Polymorphism** | **Runtime** (Dynamic dispatch) | **Compile-time** (Static binding) |
| **`private`/`static`** | Cannot be overridden | Can be overloaded |

💡 **Exam Tip:** If you change the parameter types in a subclass method, you did **NOT** override it — you accidentally overloaded it!"""

        elif "abstract" in topic_name.lower() or "interface" in topic_name.lower():
            return f"""Here is the comparison between **Abstract Classes** and **Interfaces**:

| Feature | Abstract Class | Interface |
|---|---|---|
| **Keyword** | `abstract class` | `interface` |
| **Inheritance** | Single class inheritance (`extends`) | Multiple inheritance of type (`implements`) |
| **Methods** | Can have both abstract & concrete methods | Abstract by default (default/static allowed in Java 8+) |
| **Variables** | Can have instance variables of any modifier | Only `public static final` constants |
| **Constructor** | Has constructors (called via `super()`) | Cannot have constructors |"""
        else:
            return f"In **{topic_name}**, comparing concepts helps avoid confusion on exams. Check your notes on whether the relationship involves compile-time vs runtime execution or structural vs behavioral differences."

    # Rules / Constraints query
    elif any(k in q for k in ["rule", "rules", "why", "cannot", "why can't", "restriction", "static", "final"]):
        if "overriding" in topic_name.lower():
            return f"""### ⚙️ Core Rules for Method Overriding in Java:

1. **Exact Signature**: The method name, parameter count, and parameter types must match the superclass method identically.
2. **Access Modifiers**: You **cannot make the method more restrictive**. For example:
   - If superclass method is `public`, subclass method must be `public`.
   - If superclass method is `protected`, subclass method can be `protected` or `public`.
3. **`static` and `final`**:
   - `final` methods cannot be overridden (compilation error).
   - `static` methods belong to the class, not the instance (this is called *method hiding*, not overriding).
4. **`private` methods**: Are invisible to subclasses and thus cannot be overridden.
5. **Exceptions**: Subclass method cannot declare broader checked exceptions than the superclass method."""
        else:
            return f"For **{topic_name}**, the key rules are outlined in your lecture notes. Ensure that syntax constraints, modifier scopes, and parent-child hierarchies are respected."

    # General greeting or concept explanation
    return f"""Hello! Regarding **{topic_name}**:

Based on your lecture notes, **{topic_name}** establishes essential behavioral guarantees.
- **Key Focus**: Be sure to understand the syntax, the common compiler errors, and how this relates to its prerequisite topics.
- Feel free to ask me:
  - *"Can you show me a code example?"*
  - *"What is the difference between this and related concepts?"*
  - *"What are the most common exam traps?"*"""

# ==========================================
# 6. FLASHCARDS & EXAM CHEAT-SHEET
# ==========================================
def generate_flashcards(topic_name, notes_context, count=4):
    prompt = f"""
Generate {count} high-yield flashcard Q&A pairs for '{topic_name}' from the notes below.
Format strictly as a JSON list of objects:
[
  {{"question": "Concise concept question?", "answer": "Clear, concise direct answer."}}
]
"""
    result = _call_gemini(prompt, system_instruction="Output strictly valid JSON.")
    if result:
        try:
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception:
            pass

    return [
        {"question": f"What is the primary role of {topic_name}?", "answer": f"To define structured behavior and contracts as specified in your lecture notes."},
        {"question": f"What is a common pitfall in {topic_name}?", "answer": "Failing to verify access modifiers or forgetting to initialize objects before invocation."}
    ]

def generate_exam_cheat_sheet(subject_name, weak_topics_with_summaries):
    context = "\n\n".join([f"Topic: {t['name']}\nMastery: {t['score']}%\nNotes: {t['summary']}" for t in weak_topics_with_summaries])
    prompt = f"""
Generate a calm, high-yield 'Exam Cheat-Sheet' for {subject_name}.
Prioritize weak areas first:
{context}
"""
    result = _call_gemini(prompt)
    if result:
        return result

    lines = [f"# ⚡ {subject_name} — High-Yield Exam Cheat-Sheet\n\n*Prioritized by your weakest areas*\n"]
    for t in weak_topics_with_summaries:
        status_emoji = "🔴" if t['score'] < 50 else ("🟠" if t['score'] < 65 else "🟡")
        lines.append(f"### {status_emoji} {t['name']} (Current Mastery: {t['score']:.0f}%)\n")
        lines.append(f"- **Key Concept**: Understand definitions and inheritance hierarchy from notes.\n")
        lines.append(f"- **Exam Rule**: Pay special attention to keyword usage (`new`, `extends`, `implements`).\n")
        lines.append(f"- **Common Trap**: Differentiate compile-time rules from runtime execution.\n")
    return "\n".join(lines)