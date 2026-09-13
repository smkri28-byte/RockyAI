import os
import re
import io
import html
import hashlib
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st
from google import genai
from werkzeug.security import generate_password_hash, check_password_hash
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm

# Optional: persistent login cookies
try:
    from extra_streamlit_components import CookieManager
    COOKIE_SUPPORT = True
except Exception:
    COOKIE_SUPPORT = False


# ============================================================
# ROCKYAI v1-5 — PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RockyAI v1-5",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "RockyAI v1-5"
MODEL = "gemini-2.5-flash"
DB_PATH = Path(__file__).resolve().parent / "rockyai_v1_5.db"
COOKIE_NAME = "rockyai_v1_5_session"
COOKIE_DAYS = 30

TOOLS = [
    # Existing tools
    "🤖 Ask RockyAI", "🎓 AI Tutor", "🧩 Question Solver", "📖 PDF Study",
    "📄 PDF Generator", "📝 Quiz Generator", "📚 Sample Paper", "💻 Code Generator",
    "🧠 Mind Map", "🃏 Flashcards", "📅 Study Planner", "✂️ Smart Summarizer",
    "🌐 Translator", "💡 Brainstorm", "🎯 Exam Preparation", "🧪 Periodic Table",
    # New v1-5 tools
    "🏆 Daily Challenge", "🗣️ Debate Coach", "🎤 Interview Coach", "🧭 Career Roadmap",
    "🚀 Project Builder", "📊 Presentation Maker", "🧠 Memory Trainer", "🎯 Goal Coach",
    "📘 Vocabulary Builder", "🔍 Fact Checker",
]


# ============================================================
# ROCKYAI v1-5 — PREMIUM MOUNTAIN UI
# ============================================================

st.markdown(
    """
<style>
:root {
    --red: #e11d48;
    --red2: #fb7185;
    --red3: #be123c;
    --ink: #08090c;
    --panel: #111318;
    --panel2: #171922;
    --text: #f8fafc;
    --muted: #a1a1aa;
}
.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(225,29,72,.20), transparent 30%),
        radial-gradient(circle at 90% 15%, rgba(190,18,60,.13), transparent 28%),
        linear-gradient(180deg,#07080b 0%,#0b0c10 52%,#07080b 100%);
    color: var(--text);
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#10090d,#090a0e);
    border-right: 1px solid rgba(251,113,133,.20);
}
.block-container { max-width: 1450px; padding-top: 1.4rem; }
.rocky-hero {
    position: relative; overflow: hidden; padding: 34px; border-radius: 28px;
    border: 1px solid rgba(251,113,133,.25);
    background: linear-gradient(135deg,rgba(37,10,18,.96),rgba(12,13,18,.98) 60%,rgba(22,8,13,.98));
    box-shadow: 0 22px 70px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.03);
    margin-bottom: 24px;
}
.rocky-hero:after {
    content:"🏔️"; position:absolute; right:35px; bottom:-28px; font-size:8rem; opacity:.13;
}
.rocky-hero h1 { margin:8px 0 4px; font-size:3rem; letter-spacing:-1.5px; }
.rocky-hero p { color:#c4c4cc; font-size:1.06rem; }
.rocky-card {
    padding:20px; border-radius:20px; border:1px solid rgba(251,113,133,.15);
    background:linear-gradient(145deg,rgba(25,17,22,.92),rgba(14,15,20,.92));
    margin:8px 0; box-shadow:0 10px 30px rgba(0,0,0,.18);
}
.metric-card {
    padding:20px; border-radius:18px; border:1px solid rgba(251,113,133,.16);
    background:linear-gradient(145deg,#19131a,#101116);
}
.metric-number {font-size:1.9rem;font-weight:850;color:#fff;}
.metric-label {color:#a8a8b2;font-size:.88rem;}
.badge {
    display:inline-block;padding:6px 11px;border-radius:999px;
    background:rgba(225,29,72,.12);border:1px solid rgba(251,113,133,.24);
    color:#fecdd3;margin-right:6px;font-size:.78rem;font-weight:750;letter-spacing:.4px;
}
.small-muted {color:#a1a1aa;}
.rocky-footer {text-align:center;color:#71717a;padding:34px 0 8px;font-size:.84rem;}
div[data-testid="stButton"] > button {
    border-radius:12px;border:1px solid rgba(251,113,133,.20);font-weight:700;
    background:linear-gradient(180deg,#18151a,#111216); transition:.18s ease;
}
div[data-testid="stButton"] > button:hover {
    border-color:#fb7185; box-shadow:0 0 24px rgba(225,29,72,.18); transform:translateY(-1px);
}
button[kind="primary"] {background:linear-gradient(135deg,#e11d48,#be123c) !important;border-color:#fb7185 !important;}
[data-testid="stMetricValue"] {color:#fff;}
.stTabs [data-baseweb="tab"] {font-weight:700;}
.stTabs [aria-selected="true"] {color:#fb7185 !important;}
</style>
""", unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect_db()

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            prompts_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tool TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            subject TEXT NOT NULL,
            task TEXT NOT NULL,
            target_date TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """
    )

    admin_user = os.getenv("ADMIN_USERNAME", "").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "")

    if admin_user and admin_pass:
        existing = conn.execute(
            "SELECT username FROM users WHERE username=?",
            (admin_user,),
        ).fetchone()

        if not existing:
            conn.execute(
                """
                INSERT INTO users
                (username,password_hash,role,prompts_count,created_at)
                VALUES (?,?,?,?,?)
                """,
                (
                    admin_user,
                    generate_password_hash(admin_pass),
                    "admin",
                    0,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# AUTHENTICATION
# ============================================================

def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def cookie_manager():
    if not COOKIE_SUPPORT:
        return None

    if "_cookie_manager" not in st.session_state:
        st.session_state["_cookie_manager"] = CookieManager()

    return st.session_state["_cookie_manager"]


def set_login_cookie(token):
    manager = cookie_manager()
    if manager is None:
        return

    try:
        manager.set(
            COOKIE_NAME,
            token,
            max_age=COOKIE_DAYS * 24 * 60 * 60,
        )
    except Exception:
        pass


def get_login_cookie():
    manager = cookie_manager()
    if manager is None:
        return None

    try:
        return manager.get(COOKIE_NAME)
    except Exception:
        return None


def delete_login_cookie():
    manager = cookie_manager()
    if manager is None:
        return

    try:
        manager.delete(COOKIE_NAME)
    except Exception:
        pass


def create_session(username):
    token = secrets.token_urlsafe(48)
    now = datetime.now().isoformat(timespec="seconds")

    conn = connect_db()

    conn.execute(
        "DELETE FROM sessions WHERE username=?",
        (username,),
    )

    conn.execute(
        """
        INSERT INTO sessions
        (token_hash,username,created_at,last_seen)
        VALUES (?,?,?,?)
        """,
        (hash_token(token), username, now, now),
    )

    conn.commit()
    conn.close()

    set_login_cookie(token)


def restore_session():
    token = get_login_cookie()

    if not token:
        return False

    conn = connect_db()

    row = conn.execute(
        """
        SELECT s.username,u.role
        FROM sessions s
        JOIN users u ON u.username=s.username
        WHERE s.token_hash=?
        """,
        (hash_token(token),),
    ).fetchone()

    if row:
        conn.execute(
            """
            UPDATE sessions
            SET last_seen=?
            WHERE token_hash=?
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                hash_token(token),
            ),
        )
        conn.commit()
        conn.close()

        st.session_state.logged_in = True
        st.session_state.username = row["username"]
        st.session_state.role = row["role"]
        return True

    conn.close()
    delete_login_cookie()
    return False


def logout():
    token = get_login_cookie()

    if token:
        conn = connect_db()
        conn.execute(
            "DELETE FROM sessions WHERE token_hash=?",
            (hash_token(token),),
        )
        conn.commit()
        conn.close()

    delete_login_cookie()

    for key in [
        "logged_in",
        "username",
        "role",
        "active_tool",
        "tool_selector",
    ]:
        st.session_state.pop(key, None)

    st.rerun()


def get_user(username):
    conn = connect_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (username,),
    ).fetchone()
    conn.close()
    return row


def register_user(username, password):
    username = username.strip()

    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", username):
        return False, "Username must be 3–32 characters."

    if len(password) < 6:
        return False, "Password must contain at least 6 characters."

    conn = connect_db()

    try:
        conn.execute(
            """
            INSERT INTO users
            (username,password_hash,role,prompts_count,created_at)
            VALUES (?,?,?,?,?)
            """,
            (
                username,
                generate_password_hash(password),
                "user",
                0,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return False, "That username already exists."

    conn.close()
    return True, "Account created successfully."


def login_user(username, password):
    row = get_user(username.strip())

    if row and check_password_hash(row["password_hash"], password):
        st.session_state.logged_in = True
        st.session_state.username = row["username"]
        st.session_state.role = row["role"]
        create_session(row["username"])
        return True

    return False


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "persistent_checked" not in st.session_state:
    st.session_state.persistent_checked = True

    if not st.session_state.logged_in:
        restore_session()


# ============================================================
# GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


@st.cache_resource
def get_gemini_client():
    if not GEMINI_API_KEY:
        return None

    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        return None


gemini = get_gemini_client()


def ask_rockyai(prompt, instruction=""):
    if gemini is None:
        return (
            "⚠️ Gemini is not connected.\n\n"
            "Add your **GEMINI_API_KEY** to your environment variables "
            "or Render Environment settings."
        )

    final_prompt = f"""
You are RockyAI v1-5, a professional educational AI assistant.

IMPORTANT:
- Be accurate and clear.
- Explain difficult ideas in student-friendly language.
- Do not invent information.
- Use headings, bullets and examples when useful.
- If a question is ambiguous, state the assumption you made.

SPECIAL INSTRUCTION:
{instruction}

USER REQUEST:
{prompt}
"""

    try:
        response = gemini.models.generate_content(
            model=MODEL,
            contents=final_prompt,
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

        return "RockyAI returned an empty response."

    except Exception as error:
        return (
            "RockyAI could not complete the request.\n\n"
            f"Technical error: {error}"
        )


def save_chat(tool, prompt, response):
    username = st.session_state.get("username")

    if not username:
        return

    conn = connect_db()

    conn.execute(
        """
        INSERT INTO chats
        (username,tool,prompt,response,timestamp)
        VALUES (?,?,?,?,?)
        """,
        (
            username,
            tool,
            prompt,
            response,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    conn.execute(
        """
        UPDATE users
        SET prompts_count=prompts_count+1
        WHERE username=?
        """,
        (username,),
    )

    conn.commit()
    conn.close()


def clean_code(text):
    text = re.sub(r"```[A-Za-z0-9_+#.-]*\s*", "", text)
    text = text.replace("```", "")
    return text.strip()


# ============================================================
# PDF HELPERS
# ============================================================

def extract_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []

    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pass

    return "\n\n".join(pages).strip()


def create_pdf(title, content):
    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RockyTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=14,
    )

    body_style = ParagraphStyle(
        "RockyBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7,
    )

    story = [
        Paragraph(html.escape(title), title_style),
        Spacer(1, 5),
    ]

    for line in content.splitlines():
        if line.strip():
            story.append(
                Paragraph(
                    html.escape(line),
                    body_style,
                )
            )
        else:
            story.append(Spacer(1, 5))

    document.build(story)
    return output.getvalue()


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():
    st.markdown(
        """
        <div class="rocky-hero">
            <span class="badge">ROCKYAI v1-5</span>
            <span class="badge">AI LEARNING WORKSPACE</span>
            <h1>🏔️ RockyAI</h1>
            <p>Learn faster. Practice smarter. Build better.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        st.markdown("### 🚀 RockyAI v1-5")

        st.markdown(
            """
            <div class="rocky-card">
            <b>🎓 Learn</b><br>
            AI Tutor, PDF Study, Summaries and Question Solver.
            </div>

            <div class="rocky-card">
            <b>📝 Practice</b><br>
            Quizzes, sample papers, flashcards and exam preparation.
            </div>

            <div class="rocky-card">
            <b>🚀 Create</b><br>
            Code, mind maps, project ideas, PDFs and study plans.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        login_tab, register_tab = st.tabs(
            ["🔐 Login", "✨ Create Account"]
        )

        with login_tab:
            username = st.text_input(
                "Username",
                key="login_user",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_pass",
            )

            if st.button(
                "Login to RockyAI",
                type="primary",
                use_container_width=True,
            ):
                if login_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with register_tab:
            username = st.text_input(
                "New username",
                key="new_user",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="new_pass",
            )

            confirm = st.text_input(
                "Confirm password",
                type="password",
                key="confirm_pass",
            )

            if st.button(
                "Create Account",
                use_container_width=True,
            ):
                if password != confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, message = register_user(
                        username,
                        password,
                    )

                    if ok:
                        st.success(message)
                    else:
                        st.error(message)

    st.markdown(
        '<div class="rocky-footer">RockyAI v1-5 • AI-powered learning workspace</div>',
        unsafe_allow_html=True,
    )


if not st.session_state.logged_in:
    login_page()
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🏔️ RockyAI")
    st.caption("v1-4 • Professional AI Workspace")

    st.markdown(
        f"**{html.escape(st.session_state.username)}**"
    )

    if st.session_state.role == "admin":
        st.caption("🛡️ Administrator")
    else:
        st.caption("🎓 Student")

    st.divider()

    pages = [
        "🏠 Workspace",
        "🕘 History",
        "📊 Analytics",
    ]

    if st.session_state.role == "admin":
        pages.append("🛡️ Admin Panel")

    page = st.radio(
        "Navigation",
        pages,
    )

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):
        logout()

    st.caption(
        "Persistent login: up to 30 days, depending on browser settings."
    )


# ============================================================
# METRICS
# ============================================================

def show_metrics():
    username = st.session_state.username

    user = get_user(username)

    conn = connect_db()

    conversations = conn.execute(
        "SELECT COUNT(*) AS c FROM chats WHERE username=?",
        (username,),
    ).fetchone()["c"]

    open_tasks = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM study_plans
        WHERE username=? AND done=0
        """,
        (username,),
    ).fetchone()["c"]

    completed = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM study_plans
        WHERE username=? AND done=1
        """,
        (username,),
    ).fetchone()["c"]

    conn.close()

    c1, c2, c3, c4 = st.columns(4)

    values = [
        (user["prompts_count"], "AI interactions"),
        (conversations, "Saved conversations"),
        (open_tasks, "Open study tasks"),
        (completed, "Completed tasks"),
    ]

    for column, (value, label) in zip(
        [c1, c2, c3, c4],
        values,
    ):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-number">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# TOOL: ASK ROCKYAI
# ============================================================

def ask_tool():
    st.subheader("🤖 Ask RockyAI")

    mode = st.selectbox(
        "Response style",
        [
            "Student-friendly",
            "Exam answer",
            "Detailed explanation",
            "Project mentor",
            "Quick answer",
        ],
    )

    prompt = st.text_area(
        "Ask RockyAI anything",
        height=170,
        placeholder="Explain photosynthesis, solve this question, help me plan a project...",
    )

    if st.button(
        "🚀 Ask RockyAI",
        type="primary",
    ) and prompt.strip():

        with st.spinner("RockyAI is thinking..."):
            answer = ask_rockyai(
                prompt,
                f"Response mode: {mode}",
            )

        st.markdown("### 💬 RockyAI")
        st.markdown(answer)

        save_chat(
            "Ask RockyAI",
            prompt,
            answer,
        )


# ============================================================
# TOOL: AI TUTOR
# ============================================================

def tutor_tool():
    st.subheader("🎓 AI Tutor")

    subject = st.text_input(
        "Subject",
        placeholder="Science, Maths, SST, English...",
    )

    topic = st.text_input(
        "Topic",
        placeholder="e.g. Electricity",
    )

    level = st.selectbox(
        "Teaching level",
        [
            "Beginner",
            "Class 6–7",
            "Class 8–9",
            "Class 10",
            "Advanced",
        ],
    )

    if st.button(
        "👨‍🏫 Start Tutor Session",
        type="primary",
    ) and subject.strip() and topic.strip():

        prompt = f"""
Teach me {topic} from {subject}.
Teaching level: {level}.

Use this structure:
1. What it means
2. Simple explanation
3. Example
4. Important points
5. 3 questions to test me
"""

        with st.spinner("Preparing your lesson..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        save_chat(
            "AI Tutor",
            f"{subject}: {topic}",
            answer,
        )


# ============================================================
# TOOL: QUESTION SOLVER
# ============================================================

def solver_tool():
    st.subheader("🧩 Question Solver")

    question = st.text_area(
        "Paste your question",
        height=180,
    )

    method = st.selectbox(
        "Solution style",
        [
            "Step-by-step",
            "Short exam answer",
            "Explain like a teacher",
            "Check my answer",
        ],
    )

    if st.button(
        "🧩 Solve Question",
        type="primary",
    ) and question.strip():

        prompt = f"""
Solve the following question.

STYLE: {method}

QUESTION:
{question}

Show the reasoning clearly when appropriate.
For mathematics, show formulas and calculations.
Do not invent missing values.
"""

        with st.spinner("Solving..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        save_chat(
            "Question Solver",
            question,
            answer,
        )


# ============================================================
# TOOL: PDF STUDY
# ============================================================

def pdf_study_tool():
    st.subheader("📖 PDF Study")

    uploaded = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        key="pdf_study_upload",
    )

    if uploaded is None:
        st.info("Upload notes, a chapter, worksheet or study material.")
        return

    with st.spinner("Reading PDF..."):
        text = extract_pdf(uploaded)

    if not text:
        st.error("No readable text was found.")
        return

    st.success(
        f"PDF loaded • {len(text):,} characters"
    )

    action = st.selectbox(
        "Study action",
        [
            "Summarize",
            "Explain simply",
            "Create revision notes",
            "Create questions",
            "Find definitions",
            "Find important facts",
        ],
    )

    if st.button(
        "📖 Study this PDF",
        type="primary",
    ):
        prompt = f"""
Use ONLY the source material below.

TASK:
{action}

SOURCE:
{text[:60000]}
"""

        with st.spinner("Analyzing PDF..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        save_chat(
            "PDF Study",
            action,
            answer,
        )


# ============================================================
# TOOL: PDF GENERATOR
# ============================================================

def pdf_generator_tool():
    st.subheader("📄 PDF Generator")

    title = st.text_input(
        "PDF title",
        "RockyAI Study Notes",
    )

    content = st.text_area(
        "Content",
        height=280,
        placeholder="Enter your notes, answers, revision material or project content...",
    )

    if st.button(
        "📄 Generate PDF",
        type="primary",
    ):

        if not content.strip():
            st.warning("Enter some content first.")
            return

        data = create_pdf(
            title,
            content,
        )

        filename = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            title,
        ).strip("_") or "rockyai_document"

        st.download_button(
            "⬇️ Download PDF",
            data=data,
            file_name=filename + ".pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# ============================================================
# TOOL: QUIZ
# ============================================================

def quiz_tool():
    st.subheader("📝 Quiz Generator")

    topic = st.text_input(
        "Quiz topic",
        placeholder="e.g. Human digestion",
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
    )

    count = st.slider(
        "Questions",
        5,
        20,
        5,
    )

    if st.button(
        "📝 Generate Quiz",
        type="primary",
    ) and topic.strip():

        prompt = f"""
Create {count} multiple-choice questions about:
{topic}

Difficulty: {difficulty}

For every question give:
Question
A
B
C
D
Correct answer
Short explanation

Make the quiz educational and unambiguous.
"""

        with st.spinner("Creating quiz..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        save_chat(
            "Quiz Generator",
            topic,
            answer,
        )


# ============================================================
# TOOL: SAMPLE PAPER
# ============================================================

def sample_paper_tool():
    st.subheader("📚 Sample Paper")

    grade = st.text_input(
        "Class / Grade",
        "7",
    )

    subject = st.text_input(
        "Subject",
        "Science",
    )

    marks = st.number_input(
        "Total marks",
        min_value=20,
        max_value=100,
        value=40,
        step=10,
    )

    topics = st.text_area(
        "Chapters / Topics",
        height=120,
    )

    if st.button(
        "📚 Generate Sample Paper",
        type="primary",
    ) and topics.strip():

        prompt = f"""
Create a school sample paper.

Class: {grade}
Subject: {subject}
Total marks: {marks}
Topics: {topics}

Use clear sections:
A. Objective
B. Very Short Answer
C. Short Answer
D. Long Answer
E. Competency/Application

Put marks beside each question.
After the paper, provide a separate answer key.
"""

        with st.spinner("Preparing sample paper..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        data = create_pdf(
            f"{subject} Sample Paper",
            answer,
        )

        st.download_button(
            "⬇️ Download Sample Paper PDF",
            data=data,
            file_name="RockyAI_sample_paper.pdf",
            mime="application/pdf",
        )

        save_chat(
            "Sample Paper",
            topics,
            answer,
        )


# ============================================================
# TOOL: CODE
# ============================================================

def code_tool():
    st.subheader("💻 Code Generator")

    language = st.selectbox(
        "Programming language",
        [
            "Python",
            "JavaScript",
            "HTML/CSS/JS",
            "C",
            "C++",
            "Java",
            "Arduino",
        ],
    )

    request = st.text_area(
        "Describe your program",
        height=180,
        placeholder="Build a calculator, Arduino project, website, game...",
    )

    if st.button(
        "💻 Generate Code",
        type="primary",
    ) and request.strip():

        prompt = f"""
Generate runnable {language} code.

REQUEST:
{request}

Rules:
- Return ONLY source code.
- Do not use Markdown code fences.
- Include useful comments.
- Keep the code complete.
"""

        with st.spinner("Writing code..."):
            answer = clean_code(
                ask_rockyai(prompt)
            )

        display_language = {
            "Python": "python",
            "JavaScript": "javascript",
            "HTML/CSS/JS": "html",
            "C": "c",
            "C++": "cpp",
            "Java": "java",
            "Arduino": "cpp",
        }.get(language, "text")

        st.code(
            answer,
            language=display_language,
            line_numbers=True,
        )

        st.download_button(
            "⬇️ Download Code",
            data=answer,
            file_name="rockyai_generated_code.txt",
            mime="text/plain",
        )

        save_chat(
            "Code Generator",
            request,
            answer,
        )


# ============================================================
# TOOL: MIND MAP
# ============================================================

def mindmap_tool():
    st.subheader("🧠 Mind Map")

    topic = st.text_input(
        "Central topic",
        placeholder="e.g. The Solar System",
    )

    if st.button(
        "🧠 Generate Mind Map",
        type="primary",
    ) and topic.strip():

        prompt = f"""
Create a text mind map for "{topic}".

Use:
CENTRAL TOPIC
├── Branch
│   ├── Subtopic
│   └── Subtopic
└── Branch

Include 5–8 major branches and useful subtopics.
"""

        with st.spinner("Building mind map..."):
            answer = ask_rockyai(prompt)

        st.code(answer)

        save_chat(
            "Mind Map",
            topic,
            answer,
        )


# ============================================================
# TOOL: FLASHCARDS
# ============================================================

def flashcards_tool():
    st.subheader("🃏 Flashcards")

    topic = st.text_input(
        "Flashcard topic",
        placeholder="e.g. French Revolution",
    )

    count = st.slider(
        "Number of cards",
        5,
        25,
        10,
    )

    if st.button(
        "🃏 Create Flashcards",
        type="primary",
    ) and topic.strip():

        prompt = f"""
Create {count} study flashcards about "{topic}".

Format:
CARD 1
Q: ...
A: ...

Keep answers concise and useful for revision.
"""

        with st.spinner("Creating flashcards..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        save_chat(
            "Flashcards",
            topic,
            answer,
        )


# ============================================================
# TOOL: STUDY PLANNER
# ============================================================

def planner_tool():
    st.subheader("📅 Study Planner")

    with st.form("study_plan_form"):
        subject = st.text_input("Subject")
        task = st.text_input("Task")
        target = st.date_input("Target date")

        add = st.form_submit_button(
            "➕ Add Study Task"
        )

    if add and subject.strip() and task.strip():

        conn = connect_db()

        conn.execute(
            """
            INSERT INTO study_plans
            (username,subject,task,target_date,done,created_at)
            VALUES (?,?,?,?,?,?)
            """,
            (
                st.session_state.username,
                subject.strip(),
                task.strip(),
                str(target),
                0,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        conn.commit()
        conn.close()

        st.success("Study task added.")
        st.rerun()

    conn = connect_db()

    rows = conn.execute(
        """
        SELECT id,subject,task,target_date,done
        FROM study_plans
        WHERE username=?
        ORDER BY target_date
        """,
        (st.session_state.username,),
    ).fetchall()

    conn.close()

    if not rows:
        st.info("Your study planner is empty.")
        return

    for row in rows:

        c1, c2, c3 = st.columns(
            [1, 6, 1]
        )

        with c1:
            st.write(
                "✅" if row["done"] else "📌"
            )

        with c2:
            st.markdown(
                f"**{row['subject']}** — {row['task']}"
            )
            st.caption(
                f"Target: {row['target_date']}"
            )

        with c3:
            if not row["done"]:

                if st.button(
                    "Done",
                    key=f"plan_done_{row['id']}",
                ):

                    conn = connect_db()

                    conn.execute(
                        """
                        UPDATE study_plans
                        SET done=1
                        WHERE id=?
                        """,
                        (row["id"],),
                    )

                    conn.commit()
                    conn.close()

                    st.rerun()


# ============================================================
# TOOL: SUMMARIZER
# ============================================================

def summarizer_tool():
    st.subheader("✂️ Smart Summarizer")

    text = st.text_area(
        "Paste text",
        height=260,
    )

    style = st.selectbox(
        "Summary style",
        [
            "5 key bullet points",
            "Exam revision notes",
            "Simple explanation",
            "Detailed summary",
        ],
    )

    if st.button(
        "✂️ Summarize",
        type="primary",
    ) and text.strip():

        prompt = f"""
Summarize this source as:
{style}

Preserve important facts, names, definitions and numbers.
Do not add facts not contained in the source.

SOURCE:
{text[:60000]}
"""

        with st.spinner("Summarizing..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        save_chat(
            "Smart Summarizer",
            text[:500],
            answer,
        )


# ============================================================
# TOOL: TRANSLATOR
# ============================================================

def translator_tool():
    st.subheader("🌐 Translator")

    text = st.text_area(
        "Text",
        height=200,
    )

    language = st.selectbox(
        "Translate to",
        [
            "English",
            "Hindi",
            "Marathi",
            "Spanish",
            "French",
            "German",
            "Japanese",
        ],
    )

    if st.button(
        "🌐 Translate",
        type="primary",
    ) and text.strip():

        answer = ask_rockyai(
            f"Translate this text into {language}. Preserve its meaning and formatting.\n\n{text}"
        )

        st.markdown(answer)

        save_chat(
            "Translator",
            f"{language}: {text[:500]}",
            answer,
        )


# ============================================================
# TOOL: BRAINSTORM
# ============================================================

def brainstorm_tool():
    st.subheader("💡 Brainstorm")

    idea = st.text_area(
        "What do you want to brainstorm?",
        height=170,
        placeholder="Science exhibition, startup, school project, app idea...",
    )

    focus = st.selectbox(
        "Focus",
        [
            "School project",
            "Science exhibition",
            "Startup idea",
            "App idea",
            "Problem solving",
            "Presentation",
        ],
    )

    if st.button(
        "💡 Brainstorm",
        type="primary",
    ) and idea.strip():

        prompt = f"""
Act as a creative project mentor.

TOPIC:
{idea}

FOCUS:
{focus}

Provide:
1. 10 ideas
2. Best 3 ideas
3. Why the best idea stands out
4. Required resources
5. Execution plan
6. How to make it impressive for judges
7. Possible risks and improvements
"""

        with st.spinner("Brainstorming..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        save_chat(
            "Brainstorm",
            idea,
            answer,
        )


# ============================================================
# TOOL: EXAM PREPARATION
# ============================================================

def exam_tool():
    st.subheader("🎯 Exam Preparation")

    subject = st.text_input(
        "Subject",
        placeholder="Science",
    )

    topics = st.text_area(
        "Topics / chapters",
        height=140,
    )

    days = st.number_input(
        "Days available",
        min_value=1,
        max_value=90,
        value=7,
    )

    if st.button(
        "🎯 Build Exam Strategy",
        type="primary",
    ) and subject.strip() and topics.strip():

        prompt = f"""
Create a {days}-day exam preparation plan.

SUBJECT:
{subject}

TOPICS:
{topics}

Include:
- Daily study targets
- Revision sessions
- Practice questions
- Mock-test strategy
- Final-day revision
- Time-management advice

Keep it realistic for a student.
"""

        with st.spinner("Building your exam plan..."):
            answer = ask_rockyai(prompt)

        st.markdown(answer)

        data = create_pdf(
            f"{subject} Exam Preparation Plan",
            answer,
        )

        st.download_button(
            "⬇️ Download Exam Plan PDF",
            data=data,
            file_name="RockyAI_exam_plan.pdf",
            mime="application/pdf",
        )

        save_chat(
            "Exam Preparation",
            f"{subject}: {topics}",
            answer,
        )


# ============================================================
# TOOL: PERIODIC TABLE
# ============================================================

def periodic_tool():
    st.subheader("🧪 Periodic Table Quick Reference")

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

    search = st.text_input(
        "Search by atomic number, symbol or name"
    )

    filtered = [
        element
        for element in elements
        if not search.strip()
        or search.lower() in element[0].lower()
        or search.lower() in element[1].lower()
        or search.lower() in element[2].lower()
    ]

    columns = st.columns(3)

    for index, element in enumerate(filtered):

        number, symbol, name = element

        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="rocky-card">
                    <b>{number}. {symbol}</b><br>
                    <span class="small-muted">{name}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# NEW v1-5 TOOLS
# ============================================================

def generic_ai_tool(title, icon, fields, instruction, button_text="Generate"):
    st.subheader(f"{icon} {title}")
    values = {}
    for label, placeholder in fields:
        values[label] = st.text_area(label, placeholder=placeholder, height=95)
    if st.button(f"{icon} {button_text}", type="primary") and any(v.strip() for v in values.values()):
        prompt = "\n".join(f"{k}: {v}" for k, v in values.items() if v.strip())
        with st.spinner("RockyAI is building your result..."):
            answer = ask_rockyai(prompt, instruction)
        st.markdown(answer)
        save_chat(title, prompt, answer)


def daily_challenge_tool():
    generic_ai_tool("Daily Challenge", "🏆", [("Subject / topic", "e.g. Class 7 Science"), ("Difficulty", "Easy, medium or hard")], "Create one engaging daily challenge, then give the answer separately with a short explanation.", "Create Challenge")


def debate_tool():
    generic_ai_tool("Debate Coach", "🗣️", [("Motion", "e.g. AI should be used in schools"), ("Your side", "For / Against")], "Act as a debate coach. Give arguments, counterarguments, evidence prompts, rebuttals and a strong closing statement. Keep it age-appropriate.", "Coach Me")


def interview_tool():
    generic_ai_tool("Interview Coach", "🎤", [("Role / goal", "e.g. Student council, internship, project presentation"), ("Experience", "Briefly describe your experience")], "Act as an interviewer and coach. Ask likely questions, give model answer structures, common mistakes and confidence tips.", "Prepare Me")


def career_tool():
    generic_ai_tool("Career Roadmap", "🧭", [("Interest", "e.g. AI, robotics, medicine, design"), ("Current level", "Class / skill level / experience")], "Create a realistic learning roadmap with skills, projects, milestones and next steps. Do not guarantee careers or salaries.", "Build Roadmap")


def project_tool():
    generic_ai_tool("Project Builder", "🚀", [("Project idea", "Describe your idea or problem"), ("Constraints", "Budget, time, hardware/software available")], "Turn the idea into a polished project plan with objective, features, architecture, milestones, testing and presentation points.", "Build Project")


def presentation_tool():
    generic_ai_tool("Presentation Maker", "📊", [("Topic", "Presentation topic"), ("Audience", "Class, judges, teachers, customers, etc."), ("Duration", "e.g. 5 minutes")], "Create a professional slide-by-slide presentation outline with titles, concise bullets, speaker notes and a memorable opening and closing.", "Create Slides")


def memory_tool():
    generic_ai_tool("Memory Trainer", "🧠", [("Topic", "What do you want to remember?"), ("Level", "Beginner / exam revision / advanced")], "Create an active-recall memory workout using mnemonics, chunking, retrieval questions and spaced-repetition suggestions.", "Train Memory")


def goal_tool():
    generic_ai_tool("Goal Coach", "🎯", [("Goal", "What do you want to achieve?"), ("Deadline", "Target date or time period")], "Turn the goal into measurable milestones, weekly actions, a simple success metric and a recovery plan for missed tasks.", "Plan Goal")


def vocabulary_tool():
    generic_ai_tool("Vocabulary Builder", "📘", [("Language / level", "e.g. English, Class 7"), ("Topic", "e.g. science vocabulary")], "Create a vocabulary lesson with useful words, simple meanings, example sentences, memory clues and a short quiz.", "Build Vocabulary")


def fact_checker_tool():
    generic_ai_tool("Fact Checker", "🔍", [("Claim", "Paste the statement you want checked")], "Analyze the claim carefully. Separate what can be established from what is uncertain. Do not pretend to browse or cite sources you did not access.", "Analyze Claim")


# ============================================================
# WORKSPACE
# ============================================================

def workspace():
    st.markdown(
        f"""
        <div class="rocky-hero">
            <span class="badge">ROCKYAI v1-5</span>
            <span class="badge">ONLINE</span>
            <h1>Welcome back, {html.escape(st.session_state.username)} 👋</h1>
            <p>Your AI learning and productivity dashboard is ready.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_metrics()

    st.markdown("### 🧰 RockyAI Tools")

    if "active_tool" not in st.session_state:
        st.session_state.active_tool = TOOLS[0]

    selected = st.selectbox(
        "Choose a tool",
        TOOLS,
        index=TOOLS.index(
            st.session_state.active_tool
        ),
        key="tool_selector",
    )

    st.session_state.active_tool = selected

    st.divider()

    functions = {
        "🤖 Ask RockyAI": ask_tool,
        "🎓 AI Tutor": tutor_tool,
        "🧩 Question Solver": solver_tool,
        "📖 PDF Study": pdf_study_tool,
        "📄 PDF Generator": pdf_generator_tool,
        "📝 Quiz Generator": quiz_tool,
        "📚 Sample Paper": sample_paper_tool,
        "💻 Code Generator": code_tool,
        "🧠 Mind Map": mindmap_tool,
        "🃏 Flashcards": flashcards_tool,
        "📅 Study Planner": planner_tool,
        "✂️ Smart Summarizer": summarizer_tool,
        "🌐 Translator": translator_tool,
        "💡 Brainstorm": brainstorm_tool,
        "🎯 Exam Preparation": exam_tool,
        "🧪 Periodic Table": periodic_tool,
        "🏆 Daily Challenge": daily_challenge_tool,
        "🗣️ Debate Coach": debate_tool,
        "🎤 Interview Coach": interview_tool,
        "🧭 Career Roadmap": career_tool,
        "🚀 Project Builder": project_tool,
        "📊 Presentation Maker": presentation_tool,
        "🧠 Memory Trainer": memory_tool,
        "🎯 Goal Coach": goal_tool,
        "📘 Vocabulary Builder": vocabulary_tool,
        "🔍 Fact Checker": fact_checker_tool,
    }

    functions[selected]()


# ============================================================
# HISTORY
# ============================================================

def history_page():
    st.markdown("## 🕘 Conversation History")

    conn = connect_db()

    rows = conn.execute(
        """
        SELECT id,tool,prompt,response,timestamp
        FROM chats
        WHERE username=?
        ORDER BY id DESC
        LIMIT 100
        """,
        (st.session_state.username,),
    ).fetchall()

    conn.close()

    if not rows:
        st.info("No saved conversations yet.")
        return

    for row in rows:

        with st.expander(
            f"{row['tool']} • {row['timestamp']}"
        ):
            st.markdown("**Prompt**")
            st.write(row["prompt"])

            st.markdown("**RockyAI**")
            st.markdown(row["response"])


# ============================================================
# ANALYTICS
# ============================================================

def analytics_page():
    st.markdown("## 📊 Analytics")

    username = st.session_state.username

    conn = connect_db()

    total = conn.execute(
        "SELECT COUNT(*) AS c FROM chats WHERE username=?",
        (username,),
    ).fetchone()["c"]

    tools = conn.execute(
        """
        SELECT tool,COUNT(*) AS c
        FROM chats
        WHERE username=?
        GROUP BY tool
        ORDER BY c DESC
        """,
        (username,),
    ).fetchall()

    total_tasks = conn.execute(
        "SELECT COUNT(*) AS c FROM study_plans WHERE username=?",
        (username,),
    ).fetchone()["c"]

    done_tasks = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM study_plans
        WHERE username=? AND done=1
        """,
        (username,),
    ).fetchone()["c"]

    conn.close()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "AI interactions",
        total,
    )

    c2.metric(
        "Study tasks",
        total_tasks,
    )

    c3.metric(
        "Completed tasks",
        done_tasks,
    )

    st.markdown("### 🧰 Tool usage")

    if tools:
        for row in tools:
            st.write(
                f"**{row['tool']}** — {row['c']} uses"
            )
    else:
        st.info(
            "Start using RockyAI tools to build your analytics."
        )


# ============================================================
# ADMIN
# ============================================================

def admin_page():
    st.markdown("## 🛡️ Admin Panel")

    if st.session_state.role != "admin":
        st.error("Access denied.")
        return

    conn = connect_db()

    users = conn.execute(
        """
        SELECT username,role,prompts_count,created_at
        FROM users
        ORDER BY created_at DESC
        """
    ).fetchall()

    total_chats = conn.execute(
        "SELECT COUNT(*) AS c FROM chats"
    ).fetchone()["c"]

    conn.close()

    c1, c2 = st.columns(2)

    c1.metric(
        "Total users",
        len(users),
    )

    c2.metric(
        "Total AI interactions",
        total_chats,
    )

    st.markdown("### 👥 Registered users")

    for user in users:

        st.markdown(
            f"""
            <div class="rocky-card">
                <b>{html.escape(user["username"])}</b>
                &nbsp;•&nbsp; {user["role"]}
                &nbsp;•&nbsp; {user["prompts_count"]} interactions
                <br>
                <span class="small-muted">
                    Joined: {user["created_at"]}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN ROUTER
# ============================================================

if page == "🏠 Workspace":
    workspace()

elif page == "🕘 History":
    history_page()

elif page == "📊 Analytics":
    analytics_page()

elif page == "🛡️ Admin Panel":
    admin_page()


st.markdown(
    '<div class="rocky-footer">RockyAI v1-5 • Learn • Practice • Create • Build</div>',
    unsafe_allow_html=True,
)
