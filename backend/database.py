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
        password TEXT DEFAULT 'student123',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Notebooks
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

    # 6. Quiz Questions (with difficulty: 'easy', 'medium', 'hard')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        options_json TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        difficulty TEXT DEFAULT 'medium',
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );
    """)
    try:
        cursor.execute("ALTER TABLE quiz_questions ADD COLUMN difficulty TEXT DEFAULT 'medium'")
    except Exception:
        pass

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

    # 8. Mastery Scores (Defaults to 0.0% for new topics)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mastery (
        user_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        score REAL DEFAULT 0.0,
        last_reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, topic_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );
    """)

    # 9. Incorrect Topics Tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incorrect_topics (
        user_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        mistake_count INTEGER DEFAULT 1,
        last_failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

    # Clean existing data if forcing
    cursor.execute("DELETE FROM incorrect_topics")
    cursor.execute("DELETE FROM mastery")
    cursor.execute("DELETE FROM quiz_attempts")
    cursor.execute("DELETE FROM quiz_questions")
    cursor.execute("DELETE FROM topic_prereqs")
    cursor.execute("DELETE FROM topics")
    cursor.execute("DELETE FROM notes")
    cursor.execute("DELETE FROM notebooks")
    cursor.execute("DELETE FROM users")

    # 1. Default User
    cursor.execute("""
    INSERT INTO users (id, email, name, password)
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

    # Detailed Summaries
    topics_data = [
        (
            "Classes and Objects",
            """### Classes and Objects — Comprehensive Notes

#### 📌 Detailed Definition & Theoretical Foundations
A **Class** is a user-defined blueprint, prototype, or type definition from which individual objects are created. It encapsulates state (attributes/instance variables) and behavior (methods) into a cohesive unit.
An **Object** is a concrete instance of a class occupying memory in the heap. Every object possesses three fundamental characteristics:
1. **State**: The distinct values stored in its fields at any given point in execution.
2. **Behavior**: How the object acts and responds through method invocations.
3. **Identity**: A unique memory address managed by the JVM runtime that differentiates it from all other objects, even those with identical field values.

#### ⚙️ Execution Mechanics & Core Rules
- **Memory Allocation**: Objects are dynamically created on the JVM Heap memory via the `new` keyword, which invokes the constructor.
- **Reference Variables**: The variable holding an object reference is stored on the Call Stack and points to the heap memory address.
- **The `this` Keyword**: A reference variable pointing to the current object instance within non-static methods or constructors.
- **Instance vs Static**: Instance variables belong to the specific object instance; static variables belong to the class blueprint and are shared across all instances.

#### 💡 Annotated Code Example
```java
public class Student {
    // Instance variables (State)
    private String name;
    private int studentId;

    // Parameterized Constructor
    public Student(String name, int studentId) {
        this.name = name;           // 'this.name' resolves shadowing
        this.studentId = studentId;
    }

    // Instance Method (Behavior)
    public void displayStudentProfile() {
        System.out.println("Student: " + this.name + " (ID: " + this.studentId + ")");
    }
}

public class Main {
    public static void main(String[] args) {
        // Stack stores 's1'; Heap allocates Student object
        Student s1 = new Student("Aarav", 101);
        s1.displayStudentProfile();
    }
}
```

#### ⚠️ Edge Cases, Subtleties & Common Traps
- **`NullPointerException`**: Declaring `Student s;` only creates an uninitialized stack reference. Attempting `s.displayStudentProfile()` before initializing with `new` triggers a runtime crash.
- **Shallow vs Deep References**: Assigning `Student s2 = s1;` does NOT copy the object; it simply copies the memory pointer. Mutating `s2` immediately affects `s1`.

#### 🧠 Real-World Mental Model
Think of a class as an **architectural blueprint for a house** and an object as the **actual physical house built from concrete and brick**. You cannot live inside the blueprint; you need the `new` contractor to allocate real space!""",
            1
        ),
        (
            "Constructors",
            """### Constructors — Comprehensive Notes

#### 📌 Detailed Definition & Theoretical Foundations
A **Constructor** in Java is a specialized member block invoked automatically when an object is instantiated using the `new` operator. Its primary architectural purpose is to guarantee that newly created objects enter a valid, fully initialized state before any external method can be called on them.

#### ⚙️ Execution Mechanics & Core Rules
- **Naming Rule**: The constructor name must match the class name with exact case sensitivity.
- **No Return Type**: Constructors have NO return type whatsoever — not even `void`.
- **Default No-Arg Constructor**: The Java compiler automatically inserts a default no-argument constructor `public ClassName() {}` ONLY IF the programmer declares zero constructors in the class. As soon as any custom constructor is written, the automatic default is revoked.
- **Constructor Chaining**:
  - `this(...)`: Invokes an overloaded constructor in the same class (must be the very first statement).
  - `super(...)`: Invokes a superclass constructor (must be the very first statement).

#### 💡 Annotated Code Example
```java
public class Account {
    private String accountNumber;
    private double balance;

    // Overloaded Constructor 1: Defaults balance to zero
    public Account(String accountNumber) {
        this(accountNumber, 0.0); // Constructor chaining using this(...)
    }

    // Overloaded Constructor 2: Master constructor
    public Account(String accountNumber, double initialBalance) {
        this.accountNumber = accountNumber;
        this.balance = initialBalance;
    }
}
```

#### ⚠️ Edge Cases, Subtleties & Common Traps
- **Accidental Method Declaration**: Writing `public void Account()` does NOT cause a syntax error, but it turns the constructor into a regular method! Java will treat it as a normal method, leaving the object uninitialized.
- **Superclass Default Constructor Absence**: If superclass `A` has only parameterized constructors, a subclass constructor calling `super()` will fail at compile time unless explicitly invoking `super(params)`.

#### 🧠 Real-World Mental Model
A constructor is like the **factory startup checklist** when a new smartphone is turned on for the first time: setting language, setting default memory storage, and initializing the system before you can use any apps.""",
            2
        ),
        (
            "Inheritance",
            """### Inheritance — Comprehensive Notes

#### 📌 Detailed Definition & Theoretical Foundations
**Inheritance** is a cornerstone object-oriented mechanism where a new class (derived class or subclass) acquires fields and methods from an existing class (base class or superclass). It embodies the **"is-a" relationship** (e.g. `Dog` is an `Animal`) and promotes structural code reuse and polymorphism.

#### ⚙️ Execution Mechanics & Core Rules
- **`extends` Keyword**: Declared via `class Child extends Parent`.
- **Single Class Inheritance**: Java explicitly forbids a class from extending more than one direct parent class to prevent the ambiguities of multiple inheritance (the *Diamond Problem*).
- **The `super` Keyword**:
  - `super.method()`: Invokes superclass implementations.
  - `super(args)`: Passes initialization data up to the parent constructor.
- **Access Modifier Visibility**:
  - `private`: Never inherited directly.
  - `protected`: Accessible within the same package and by subclasses across other packages.
  - `public`: Inherited and universally accessible.

#### 💡 Annotated Code Example
```java
class Vehicle {
    protected String brand;

    public Vehicle(String brand) {
        this.brand = brand;
    }

    public void start() {
        System.out.println("Vehicle engine starts.");
    }
}

class ElectricCar extends Vehicle {
    private int batteryCapacity;

    public ElectricCar(String brand, int batteryCapacity) {
        super(brand); // Delegates to parent constructor first
        this.batteryCapacity = batteryCapacity;
    }

    @Override
    public void start() {
        System.out.println(brand + " starts silently on electric power.");
    }
}
```

#### ⚠️ Edge Cases, Subtleties & Common Traps
- **Constructor Execution Order**: Superclass constructors ALWAYS execute before subclass constructors, from top of the inheritance hierarchy down.
- **Composition vs Inheritance**: Prefer composition ("has-a") over inheritance when relationships are not strictly hierarchical to avoid fragile base class syndrome.

#### 🧠 Real-World Mental Model
Like biological inheritance: a child inherits genetic blueprints (eye color, blood type) from parents, but can develop unique skills (playing piano) and adapt inherited behaviors.""",
            3
        ),
        (
            "Method Overriding",
            """### Method Overriding — Comprehensive Notes

#### 📌 Detailed Definition & Theoretical Foundations
**Method Overriding** occurs when a subclass provides a specific, specialized implementation of a method that is already declared in its superclass. It is the primary engine behind **Runtime Polymorphism (Dynamic Method Dispatch)**, enabling a single interface or base reference to evoke different runtime behaviors based on the actual object in memory.

#### ⚙️ Execution Mechanics & Core Rules
- **Exact Method Signature**: The overridden method must have the **exact same name, exact same parameter count, and exact same parameter types** as the superclass method.
- **Return Type**: Must be identical or a *covariant return type* (a subclass of the original return type).
- **Access Modifier Rule**: The subclass method **CANNOT be more restrictive** than the superclass method (e.g., overriding a `protected` method with `private` is forbidden; expanding to `public` is permitted).
- **Restrictions**:
  - `static` methods CANNOT be overridden (this is *method hiding*).
  - `final` methods CANNOT be overridden.
  - `private` methods are not visible to subclasses and cannot be overridden.
- **`@Override` Annotation**: Tells the compiler to verify that the method actually overrides a superclass method, catching spelling errors at compile time.

#### 💡 Annotated Code Example
```java
class PaymentProcessor {
    public void process(double amount) {
        System.out.println("Processing standard generic payment of $" + amount);
    }
}

class UPIPayment extends PaymentProcessor {
    @Override // Compiler verifies method signature matches parent
    public void process(double amount) {
        System.out.println("Processing instant UPI payment of $" + amount + " via QR code.");
    }
}

public class TestPolymorphism {
    public static void main(String[] args) {
        // Reference is PaymentProcessor, runtime object is UPIPayment
        PaymentProcessor p = new UPIPayment();
        p.process(450.0); // Resolved dynamically at runtime to UPIPayment!
    }
}
```

#### ⚠️ Edge Cases, Subtleties & Common Traps
- **Overloading vs Overriding Trap**: Accidentally changing parameter types (e.g. `process(int amount)` instead of `process(double amount)`) results in *method overloading*, leaving the original method un-overridden!
- **Private Parent Methods**: If a parent method is `private`, a method in the child with the same signature is considered an entirely separate method, not an override.

#### 🧠 Real-World Mental Model
Universal Remote Control: Pressing the "Power" button sends the same signal, but a Television turns on a screen while an Audio System turns on speakers.""",
            4
        ),
        (
            "Abstract Classes",
            """### Abstract Classes — Comprehensive Notes

#### 📌 Detailed Definition & Theoretical Foundations
An **Abstract Class** in Java is an incomplete, restricted class declared with the `abstract` keyword. It serves as a generalized conceptual framework designed strictly for inheritance and cannot be directly instantiated. It provides a common template and partial implementation that concrete subclasses must complete.

#### ⚙️ Execution Mechanics & Core Rules
- **Direct Instantiation Forbidden**: Attempting `new AbstractClass()` produces an immediate compile-time error.
- **Abstract Methods**: Declared without a method body (`abstract void calculateArea();`). They define a mandatory contract for child classes.
- **Concrete Members Permitted**: Unlike pure interfaces, an abstract class can contain concrete methods with bodies, instance fields, constants, and constructors.
- **Subclass Obligation**: Any concrete subclass extending an abstract class MUST override and implement all inherited abstract methods; otherwise, the subclass itself must be declared `abstract`.

#### 💡 Annotated Code Example
```java
abstract class GraphicObject {
    int x, y;

    // Concrete constructor (invoked via super() by children)
    public GraphicObject(int x, int y) {
        this.x = x;
        this.y = y;
    }

    // Concrete method shared by all graphics
    public void moveTo(int newX, int newY) {
        this.x = newX;
        this.y = newY;
    }

    // Abstract method: Every shape draws differently
    public abstract void draw();
}

class Circle extends GraphicObject {
    int radius;

    public Circle(int x, int y, int radius) {
        super(x, y);
        this.radius = radius;
    }

    @Override
    public void draw() {
        System.out.println("Drawing circle at (" + x + "," + y + ") with radius " + radius);
    }
}
```

#### ⚠️ Edge Cases, Subtleties & Common Traps
- **Abstract Method inside Non-Abstract Class**: A class containing even one abstract method MUST be declared abstract, otherwise compilation fails.
- **Constructors in Abstract Classes**: Even though you cannot instantiate an abstract class directly, it CAN and should define constructors to initialize state for its subclasses via `super()`.

#### 🧠 Real-World Mental Model
Think of the concept of an **"Animal"**. You cannot touch or point to an abstract animal in the wild — you can only point to a concrete dog, cat, or lion that inherits animal properties.""",
            5
        ),
        (
            "Interfaces",
            """### Interfaces — Comprehensive Notes

#### 📌 Detailed Definition & Theoretical Foundations
An **Interface** in Java is a formal contract that specifies what a class must do, without dictating how it must do it. It establishes full abstraction and enables Java to achieve **multiple inheritance of type**, allowing unrelated classes to implement the exact same behavioral contract.

#### ⚙️ Execution Mechanics & Core Rules
- **Keywords**: Declared using `interface` and adopted using `implements`.
- **Fields / Variables**: All variables declared inside an interface are implicitly **`public static final`** constants.
- **Methods**:
  - Prior to Java 8, all methods were implicitly **`public abstract`**.
  - Java 8+ introduced `default` methods (providing backward-compatible fallback implementations) and `static` utility methods.
  - Java 9+ added `private` helper methods for internal interface reuse.
- **Multiple Implementation**: A class can implement multiple interfaces: `class Robot implements Drivable, Rechargeable, Programmable`.

#### 💡 Annotated Code Example
```java
interface Audible {
    int MAX_DECIBELS = 120; // public static final constant
    void playSound();       // public abstract method
}

interface Recordable {
    void startRecording();
}

// Implementing multiple interfaces simultaneously
class SmartSpeaker implements Audible, Recordable {
    @Override
    public void playSound() { // MUST be public
        System.out.println("Playing audio stream at high fidelity.");
    }

    @Override
    public void startRecording() {
        System.out.println("Recording voice input.");
    }
}
```

#### ⚠️ Edge Cases, Subtleties & Common Traps
- **Visibility Shrinkage Error**: When implementing an interface method, forgetting the `public` access modifier causes an error (`"cannot reduce visibility of inherited method"`), because interface methods are public by default!
- **Diamond Problem with Default Methods**: If two interfaces provide conflicting `default` methods with the same signature, the implementing class MUST override the method to manually resolve the ambiguity.

#### 🧠 Real-World Mental Model
A **standard electrical wall socket**: The socket defines an interface (pin dimensions, 230V AC). It doesn't care whether you plug in a laptop, toaster, or television, as long as the device implements the prong interface!""",
            6
        )
    ]

    nb1_tids = {}
    for name, sum_txt, ord_idx in topics_data:
        cursor.execute("INSERT INTO topics (notebook_id, name, summary, order_index) VALUES (?, ?, ?, ?)",
                       (nb1_id, name, sum_txt, ord_idx))
        nb1_tids[name] = cursor.lastrowid

    # Prerequisites
    prereqs = [
        ("Constructors", "Classes and Objects"),
        ("Inheritance", "Classes and Objects"),
        ("Method Overriding", "Inheritance"),
        ("Abstract Classes", "Inheritance"),
        ("Interfaces", "Abstract Classes"),
    ]
    for top_n, pre_n in prereqs:
        cursor.execute("INSERT INTO topic_prereqs VALUES (?, ?)", (nb1_tids[top_n], nb1_tids[pre_n]))

    # =========================================================================
    # SEED 3 SECTIONS (EASY, MEDIUM, HARD) WITH 5 QUESTIONS EACH PER TOPIC
    # =========================================================================
    # Focus on Method Overriding (the main demo topic)
    mo_id = nb1_tids["Method Overriding"]
    mo_quizzes = [
        # --- EASY SECTION (5 Questions) ---
        (mo_id, "Which annotation is recommended when overriding a method in Java for compile-time validation?",
         ["@Inherit", "@Override", "@Overload", "@Implement"], "@Override",
         "The @Override annotation asks the compiler to check that the method matches a parent method signature.", "easy"),
        (mo_id, "Where does method overriding take place?",
         ["Inside the same class", "Between superclass and subclass", "Inside an interface only", "Within separate packages only"],
         "Between superclass and subclass", "Method overriding requires an inheritance relationship between parent and child classes.", "easy"),
        (mo_id, "Which keyword establishes the inheritance relationship needed for overriding in Java?",
         ["implements", "extends", "inherits", "super"], "extends",
         "The 'extends' keyword establishes class inheritance.", "easy"),
        (mo_id, "Can a method with the exact same name and parameters in a subclass override a superclass method?",
         ["Yes, that is the definition of overriding", "No, it causes a compile error", "Only if both methods are static", "Only if parameters differ"],
         "Yes, that is the definition of overriding", "Matching name and parameters between subclass and superclass defines method overriding.", "easy"),
        (mo_id, "Method overriding is an example of which type of polymorphism?",
         ["Compile-time polymorphism", "Runtime polymorphism", "Parametric polymorphism", "Static binding"],
         "Runtime polymorphism", "Method overriding is resolved at runtime through dynamic method dispatch.", "easy"),

        # --- MEDIUM SECTION (5 Questions) ---
        (mo_id, "Which access modifier restriction applies when overriding a protected method in a subclass?",
         ["Subclass method can be private or protected", "Subclass method must be private", "Subclass method can be protected or public, but not private", "Subclass method must be package-private"],
         "Subclass method can be protected or public, but not private",
         "Overriding methods cannot reduce visibility. It can stay protected or expand to public.", "medium"),
        (mo_id, "What happens if a subclass declares a method with the same name as the superclass, but different parameter types?",
         ["It overrides the superclass method", "It overloads the method", "It causes a compiler syntax error", "It creates a runtime crash"],
         "It overloads the method", "Different parameters create method overloading, not overriding.", "medium"),
        (mo_id, "Which types of methods CANNOT be overridden in a Java subclass?",
         ["public and protected methods", "final, static, and private methods", "methods returning void", "abstract methods"],
         "final, static, and private methods", "Static methods are hidden, final methods cannot be changed, and private methods are not inherited.", "medium"),
        (mo_id, "How can a subclass method invoke the overridden method from its parent class?",
         ["this.methodName()", "super.methodName()", "parent.methodName()", "base.methodName()"],
         "super.methodName()", "The 'super' keyword allows subclasses to call superclass implementations.", "medium"),
        (mo_id, "What is a covariant return type in Java method overriding?",
         ["Returning void instead of a class", "Returning a subclass of the superclass method's return type", "Returning an array instead of a primitive", "Changing return type from int to double"],
         "Returning a subclass of the superclass method's return type",
         "A covariant return type allows the overriding method to return a narrower subtype.", "medium"),

        # --- HARD SECTION (5 Questions) ---
        (mo_id, "What happens when you declare a static method in a subclass with the same signature as a static method in the superclass?",
         ["Method overriding with dynamic dispatch", "Method hiding (resolved at compile-time by reference type)", "Compilation error: static cannot match", "Undefined behavior"],
         "Method hiding (resolved at compile-time by reference type)",
         "Static methods are bound at compile time based on reference type; this is method hiding, not overriding.", "hard"),
        (mo_id, "If a superclass method throws an IOException, what checked exceptions can the overriding subclass method declare?",
         ["Any Exception including Exception or Throwable", "IOException or its subclasses (e.g. FileNotFoundException), or no exception", "Only broader checked exceptions", "It must declare the exact same exception or fail"],
         "IOException or its subclasses (e.g. FileNotFoundException), or no exception",
         "An overriding method can throw narrower (covariant) checked exceptions, but cannot throw broader checked exceptions.", "hard"),
        (mo_id, "Given `Parent p = new Child();`, what happens if the Child class overrides method `foo()` and `foo()` is called on `p`?",
         ["Parent's foo() executes because reference is Parent", "Child's foo() executes via dynamic method dispatch", "Compilation error unless casted", "Both execute in sequence"],
         "Child's foo() executes via dynamic method dispatch",
         "Java invokes the implementation based on the actual object created in the heap at runtime.", "hard"),
        (mo_id, "Can a subclass override a method that has default (package-private) access from a superclass in a different package?",
         ["Yes, with public access", "No, because package-private members are not visible outside their package", "Yes, if the subclass is public", "Only with protected access"],
         "No, because package-private members are not visible outside their package",
         "Members with package-private access are completely invisible to classes in other packages and cannot be overridden.", "hard"),
        (mo_id, "What occurs if an overridden method is called from inside the superclass constructor during object creation?",
         ["Subclass overridden method runs before subclass constructor has initialized its own fields", "Superclass method runs safely", "Java throws an IllegalStateException", "Method invocation is queued until both constructors finish"],
         "Subclass overridden method runs before subclass constructor has initialized its own fields",
         "Calling overridable methods from constructors is a dangerous trap: the child override executes while child fields are still null/0!", "hard")
    ]

    for tid, q, opts, ans, exp, diff in mo_quizzes:
        cursor.execute("""
        INSERT INTO quiz_questions (topic_id, question, options_json, correct_answer, explanation, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (tid, q, json.dumps(opts), ans, exp, diff))

    # Also seed 5 easy, 5 medium, 5 hard for Classes and Objects
    co_id = nb1_tids["Classes and Objects"]
    co_quizzes = [
        # Easy (5)
        (co_id, "Which keyword allocates memory for a new object in Java?", ["alloc", "create", "new", "malloc"], "new", "The 'new' keyword dynamically creates object instances on the heap.", "easy"),
        (co_id, "What does a class in Java represent?", ["A blueprint for creating objects", "A running thread", "A compiled binary file", "A memory pointer"], "A blueprint for creating objects", "A class defines the blueprint or template.", "easy"),
        (co_id, "Where are objects allocated in Java runtime memory?", ["Heap memory", "Stack memory", "Register file", "ROM"], "Heap memory", "Object instances reside in the Heap.", "easy"),
        (co_id, "Which keyword refers to the current object instance within a method?", ["self", "this", "super", "current"], "this", "The 'this' keyword refers to the current object.", "easy"),
        (co_id, "What are variables declared directly inside a class but outside methods called?", ["Local variables", "Instance variables", "Parameter variables", "Global constants"], "Instance variables", "They represent the state of an instance.", "easy"),

        # Medium (5)
        (co_id, "What is the default value of an uninitialized object reference instance variable in Java?", ["0", "null", "undefined", "false"], "null", "Unassigned object references default to null.", "medium"),
        (co_id, "What happens when `Student s2 = s1;` is executed where `s1` is an existing object?", ["A duplicate object is cloned in heap", "Both s1 and s2 point to the same memory object", "s1 is deleted from memory", "Compilation error"], "Both s1 and s2 point to the same memory object", "Reference assignment copies the memory pointer, not the object.", "medium"),
        (co_id, "Which access modifier allows access only within the class itself?", ["protected", "private", "public", "default"], "private", "Private members cannot be accessed outside the class.", "medium"),
        (co_id, "What exception is thrown if you invoke a method on a reference variable holding null?", ["IllegalArgumentException", "NullPointerException", "IndexOutOfBoundsException", "ClassCastException"], "NullPointerException", "Dereferencing null throws NullPointerException.", "medium"),
        (co_id, "Can a Java class contain multiple methods with the exact same name?", ["No, never", "Yes, if parameter lists differ (overloading)", "Only if return types differ", "Only if one is private"], "Yes, if parameter lists differ (overloading)", "Method overloading permits matching names with different parameter lists.", "medium"),

        # Hard (5)
        (co_id, "How does the JVM Garbage Collector identify an object as eligible for reclamation?", ["When its reference count hits zero", "When it is no longer reachable from any GC roots", "After exactly 60 seconds of inactivity", "When its class is unloaded"], "When it is no longer reachable from any GC roots", "Java GC uses root reachability analysis.", "hard"),
        (co_id, "What is the purpose of the `finalize()` method, and what is its status in modern Java?", ["It runs before object creation; active", "It was called before garbage collection; deprecated since Java 9", "It makes an object immutable; active", "It flushes file streams; standard"], "It was called before garbage collection; deprecated since Java 9", "Finalizers were unpredictable and are deprecated.", "hard"),
        (co_id, "What is the object header in JVM memory layout?", ["A string containing the class name", "Mark Word and Klass Pointer containing metadata and lock status", "An array storing all instance fields", "A timestamp of creation"], "Mark Word and Klass Pointer containing metadata and lock status", "Object headers contain memory mark words and class pointers.", "hard"),
        (co_id, "Why does Java avoid using raw memory pointers exposed to programmers like C++?", ["To simplify compilation speed", "Memory safety, garbage collection integrity, and security sandboxing", "Because heap memory cannot support pointers", "To prevent multithreading"], "Memory safety, garbage collection integrity, and security sandboxing", "Managed references prevent buffer overflows and dangling pointers.", "hard"),
        (co_id, "What is Escape Analysis performed by the Java JIT compiler on objects?", ["Checking if objects escape into external networks", "Determining if an object's lifetime is confined to a single method to allocate on stack", "Detecting null pointer exceptions before execution", "Measuring heap fragmentation"], "Determining if an object's lifetime is confined to a single method to allocate on stack", "Escape analysis allows scalar replacement or stack allocation.", "hard")
    ]

    for tid, q, opts, ans, exp, diff in co_quizzes:
        cursor.execute("""
        INSERT INTO quiz_questions (topic_id, question, options_json, correct_answer, explanation, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (tid, q, json.dumps(opts), ans, exp, diff))

    # Also seed 5 easy, 5 medium, 5 hard for Interfaces
    int_id = nb1_tids["Interfaces"]
    int_quizzes = [
        # Easy (5)
        (int_id, "Which keyword is used by a class to adopt an interface in Java?", ["extends", "implements", "inherits", "import"], "implements", "Classes use 'implements' for interfaces.", "easy"),
        (int_id, "What are variables declared inside an interface by default?", ["private", "public static final", "protected", "volatile"], "public static final", "Interface variables are constants by default.", "easy"),
        (int_id, "Can a Java class implement more than one interface simultaneously?", ["Yes, multiple interfaces can be implemented", "No, only single interface allowed", "Only if all interfaces have no methods", "Only abstract classes can"], "Yes, multiple interfaces can be implemented", "Java supports multiple inheritance of interface types.", "easy"),
        (int_id, "What is the default access modifier of methods declared in an interface?", ["package-private", "public abstract", "protected", "private"], "public abstract", "Interface methods are public abstract by default.", "easy"),
        (int_id, "Which keyword was introduced in Java 8 to allow method implementations in interfaces?", ["virtual", "default", "concrete", "static only"], "default", "The 'default' keyword enables interface methods with bodies.", "easy"),

        # Medium (5)
        (int_id, "What happens if a class implements an interface but omits the 'public' keyword on an overridden method?",
         ["It compiles normally", "Compilation error: cannot reduce visibility", "It becomes package-private", "It creates an overload"], "Compilation error: cannot reduce visibility", "Interface methods are public, so overriding methods must be public.", "medium"),
        (int_id, "Can an interface in Java extend another interface?", ["No, interfaces cannot extend anything", "Yes, using the 'extends' keyword", "Yes, using the 'implements' keyword", "Only if it is a functional interface"], "Yes, using the 'extends' keyword", "Interfaces extend other interfaces using 'extends'.", "medium"),
        (int_id, "What is a Functional Interface in Java?", ["An interface with no methods", "An interface with exactly one abstract method", "An interface with all static methods", "An interface with multiple inheritance"], "An interface with exactly one abstract method", "Functional interfaces have single abstract method (SAM) for lambdas.", "medium"),
        (int_id, "Can an interface have constructors in Java?", ["Yes, default constructors only", "No, interfaces cannot have constructors", "Yes, if declared private", "Only abstract constructors"], "No, interfaces cannot have constructors", "Interfaces have no instance state to initialize.", "medium"),
        (int_id, "What is a marker interface in Java?", ["An interface with only default methods", "An empty interface with no methods or fields (e.g. Serializable)", "An interface that marks compiler warnings", "An interface with exactly 10 constants"], "An empty interface with no methods or fields (e.g. Serializable)", "Marker interfaces signal runtime metadata to the JVM.", "medium"),

        # Hard (5)
        (int_id, "How is the diamond conflict resolved if a class implements two interfaces having identical default method signatures?",
         ["The compiler picks the first interface listed", "Compilation error unless the implementing class explicitly overrides the method", "The JVM resolves it randomly at runtime", "The method is ignored"],
         "Compilation error unless the implementing class explicitly overrides the method", "Java requires explicit manual resolution via InterfaceName.super.method().", "hard"),
        (int_id, "Can private methods exist inside Java interfaces?", ["No, interfaces only allow public members", "Yes, introduced in Java 9 for helper code sharing between default methods", "Only private static fields are allowed", "Only in package-private interfaces"], "Yes, introduced in Java 9 for helper code sharing between default methods", "Java 9 introduced private and private static interface methods.", "hard"),
        (int_id, "What is the key structural difference between an abstract class and an interface regarding state?",
         ["Abstract classes can maintain mutable instance state; interfaces cannot", "Interfaces can have constructors; abstract classes cannot", "There is no difference in state management", "Abstract classes cannot declare fields"],
         "Abstract classes can maintain mutable instance state; interfaces cannot", "Interfaces only have static constants; abstract classes have instance variables.", "hard"),
        (int_id, "Can an interface define a default method that overrides a method from `java.lang.Object` (e.g. `equals` or `toString`)?",
         ["Yes, default methods can override Object methods", "No, compilation error: default method cannot override a method from java.lang.Object", "Only toString() can be overridden", "Only if marked final"],
         "No, compilation error: default method cannot override a method from java.lang.Object", "Object methods always take precedence over interface default methods.", "hard"),
        (int_id, "How does JVM invokeinterface bytecode instruction differ from invokevirtual in dispatch efficiency?",
         ["invokeinterface is identical to invokevirtual", "invokeinterface requires dynamic table searching (itables) because class layouts vary", "invokeinterface is faster because it bypasses vtables", "invokeinterface is only used for static methods"],
         "invokeinterface requires dynamic table searching (itables) because class layouts vary", "Interface method calls use itables which require search caching.", "hard")
    ]

    for tid, q, opts, ans, exp, diff in int_quizzes:
        cursor.execute("""
        INSERT INTO quiz_questions (topic_id, question, options_json, correct_answer, explanation, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (tid, q, json.dumps(opts), ans, exp, diff))

    # Seed Initial Mastery Scores & Incorrect Topics Demonstration
    # Method Overriding: 42% (Failed recently -> recorded in incorrect_topics!)
    # Interfaces: 55% (Failed recently -> recorded in incorrect_topics!)
    # Abstract Classes: 58%
    # Inheritance: 68%
    # Constructors: 82%
    # Classes and Objects: 89%
    now = datetime.now()
    initial_mastery = [
        ("Classes and Objects", 89.0, now - timedelta(days=2)),
        ("Constructors", 82.0, now - timedelta(days=3)),
        ("Inheritance", 68.0, now - timedelta(days=5)),
        ("Method Overriding", 42.0, now - timedelta(days=1)),
        ("Abstract Classes", 58.0, now - timedelta(days=4)),
        ("Interfaces", 55.0, now - timedelta(days=6)),
    ]
    for name, sc, dt in initial_mastery:
        cursor.execute("INSERT INTO mastery (user_id, topic_id, score, last_reviewed_at) VALUES (?, ?, ?, ?)",
                       (user_id, nb1_tids[name], sc, dt.strftime("%Y-%m-%d %H:%M:%S")))

    # Pre-seed Incorrect Topics: Method Overriding and Interfaces
    cursor.execute("""
    INSERT INTO incorrect_topics (user_id, topic_id, mistake_count, last_failed_at)
    VALUES (?, ?, 2, ?)
    """, (user_id, nb1_tids["Method Overriding"], (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("""
    INSERT INTO incorrect_topics (user_id, topic_id, mistake_count, last_failed_at)
    VALUES (?, ?, 1, ?)
    """, (user_id, nb1_tids["Interfaces"], (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")))

    # Record past failed attempts for history
    cursor.execute("""
    INSERT INTO quiz_attempts (user_id, question_id, topic_id, user_answer, is_correct, confidence, attempted_at)
    SELECT ?, id, topic_id, 'Wrong Option', 0, 'Confident', ?
    FROM quiz_questions WHERE topic_id = ? LIMIT 1
    """, (user_id, (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), nb1_tids["Method Overriding"]))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_demo_data(force=True)
    print("Database initialized and demo data seeded with 3 sections (Easy, Medium, Hard with 5 Qs each)!")
