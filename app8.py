import os
import re
import io
import html
import hashlib
import secrets
import sqlite3
from datetime import datetime, date
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


# ============================================================
# ROCKYAI v1-6
# PREMIUM AI LEARNING WORKSPACE
# ============================================================

APP_NAME = "RockyAI v1-6"
APP_VERSION = "1.6"
MODEL = "gemini-2.5-flash"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rockyai_v1_6.db"

COOKIE_NAME = "rockyai_v1_6_session"
COOKIE_DAYS = 30


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PREMIUM RED UI
# ============================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --red: #ef233c;
    --red2: #ff4d6d;
    --red3: #be123c;
    --dark: #070709;
    --dark2: #0d0d11;
    --panel: #111116;
    --panel2: #17171e;
    --border: rgba(255,255,255,.08);
    --redborder: rgba(239,35,60,.25);
    --text: #f8fafc;
    --muted: #a1a1aa;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 5% 0%,
            rgba(239,35,60,.16),
            transparent 25%
        ),
        radial-gradient(
            circle at 95% 15%,
            rgba(190,18,60,.12),
            transparent 25%
        ),
        linear-gradient(
            135deg,
            #050506 0%,
            #0b0b0f 50%,
            #070708 100%
        );
    color: var(--text);
}

.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #12080c 0%,
            #0b090c 45%,
            #070709 100%
        );
    border-right: 1px solid rgba(239,35,60,.20);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.2rem;
}

/* BUTTONS */

div[data-testid="stButton"] > button {
    border-radius: 13px;
    border: 1px solid rgba(255,255,255,.08);
    background:
        linear-gradient(
            180deg,
            #1a1a20,
            #101014
        );
    color: #fff;
    font-weight: 700;
    transition: .18s ease;
}

div[data-testid="stButton"] > button:hover {
    border-color: rgba(255,77,109,.55);
    box-shadow:
        0 0 25px rgba(239,35,60,.15);
    transform: translateY(-1px);
}

button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #ef233c,
            #be123c
        ) !important;
    border-color: #ff4d6d !important;
    color: white !important;
}

/* INPUTS */

.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"],
.stNumberInput input {
    background: #111116 !important;
    color: white !important;
    border-color: rgba(255,255,255,.09) !important;
    border-radius: 12px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #ef233c !important;
    box-shadow: 0 0 0 1px #ef233c !important;
}

/* HERO */

.rocky-hero {
    position: relative;
    overflow: hidden;

    padding: 36px;

    border-radius: 28px;

    background:
        linear-gradient(
            135deg,
            rgba(55,8,18,.95),
            rgba(16,16,22,.98) 55%,
            rgba(30,7,13,.98)
        );

    border: 1px solid rgba(255,77,109,.22);

    box-shadow:
        0 25px 80px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.04);

    margin-bottom: 24px;
}

.rocky-hero:after {
    content: "🏔️";
    position: absolute;
    right: 30px;
    bottom: -32px;
    font-size: 9rem;
    opacity: .12;
}

.hero-logo {
    font-size: 3.5rem;
}

.hero-title {
    font-size: 3.1rem;
    font-weight: 900;
    letter-spacing: -2px;
    margin: 5px 0;
}

.hero-subtitle {
    color: #c7c7ce;
    font-size: 1.05rem;
}

.badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    background: rgba(239,35,60,.12);
    border: 1px solid rgba(255,77,109,.24);
    color: #fecdd3;
    margin-right: 6px;
    font-size: .76rem;
    font-weight: 800;
    letter-spacing: .4px;
}

/* CARDS */

.rocky-card {
    padding: 21px;
    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(27,22,27,.95),
            rgba(13,14,19,.95)
        );

    border: 1px solid rgba(255,255,255,.07);

    box-shadow:
        0 12px 35px rgba(0,0,0,.18);

    margin: 8px 0;
}

.feature-card {
    min-height: 165px;
    padding: 22px;

    border-radius: 22px;

    background:
        linear-gradient(
            145deg,
            rgba(28,19,24,.95),
            rgba(12,13,18,.97)
        );

    border: 1px solid rgba(239,35,60,.13);

    transition: .2s ease;

    margin-bottom: 15px;
}

.feature-card:hover {
    transform: translateY(-3px);
    border-color: rgba(255,77,109,.35);
    box-shadow:
        0 15px 45px rgba(239,35,60,.10);
}

.feature-icon {
    font-size: 2rem;
}

.feature-title {
    font-weight: 800;
    font-size: 1.02rem;
    margin-top: 8px;
}

.feature-description {
    color: #9f9fa8;
    font-size: .84rem;
    margin-top: 6px;
}

/* METRICS */

.metric-card {
    padding: 20px;
    border-radius: 18px;

    background:
        linear-gradient(
            145deg,
            #191319,
            #101116
        );

    border: 1px solid rgba(239,35,60,.15);
}

.metric-number {
    font-size: 1.85rem;
    font-weight: 900;
}

.metric-label {
    color: #a8a8b2;
    font-size: .84rem;
}

/* SECTION */

.section-title {
    font-size: 1.45rem;
    font-weight: 850;
    margin-top: 20px;
    margin-bottom: 10px;
}

/* AI RESPONSE */

.ai-response {
    padding: 24px;

    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(26,15,20,.92),
            rgba(13,14,19,.96)
        );

    border-left: 3px solid #ef233c;

    border-top: 1px solid rgba(255,255,255,.05);
    border-right: 1px solid rgba(255,255,255,.05);
    border-bottom: 1px solid rgba(255,255,255,.05);

    margin-top: 15px;
}

/* STATUS */

.status-online {
    color: #fb7185;
    font-weight: 800;
}

/* FOOTER */

.rocky-footer {
    text-align: center;
    color: #71717a;
    padding: 40px 0 10px;
    font-size: .82rem;
}

/* TABS */

.stTabs [data-baseweb="tab"] {
    font-weight: 700;
}

.stTabs [aria-selected="true"] {
    color: #ff4d6d !important;
}

/* EXPANDERS */

.streamlit-expanderHeader {
    background: #111116 !important;
    border-radius: 12px !important;
}

/* DATAFRAME */

[data-testid="stDataFrame"] {
    border-radius: 15px;
    overflow: hidden;
}

/* DIVIDER */

hr {
    border-color: rgba(255,255,255,.06) !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def connect_db():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

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

        CREATE TABLE IF NOT EXISTS favorites (
            username TEXT NOT NULL,
            tool TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(username, tool)
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            goal TEXT NOT NULL,
            deadline TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    admin_user = os.getenv(
        "ADMIN_USERNAME",
        ""
    ).strip()

    admin_pass = os.getenv(
        "ADMIN_PASSWORD",
        ""
    )

    if admin_user and admin_pass:

        existing = conn.execute(
            "SELECT username FROM users WHERE username=?",
            (admin_user,)
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
                    datetime.now().isoformat(timespec="seconds")
                )
            )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# SESSION / LOGIN
# ============================================================

def hash_token(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


try:

    from extra_streamlit_components import CookieManager

    COOKIE_SUPPORT = True

except Exception:

    COOKIE_SUPPORT = False


def cookie_manager():

    if not COOKIE_SUPPORT:
        return None

    if "_cookie_manager" not in st.session_state:

        st.session_state["_cookie_manager"] = (
            CookieManager()
        )

    return st.session_state["_cookie_manager"]


def set_login_cookie(token):

    manager = cookie_manager()

    if manager is None:
        return

    try:

        manager.set(
            COOKIE_NAME,
            token,
            max_age=COOKIE_DAYS * 24 * 60 * 60
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

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    conn = connect_db()

    conn.execute(
        "DELETE FROM sessions WHERE username=?",
        (username,)
    )

    conn.execute(
        """
        INSERT INTO sessions
        (token_hash,username,created_at,last_seen)
        VALUES (?,?,?,?)
        """,
        (
            hash_token(token),
            username,
            now,
            now
        )
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
        JOIN users u
        ON u.username=s.username
        WHERE s.token_hash=?
        """,
        (hash_token(token),)
    ).fetchone()

    if row:

        conn.execute(
            """
            UPDATE sessions
            SET last_seen=?
            WHERE token_hash=?
            """,
            (
                datetime.now().isoformat(
                    timespec="seconds"
                ),
                hash_token(token)
            )
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
            (hash_token(token),)
        )

        conn.commit()
        conn.close()

    delete_login_cookie()

    for key in list(st.session_state.keys()):

        if key.startswith(
            (
                "logged_in",
                "username",
                "role",
                "active_",
                "tool_",
                "page_"
            )
        ):
            st.session_state.pop(
                key,
                None
            )

    st.rerun()


def get_user(username):

    conn = connect_db()

    row = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    conn.close()

    return row


def register_user(username, password):

    username = username.strip()

    if not re.fullmatch(
        r"[A-Za-z0-9_.-]{3,32}",
        username
    ):
        return (
            False,
            "Username must contain 3–32 letters, numbers, dots, underscores or hyphens."
        )

    if len(password) < 6:

        return (
            False,
            "Password must contain at least 6 characters."
        )

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
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return (
            False,
            "That username already exists."
        )

    conn.close()

    return (
        True,
        "Account created successfully."
    )


def login_user(username, password):

    row = get_user(
        username.strip()
    )

    if row and check_password_hash(
        row["password_hash"],
        password
    ):

        st.session_state.logged_in = True
        st.session_state.username = row["username"]
        st.session_state.role = row["role"]

        create_session(
            row["username"]
        )

        return True

    return False


if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if (
    "persistent_checked"
    not in st.session_state
):

    st.session_state.persistent_checked = True

    if not st.session_state.logged_in:

        restore_session()


# ============================================================
# GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()


@st.cache_resource
def get_gemini_client():

    if not GEMINI_API_KEY:
        return None

    try:

        return genai.Client(
            api_key=GEMINI_API_KEY
        )

    except Exception:

        return None


gemini = get_gemini_client()


def ask_rockyai(
    prompt,
    instruction=""
):

    if gemini is None:

        return (
            "⚠️ **Gemini is not connected.**\n\n"
            "Add `GEMINI_API_KEY` to your environment variables "
            "or Render Environment settings."
        )

    final_prompt = f"""
You are RockyAI v1-6.

You are a professional educational,
productivity and project AI assistant.

CORE RULES:
- Be accurate.
- Never knowingly invent facts.
- Explain difficult ideas clearly.
- Use headings and bullets when useful.
- Adapt explanations to the requested level.
- Be practical and actionable.
- For school questions, use student-friendly language.
- For coding, produce complete runnable code.
- For planning, produce realistic steps.
- If information is uncertain, say so.

SPECIAL INSTRUCTION:
{instruction}

USER REQUEST:
{prompt}
"""

    try:

        response = gemini.models.generate_content(
            model=MODEL,
            contents=final_prompt
        )

        text = getattr(
            response,
            "text",
            None
        )

        if text:

            return text.strip()

        return (
            "RockyAI returned an empty response."
        )

    except Exception as error:

        return (
            "RockyAI could not complete the request.\n\n"
            f"Technical error: {error}"
        )


def save_chat(
    tool,
    prompt,
    response
):

    username = st.session_state.get(
        "username"
    )

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
            datetime.now().isoformat(
                timespec="seconds"
            )
        )
    )

    conn.execute(
        """
        UPDATE users
        SET prompts_count=prompts_count+1
        WHERE username=?
        """,
        (username,)
    )

    conn.commit()
    conn.close()


def clean_code(text):

    text = re.sub(
        r"```[A-Za-z0-9_+#.-]*\s*",
        "",
        text
    )

    text = text.replace(
        "```",
        ""
    )

    return text.strip()


# ============================================================
# PDF
# ============================================================

def extract_pdf(uploaded_file):

    reader = PdfReader(
        uploaded_file
    )

    pages = []

    for page in reader.pages:

        try:

            pages.append(
                page.extract_text() or ""
            )

        except Exception:
            pass

    return "\n\n".join(
        pages
    ).strip()


def create_pdf(
    title,
    content
):

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RockyTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=14
    )

    body_style = ParagraphStyle(
        "RockyBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7
    )

    story = [
        Paragraph(
            html.escape(title),
            title_style
        ),
        Spacer(1, 5)
    ]

    for line in content.splitlines():

        if line.strip():

            story.append(
                Paragraph(
                    html.escape(line),
                    body_style
                )
            )

        else:

            story.append(
                Spacer(1, 5)
            )

    document.build(
        story
    )

    return output.getvalue()


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    st.markdown(
        """
        <div class="rocky-hero">

            <span class="badge">
                ROCKYAI v1-6
            </span>

            <span class="badge">
                NEXT-GEN AI WORKSPACE
            </span>

            <div class="hero-logo">
                🏔️
            </div>

            <div class="hero-title">
                RockyAI
            </div>

            <div class="hero-subtitle">
                Learn faster. Think smarter. Build bigger.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    left, right = st.columns(
        [1.15, .85]
    )

    with left:

        st.markdown(
            "## 🚀 Your AI command center"
        )

        cards = [
            (
                "🎓",
                "Learn",
                "AI Tutor, PDF Study, summaries and personalized explanations."
            ),
            (
                "🧠",
                "Practice",
                "Quizzes, flashcards, challenges and exam preparation."
            ),
            (
                "🚀",
                "Create",
                "Projects, presentations, code, PDFs and mind maps."
            ),
            (
                "🎯",
                "Improve",
                "Goals, memory training, career planning and productivity."
            )
        ]

        for icon, title, desc in cards:

            st.markdown(
                f"""
                <div class="feature-card">

                    <div class="feature-icon">
                        {icon}
                    </div>

                    <div class="feature-title">
                        {title}
                    </div>

                    <div class="feature-description">
                        {desc}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    with right:

        login_tab, register_tab = st.tabs(
            [
                "🔐 Login",
                "✨ Create Account"
            ]
        )

        with login_tab:

            username = st.text_input(
                "Username",
                key="login_user_v16"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_pass_v16"
            )

            if st.button(
                "🚀 Enter RockyAI",
                type="primary",
                use_container_width=True
            ):

                if login_user(
                    username,
                    password
                ):

                    st.success(
                        "Welcome back!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Invalid username or password."
                    )

        with register_tab:

            username = st.text_input(
                "New username",
                key="new_user_v16"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="new_pass_v16"
            )

            confirm = st.text_input(
                "Confirm password",
                type="password",
                key="confirm_pass_v16"
            )

            if st.button(
                "✨ Create RockyAI Account",
                type="primary",
                use_container_width=True
            ):

                if password != confirm:

                    st.error(
                        "Passwords do not match."
                    )

                else:

                    ok, message = register_user(
                        username,
                        password
                    )

                    if ok:

                        st.success(
                            message
                        )

                    else:

                        st.error(
                            message
                        )

    st.markdown(
        """
        <div class="rocky-footer">
            🏔️ RockyAI v1-6
            • Learn
            • Practice
            • Create
            • Build
        </div>
        """,
        unsafe_allow_html=True
    )


if not st.session_state.logged_in:

    login_page()

    st.stop()


# ============================================================
# TOOL CATALOG
# ============================================================

TOOLS = [

    ("🤖", "Ask RockyAI", "Your general-purpose AI assistant."),
    ("🎓", "AI Tutor", "Learn any topic step by step."),
    ("🧩", "Question Solver", "Solve and understand difficult questions."),
    ("📖", "PDF Study", "Turn PDFs into study material."),
    ("📄", "PDF Generator", "Create downloadable PDFs."),
    ("📝", "Quiz Generator", "Create custom practice quizzes."),
    ("📚", "Sample Paper", "Generate complete exam papers."),
    ("💻", "Code Generator", "Create programs and projects."),
    ("🧠", "Mind Map", "Convert topics into structured maps."),
    ("🃏", "Flashcards", "Create revision flashcards."),
    ("📅", "Study Planner", "Manage your study tasks."),
    ("✂️", "Smart Summarizer", "Turn long text into concise notes."),
    ("🌐", "Translator", "Translate text between languages."),
    ("💡", "Brainstorm", "Generate creative ideas."),
    ("🎯", "Exam Preparation", "Build a complete exam strategy."),
    ("🧪", "Periodic Table", "Explore common chemical elements."),

    ("🏆", "Daily Challenge", "Get a daily learning challenge."),
    ("🗣️", "Debate Coach", "Prepare arguments and rebuttals."),
    ("🎤", "Interview Coach", "Practice interviews."),
    ("🧭", "Career Roadmap", "Explore learning paths."),
    ("🚀", "Project Builder", "Turn ideas into projects."),
    ("📊", "Presentation Maker", "Build presentation structures."),
    ("🧠", "Memory Trainer", "Train active recall."),
    ("🎯", "Goal Coach", "Turn goals into action plans."),
    ("📘", "Vocabulary Builder", "Build stronger vocabulary."),
    ("🔍", "Fact Checker", "Analyze claims carefully."),

    # NEW v1-6
    ("🧮", "Math Coach", "Practice and understand mathematics."),
    ("🧑‍🔬", "Science Lab", "Explore science concepts and experiments."),
    ("📰", "Article Analyzer", "Analyze and summarize articles."),
    ("🧑‍💻", "Code Debugger", "Find and explain programming errors."),
    ("🔐", "Study Mode", "Focused distraction-free AI study."),
    ("⚡", "Quick Explain", "Explain any concept in seconds."),
    ("📋", "Assignment Helper", "Plan and improve assignments."),
    ("🏅", "Achievement Center", "Track your RockyAI progress."),
]


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:10px 0 15px;
        ">
            <div style="font-size:3rem;">
                🏔️
            </div>

            <div style="
                font-size:1.35rem;
                font-weight:900;
            ">
                RockyAI
            </div>

            <div style="
                color:#fb7185;
                font-size:.75rem;
                font-weight:800;
            ">
                VERSION 1.6
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    username = st.session_state.username

    st.markdown(
        f"### 👋 {html.escape(username)}"
    )

    if st.session_state.role == "admin":

        st.caption(
            "🛡️ Administrator"
        )

    else:

        st.caption(
            "🎓 Student"
        )

    st.divider()

    navigation = [
        "🏠 Dashboard",
        "🧰 AI Tools",
        "⭐ Favorites",
        "🕘 History",
        "📅 Planner",
        "🎯 Goals",
        "📊 Analytics",
        "🏅 Achievements",
    ]

    if st.session_state.role == "admin":

        navigation.append(
            "🛡️ Admin Panel"
        )

    page = st.radio(
        "Navigation",
        navigation,
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown(
        """
        <div class="rocky-card">

        <b>⚡ RockyAI Status</b>

        <br><br>

        <span class="status-online">
        ● ONLINE
        </span>

        <br>

        <span class="small-muted">
        Gemini AI connected
        </span>

        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()

    st.caption(
        "Persistent login enabled for up to 30 days."
    )


# ============================================================
# METRICS
# ============================================================

def get_metrics():

    username = st.session_state.username

    user = get_user(
        username
    )

    conn = connect_db()

    conversations = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM chats
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    tasks = conn.execute(
        """
        SELECT COUNT(*)
        AS c
        FROM study_plans
        WHERE username=? AND done=0
        """,
        (username,)
    ).fetchone()["c"]

    completed = conn.execute(
        """
        SELECT COUNT(*)
        AS c
        FROM study_plans
        WHERE username=? AND done=1
        """,
        (username,)
    ).fetchone()["c"]

    favorites = conn.execute(
        """
        SELECT COUNT(*)
        AS c
        FROM favorites
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    conn.close()

    return [
        (
            user["prompts_count"],
            "AI interactions"
        ),
        (
            conversations,
            "Saved conversations"
        ),
        (
            tasks,
            "Open tasks"
        ),
        (
            favorites,
            "Favorite tools"
        )
    ]


def show_metrics():

    columns = st.columns(4)

    for column, (value, label) in zip(
        columns,
        get_metrics()
    ):

        with column:

            st.markdown(
                f"""
                <div class="metric-card">

                    <div class="metric-number">
                        {value}
                    </div>

                    <div class="metric-label">
                        {label}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# AI RESPONSE DISPLAY
# ============================================================

def display_ai_result(
    answer,
    download_name="rockyai_result.txt"
):

    st.markdown(
        "### 💬 RockyAI"
    )

    st.markdown(
        f"""
        <div class="ai-response">
        {answer.replace(chr(10), "<br>")}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.download_button(
        "⬇️ Download Response",
        data=answer,
        file_name=download_name,
        mime="text/plain"
    )


# ============================================================
# FAVORITES
# ============================================================

def is_favorite(tool):

    conn = connect_db()

    row = conn.execute(
        """
        SELECT 1
        FROM favorites
        WHERE username=? AND tool=?
        """,
        (
            st.session_state.username,
            tool
        )
    ).fetchone()

    conn.close()

    return row is not None


def toggle_favorite(tool):

    conn = connect_db()

    existing = conn.execute(
        """
        SELECT 1
        FROM favorites
        WHERE username=? AND tool=?
        """,
        (
            st.session_state.username,
            tool
        )
    ).fetchone()

    if existing:

        conn.execute(
            """
            DELETE FROM favorites
            WHERE username=? AND tool=?
            """,
            (
                st.session_state.username,
                tool
            )
        )

    else:

        conn.execute(
            """
            INSERT INTO favorites
            (username,tool,created_at)
            VALUES (?,?,?)
            """,
            (
                st.session_state.username,
                tool,
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )

    conn.commit()
    conn.close()


# ============================================================
# TOOL: ASK
# ============================================================

def ask_tool():

    st.markdown(
        "## 🤖 Ask RockyAI"
    )

    mode = st.selectbox(
        "Response mode",
        [
            "Student-friendly",
            "Exam answer",
            "Detailed explanation",
            "Project mentor",
            "Quick answer",
            "Professional"
        ]
    )

    prompt = st.text_area(
        "What would you like to ask?",
        height=190,
        placeholder=(
            "Ask RockyAI anything..."
        )
    )

    if st.button(
        "🚀 Ask RockyAI",
        type="primary"
    ) and prompt.strip():

        with st.spinner(
            "RockyAI is thinking..."
        ):

            answer = ask_rockyai(
                prompt,
                f"Response mode: {mode}"
            )

        display_ai_result(
            answer
        )

        save_chat(
            "Ask RockyAI",
            prompt,
            answer
        )


# ============================================================
# TOOL: AI TUTOR
# ============================================================

def tutor_tool():

    st.markdown(
        "## 🎓 AI Tutor"
    )

    c1, c2 = st.columns(2)

    with c1:

        subject = st.text_input(
            "Subject",
            placeholder="Science, Maths, SST..."
        )

    with c2:

        level = st.selectbox(
            "Learning level",
            [
                "Beginner",
                "Class 6–7",
                "Class 8–9",
                "Class 10",
                "Advanced"
            ]
        )

    topic = st.text_input(
        "Topic",
        placeholder="e.g. Electricity"
    )

    if st.button(
        "👨‍🏫 Start Lesson",
        type="primary"
    ) and subject.strip() and topic.strip():

        prompt = f"""
Teach me:

Subject: {subject}
Topic: {topic}
Level: {level}

Use:

1. What it means
2. Simple explanation
3. Real-world example
4. Important points
5. Common mistakes
6. Three practice questions
"""

        with st.spinner(
            "Preparing lesson..."
        ):

            answer = ask_rockyai(
                prompt
            )

        display_ai_result(
            answer
        )

        save_chat(
            "AI Tutor",
            f"{subject}: {topic}",
            answer
        )


# ============================================================
# QUESTION SOLVER
# ============================================================

def solver_tool():

    st.markdown(
        "## 🧩 Question Solver"
    )

    question = st.text_area(
        "Paste your question",
        height=200
    )

    method = st.selectbox(
        "Solution style",
        [
            "Step-by-step",
            "Short exam answer",
            "Teacher explanation",
            "Check my answer"
        ]
    )

    if st.button(
        "🧩 Solve",
        type="primary"
    ) and question.strip():

        prompt = f"""
Solve this question.

STYLE:
{method}

QUESTION:
{question}

Show calculations where necessary.
Do not invent missing information.
"""

        with st.spinner(
            "Solving..."
        ):

            answer = ask_rockyai(
                prompt
            )

        display_ai_result(
            answer
        )

        save_chat(
            "Question Solver",
            question,
            answer
        )


# ============================================================
# PDF STUDY
# ============================================================

def pdf_study_tool():

    st.markdown(
        "## 📖 PDF Study"
    )

    uploaded = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        key="pdf_v16"
    )

    if uploaded is None:

        st.info(
            "Upload notes, chapters, worksheets or study material."
        )

        return

    with st.spinner(
        "Reading PDF..."
    ):

        text = extract_pdf(
            uploaded
        )

    if not text:

        st.error(
            "No readable text found."
        )

        return

    st.success(
        f"PDF loaded • {len(text):,} characters"
    )

    action = st.selectbox(
        "What should RockyAI do?",
        [
            "Summarize",
            "Explain simply",
            "Create revision notes",
            "Create questions",
            "Find definitions",
            "Find important facts",
            "Create a quiz"
        ]
    )

    if st.button(
        "📖 Analyze PDF",
        type="primary"
    ):

        prompt = f"""
Use ONLY the source below.

TASK:
{action}

SOURCE:
{text[:60000]}
"""

        with st.spinner(
            "Analyzing..."
        ):

            answer = ask_rockyai(
                prompt
            )

        display_ai_result(
            answer
        )

        save_chat(
            "PDF Study",
            action,
            answer
        )


# ============================================================
# PDF GENERATOR
# ============================================================

def pdf_generator_tool():

    st.markdown(
        "## 📄 PDF Generator"
    )

    title = st.text_input(
        "Document title",
        "RockyAI Study Notes"
    )

    content = st.text_area(
        "Content",
        height=300
    )

    if st.button(
        "📄 Generate PDF",
        type="primary"
    ):

        if not content.strip():

            st.warning(
                "Enter content first."
            )

            return

        data = create_pdf(
            title,
            content
        )

        filename = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            title
        ).strip("_") or "rockyai_document"

        st.download_button(
            "⬇️ Download PDF",
            data=data,
            file_name=filename + ".pdf",
            mime="application/pdf",
            use_container_width=True
        )


# ============================================================
# QUIZ
# ============================================================

def quiz_tool():

    st.markdown(
        "## 📝 Quiz Generator"
    )

    topic = st.text_input(
        "Topic",
        placeholder="e.g. Human digestion"
    )

    c1, c2 = st.columns(2)

    with c1:

        difficulty = st.selectbox(
            "Difficulty",
            [
                "Easy",
                "Medium",
                "Hard",
                "Mixed"
            ]
        )

    with c2:

        count = st.slider(
            "Questions",
            5,
            30,
            10
        )

    if st.button(
        "📝 Generate Quiz",
        type="primary"
    ) and topic.strip():

        prompt = f"""
Create {count} multiple-choice questions.

Topic:
{topic}

Difficulty:
{difficulty}

For every question provide:
A
B
C
D
Correct answer
Short explanation

Make questions educational and unambiguous.
"""

        with st.spinner(
            "Creating quiz..."
        ):

            answer = ask_rockyai(
                prompt
            )

        display_ai_result(
            answer,
            "rockyai_quiz.txt"
        )

        save_chat(
            "Quiz Generator",
            topic,
            answer
        )


# ============================================================
# SAMPLE PAPER
# ============================================================

def sample_paper_tool():

    st.markdown(
        "## 📚 Sample Paper"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        grade = st.text_input(
            "Class",
            "7"
        )

    with c2:

        subject = st.text_input(
            "Subject",
            "Science"
        )

    with c3:

        marks = st.number_input(
            "Total marks",
            20,
            100,
            40,
            step=10
        )

    topics = st.text_area(
        "Chapters / Topics",
        height=120
    )

    if st.button(
        "📚 Generate Paper",
        type="primary"
    ) and topics.strip():

        prompt = f"""
Create a school sample paper.

Class: {grade}
Subject: {subject}
Total marks: {marks}
Topics: {topics}

Sections:
A. Objective
B. Very Short Answer
C. Short Answer
D. Long Answer
E. Competency/Application

Include marks.

After the paper provide a separate answer key.
"""

        with st.spinner(
            "Creating paper..."
        ):

            answer = ask_rockyai(
                prompt
            )

        display_ai_result(
            answer,
            "rockyai_sample_paper.txt"
        )

        data = create_pdf(
            f"{subject} Sample Paper",
            answer
        )

        st.download_button(
            "📄 Download Paper PDF",
            data=data,
            file_name="RockyAI_sample_paper.pdf",
            mime="application/pdf"
        )

        save_chat(
            "Sample Paper",
            topics,
            answer
        )


# ============================================================
# CODE GENERATOR
# ============================================================

def code_tool():

    st.markdown(
        "## 💻 Code Generator"

    )

    language = st.selectbox(
        "Language",
        [
            "Python",
            "JavaScript",
            "HTML/CSS/JS",
            "C",
            "C++",
            "Java",
            "Arduino"
        ]
    )

    request = st.text_area(
        "Describe the program",
        height=200
    )

    if st.button(
        "💻 Generate Code",
        type="primary"
    ) and request.strip():

        prompt = f"""
Generate complete runnable {language} code.

REQUEST:
{request}

Rules:
- Return ONLY source code.
- No Markdown code fences.
- Include useful comments.
- Make the code complete.
"""

        with st.spinner(
            "Writing code..."
        ):

            answer = clean_code(
                ask_rockyai(
                    prompt
                )
            )

        lang = {
            "Python": "python",
            "JavaScript": "javascript",
            "HTML/CSS/JS": "html",
            "C": "c",
            "C++": "cpp",
            "Java": "java",
            "Arduino": "cpp"
        }.get(
            language,
            "text"
        )

        st.code(
            answer,
            language=lang,
            line_numbers=True
        )

        st.download_button(
            "⬇️ Download Code",
            data=answer,
            file_name="rockyai_code.txt",
            mime="text/plain"
        )

        save_chat(
            "Code Generator",
            request,
            answer
        )


# ============================================================
# MIND MAP
# ============================================================

def mindmap_tool():

    st.markdown(
        "## 🧠 Mind Map"
    )

    topic = st.text_input(
        "Central topic"
    )

    if st.button(
        "🧠 Build Mind Map",
        type="primary"
    ) and topic.strip():

        prompt = f"""
Create a text mind map for:

{topic}

Use:

CENTRAL TOPIC
├── Branch
│   ├── Subtopic
│   └── Subtopic
└── Branch

Create 6–8 major branches.
"""

        with st.spinner(
            "Building..."
        ):

            answer = ask_rockyai(
                prompt
            )

        st.code(
            answer
        )

        save_chat(
            "Mind Map",
            topic,
            answer
        )


# ============================================================
# FLASHCARDS
# ============================================================

def flashcards_tool():

    st.markdown(
        "## 🃏 Flashcards"
    )

    topic = st.text_input(
        "Topic"
    )

    count = st.slider(
        "Cards",
        5,
        30,
        10
    )

    if st.button(
        "🃏 Create Flashcards",
        type="primary"
    ) and topic.strip():

        prompt = f"""
Create {count} study flashcards about:

{topic}

Format:

CARD 1
Q:
A:

Keep answers concise.
"""

        with st.spinner(
            "Creating..."
        ):

            answer = ask_rockyai(
                prompt
            )

        display_ai_result(
            answer
        )

        save_chat(
            "Flashcards",
            topic,
            answer
        )


# ============================================================
# SMART SUMMARIZER
# ============================================================

def summarizer_tool():

    st.markdown(
        "## ✂️ Smart Summarizer"
    )

    text = st.text_area(
        "Paste text",
        height=300
    )

    style = st.selectbox(
        "Summary type",
        [
            "5 key points",
            "Exam revision notes",
            "Simple explanation",
            "Detailed summary",
            "One-page notes"
        ]
    )

    if st.button(
        "✂️ Summarize",
        type="primary"
    ) and text.strip():

        prompt = f"""
Summarize the source using:

{style}

Preserve important facts,
definitions, names and numbers.

SOURCE:

{text[:60000]}
"""

        with st.spinner(
            "Summarizing..."
        ):

            answer = ask_rockyai(
                prompt
            )

        display_ai_result(
            answer
        )

        save_chat(
            "Smart Summarizer",
            text[:500],
            answer
        )


# ============================================================
# TRANSLATOR
# ============================================================

def translator_tool():

    st.markdown(
        "## 🌐 Translator"
    )

    text = st.text_area(
        "Text",
        height=220
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
            "Japanese"
        ]
    )

    if st.button(
        "🌐 Translate",
        type="primary"
    ) and text.strip():

        answer = ask_rockyai(
            f"""
Translate this text into {language}.

Preserve meaning and formatting.

TEXT:
{text}
"""
        )

        display_ai_result(
            answer
        )

        save_chat(
            "Translator",
            text[:500],
            answer
        )


# ============================================================
# GENERIC AI TOOL
# ============================================================

def generic_ai_tool(
    title,
    icon,
    fields,
    instruction,
    button
):

    st.markdown(
        f"## {icon} {title}"
    )

    values = {}

    for label, placeholder in fields:

        values[label] = st.text_area(
            label,
            placeholder=placeholder,
            height=100
        )

    if st.button(
        f"{icon} {button}",
        type="primary"
    ) and any(
        v.strip()
        for v in values.values()
    ):

        prompt = "\n".join(
            f"{key}: {value}"
            for key, value in values.items()
            if value.strip()
        )

        with st.spinner(
            "RockyAI is working..."
        ):

            answer = ask_rockyai(
                prompt,
                instruction
            )

        display_ai_result(
            answer
        )

        save_chat(
            title,
            prompt,
            answer
        )


# ============================================================
# STUDY PLANNER
# ============================================================

def planner_page():

    st.markdown(
        "## 📅 Study Planner"
    )

    with st.form(
        "v16_plan_form"
    ):

        c1, c2 = st.columns(2)

        with c1:

            subject = st.text_input(
                "Subject"
            )

        with c2:

            target = st.date_input(
                "Target date"
            )

        task = st.text_input(
            "Task"
        )

        add = st.form_submit_button(
            "➕ Add Task"
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
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )

        conn.commit()
        conn.close()

        st.success(
            "Study task added."
        )

        st.rerun()

    conn = connect_db()

    rows = conn.execute(
        """
        SELECT id,subject,task,target_date,done
        FROM study_plans
        WHERE username=?
        ORDER BY target_date
        """,
        (st.session_state.username,)
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "No study tasks yet."
        )

        return

    for row in rows:

        c1, c2, c3 = st.columns(
            [1, 7, 1]
        )

        with c1:

            st.write(
                "✅"
                if row["done"]
                else "📌"
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
                    key=f"done_{row['id']}"
                ):

                    conn = connect_db()

                    conn.execute(
                        """
                        UPDATE study_plans
                        SET done=1
                        WHERE id=?
                        """,
                        (row["id"],)
                    )

                    conn.commit()
                    conn.close()

                    st.rerun()


# ============================================================
# GOALS
# ============================================================

def goals_page():

    st.markdown(
        "## 🎯 Goal Coach"
    )

    with st.form(
        "goal_form_v16"
    ):

        goal = st.text_input(
            "Your goal",
            placeholder="e.g. Score 90% in Science"
        )

        deadline = st.text_input(
            "Deadline",
            placeholder="e.g. 30 days"
        )

        add = st.form_submit_button(
            "🎯 Add Goal"
        )

    if add and goal.strip():

        conn = connect_db()

        conn.execute(
            """
            INSERT INTO goals
            (username,goal,deadline,progress,created_at)
            VALUES (?,?,?,?,?)
            """,
            (
                st.session_state.username,
                goal,
                deadline,
                0,
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )

        conn.commit()
        conn.close()

        st.success(
            "Goal created."
        )

        st.rerun()

    conn = connect_db()

    rows = conn.execute(
        """
        SELECT *
        FROM goals
        WHERE username=?
        ORDER BY id DESC
        """,
        (st.session_state.username,)
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "Create your first goal."
        )

        return

    for row in rows:

        st.markdown(
            f"""
            <div class="rocky-card">

            <b>🎯 {html.escape(row["goal"])}</b>

            <br>

            <span class="small-muted">
            Deadline: {html.escape(row["deadline"])}
            </span>

            </div>
            """,
            unsafe_allow_html=True
        )

        progress = st.slider(
            "Progress",
            0,
            100,
            int(row["progress"]),
            key=f"goal_{row['id']}"
        )

        if progress != row["progress"]:

            conn = connect_db()

            conn.execute(
                """
                UPDATE goals
                SET progress=?
                WHERE id=?
                """,
                (
                    progress,
                    row["id"]
                )
            )

            conn.commit()
            conn.close()


# ============================================================
# HISTORY
# ============================================================

def history_page():

    st.markdown(
        "## 🕘 Conversation History"
    )

    conn = connect_db()

    rows = conn.execute(
        """
        SELECT id,tool,prompt,response,timestamp
        FROM chats
        WHERE username=?
        ORDER BY id DESC
        LIMIT 100
        """,
        (st.session_state.username,)
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "Your AI history will appear here."
        )

        return

    for row in rows:

        with st.expander(
            f"{row['tool']} • {row['timestamp']}"
        ):

            st.markdown(
                "**Prompt**"
            )

            st.write(
                row["prompt"]
            )

            st.markdown(
                "**RockyAI**"
            )

            st.markdown(
                row["response"]
            )


# ============================================================
# FAVORITES
# ============================================================

def favorites_page():

    st.markdown(
        "## ⭐ Favorite Tools"
    )

    conn = connect_db()

    rows = conn.execute(
        """
        SELECT tool
        FROM favorites
        WHERE username=?
        ORDER BY created_at DESC
        """,
        (st.session_state.username,)
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "You have not favorited any tools yet."
        )

        return

    for row in rows:

        st.markdown(
            f"⭐ **{row['tool']}**"
        )


# ============================================================
# ANALYTICS
# ============================================================

def analytics_page():

    st.markdown(
        "## 📊 Your Analytics"
    )

    username = st.session_state.username

    conn = connect_db()

    total = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM chats
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    tasks = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM study_plans
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    completed = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM study_plans
        WHERE username=? AND done=1
        """,
        (username,)
    ).fetchone()["c"]

    goals = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM goals
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    tools = conn.execute(
        """
        SELECT tool,COUNT(*) AS c
        FROM chats
        WHERE username=?
        GROUP BY tool
        ORDER BY c DESC
        """,
        (username,)
    ).fetchall()

    conn.close()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "AI interactions",
        total
    )

    c2.metric(
        "Study tasks",
        tasks
    )

    c3.metric(
        "Completed",
        completed
    )

    c4.metric(
        "Goals",
        goals
    )

    st.markdown(
        "### 🧰 Most Used Tools"
    )

    if tools:

        for row in tools:

            st.write(
                f"**{row['tool']}** — {row['c']} uses"
            )

    else:

        st.info(
            "Use RockyAI tools to generate analytics."
        )


# ============================================================
# ACHIEVEMENTS
# ============================================================

def achievements_page():

    st.markdown(
        "## 🏅 Achievement Center"
    )

    username = st.session_state.username

    conn = connect_db()

    interactions = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM chats
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    tasks = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM study_plans
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    goals = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM goals
        WHERE username=?
        """,
        (username,)
    ).fetchone()["c"]

    conn.close()

    achievements = [

        (
            "🌱",
            "First Step",
            interactions >= 1,
            "Complete your first AI interaction."
        ),

        (
            "🔥",
            "AI Explorer",
            interactions >= 10,
            "Complete 10 AI interactions."
        ),

        (
            "🚀",
            "Power User",
            interactions >= 50,
            "Complete 50 AI interactions."
        ),

        (
            "📅",
            "Planner",
            tasks >= 1,
            "Create your first study task."
        ),

        (
            "🎯",
            "Goal Setter",
            goals >= 1,
            "Create your first goal."
        ),

    ]

    for icon, name, unlocked, desc in achievements:

        status = (
            "UNLOCKED"
            if unlocked
            else "LOCKED"
        )

        st.markdown(
            f"""
            <div class="rocky-card">

                <span style="font-size:2rem;">
                    {icon}
                </span>

                <b>
                    {name}
                </b>

                <span class="badge">
                    {status}
                </span>

                <br>

                <span class="small-muted">
                    {desc}
                </span>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# ADMIN
# ============================================================

def admin_page():

    st.markdown(
        "## 🛡️ Admin Panel"
    )

    if st.session_state.role != "admin":

        st.error(
            "Access denied."
        )

        return

    conn = connect_db()

    users = conn.execute(
        """
        SELECT username,role,prompts_count,created_at
        FROM users
        ORDER BY created_at DESC
        """
    ).fetchall()

    chats = conn.execute(
        "SELECT COUNT(*) AS c FROM chats"
    ).fetchone()["c"]

    conn.close()

    c1, c2 = st.columns(2)

    c1.metric(
        "Registered users",
        len(users)
    )

    c2.metric(
        "Total AI interactions",
        chats
    )

    st.markdown(
        "### 👥 Users"
    )

    for user in users:

        st.markdown(
            f"""
            <div class="rocky-card">

                <b>
                    {html.escape(user["username"])}
                </b>

                &nbsp; • &nbsp;

                {user["role"]}

                <br>

                <span class="small-muted">
                    {user["prompts_count"]}
                    interactions
                    • Joined
                    {user["created_at"]}
                </span>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# NEW TOOLS
# ============================================================

def math_coach_tool():

    generic_ai_tool(
        "Math Coach",
        "🧮",
        [
            (
                "Topic",
                "Fractions, algebra, percentages..."
            ),
            (
                "Question / skill",
                "What do you want to practice?"
            )
        ],
        """
Act as a mathematics teacher.

Explain the concept clearly,
show formulas,
solve examples,
then provide practice questions.
Never skip important calculations.
""",
        "Start Math Coaching"
    )


def science_lab_tool():

    generic_ai_tool(
        "Science Lab",
        "🧑‍🔬",
        [
            (
                "Topic",
                "e.g. Photosynthesis"
            ),
            (
                "Experiment",
                "Optional experiment or concept"
            )
        ],
        """
Act as a science teacher.

Explain the scientific principle,
materials,
procedure,
observations,
result,
safety considerations
and real-world application.

Never suggest dangerous experiments.
""",
        "Explore Science"
    )


def article_analyzer_tool():

    generic_ai_tool(
        "Article Analyzer",
        "📰",
        [
            (
                "Article",
                "Paste article text"
            )
        ],
        """
Analyze the article.

Provide:
- Main idea
- Key points
- Important facts
- Tone
- Possible bias
- Conclusion
- Short summary

Do not invent information.
""",
        "Analyze Article"
    )


def debugger_tool():

    generic_ai_tool(
        "Code Debugger",
        "🧑‍💻",
        [
            (
                "Programming language",
                "Python, C++, JavaScript..."
            ),
            (
                "Code",
                "Paste your code"
            ),
            (
                "Error",
                "Paste the error message if available"
            )
        ],
        """
Act as a professional programming debugger.

Identify:
1. Error
2. Cause
3. Corrected code
4. Explanation
5. Prevention tips

Return complete corrected code.
""",
        "Debug Code"
    )


def study_mode_tool():

    generic_ai_tool(
        "Study Mode",
        "🔐",
        [
            (
                "Subject",
                "What are you studying?"
            ),
            (
                "Topic",
                "What topic?"
            ),
            (
                "Goal",
                "Understand, revise, test, etc."
            )
        ],
        """
Act as a focused study coach.

Create a distraction-free session containing:
- Learning objective
- Short lesson
- Active recall
- Practice
- Mini test
- Final recap

Do not overwhelm the learner.
""",
        "Enter Study Mode"
    )


def quick_explain_tool():

    generic_ai_tool(
        "Quick Explain",
        "⚡",
        [
            (
                "Concept",
                "What should RockyAI explain?"
            )
        ],
        """
Explain the concept in under 2 minutes of reading.

Use:
1. Simple definition
2. Example
3. Why it matters
4. One memory trick
""",
        "Explain"
    )


def assignment_helper_tool():

    generic_ai_tool(
        "Assignment Helper",
        "📋",
        [
            (
                "Assignment",
                "Describe the assignment"
            ),
            (
                "Requirements",
                "Teacher instructions"
            )
        ],
        """
Help organize the assignment.

Provide:
- Understanding of the task
- Research/learning steps
- Structure
- Checklist
- Quality improvements

Do not falsely claim completed work or sources.
""",
        "Build Assignment Plan"
    )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page():

    st.markdown(
        f"""
        <div class="rocky-hero">

            <span class="badge">
                ROCKYAI v1-6
            </span>

            <span class="badge">
                ● ONLINE
            </span>

            <div class="hero-title">
                Welcome back,
                {html.escape(st.session_state.username)} 👋
            </div>

            <div class="hero-subtitle">
                Your AI learning command center is ready.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    show_metrics()

    st.markdown(
        '<div class="section-title">⚡ Quick Actions</div>',
        unsafe_allow_html=True
    )

    quick_tools = [
        "🤖 Ask RockyAI",
        "🎓 AI Tutor",
        "📝 Quiz Generator",
        "💻 Code Generator",
        "📖 PDF Study",
        "🎯 Exam Preparation"
    ]

    cols = st.columns(3)

    for index, tool_name in enumerate(
        quick_tools
    ):

        icon, title, desc = next(
            (
                item
                for item in TOOLS
                if item[1] == tool_name.split(
                    " ",
                    1
                )[1]
            ),
            (
                "🤖",
                tool_name,
                ""
            )
        )

        with cols[index % 3]:

            st.markdown(
                f"""
                <div class="feature-card">

                    <div class="feature-icon">
                        {icon}
                    </div>

                    <div class="feature-title">
                        {title}
                    </div>

                    <div class="feature-description">
                        {desc}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"Open {title}",
                key=f"dash_{index}",
                use_container_width=True
            ):

                st.session_state.quick_tool = tool_name
                st.session_state.current_page = "🧰 AI Tools"
                st.rerun()

    st.markdown(
        '<div class="section-title">✨ What's New in v1-6</div>',
        unsafe_allow_html=True
    )

    new_features = [
        "🎨 Completely redesigned interface",
        "🔎 Better AI tool discovery",
        "⭐ Favorite tools",
        "🎯 Personal goals",
        "🏅 Achievement system",
        "🧮 Math Coach",
        "🧑‍🔬 Science Lab",
        "🧑‍💻 Code Debugger",
        "🔐 Focused Study Mode",
        "⚡ Quick Explain"
    ]

    cols = st.columns(2)

    for i, feature in enumerate(
        new_features
    ):

        with cols[i % 2]:

            st.markdown(
                f"""
                <div class="rocky-card">
                    {feature}
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# AI TOOLS DIRECTORY
# ============================================================

def tools_page():

    st.markdown(
        "## 🧰 AI Tools"
    )

    search = st.text_input(
        "🔎 Search RockyAI tools",
        placeholder="Search quiz, code, PDF, study, career..."
    )

    categories = [
        "All",
        "Study",
        "Create",
        "Productivity",
        "Career",
        "New v1-6"
    ]

    category = st.radio(
        "Category",
        categories,
        horizontal=True
    )

    selected = None

    filtered = TOOLS

    if search.strip():

        filtered = [
            item
            for item in filtered
            if search.lower()
            in (
                item[1] + " " + item[2]
            ).lower()
        ]

    cols = st.columns(3)

    for index, (icon, title, desc) in enumerate(
        filtered
    ):

        with cols[index % 3]:

            st.markdown(
                f"""
                <div class="feature-card">

                    <div class="feature-icon">
                        {icon}
                    </div>

                    <div class="feature-title">
                        {title}
                    </div>

                    <div class="feature-description">
                        {desc}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            c1, c2 = st.columns(
                [3, 1]
            )

            with c1:

                if st.button(
                    "Open",
                    key=f"open_tool_{index}_{title}",
                    use_container_width=True
                ):

                    selected = title

            with c2:

                star = (
                    "⭐"
                    if is_favorite(title)
                    else "☆"
                )

                if st.button(
                    star,
                    key=f"fav_{index}_{title}",
                    use_container_width=True
                ):

                    toggle_favorite(title)

                    st.rerun()

    if selected:

        st.divider()

        open_tool(
            selected
        )


# ============================================================
# TOOL ROUTER
# ============================================================

def open_tool(title):

    functions = {

        "Ask RockyAI":
            ask_tool,

        "AI Tutor":
            tutor_tool,

        "Question Solver":
            solver_tool,

        "PDF Study":
            pdf_study_tool,

        "PDF Generator":
            pdf_generator_tool,

        "Quiz Generator":
            quiz_tool,

        "Sample Paper":
            sample_paper_tool,

        "Code Generator":
            code_tool,

        "Mind Map":
            mindmap_tool,

        "Flashcards":
            flashcards_tool,

        "Study Planner":
            planner_page,

        "Smart Summarizer":
            summarizer_tool,

        "Translator":
            translator_tool,

        "Brainstorm":
            lambda: generic_ai_tool(
                "Brainstorm",
                "💡",
                [
                    (
                        "Idea",
                        "What do you want to brainstorm?"
                    ),
                    (
                        "Goal",
                        "School project, startup, app..."
                    )
                ],
                """
Generate creative ideas,
rank the best options,
explain why they stand out,
and provide an execution plan.
""",
                "Brainstorm"
            ),

        "Exam Preparation":
            lambda: generic_ai_tool(
                "Exam Preparation",
                "🎯",
                [
                    (
                        "Subject",
                        "Subject"
                    ),
                    (
                        "Topics",
                        "Chapters/topics"
                    ),
                    (
                        "Days",
                        "Days available"
                    )
                ],
                """
Create a realistic exam preparation strategy
with daily targets, revision, practice tests,
time management and final revision.
""",
                "Build Strategy"
            ),

        "Periodic Table":
            lambda: periodic_table_page(),

        "Daily Challenge":
            lambda: generic_ai_tool(
                "Daily Challenge",
                "🏆",
                [
                    (
                        "Subject",
                        "e.g. Class 7 Science"
                    ),
                    (
                        "Difficulty",
                        "Easy / Medium / Hard"
                    )
                ],
                """
Create one engaging learning challenge,
then provide the answer separately
with a short explanation.
""",
                "Create Challenge"
            ),

        "Debate Coach":
            lambda: generic_ai_tool(
                "Debate Coach",
                "🗣️",
                [
                    (
                        "Motion",
                        "e.g. AI should be used in schools"
                    ),
                    (
                        "Your side",
                        "For / Against"
                    )
                ],
                """
Act as a debate coach.
Give arguments, counterarguments,
rebuttals and a strong closing statement.
""",
                "Coach Me"
            ),

        "Interview Coach":
            lambda: generic_ai_tool(
                "Interview Coach",
                "🎤",
                [
                    (
                        "Role",
                        "Student council, internship..."
                    ),
                    (
                        "Experience",
                        "Your experience"
                    )
                ],
                """
Prepare the user for an interview.
Provide likely questions,
answer structures,
mistakes and confidence tips.
""",
                "Prepare Me"
            ),

        "Career Roadmap":
            lambda: generic_ai_tool(
                "Career Roadmap",
                "🧭",
                [
                    (
                        "Interest",
                        "AI, robotics, medicine..."
                    ),
                    (
                        "Current level",
                        "Class / experience"
                    )
                ],
                """
Create a realistic learning roadmap
with skills, projects, milestones
and next steps.
Do not guarantee salary or employment.
""",
                "Build Roadmap"
            ),

        "Project Builder":
            lambda: generic_ai_tool(
                "Project Builder",
                "🚀",
                [
                    (
                        "Project idea",
                        "Describe the idea"
                    ),
                    (
                        "Constraints",
                        "Budget, time, hardware..."
                    )
                ],
                """
Turn the idea into a polished project plan
with objective, features, architecture,
milestones, testing and presentation points.
""",
                "Build Project"
            ),

        "Presentation Maker":
            lambda: generic_ai_tool(
                "Presentation Maker",
                "📊",
                [
                    (
                        "Topic",
                        "Presentation topic"
                    ),
                    (
                        "Audience",
                        "Class, judges..."
                    ),
                    (
                        "Duration",
                        "e.g. 5 minutes"
                    )
                ],
                """
Create a professional slide-by-slide presentation
with titles, bullets, speaker notes,
opening and closing.
""",
                "Create Slides"
            ),

        "Memory Trainer":
            lambda: generic_ai_tool(
                "Memory Trainer",
                "🧠",
                [
                    (
                        "Topic",
                        "What do you want to remember?"
                    ),
                    (
                        "Level",
                        "Beginner / Exam"
                    )
                ],
                """
Create an active recall memory workout
using mnemonics, chunking,
retrieval questions and spaced repetition.
""",
                "Train Memory"
            ),

        "Goal Coach":
            lambda: generic_ai_tool(
                "Goal Coach",
                "🎯",
                [
                    (
                        "Goal",
                        "What do you want to achieve?"
                    ),
                    (
                        "Deadline",
                        "Target date"
                    )
                ],
                """
Turn the goal into measurable milestones,
weekly actions, success metrics
and recovery plans.
""",
                "Plan Goal"
            ),

        "Vocabulary Builder":
            lambda: generic_ai_tool(
                "Vocabulary Builder",
                "📘",
                [
                    (
                        "Language / level",
                        "English, Class 7..."
                    ),
                    (
                        "Topic",
                        "Science vocabulary..."
                    )
                ],
                """
Create vocabulary lessons with meanings,
examples, memory clues and a short quiz.
""",
                "Build Vocabulary"
            ),

        "Fact Checker":
            lambda: generic_ai_tool(
                "Fact Checker",
                "🔍",
                [
                    (
                        "Claim",
                        "Paste claim"
                    )
                ],
                """
Analyze the claim carefully.
Separate established information
from uncertainty.
Do not pretend to browse
or cite sources not accessed.
""",
                "Analyze Claim"
            ),

        "Math Coach":
            math_coach_tool,

        "Science Lab":
            science_lab_tool,

        "Article Analyzer":
            article_analyzer_tool,

        "Code Debugger":
            debugger_tool,

        "Study Mode":
            study_mode_tool,

        "Quick Explain":
            quick_explain_tool,

        "Assignment Helper":
            assignment_helper_tool,
    }

    function = functions.get(
        title
    )

    if function:

        function()

    else:

        st.error(
            "Tool not implemented."
        )


# ============================================================
# PERIODIC TABLE
# ============================================================

def periodic_table_page():

    st.markdown(
        "## 🧪 Periodic Table"
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
        ("18", "Ar", "Argon")

    ]

    search = st.text_input(
        "Search element"
    )

    filtered = [

        item
        for item in elements

        if not search.strip()
        or search.lower() in item[0].lower()
        or search.lower() in item[1].lower()
        or search.lower() in item[2].lower()

    ]

    cols = st.columns(3)

    for index, (
        number,
        symbol,
        name
    ) in enumerate(filtered):

        with cols[index % 3]:

            st.markdown(
                f"""
                <div class="rocky-card">

                    <b>
                        {number}. {symbol}
                    </b>

                    <br>

                    <span class="small-muted">
                        {name}
                    </span>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# MAIN ROUTER
# ============================================================

if page == "🏠 Dashboard":

    dashboard_page()

elif page == "🧰 AI Tools":

    if "quick_tool" in st.session_state:

        selected_tool = st.session_state.pop(
            "quick_tool"
        )

        open_tool(
            selected_tool
        )

    else:

        tools_page()

elif page == "⭐ Favorites":

    favorites_page()

elif page == "🕘 History":

    history_page()

elif page == "📅 Planner":

    planner_page()

elif page == "🎯 Goals":

    goals_page()

elif page == "📊 Analytics":

    analytics_page()

elif page == "🏅 Achievements":

    achievements_page()

elif page == "🛡️ Admin Panel":

    admin_page()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="rocky-footer">

        🏔️ <b>RockyAI v1-6</b>

        <br>

        Learn • Practice • Create • Build • Improve

        <br><br>

        Powered by Gemini AI

    </div>
    """,
    unsafe_allow_html=True
)
