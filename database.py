import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adhyay.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT DEFAULT 'password123',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT 'password123'")
    except Exception:
        pass


    # 2. Notebooks (Multiple notebooks can exist simultaneously for each user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notebooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 3. Notes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notebook_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        page_count INTEGER DEFAULT 1,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
    );
    """)

    # 4. Topics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notebook_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        summary TEXT,
        order_index INTEGER DEFAULT 0,
        FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
    );
    """)

    # 5. Topic Prerequisites
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topic_prereqs (
        topic_id INTEGER NOT NULL,
        prereq_topic_id INTEGER NOT NULL,
        PRIMARY KEY (topic_id, prereq_topic_id),
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
        FOREIGN KEY (prereq_topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );
    """)

    # 6. Quiz Questions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        options_json TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );
    """)

    # 7. Quiz Attempts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        user_answer TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        confidence TEXT NOT NULL, -- 'Guessed', 'Somewhat Sure', 'Confident'
        attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE,
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );
    """)

    # 8. Mastery Scores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mastery (
        user_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        score REAL NOT NULL, -- 0.0 to 100.0
        last_reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, topic_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def seed_demo_data(force=False):
    conn = get_connection()
    cursor = conn.cursor()

    if not force:
        cursor.execute("SELECT id FROM notebooks LIMIT 1")
        if cursor.fetchone():
            conn.close()
            return

    # Seed Default Student Users
    cursor.execute("""
    INSERT OR REPLACE INTO users (id, email, name, password)
    VALUES (1, 'student@adhyay.edu', 'Adhyay Student', 'student123')
    """)
    user_id = 1

    # =========================================================================
    # NOTEBOOK 1: JAVA PROGRAMMING (OOP)
    # =========================================================================
    cursor.execute("""
    INSERT INTO notebooks (user_id, subject_name, description)
    VALUES (?, 'Java Programming (OOP)', 'Core Object-Oriented Programming concepts in Java: classes, polymorphism, and abstraction.')
    """, (user_id,))
    nb1_id = cursor.lastrowid

    nb1_notes = """
Java Object Oriented Programming Notes:
Classes and Objects: A class is a blueprint or template for creating objects. An object is an instance of a class with state and behavior.
Constructors: Special methods invoked during object creation to initialize fields. Constructors have no return type and match the class name exactly.
Inheritance: Mechanism where a child class inherits properties and methods from a parent class using the 'extends' keyword. Java supports single class inheritance.
Method Overriding: When a subclass provides a specific implementation of a method already defined in its superclass. Must have the exact same signature and return type. Cannot override private, static, or final methods.
Abstract Classes: Classes declared with 'abstract' that cannot be instantiated directly. May contain abstract methods (without body) as well as concrete methods.
Interfaces: A contract specifying what a class must do. Declared with 'interface', implemented with 'implements'. All methods are public and abstract by default (prior to Java 8). A class can implement multiple interfaces.
"""
    cursor.execute("""
    INSERT INTO notes (notebook_id, filename, raw_text, page_count)
    VALUES (?, 'Java_OOP_Lecture_Notes.pdf', ?, 6)
    """, (nb1_id, nb1_notes))

    nb1_topics = [
        ("Classes and Objects", "### Classes and Objects\n\n**Definition:** A class is a blueprint for creating objects. An object has state (attributes) and behavior (methods).\n\n**Key Rules:**\n- `new` keyword allocates heap memory.\n- `this` refers to the current instance.\n\n**Example:**\n```java\nclass Student {\n    String name;\n    void study() { System.out.println(\"Studying\"); }\n}\n```\n\n**Common Pitfalls:** Calling methods on an uninitialized reference causes a `NullPointerException`.", 1),
        ("Constructors", "### Constructors\n\n**Definition:** Special method invoked when an object is instantiated to initialize instance variables.\n\n**Key Rules:**\n- Matches class name exactly.\n- No return type (not even void).\n- Default constructor is provided only if no explicit constructor is defined.\n\n**Example:**\n```java\npublic Student(String name) { this.name = name; }\n```\n\n**Common Pitfalls:** Adding `void` to a constructor definition turns it into a normal method.", 2),
        ("Inheritance", "### Inheritance\n\n**Definition:** Mechanism where a subclass inherits state and methods from a superclass using `extends`.\n\n**Key Rules:**\n- `extends` keyword.\n- Java supports single class inheritance.\n- `super()` calls superclass constructor.\n\n**Example:**\n```java\nclass Dog extends Animal { void bark() {} }\n```\n\n**Common Pitfalls:** Private members of the superclass are not directly accessible in the subclass.", 3),
        ("Method Overriding", "### Method Overriding\n\n**Definition:** When a subclass redefines a method from its superclass with the exact same signature.\n\n**Key Rules:**\n- Exact same name, arguments, and compatible return type.\n- Cannot have more restrictive access.\n- Static, private, and final methods CANNOT be overridden.\n- Dynamic method dispatch resolves method call at runtime.\n\n**Example:**\n```java\n@Override\npublic void draw() { System.out.println(\"Circle\"); }\n```\n\n**Common Pitfalls:** Changing parameters creates overloading, not overriding.", 4),
        ("Abstract Classes", "### Abstract Classes\n\n**Definition:** Incomplete class declared with `abstract` that cannot be instantiated directly.\n\n**Key Rules:**\n- Can contain both abstract (bodyless) and concrete methods.\n- Subclasses must implement all abstract methods or declare themselves abstract.\n\n**Example:**\n```java\nabstract class Vehicle { abstract void drive(); }\n```\n\n**Common Pitfalls:** Calling `new Vehicle()` fails compilation.", 5),
        ("Interfaces", "### Interfaces\n\n**Definition:** Blueprint of a class specifying what it must do. Enables multiple inheritance of type.\n\n**Key Rules:**\n- Uses `interface` and `implements`.\n- Variables are `public static final`.\n- Methods are `public abstract` by default.\n\n**Example:**\n```java\ninterface Drivable { void drive(); }\n```\n\n**Common Pitfalls:** Forgetting `public` when implementing an interface method in a class.", 6)
    ]

    nb1_tids = {}
    for name, sum_txt, ord_idx in nb1_topics:
        cursor.execute("INSERT INTO topics (notebook_id, name, summary, order_index) VALUES (?, ?, ?, ?)",
                       (nb1_id, name, sum_txt, ord_idx))
        nb1_tids[name] = cursor.lastrowid

    # Seed Prereqs for NB1
    nb1_prereqs = [
        ("Constructors", "Classes and Objects"),
        ("Inheritance", "Classes and Objects"),
        ("Method Overriding", "Inheritance"),
        ("Abstract Classes", "Inheritance"),
        ("Interfaces", "Abstract Classes"),
    ]
    for top_n, pre_n in nb1_prereqs:
        cursor.execute("INSERT INTO topic_prereqs VALUES (?, ?)", (nb1_tids[top_n], nb1_tids[pre_n]))

    # Seed Quizzes for NB1
    nb1_quizzes = [
        (nb1_tids["Classes and Objects"], "Which keyword is used to allocate memory for an object in Java?", ["alloc", "create", "new", "malloc"], "new", "The 'new' keyword dynamically creates object instances on the heap."),
        (nb1_tids["Constructors"], "What return type does a Java constructor declare?", ["void", "None (no return type)", "int", "boolean"], "None (no return type)", "Constructors never declare any return type."),
        (nb1_tids["Inheritance"], "Which keyword establishes inheritance between two classes in Java?", ["implements", "inherits", "extends", "super"], "extends", "The 'extends' keyword is used for class inheritance."),
        (nb1_tids["Method Overriding"], "Which method type CANNOT be overridden in a Java subclass?", ["public", "protected", "static and final", "package-private"], "static and final", "Static and final methods cannot be overridden dynamically."),
        (nb1_tids["Method Overriding"], "What happens if you change parameter types when overriding a superclass method?", ["Compilation error", "It creates method overloading instead", "The superclass method is deleted", "Runtime exception"], "It creates method overloading instead", "Changing parameter signatures results in method overloading, not overriding."),
        (nb1_tids["Abstract Classes"], "Can an abstract class be instantiated directly using 'new'?", ["Yes, always", "Only if it has no abstract methods", "No, never", "Yes, in the same package"], "No, never", "Abstract classes cannot be directly instantiated."),
        (nb1_tids["Interfaces"], "What are variables declared inside a Java interface by default?", ["private and static", "public, static, and final", "protected and transient", "package-private"], "public, static, and final", "All fields in a Java interface are implicitly public, static, and final constants.")
    ]
    for tid, q, opts, ans, exp in nb1_quizzes:
        cursor.execute("INSERT INTO quiz_questions (topic_id, question, options_json, correct_answer, explanation) VALUES (?, ?, ?, ?, ?)",
                       (tid, q, json.dumps(opts), ans, exp))

    now = datetime.now()
    nb1_mastery = [
        ("Classes and Objects", 89.0, now - timedelta(days=2)),
        ("Constructors", 82.0, now - timedelta(days=3)),
        ("Inheritance", 68.0, now - timedelta(days=5)),
        ("Method Overriding", 42.0, now - timedelta(days=1)),
        ("Abstract Classes", 58.0, now - timedelta(days=4)),
        ("Interfaces", 55.0, now - timedelta(days=6)),
    ]
    for name, sc, dt in nb1_mastery:
        cursor.execute("INSERT INTO mastery VALUES (?, ?, ?, ?)", (user_id, nb1_tids[name], sc, dt.strftime("%Y-%m-%d %H:%M:%S")))

    # =========================================================================
    # NOTEBOOK 2: DATA STRUCTURES & ALGORITHMS (Simultaneous Notebook)
    # =========================================================================
    cursor.execute("""
    INSERT INTO notebooks (user_id, subject_name, description)
    VALUES (?, 'Data Structures & Algorithms', 'Foundational data organization: Arrays, Linked Lists, Trees, and Algorithmic complexity.')
    """, (user_id,))
    nb2_id = cursor.lastrowid

    nb2_notes = """
Data Structures Lecture Notes:
Arrays: Contiguous memory allocation, O(1) random access by index, fixed capacity. Insertion and deletion require O(n) element shifting.
Linked Lists: Sequence of nodes where each node contains data and a pointer to the next node. Dynamic size, O(1) insertion at head, O(n) access.
Stacks: Last-In First-Out (LIFO) structure with push() and pop() in O(1) time. Used in function call stacks and backtracking.
Queues: First-In First-Out (FIFO) structure with enqueue() at rear and dequeue() at front in O(1) time. Used in BFS and scheduling.
Binary Search Trees (BST): Hierarchical tree where for every node, left subtree values < node value < right subtree values. O(log n) average search time.
"""
    cursor.execute("INSERT INTO notes (notebook_id, filename, raw_text, page_count) VALUES (?, 'DSA_Core_Notes.pdf', ?, 5)",
                   (nb2_id, nb2_notes))

    nb2_topics = [
        ("Arrays and Memory", "### Arrays and Memory\n\n**Definition:** Contiguous sequential block of memory holding elements of the same data type.\n\n**Key Rules:**\n- Index lookup is O(1).\n- Fixed capacity upon creation.\n- Insertion/deletion at arbitrary position takes O(n) time.\n\n**Common Pitfalls:** IndexOutOfBoundsException.", 1),
        ("Linked Lists", "### Linked Lists\n\n**Definition:** Linear collection of nodes where each node stores a data value and a reference pointer to the next node.\n\n**Key Rules:**\n- Dynamic memory allocation.\n- O(1) insertion at the head.\n- O(n) linear search to find an element by index.\n\n**Common Pitfalls:** Losing the head pointer causes entire list to be garbage collected.", 2),
        ("Stacks and Queues", "### Stacks and Queues\n\n**Definition:** Restricted linear structures: Stack is LIFO (Last-In-First-Out) and Queue is FIFO (First-In-First-Out).\n\n**Key Rules:**\n- Stack push/pop take O(1).\n- Queue enqueue/dequeue take O(1).\n\n**Common Pitfalls:** Popping from an empty stack causes Stack Underflow.", 3),
        ("Binary Search Trees", "### Binary Search Trees (BST)\n\n**Definition:** A binary tree where for every node, values in the left subtree are smaller and values in the right subtree are greater.\n\n**Key Rules:**\n- In-order traversal visits nodes in strictly sorted ascending order.\n- Average search/insert is O(log n); worst-case degraded tree is O(n).\n\n**Common Pitfalls:** Unbalanced BST degrades to a linked list.", 4)
    ]

    nb2_tids = {}
    for name, sum_txt, ord_idx in nb2_topics:
        cursor.execute("INSERT INTO topics (notebook_id, name, summary, order_index) VALUES (?, ?, ?, ?)",
                       (nb2_id, name, sum_txt, ord_idx))
        nb2_tids[name] = cursor.lastrowid

    # Prereqs for NB2: Arrays -> Linked Lists -> Stacks and Queues -> BST
    cursor.execute("INSERT INTO topic_prereqs VALUES (?, ?)", (nb2_tids["Linked Lists"], nb2_tids["Arrays and Memory"]))
    cursor.execute("INSERT INTO topic_prereqs VALUES (?, ?)", (nb2_tids["Stacks and Queues"], nb2_tids["Linked Lists"]))
    cursor.execute("INSERT INTO topic_prereqs VALUES (?, ?)", (nb2_tids["Binary Search Trees"], nb2_tids["Stacks and Queues"]))

    # Quizzes for NB2
    nb2_quizzes = [
        (nb2_tids["Arrays and Memory"], "What is the time complexity of accessing an array element by its index?", ["O(1)", "O(n)", "O(log n)", "O(n^2)"], "O(1)", "Arrays provide constant time random access via base address arithmetic."),
        (nb2_tids["Linked Lists"], "What is the main advantage of a linked list over a standard array?", ["Faster random element access", "Dynamic resizing without memory reallocation", "Lower memory overhead per element", "Automatic sorting"], "Dynamic resizing without memory reallocation", "Linked lists do not require contiguous memory blocks and can grow dynamically."),
        (nb2_tids["Stacks and Queues"], "Which data structure follows the Last-In First-Out (LIFO) principle?", ["Queue", "Stack", "Binary Tree", "Heap"], "Stack", "Stacks operate strictly on LIFO (Last In First Out)."),
        (nb2_tids["Binary Search Trees"], "Which tree traversal of a Binary Search Tree produces elements in sorted ascending order?", ["Pre-order", "In-order", "Post-order", "Level-order"], "In-order", "In-order traversal (Left, Root, Right) processes BST nodes in non-decreasing order.")
    ]
    for tid, q, opts, ans, exp in nb2_quizzes:
        cursor.execute("INSERT INTO quiz_questions (topic_id, question, options_json, correct_answer, explanation) VALUES (?, ?, ?, ?, ?)",
                       (tid, q, json.dumps(opts), ans, exp))

    nb2_mastery = [
        ("Arrays and Memory", 92.0, now - timedelta(days=1)),
        ("Linked Lists", 74.0, now - timedelta(days=3)),
        ("Stacks and Queues", 60.0, now - timedelta(days=5)),
        ("Binary Search Trees", 45.0, now - timedelta(days=2)),
    ]
    for name, sc, dt in nb2_mastery:
        cursor.execute("INSERT INTO mastery VALUES (?, ?, ?, ?)", (user_id, nb2_tids[name], sc, dt.strftime("%Y-%m-%d %H:%M:%S")))

    # =========================================================================
    # NOTEBOOK 3: DIGITAL LOGIC & COMPUTER ORGANIZATION (Simultaneous Notebook)
    # =========================================================================
    cursor.execute("""
    INSERT INTO notebooks (user_id, subject_name, description)
    VALUES (?, 'Digital Logic Design', 'Hardware design principles: Boolean algebra, logic gates, combinational and sequential circuits.')
    """, (user_id,))
    nb3_id = cursor.lastrowid

    nb3_notes = """
Digital Logic Notes:
Logic Gates: AND, OR, NOT, NAND, NOR, XOR, XNOR. NAND and NOR are universal gates because any boolean function can be realized using them alone.
Boolean Algebra: De Morgan's Laws: NOT(A AND B) = NOT A OR NOT B, and NOT(A OR B) = NOT A AND NOT B.
Combinational Circuits: Output depends solely on the current input (Multiplexers, Decoders, Encoders, Adders). No memory element.
Sequential Circuits: Output depends on current input AND previous states (Flip-flops, Counters, Shift Registers). Contains memory/feedback.
"""
    cursor.execute("INSERT INTO notes (notebook_id, filename, raw_text, page_count) VALUES (?, 'Digital_Logic_Notes.pdf', ?, 4)",
                   (nb3_id, nb3_notes))

    nb3_topics = [
        ("Boolean Algebra & Gates", "### Boolean Algebra & Gates\n\n**Definition:** Mathematical rules governing binary variables and logic gates (AND, OR, NOT, NAND, NOR, XOR).\n\n**Key Rules:**\n- NAND and NOR are universal gates.\n- De Morgan's Laws.\n\n**Common Pitfalls:** Forgetting that XOR output is 1 only when inputs differ.", 1),
        ("Combinational Circuits", "### Combinational Circuits\n\n**Definition:** Digital circuits whose output depends only on the current combination of inputs at that instant.\n\n**Key Rules:**\n- No feedback loops or internal memory.\n- Examples: Adders, Decoders, Multiplexers (Mux).\n\n**Common Pitfalls:** Confusing Multiplexers (many to one) with Demultiplexers.", 2),
        ("Sequential Circuits & Flip-Flops", "### Sequential Circuits & Flip-Flops\n\n**Definition:** Circuits whose output depends on both current inputs and past states stored in memory elements.\n\n**Key Rules:**\n- Clock signal controls state transitions.\n- Flip-flops store 1 bit of memory (SR, JK, D, T flip-flops).\n\n**Common Pitfalls:** Race around condition in JK flip-flop when J=1, K=1 and clock pulse is wide.", 3)
    ]

    nb3_tids = {}
    for name, sum_txt, ord_idx in nb3_topics:
        cursor.execute("INSERT INTO topics (notebook_id, name, summary, order_index) VALUES (?, ?, ?, ?)",
                       (nb3_id, name, sum_txt, ord_idx))
        nb3_tids[name] = cursor.lastrowid

    cursor.execute("INSERT INTO topic_prereqs VALUES (?, ?)", (nb3_tids["Combinational Circuits"], nb3_tids["Boolean Algebra & Gates"]))
    cursor.execute("INSERT INTO topic_prereqs VALUES (?, ?)", (nb3_tids["Sequential Circuits & Flip-Flops"], nb3_tids["Combinational Circuits"]))

    nb3_quizzes = [
        (nb3_tids["Boolean Algebra & Gates"], "Which of the following gates is considered a Universal Gate in digital logic?", ["AND", "OR", "NAND", "XOR"], "NAND", "NAND and NOR gates are universal because any boolean logic function can be constructed using only them."),
        (nb3_tids["Combinational Circuits"], "What defines a combinational logic circuit?", ["It requires a clock signal", "Its output depends only on the present inputs", "It stores past outputs in flip-flops", "It uses magnetic memory"], "Its output depends only on the present inputs", "Combinational circuits have no memory element; outputs depend strictly on current inputs."),
        (nb3_tids["Sequential Circuits & Flip-Flops"], "What is the primary function of a D Flip-Flop?", ["To perform binary addition", "To delay or store 1 bit of data", "To decode binary numbers", "To convert analog signals to digital"], "To delay or store 1 bit of data", "A D flip-flop captures the value of the D input at the clock edge and stores that single bit.")
    ]
    for tid, q, opts, ans, exp in nb3_quizzes:
        cursor.execute("INSERT INTO quiz_questions (topic_id, question, options_json, correct_answer, explanation) VALUES (?, ?, ?, ?, ?)",
                       (tid, q, json.dumps(opts), ans, exp))

    nb3_mastery = [
        ("Boolean Algebra & Gates", 85.0, now - timedelta(days=2)),
        ("Combinational Circuits", 62.0, now - timedelta(days=4)),
        ("Sequential Circuits & Flip-Flops", 48.0, now - timedelta(days=1)),
    ]
    for name, sc, dt in nb3_mastery:
        cursor.execute("INSERT INTO mastery VALUES (?, ?, ?, ?)", (user_id, nb3_tids[name], sc, dt.strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_demo_data(force=True)
    print("Database seeded with 3 simultaneous notebooks: Java OOP, Data Structures, and Digital Logic.")
