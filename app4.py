import os
import re
import sqlite3
from io import BytesIO
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types
from werkzeug.security import generate_password_hash, check_password_hash

from PyPDF2 import PdfReader

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)


# ============================================================
# ROCKYAI v1-3
# AI POWERED LEARNING ASSISTANT
# ============================================================

st.set_page_config(
    page_title="RockyAI v1-3",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at top right, #10234a 0%, transparent 35%),
        radial-gradient(circle at bottom left, #07152d 0%, transparent 40%),
        #050810;
    color: #f8fafc;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07111f, #030712);
    border-right: 1px solid #172554;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0;
}

h1, h2, h3 {
    color: #f8fafc;
}

.rocky-title {
    font-size: 48px;
    font-weight: 800;
    letter-spacing: -2px;
    margin-bottom: 0;
}

.rocky-subtitle {
    color: #94a3b8;
    font-size: 17px;
    margin-top: 4px;
}

.tool-card {
    background: linear-gradient(
        145deg,
        rgba(15, 23, 42, 0.95),
        rgba(7, 15, 30, 0.95)
    );
    border: 1px solid #1e3a5f;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.25);
}

.hero-card {
    background:
        linear-gradient(
            135deg,
            rgba(30, 64, 175, 0.25),
            rgba(15, 23, 42, 0.9)
        );
    border: 1px solid #2563eb;
    border-radius: 24px;
    padding: 30px;
    margin-bottom: 25px;
}

.stat-card {
    background: #0b1220;
    border: 1px solid #1e293b;
    border-radius: 15px;
    padding: 18px;
    text-align: center;
}

.stat-number {
    font-size: 30px;
    font-weight: 800;
    color: #60a5fa;
}

.stat-label {
    color: #94a3b8;
}

.footer {
    text-align: center;
    color: #64748b;
    margin-top: 50px;
    padding: 25px;
    border-top: 1px solid #172033;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "rockyai_v1_3.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            prompts_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tool TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


init_database()


# ============================================================
# ADMIN INITIALIZATION
# ============================================================

def create_initial_admin():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        return

    conn = get_connection()
    cursor = conn.cursor()

    existing = cursor.execute(
        "SELECT username FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if not existing:
        cursor.execute(
            """
            INSERT INTO users
            (username, password_hash, role, prompts_count, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                username,
                generate_password_hash(password),
                "admin",
                0,
                datetime.now().isoformat(),
            ),
        )

    conn.commit()
    conn.close()


create_initial_admin()


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error(
        "GEMINI_API_KEY is not configured. "
        "Add it to your Render Environment Variables."
    )
    st.stop()


client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None


# ============================================================
# DATABASE HELPERS
# ============================================================

def save_chat(username, tool, prompt, response):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chats
        (username, tool, prompt, response, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username,
            tool,
            prompt,
            response,
            datetime.now().isoformat(),
        ),
    )

    cursor.execute(
        """
        UPDATE users
        SET prompts_count = prompts_count + 1
        WHERE username = ?
        """,
        (username,),
    )

    conn.commit()
    conn.close()


def get_user_count():
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]
    conn.close()
    return count


def get_chat_count(username=None):
    conn = get_connection()

    if username:
        count = conn.execute(
            "SELECT COUNT(*) FROM chats WHERE username = ?",
            (username,),
        ).fetchone()[0]
    else:
        count = conn.execute(
            "SELECT COUNT(*) FROM chats"
        ).fetchone()[0]

    conn.close()
    return count


# ============================================================
# GEMINI FUNCTION
# ============================================================

def ask_gemini(prompt, system_instruction=None):
    try:

        config = None

        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config,
        )

        if not response or not response.text:
            return "RockyAI did not receive a response."

        return response.text.strip()

    except Exception as e:
        return f"RockyAI encountered an error: {str(e)}"


# ============================================================
# CLEAN GENERATED CODE
# ============================================================

def clean_code_response(code):
    """
    Removes Markdown code fences that Gemini may add.
    Keeps the actual source code clean.
    """

    if not code:
        return ""

    code = code.strip()

    # Remove ```python, ```javascript etc.
    code = re.sub(
        r"^```[a-zA-Z0-9_+#.-]*\s*",
        "",
        code,
        flags=re.IGNORECASE,
    )

    # Remove closing ```
    code = re.sub(
        r"\s*```$",
        "",
        code,
    )

    return code.strip()


# ============================================================
# LOGIN FUNCTIONS
# ============================================================

def register_user(username, password):

    username = username.strip()

    if not username or not password:
        return False, "Username and password are required."

    if len(password) < 6:
        return False, "Password must contain at least 6 characters."

    conn = get_connection()

    existing = conn.execute(
        "SELECT username FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if existing:
        conn.close()
        return False, "Username already exists."

    conn.execute(
        """
        INSERT INTO users
        (username, password_hash, role, prompts_count, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username,
            generate_password_hash(password),
            "user",
            0,
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()

    return True, "Account created successfully."


def login_user(username, password):

    conn = get_connection()

    user = conn.execute(
        """
        SELECT username, password_hash, role
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    conn.close()

    if not user:
        return False

    if check_password_hash(user["password_hash"], password):

        st.session_state.logged_in = True
        st.session_state.username = user["username"]
        st.session_state.role = user["role"]

        return True

    return False


# ============================================================
# AUTH SCREEN
# ============================================================

def show_auth():

    st.markdown(
        """
        <div class="hero-card">
            <div class="rocky-title">🤖 RockyAI</div>
            <div class="rocky-subtitle">
                Your AI-powered learning workspace
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(
        ["🔐 Login", "📝 Create Account"]
    )

    with tab1:

        username = st.text_input(
            "Username",
            key="login_username",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login to RockyAI",
            use_container_width=True,
            type="primary",
        ):

            if login_user(username, password):

                st.success("Login successful!")
                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

    with tab2:

        new_username = st.text_input(
            "Choose username",
            key="register_username",
        )

        new_password = st.text_input(
            "Choose password",
            type="password",
            key="register_password",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="confirm_password",
        )

        if st.button(
            "Create Account",
            use_container_width=True,
        ):

            if new_password != confirm_password:

                st.error("Passwords do not match.")

            else:

                success, message = register_user(
                    new_username,
                    new_password,
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    try:

        reader = PdfReader(uploaded_file)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

            if len(text) >= 15000:
                break

        return text[:15000]

    except Exception as e:

        return f"Could not read PDF: {e}"


# ============================================================
# PDF GENERATOR
# ============================================================

def create_pdf(title, content):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RockyTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=28,
        spaceAfter=20,
    )

    body_style = ParagraphStyle(
        "RockyBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=16,
        spaceAfter=9,
    )

    story = []

    story.append(
        Paragraph(
            title,
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Generated by RockyAI v1-3",
            ParagraphStyle(
                "Subtitle",
                parent=body_style,
                alignment=TA_CENTER,
                fontSize=9,
            ),
        )
    )

    story.append(Spacer(1, 12))

    lines = content.split("\n")

    for line in lines:

        line = line.strip()

        if not line:
            story.append(Spacer(1, 6))
            continue

        safe_line = (
            line
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        story.append(
            Paragraph(
                safe_line,
                body_style,
            )
        )

    document.build(story)

    buffer.seek(0)

    return buffer


# ============================================================
# SIDEBAR
# ============================================================

def show_sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div style="
                font-size:28px;
                font-weight:800;
                color:#60a5fa;
                margin-bottom:4px;
            ">
                🤖 RockyAI
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("v1-3 • AI Learning Workspace")

        st.divider()

        st.write(
            f"👤 **{st.session_state.username}**"
        )

        if st.session_state.role == "admin":
            st.caption("👑 Administrator")
        else:
            st.caption("🎓 Student")

        st.divider()

        pages = [
            "🏠 Workspace",
            "📜 History",
            "📊 Analytics",
        ]

        if st.session_state.role == "admin":
            pages.append("👑 Admin Panel")

        page = st.radio(
            "Navigation",
            pages,
        )

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):

            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None

            st.rerun()

        return page


# ============================================================
# WORKSPACE
# ============================================================

def workspace():

    st.markdown(
        """
        <div class="hero-card">

        <div class="rocky-title">
        🤖 RockyAI
        </div>

        <div class="rocky-subtitle">
        Learn smarter. Create faster. Understand better.
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    tool = st.selectbox(
        "Choose a RockyAI Tool",
        [
            "🤖 Ask RockyAI",
            "📖 PDF Study",
            "📄 PDF Generator",
            "📝 Quiz Generator",
            "📚 Sample Paper",
            "💻 Code Generator",
            "🧠 Mind Map",
            "🧪 Periodic Table",
        ],
    )

    st.divider()


    # ========================================================
    # ASK AI
    # ========================================================

    if tool == "🤖 Ask RockyAI":

        st.subheader("🤖 Ask RockyAI")

        prompt = st.text_area(
            "What would you like to learn?",
            height=180,
            placeholder=(
                "Example: Explain photosynthesis "
                "for a Class 7 student."
            ),
        )

        if st.button(
            "🚀 Ask RockyAI",
            type="primary",
        ):

            if not prompt.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                with st.spinner(
                    "RockyAI is thinking..."
                ):

                    result = ask_gemini(
                        prompt,
                        """
                        You are RockyAI, a friendly AI
                        learning assistant.

                        Explain concepts clearly and
                        at the student's level.

                        Use headings, bullet points,
                        examples and simple explanations
                        when useful.

                        Do not unnecessarily output
                        programming code unless requested.
                        """,
                    )

                save_chat(
                    st.session_state.username,
                    "Ask AI",
                    prompt,
                    result,
                )

                st.subheader(
                    "💡 RockyAI's Answer"
                )

                # NORMAL AI OUTPUT
                st.write(result)


    # ========================================================
    # PDF STUDY
    # ========================================================

    elif tool == "📖 PDF Study":

        st.subheader("📖 PDF Study Assistant")

        uploaded = st.file_uploader(
            "Upload a textbook, notes or study PDF",
            type=["pdf"],
        )

        if uploaded:

            with st.spinner(
                "Reading your PDF..."
            ):

                pdf_text = extract_pdf_text(
                    uploaded
                )

            if pdf_text:

                st.success(
                    "PDF loaded successfully!"
                )

                question = st.text_area(
                    "Ask something about this PDF",
                    placeholder=(
                        "Example: Summarize chapter 2."
                    ),
                    height=140,
                )

                if st.button(
                    "🔍 Ask About PDF",
                    type="primary",
                ):

                    if not question.strip():

                        st.warning(
                            "Enter a question first."
                        )

                    else:

                        prompt = f"""
                        Answer the student's question
                        using the following PDF content.

                        PDF CONTENT:
                        {pdf_text}

                        QUESTION:
                        {question}

                        Give a clear educational answer.
                        """

                        with st.spinner(
                            "RockyAI is studying the PDF..."
                        ):

                            result = ask_gemini(
                                prompt
                            )

                        save_chat(
                            st.session_state.username,
                            "PDF Study",
                            question,
                            result,
                        )

                        st.subheader(
                            "📚 Answer"
                        )

                        st.write(result)


    # ========================================================
    # PDF GENERATOR
    # ========================================================

    elif tool == "📄 PDF Generator":

        st.subheader("📄 RockyAI PDF Generator")

        title = st.text_input(
            "PDF Title",
            "RockyAI Study Notes",
        )

        content = st.text_area(
            "Content",
            height=300,
            placeholder=(
                "Enter notes, revision material, "
                "questions or any content..."
            ),
        )

        if st.button(
            "📄 Generate PDF",
            type="primary",
        ):

            if not content.strip():

                st.warning(
                    "Please enter some content."
                )

            else:

                pdf = create_pdf(
                    title,
                    content,
                )

                st.success(
                    "PDF generated successfully!"
                )

                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf,
                    file_name=(
                        "RockyAI_v1-3_Generated.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )


    # ========================================================
    # QUIZ GENERATOR
    # ========================================================

    elif tool == "📝 Quiz Generator":

        st.subheader("📝 Quiz Generator")

        topic = st.text_input(
            "Quiz Topic",
            placeholder=(
                "Example: Electricity - Class 7"
            ),
        )

        difficulty = st.selectbox(
            "Difficulty",
            [
                "Easy",
                "Medium",
                "Hard",
            ],
        )

        if st.button(
            "📝 Generate Quiz",
            type="primary",
        ):

            if not topic.strip():

                st.warning(
                    "Enter a topic."
                )

            else:

                prompt = f"""
                Create exactly 5 multiple-choice
                questions about:

                {topic}

                Difficulty:
                {difficulty}

                Format:

                Q1. Question
                A. Option
                B. Option
                C. Option
                D. Option

                Answer: A

                Repeat for all 5 questions.
                """

                with st.spinner(
                    "Creating your quiz..."
                ):

                    result = ask_gemini(
                        prompt
                    )

                save_chat(
                    st.session_state.username,
                    "Quiz Generator",
                    topic,
                    result,
                )

                st.subheader(
                    "📝 Your Quiz"
                )

                st.write(result)


    # ========================================================
    # SAMPLE PAPER
    # ========================================================

    elif tool == "📚 Sample Paper":

        st.subheader(
            "📚 Sample Paper Generator"
        )

        subject = st.text_input(
            "Subject",
            placeholder="Science",
        )

        chapters = st.text_area(
            "Chapters / Topics",
            placeholder=(
                "Chapter 1, Chapter 2, Chapter 3..."
            ),
        )

        marks = st.number_input(
            "Total Marks",
            min_value=10,
            max_value=200,
            value=40,
            step=10,
        )

        if st.button(
            "📚 Generate Sample Paper",
            type="primary",
        ):

            if not subject.strip():

                st.warning(
                    "Enter a subject."
                )

            else:

                prompt = f"""
                Create a professional school sample
                question paper.

                Subject:
                {subject}

                Chapters:
                {chapters}

                Total Marks:
                {marks}

                Include:
                - Clear title
                - Instructions
                - Multiple sections
                - MCQs
                - Short-answer questions
                - Long-answer questions
                - Appropriate marks

                Make the paper suitable for a school student.
                """

                with st.spinner(
                    "Generating sample paper..."
                ):

                    result = ask_gemini(
                        prompt
                    )

                save_chat(
                    st.session_state.username,
                    "Sample Paper",
                    subject,
                    result,
                )

                st.subheader(
                    "📚 Generated Sample Paper"
                )

                st.write(result)

                pdf = create_pdf(
                    f"{subject} Sample Paper",
                    result,
                )

                st.download_button(
                    "⬇️ Download Sample Paper PDF",
                    data=pdf,
                    file_name=(
                        "RockyAI_v1-3_Sample_Paper.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )


    # ========================================================
    # CODE GENERATOR
    # ========================================================

    elif tool == "💻 Code Generator":

        st.subheader("💻 RockyAI Code Generator")

        language = st.selectbox(
            "Programming Language",
            [
                "python",
                "javascript",
                "html",
                "css",
                "java",
                "cpp",
                "c",
                "sql",
                "arduino",
                "json",
                "bash",
            ],
        )

        prompt = st.text_area(
            "Describe what you want to build",
            height=180,
            placeholder=(
                "Example: Create a Python calculator "
                "with a graphical interface."
            ),
        )

        if st.button(
            "💻 Generate Code",
            type="primary",
        ):

            if not prompt.strip():

                st.warning(
                    "Describe the code you want."
                )

            else:

                code_prompt = f"""
                Generate ONLY executable {language} code.

                User request:
                {prompt}

                IMPORTANT:
                - Return ONLY source code.
                - Do NOT explain the code.
                - Do NOT add an introduction.
                - Do NOT add a conclusion.
                - Do NOT use Markdown code fences.
                - Do NOT write ```.
                - Make the code complete and runnable.
                """

                with st.spinner(
                    "RockyAI is writing your code..."
                ):

                    result = ask_gemini(
                        code_prompt
                    )

                # CLEAN GEMINI RESPONSE
                clean_code = clean_code_response(
                    result
                )

                save_chat(
                    st.session_state.username,
                    "Code Generator",
                    prompt,
                    clean_code,
                )

                st.subheader(
                    "💻 Generated Code"
                )

                # THIS IS THE IMPORTANT FIX
                st.code(
                    clean_code,
                    language=language,
                    line_numbers=True,
                )

                st.download_button(
                    "⬇️ Download Code",
                    data=clean_code,
                    file_name=(
                        f"rockyai_code.{get_extension(language)}"
                    ),
                    mime="text/plain",
                )


    # ========================================================
    # MIND MAP
    # ========================================================

    elif tool == "🧠 Mind Map":

        st.subheader("🧠 AI Mind Map")

        topic = st.text_input(
            "Mind Map Topic",
            placeholder="Example: Photosynthesis",
        )

        if st.button(
            "🧠 Generate Mind Map",
            type="primary",
        ):

            if not topic.strip():

                st.warning(
                    "Enter a topic."
                )

            else:

                prompt = f"""
                Create a text-based mind map for:

                {topic}

                Use this structure:

                MAIN TOPIC
                ├── Branch 1
                │   ├── Point
                │   └── Point
                ├── Branch 2
                │   ├── Point
                │   └── Point
                └── Branch 3

                Keep it educational and organized.
                """

                with st.spinner(
                    "Building mind map..."
                ):

                    result = ask_gemini(
                        prompt
                    )

                save_chat(
                    st.session_state.username,
                    "Mind Map",
                    topic,
                    result,
                )

                st.subheader(
                    "🧠 Mind Map"
                )

                st.code(
                    result,
                    language="text",
                )


    # ========================================================
    # PERIODIC TABLE
    # ========================================================

    elif tool == "🧪 Periodic Table":

        st.subheader(
            "🧪 Periodic Table Explorer"
        )

        elements = [
            ("1", "H", "Hydrogen"),
            ("2", "He", "Helium"),
            ("3", "Li", "Lithium"),
            ("4", "Be", "Beryllium"),
            ("5", "B", "Boron"),
            ("6", "C", "Carbon"),
            ("7", "N", "Nitrogen"),
            ("8", "O", "Oxygen"),
            ("9", "F", "Fluorine"),
            ("10", "Ne", "Neon"),
            ("11", "Na", "Sodium"),
            ("12", "Mg", "Magnesium"),
            ("13", "Al", "Aluminium"),
            ("14", "Si", "Silicon"),
            ("15", "P", "Phosphorus"),
            ("16", "S", "Sulfur"),
            ("17", "Cl", "Chlorine"),
            ("18", "Ar", "Argon"),
        ]

        element_choice = st.selectbox(
            "Choose an element",
            [
                f"{number} — {symbol} — {name}"
                for number, symbol, name
                in elements
            ],
        )

        number, symbol, name = element_choice.split(
            " — "
        )

        st.markdown(
            f"""
            <div class="tool-card">

            <h2>{symbol}</h2>

            <h3>{name}</h3>

            <p>
            Atomic Number: <b>{number}</b>
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# FILE EXTENSIONS
# ============================================================

def get_extension(language):

    extensions = {
        "python": "py",
        "javascript": "js",
        "html": "html",
        "css": "css",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "sql": "sql",
        "arduino": "ino",
        "json": "json",
        "bash": "sh",
    }

    return extensions.get(
        language,
        "txt",
    )


# ============================================================
# HISTORY
# ============================================================

def history_page():

    st.title("📜 Chat History")

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT tool, prompt, response, timestamp
        FROM chats
        WHERE username = ?
        ORDER BY id DESC
        """,
        (st.session_state.username,),
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "You don't have any saved chats yet."
        )

        return

    for row in rows:

        with st.expander(
            f"🛠️ {row['tool']} • {row['timestamp']}"
        ):

            st.markdown(
                "**Prompt:**"
            )

            st.write(
                row["prompt"]
            )

            st.markdown(
                "**Response:**"
            )

            if row["tool"] == "Code Generator":

                st.code(
                    clean_code_response(
                        row["response"]
                    ),
                    language="text",
                    line_numbers=True,
                )

            else:

                st.write(
                    row["response"]
                )


# ============================================================
# ANALYTICS
# ============================================================

def analytics_page():

    st.title("📊 Analytics")

    username = st.session_state.username

    conn = get_connection()

    user = conn.execute(
        """
        SELECT prompts_count, created_at
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    conn.close()

    total = user["prompts_count"] if user else 0

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">AI Requests</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">
                    {get_chat_count(username)}
                </div>
                <div class="stat-label">Saved Chats</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">
                    🤖
                </div>
                <div class="stat-label">
                    RockyAI User
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader(
        "🚀 Your RockyAI Workspace"
    )

    st.write(
        """
        RockyAI combines AI learning tools into one
        workspace so students can ask questions,
        study PDFs, create quizzes, generate sample
        papers, write code and create study material.
        """
    )


# ============================================================
# ADMIN PANEL
# ============================================================

def admin_page():

    st.title("👑 Admin Panel")

    if st.session_state.role != "admin":

        st.error(
            "You do not have administrator access."
        )

        return

    st.metric(
        "Registered Users",
        get_user_count(),
    )

    st.metric(
        "Total AI Requests",
        get_chat_count(),
    )

    st.divider()

    st.subheader(
        "👥 Registered Users"
    )

    conn = get_connection()

    users = conn.execute(
        """
        SELECT username, role,
               prompts_count, created_at
        FROM users
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    for user in users:

        col1, col2, col3, col4 = st.columns(
            [2, 1, 1, 2]
        )

        with col1:
            st.write(
                f"👤 **{user['username']}**"
            )

        with col2:
            st.write(
                user["role"]
            )

        with col3:
            st.write(
                f"{user['prompts_count']} requests"
            )

        with col4:
            st.caption(
                user["created_at"]
            )

        if (
            user["username"]
            != st.session_state.username
        ):

            if st.button(
                f"🗑️ Delete {user['username']}",
                key=f"delete_{user['username']}",
            ):

                conn = get_connection()

                conn.execute(
                    """
                    DELETE FROM chats
                    WHERE username = ?
                    """,
                    (user["username"],),
                )

                conn.execute(
                    """
                    DELETE FROM users
                    WHERE username = ?
                    """,
                    (user["username"],),
                )

                conn.commit()
                conn.close()

                st.success(
                    "User deleted."
                )

                st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

if not st.session_state.logged_in:

    show_auth()

else:

    page = show_sidebar()

    if page == "🏠 Workspace":

        workspace()

    elif page == "📜 History":

        history_page()

    elif page == "📊 Analytics":

        analytics_page()

    elif page == "👑 Admin Panel":

        admin_page()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🤖 <b>RockyAI v1-3</b><br>
        AI-powered learning workspace
    </div>
    """,
    unsafe_allow_html=True,
)
