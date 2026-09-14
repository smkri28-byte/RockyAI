import os
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

try:
    import extra_streamlit_components as stx
except Exception:
    stx = None


# =========================================================
# ROCKYAI CONFIG
# =========================================================

APP_NAME = "RockyAI v1-6"
APP_VERSION = "1.6"
MODEL = "gemini-2.5-flash"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rockyai_v1_6.db"

COOKIE_NAME = "rockyai_v1_6_session"

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()

# =========================================================
# ADMIN CREDENTIALS
# THESE COME FROM RENDER ENVIRONMENT VARIABLES
# =========================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
).strip()

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "password123"
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# PROFESSIONAL RED UI
# =========================================================

st.markdown(
    """
<style>

@import url(
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap'
);

:root {
    --red: #ef233c;
    --red2: #ff4d6d;
    --red3: #be123c;

    --bg: #070708;
    --surface: #101014;
    --surface2: #17171d;

    --border: rgba(255,255,255,0.09);

    --text: #f7f7f8;
    --muted: #a1a1aa;
}

html,
body,
[class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {

    background:
        radial-gradient(
            circle at 15% 0%,
            rgba(239,35,60,0.14),
            transparent 30%
        ),

        radial-gradient(
            circle at 90% 10%,
            rgba(190,18,60,0.10),
            transparent 28%
        ),

        var(--bg);

    color: var(--text);
}


/* SIDEBAR */

section[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            #0b0b0e,
            #08080a
        );

    border-right:
        1px solid var(--border);
}


/* HERO */

.rocky-hero {

    padding: 34px;

    border:
        1px solid rgba(239,35,60,0.25);

    border-radius: 24px;

    background:
        linear-gradient(
            135deg,
            rgba(239,35,60,0.16),
            rgba(20,20,25,0.96) 50%
        );

    box-shadow:
        0 20px 60px rgba(0,0,0,0.28);

    margin-bottom: 24px;
}


.badge {

    display: inline-block;

    padding: 6px 11px;

    margin-right: 7px;

    border-radius: 999px;

    background:
        rgba(239,35,60,0.14);

    border:
        1px solid rgba(239,35,60,0.30);

    color: #ff8a9a;

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 0.08em;
}


.hero-title {

    font-size:
        clamp(28px, 4vw, 48px);

    line-height: 1.05;

    font-weight: 900;

    margin-top: 18px;
}


.hero-subtitle {

    color: var(--muted);

    margin-top: 10px;

    font-size: 16px;
}


/* SECTION */

.section-title {

    font-size: 23px;

    font-weight: 800;

    margin:
        28px 0 15px;
}


/* CARDS */

.feature-card,
.metric-card {

    background:
        linear-gradient(
            145deg,
            #15151a,
            #0e0e12
        );

    border:
        1px solid var(--border);

    border-radius: 18px;

    padding: 20px;

    margin-bottom: 12px;

    transition:
        transform 0.18s ease,
        border-color 0.18s ease;
}


.feature-card:hover {

    transform:
        translateY(-2px);

    border-color:
        rgba(239,35,60,0.32);
}


.feature-icon {

    font-size: 29px;
}


.feature-title {

    font-size: 17px;

    font-weight: 800;

    margin-top: 8px;
}


.feature-description {

    color: var(--muted);

    font-size: 13px;

    margin-top: 6px;

    line-height: 1.5;
}


/* METRICS */

.metric-number {

    font-size: 30px;

    font-weight: 900;
}


.metric-label {

    color: var(--muted);

    font-size: 12px;
}


/* AI RESPONSE */

.ai-response {

    background:
        #101014;

    border:
        1px solid var(--border);

    border-left:
        4px solid var(--red);

    border-radius: 14px;

    padding: 20px;

    margin-top: 14px;

    line-height: 1.65;
}


/* FOOTER */

.rocky-footer {

    text-align: center;

    color: #71717a;

    padding:
        35px 0 15px;

    font-size: 12px;
}


/* BUTTONS */

div.stButton > button {

    border-radius: 12px;

    font-weight: 700;

    transition:
        all 0.18s ease;
}


div.stButton > button:hover {

    border-color:
        var(--red);

    transform:
        translateY(-1px);
}


/* INPUTS */

.stTextInput input,
.stTextArea textarea {

    border-radius:
        12px !important;
}


.small-muted {

    color: var(--muted);

    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# DATABASE
# =========================================================

def get_conn():

    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_conn()

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

    # -----------------------------------------------------
    # ADMIN ACCOUNT FROM RENDER ENVIRONMENT VARIABLES
    # -----------------------------------------------------

    if ADMIN_USERNAME and ADMIN_PASSWORD:

        existing = conn.execute(
            """
            SELECT username
            FROM users
            WHERE username=?
            """,
            (ADMIN_USERNAME,)
        ).fetchone()

        password_hash = generate_password_hash(
            ADMIN_PASSWORD
        )

        if existing:

            conn.execute(
                """
                UPDATE users

                SET
                    password_hash=?,
                    role='admin'

                WHERE username=?
                """,
                (
                    password_hash,
                    ADMIN_USERNAME
                )
            )

        else:

            conn.execute(
                """
                INSERT INTO users
                (
                    username,
                    password_hash,
                    role,
                    prompts_count,
                    created_at
                )

                VALUES (?,?,?,?,?)
                """,
                (
                    ADMIN_USERNAME,
                    password_hash,
                    "admin",
                    0,
                    datetime.now().isoformat(
                        timespec="seconds"
                    )
                )
            )

    conn.commit()
    conn.close()


init_db()


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "navigation" not in st.session_state:
    st.session_state.navigation = "🏠 Dashboard"

if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = None

if "current_tool" not in st.session_state:
    st.session_state.current_tool = "RockyAI"


# =========================================================
# COOKIE MANAGER
# =========================================================

cookie_manager = None

if stx:

    try:
        cookie_manager = stx.CookieManager()

    except Exception:
        cookie_manager = None


def set_cookie(token):

    if cookie_manager:

        try:

            cookie_manager.set(
                COOKIE_NAME,
                token
            )

        except Exception:
            pass


def get_cookie():

    if cookie_manager:

        try:

            return cookie_manager.get(
                COOKIE_NAME
            )

        except Exception:
            return None

    return None


def delete_cookie():

    if cookie_manager:

        try:

            cookie_manager.delete(
                COOKIE_NAME
            )

        except Exception:
            pass


# =========================================================
# SESSION HELPERS
# =========================================================

def hash_token(token):

    return hashlib.sha256(
        token.encode()
    ).hexdigest()


def create_session(username):

    token = secrets.token_urlsafe(48)

    token_hash = hash_token(token)

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    conn = get_conn()

    conn.execute(
        """
        INSERT OR REPLACE INTO sessions
        (
            token_hash,
            username,
            created_at,
            last_seen
        )

        VALUES (?,?,?,?)
        """,
        (
            token_hash,
            username,
            now,
            now
        )
    )

    conn.commit()
    conn.close()

    set_cookie(token)

    st.session_state.logged_in = True
    st.session_state.username = username


def restore_session():

    token = get_cookie()

    if not token:
        return False

    token_hash = hash_token(token)

    conn = get_conn()

    row = conn.execute(
        """
        SELECT username
        FROM sessions
        WHERE token_hash=?
        """,
        (token_hash,)
    ).fetchone()

    if not row:

        conn.close()

        return False

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
            token_hash
        )
    )

    conn.commit()
    conn.close()

    st.session_state.logged_in = True

    st.session_state.username = row[
        "username"
    ]

    return True


def logout():

    token = get_cookie()

    if token:

        conn = get_conn()

        conn.execute(
            """
            DELETE FROM sessions
            WHERE token_hash=?
            """,
            (hash_token(token),)
        )

        conn.commit()
        conn.close()

    delete_cookie()

    st.session_state.logged_in = False
    st.session_state.username = ""

    st.rerun()


# =========================================================
# AUTH
# =========================================================

def login_user(
    username,
    password
):

    username = username.strip()

    conn = get_conn()

    row = conn.execute(
        """
        SELECT
            username,
            password_hash
        FROM users
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    conn.close()

    if not row:
        return False

    try:

        valid = check_password_hash(
            row["password_hash"],
            password
        )

    except Exception:
        valid = False

    if valid:

        create_session(username)

        return True

    return False


def register_user(
    username,
    password
):

    username = username.strip()

    if len(username) < 3:
        return False, "Username must have at least 3 characters."

    if len(username) > 30:
        return False, "Username is too long."

    if not username.replace(
        "_", ""
    ).replace(
        "-", ""
    ).isalnum():

        return False, (
            "Username can contain letters, "
            "numbers, _ and - only."
        )

    if len(password) < 6:
        return False, (
            "Password must have at least 6 characters."
        )

    conn = get_conn()

    exists = conn.execute(
        """
        SELECT username
        FROM users
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    if exists:

        conn.close()

        return False, "Username already exists."

    conn.execute(
        """
        INSERT INTO users
        (
            username,
            password_hash,
            role,
            prompts_count,
            created_at
        )

        VALUES (?,?,?,?,?)
        """,
        (
            username,
            generate_password_hash(
                password
            ),
            "user",
            0,
            datetime.now().isoformat(
                timespec="seconds"
            )
        )
    )

    conn.commit()
    conn.close()

    return True, "Account created successfully."


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    st.markdown(
        """
        <div class="rocky-hero">

            <span class="badge">
                ROCKYAI v1-6
            </span>

            <span class="badge">
                ● ONLINE
            </span>

            <div class="hero-title">
                🏔️ Welcome to RockyAI
            </div>

            <div class="hero-subtitle">
                Your AI learning, coding and
                productivity command center.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    left, center, right = st.columns(
        [1, 1.4, 1]
    )

    with center:

        login_tab, register_tab = st.tabs(
            [
                "🔐 Login",
                "✨ Create Account"
            ]
        )

        with login_tab:

            username = st.text_input(
                "Username",
                key="login_username"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            if st.button(
                "🚀 Login",
                type="primary",
                use_container_width=True
            ):

                if login_user(
                    username,
                    password
                ):

                    st.success(
                        "Login successful!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Invalid username or password."
                    )

        with register_tab:

            new_username = st.text_input(
                "Choose username",
                key="new_username"
            )

            new_password = st.text_input(
                "Choose password",
                type="password",
                key="new_password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="confirm_password"
            )

            if st.button(
                "✨ Create Account",
                use_container_width=True
            ):

                if new_password != confirm_password:

                    st.error(
                        "Passwords do not match."
                    )

                else:

                    ok, message = register_user(
                        new_username,
                        new_password
                    )

                    if ok:

                        st.success(message)

                    else:

                        st.error(message)


# =========================================================
# GEMINI
# =========================================================

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


def save_chat(
    tool,
    prompt,
    response
):

    conn = get_conn()

    conn.execute(
        """
        INSERT INTO chats
        (
            username,
            tool,
            prompt,
            response,
            timestamp
        )

        VALUES (?,?,?,?,?)
        """,
        (
            st.session_state.username,
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

        SET prompts_count =
            prompts_count + 1

        WHERE username=?
        """,
        (
            st.session_state.username,
        )
    )

    conn.commit()
    conn.close()


def ask_rockyai(
    prompt,
    instruction=None
):

    if not gemini:

        return (
            "⚠️ Gemini API is not configured.\n\n"
            "Please add `GEMINI_API_KEY` to your "
            "Render Environment Variables."
        )

    system_instruction = instruction or """
You are RockyAI, a professional AI assistant.

Be accurate, helpful and clear.

For educational questions:
- explain step by step
- use examples
- match the user's level

For programming:
- provide clean code
- explain important parts
- mention setup instructions

Use headings and bullet points where useful.

Never claim to have performed an action
that you cannot actually perform.
"""

    full_prompt = f"""
{system_instruction}

USER REQUEST:

{prompt}
"""

    try:

        result = gemini.models.generate_content(
            model=MODEL,
            contents=full_prompt
        )

        response = getattr(
            result,
            "text",
            None
        )

        if not response:

            return (
                "RockyAI could not generate "
                "a response."
            )

        save_chat(
            st.session_state.current_tool,
            prompt,
            response
        )

        return response

    except Exception as error:

        return (
            "⚠️ RockyAI encountered an error:\n\n"
            f"{error}"
        )


# =========================================================
# TOOL LIST
# =========================================================

TOOLS = [

    (
        "🤖",
        "Ask RockyAI",
        "Your general-purpose AI assistant."
    ),

    (
        "🎓",
        "AI Tutor",
        "Learn any topic step by step."
    ),

    (
        "🧩",
        "Question Solver",
        "Solve and understand difficult questions."
    ),

    (
        "📖",
        "PDF Study",
        "Turn PDFs into study material."
    ),

    (
        "📄",
        "PDF Generator",
        "Create downloadable PDFs."
    ),

    (
        "📝",
        "Quiz Generator",
        "Create custom practice quizzes."
    ),

    (
        "📚",
        "Sample Paper",
        "Generate complete exam papers."
    ),

    (
        "💻",
        "Code Generator",
        "Create programs and projects."
    ),

    (
        "🧠",
        "Mind Map",
        "Convert topics into structured maps."
    ),

    (
        "🃏",
        "Flashcards",
        "Create revision flashcards."
    ),

    (
        "📅",
        "Study Planner",
        "Manage your study tasks."
    ),

    (
        "✂️",
        "Smart Summarizer",
        "Turn long text into concise notes."
    ),

    (
        "🌐",
        "Translator",
        "Translate between languages."
    ),

    (
        "💡",
        "Brainstorm",
        "Generate creative ideas."
    ),

    (
        "🎯",
        "Exam Preparation",
        "Build an exam strategy."
    ),

    (
        "🧪",
        "Periodic Table",
        "Explore common chemical elements."
    ),

    (
        "🏆",
        "Daily Challenge",
        "Get a daily learning challenge."
    ),

    (
        "🗣️",
        "Debate Coach",
        "Prepare arguments and rebuttals."
    ),

    (
        "🎤",
        "Interview Coach",
        "Practice interviews."
    ),

    (
        "🧭",
        "Career Roadmap",
        "Explore learning paths."
    ),

    (
        "🚀",
        "Project Builder",
        "Turn ideas into projects."
    ),

    (
        "📊",
        "Presentation Maker",
        "Build presentation structures."
    ),

    (
        "🧠",
        "Memory Trainer",
        "Train active recall."
    ),

    (
        "📘",
        "Vocabulary Builder",
        "Build stronger vocabulary."
    ),

    (
        "🔍",
        "Fact Checker",
        "Analyze claims carefully."
    ),

    (
        "🧮",
        "Math Coach",
        "Practice mathematics."
    ),

    (
        "🧑‍🔬",
        "Science Lab",
        "Explore science concepts."
    ),

    (
        "📰",
        "Article Analyzer",
        "Analyze articles."
    ),

    (
        "🧑‍💻",
        "Code Debugger",
        "Find programming errors."
    ),

    (
        "🔐",
        "Study Mode",
        "Focused AI study."
    ),

    (
        "⚡",
        "Quick Explain",
        "Explain concepts quickly."
    ),

    (
        "📋",
        "Assignment Helper",
        "Plan assignments."
    ),
]


# =========================================================
# METRICS
# =========================================================

def get_metrics():

    conn = get_conn()

    username = st.session_state.username

    user = conn.execute(
        """
        SELECT prompts_count
        FROM users
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    chats = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM chats
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    plans = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM study_plans
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    conn.close()

    return {

        "prompts":
            user["prompts_count"]
            if user else 0,

        "chats":
            chats["total"]
            if chats else 0,

        "plans":
            plans["total"]
            if plans else 0
    }


def show_metrics():

    metrics = get_metrics()

    cols = st.columns(3)

    data = [

        (
            "🤖",
            metrics["prompts"],
            "AI Prompts"
        ),

        (
            "💬",
            metrics["chats"],
            "Saved Chats"
        ),

        (
            "📅",
            metrics["plans"],
            "Study Tasks"
        )
    ]

    for col, item in zip(
        cols,
        data
    ):

        icon, value, label = item

        with col:

            st.markdown(
                f"""
                <div class="metric-card">

                    <div>
                        {icon}
                    </div>

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


# =========================================================
# DASHBOARD
# =========================================================

def dashboard_page():

    username = html.escape(
        st.session_state.username
    )

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
                {username} 👋
            </div>

            <div class="hero-subtitle">
                Your AI learning command center
                is ready.
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

        title = tool_name.split(
            " ",
            1
        )[1]

        match = next(
            (
                item
                for item in TOOLS
                if item[1] == title
            ),
            None
        )

        if match:

            icon, title, description = match

        else:

            icon = "🤖"
            description = ""

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
                        {description}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"Open {title}",
                key=f"dashboard_{index}",
                use_container_width=True
            ):

                st.session_state.selected_tool = title

                st.session_state.navigation = (
                    "🧰 AI Tools"
                )

                st.rerun()


# =========================================================
# GENERIC AI TOOL
# =========================================================

def generic_ai_tool(
    title,
    instruction
):

    st.markdown(
        f"""
        <div class="section-title">
            {title}
        </div>
        """,
        unsafe_allow_html=True
    )

    prompt = st.text_area(
        "Enter your request",
        height=190,
        key=f"input_{title}"
    )

    if st.button(
        f"🚀 Run {title}",
        type="primary",
        use_container_width=True,
        key=f"run_{title}"
    ):

        if not prompt.strip():

            st.warning(
                "Please enter something first."
            )

            return

        st.session_state.current_tool = title

        with st.spinner(
            "RockyAI is thinking..."
        ):

            answer = ask_rockyai(
                prompt,
                instruction
            )

        st.markdown(
            '<div class="ai-response">',
            unsafe_allow_html=True
        )

        st.markdown(answer)

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# =========================================================
# BASIC AI TOOLS
# =========================================================

def ask_tool():

    generic_ai_tool(
        "🤖 Ask RockyAI",

        """
You are RockyAI.

Answer the user's request accurately,
clearly and helpfully.

Use examples where useful.
"""
    )


def tutor_tool():

    generic_ai_tool(
        "🎓 AI Tutor",

        """
Act as a patient expert teacher.

Explain the topic step by step.

Adapt the explanation to the student's
level.

Include a short practice question
when appropriate.
"""
    )


def solver_tool():

    generic_ai_tool(
        "🧩 Question Solver",

        """
Solve the question carefully.

For mathematics:
show calculations.

For science:
explain the concept.

For school questions:
give a clear educational explanation.
"""
    )


def quiz_tool():

    generic_ai_tool(
        "📝 Quiz Generator",

        """
Create a high-quality quiz.

Respect the requested:

- class
- subject
- topic
- marks
- difficulty
- number of questions

Give answers separately when requested.
"""
    )


def sample_paper_tool():

    generic_ai_tool(
        "📚 Sample Paper",

        """
Create a professional sample examination paper.

Include:

- instructions
- sections
- marks
- balanced difficulty
- appropriate question types

Do not invent a syllabus if the user
has not provided one.
"""
    )


def code_tool():

    generic_ai_tool(
        "💻 Code Generator",

        """
Generate clean, copy-paste-ready code.

Clearly state the programming language.

Explain:

1. What the code does
2. How to install requirements
3. How to run it
"""
    )


def mindmap_tool():

    generic_ai_tool(
        "🧠 Mind Map",

        """
Convert the topic into a structured
text mind map.

Use:

Main Topic
├── Branch
│   ├── Sub-branch
│   └── Sub-branch
└── Branch
"""
    )


def flashcards_tool():

    generic_ai_tool(
        "🃏 Flashcards",

        """
Create revision flashcards.

Format:

Card 1
Question:
Answer:

Keep the answers concise and accurate.
"""
    )


def summarizer_tool():

    generic_ai_tool(
        "✂️ Smart Summarizer",

        """
Summarize the supplied material.

Keep:

- important facts
- definitions
- key ideas
- examples

Use headings and bullets.
"""
    )


def translator_tool():

    generic_ai_tool(
        "🌐 Translator",

        """
Translate accurately.

Preserve:

- meaning
- tone
- formatting

Do not add unnecessary commentary.
"""
    )


def math_coach_tool():

    generic_ai_tool(
        "🧮 Math Coach",

        """
Act as a mathematics teacher.

Show the method step by step.

Verify the final answer.
"""
    )


def science_lab_tool():

    generic_ai_tool(
        "🧑‍🔬 Science Lab",

        """
Explain science concepts clearly.

For experiments include:

- materials
- procedure
- observations
- result
- safety notes
"""
    )


def article_analyzer_tool():

    generic_ai_tool(
        "📰 Article Analyzer",

        """
Analyze the supplied article.

Identify:

- main idea
- key points
- evidence
- tone
- conclusion
- concise summary
"""
    )


def debugger_tool():

    generic_ai_tool(
        "🧑‍💻 Code Debugger",

        """
Analyze the supplied code.

Identify:

- syntax errors
- logical errors
- runtime problems

Explain why they occur and provide
corrected code.
"""
    )


def study_mode_tool():

    generic_ai_tool(
        "🔐 Study Mode",

        """
Act as a focused study coach.

Keep the session:

- structured
- concise
- educational
- distraction-free
"""
    )


def quick_explain_tool():

    generic_ai_tool(
        "⚡ Quick Explain",

        """
Explain the concept quickly.

Use:

- simple language
- one example
- one key takeaway
"""
    )


def assignment_helper_tool():

    generic_ai_tool(
        "📋 Assignment Helper",

        """
Help organize and improve an assignment.

Provide:

- structure
- key points
- checklist
- improvement suggestions
"""
    )


# =========================================================
# PDF EXTRACTION
# =========================================================

def extract_pdf(
    uploaded_file
):

    try:

        reader = PdfReader(
            uploaded_file
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(
            pages
        )

    except Exception as error:

        return (
            f"PDF extraction error: {error}"
        )


# =========================================================
# PDF GENERATION
# =========================================================

def create_pdf(
    title,
    body
):

    buffer = io.BytesIO()

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RockyTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=15
    )

    normal_style = ParagraphStyle(
        "RockyNormal",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=8
    )

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    story = []

    story.append(
        Paragraph(
            html.escape(title),
            title_style
        )
    )

    for line in body.split("\n"):

        line = line.strip()

        if not line:
            continue

        safe_line = html.escape(
            line
        )

        story.append(
            Paragraph(
                safe_line,
                normal_style
            )
        )

        story.append(
            Spacer(
                1,
                2 * mm
            )
        )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer


# =========================================================
# PDF STUDY
# =========================================================

def pdf_study_tool():

    st.markdown(
        '<div class="section-title">📖 PDF Study</div>',
        unsafe_allow_html=True
    )

    uploaded = st.file_uploader(
        "Upload your PDF",
        type=["pdf"],
        key="pdf_study_upload"
    )

    if not uploaded:
        return

    text = extract_pdf(
        uploaded
    )

    if text.startswith(
        "PDF extraction error"
    ):

        st.error(text)

        return

    st.success(
        "PDF loaded successfully."
    )

    action = st.selectbox(
        "What should RockyAI do?",
        [
            "Summarize",
            "Create Notes",
            "Create Questions",
            "Explain Simply"
        ]
    )

    if st.button(
        "🚀 Process PDF",
        type="primary",
        use_container_width=True
    ):

        st.session_state.current_tool = (
            "PDF Study"
        )

        prompt = f"""
Here is the extracted PDF content:

{text[:50000]}

Task:
{action}

Create useful educational output.
"""

        with st.spinner(
            "Reading your PDF..."
        ):

            answer = ask_rockyai(
                prompt
            )

        st.markdown(
            '<div class="ai-response">',
            unsafe_allow_html=True
        )

        st.markdown(answer)

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# =========================================================
# PDF GENERATOR
# =========================================================

def pdf_generator_tool():

    st.markdown(
        '<div class="section-title">📄 PDF Generator</div>',
        unsafe_allow_html=True
    )

    title = st.text_input(
        "PDF title"
    )

    body = st.text_area(
        "PDF content",
        height=300
    )

    if st.button(
        "📄 Generate PDF",
        type="primary",
        use_container_width=True
    ):

        if not title.strip():

            st.warning(
                "Please enter a PDF title."
            )

            return

        if not body.strip():

            st.warning(
                "Please enter PDF content."
            )

            return

        pdf = create_pdf(
            title,
            body
        )

        st.success(
            "PDF created successfully!"
        )

        st.download_button(
            "⬇️ Download PDF",
            data=pdf,
            file_name="rockyai_document.pdf",
            mime="application/pdf",
            use_container_width=True
        )


# =========================================================
# STUDY PLANNER
# =========================================================

def planner_page():

    st.markdown(
        '<div class="section-title">📅 Study Planner</div>',
        unsafe_allow_html=True
    )

    with st.form(
        "study_planner_form"
    ):

        subject = st.text_input(
            "Subject"
        )

        task = st.text_input(
            "Task"
        )

        target_date = st.date_input(
            "Target date"
        )

        submitted = st.form_submit_button(
            "➕ Add Study Task",
            use_container_width=True
        )

        if submitted:

            if not subject.strip():

                st.error(
                    "Enter a subject."
                )

            elif not task.strip():

                st.error(
                    "Enter a task."
                )

            else:

                conn = get_conn()

                conn.execute(
                    """
                    INSERT INTO study_plans
                    (
                        username,
                        subject,
                        task,
                        target_date,
                        done,
                        created_at
                    )

                    VALUES (?,?,?,?,?,?)
                    """,
                    (
                        st.session_state.username,
                        subject,
                        task,
                        str(target_date),
                        0,
                        datetime.now().isoformat(
                            timespec="seconds"
                        )
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "Study task added!"
                )

                st.rerun()

    st.markdown(
        '<div class="section-title">📋 Your Tasks</div>',
        unsafe_allow_html=True
    )

    conn = get_conn()

    rows = conn.execute(
        """
        SELECT *
        FROM study_plans

        WHERE username=?

        ORDER BY target_date ASC
        """,
        (
            st.session_state.username,
        )
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "You have no study tasks yet."
        )

        return

    for row in rows:

        st.markdown(
            f"""
            <div class="feature-card">

                <div class="feature-title">
                    📚 {html.escape(row["subject"])}
                </div>

                <div class="feature-description">
                    {html.escape(row["task"])}
                    <br><br>
                    📅 Target:
                    {html.escape(row["target_date"])}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# HISTORY
# =========================================================

def history_page():

    st.markdown(
        '<div class="section-title">🕘 History</div>',
        unsafe_allow_html=True
    )

    conn = get_conn()

    rows = conn.execute(
        """
        SELECT
            tool,
            prompt,
            response,
            timestamp

        FROM chats

        WHERE username=?

        ORDER BY id DESC

        LIMIT 50
        """,
        (
            st.session_state.username,
        )
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "No AI history yet."
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
                "**Response**"
            )

            st.markdown(
                row["response"]
            )


# =========================================================
# ANALYTICS
# =========================================================

def analytics_page():

    st.markdown(
        '<div class="section-title">📊 Analytics</div>',
        unsafe_allow_html=True
    )

    show_metrics()

    conn = get_conn()

    rows = conn.execute(
        """
        SELECT
            tool,
            COUNT(*) AS total

        FROM chats

        WHERE username=?

        GROUP BY tool

        ORDER BY total DESC
        """,
        (
            st.session_state.username,
        )
    ).fetchall()

    conn.close()

    if rows:

        st.markdown(
            '<div class="section-title">🧰 Tool Usage</div>',
            unsafe_allow_html=True
        )

        for row in rows:

            st.write(
                f"**{row['tool']}** — "
                f"{row['total']} uses"
            )

    else:

        st.info(
            "Use RockyAI tools to start "
            "building your analytics."
        )


# =========================================================
# PERIODIC TABLE
# =========================================================

def periodic_table_page():

    st.markdown(
        '<div class="section-title">🧪 Periodic Table</div>',
        unsafe_allow_html=True
    )

    elements = [

        ("H", "Hydrogen", 1),
        ("He", "Helium", 2),
        ("Li", "Lithium", 3),
        ("Be", "Beryllium", 4),
        ("B", "Boron", 5),
        ("C", "Carbon", 6),
        ("N", "Nitrogen", 7),
        ("O", "Oxygen", 8),
        ("F", "Fluorine", 9),
        ("Ne", "Neon", 10),
        ("Na", "Sodium", 11),
        ("Mg", "Magnesium", 12),
        ("Al", "Aluminium", 13),
        ("Si", "Silicon", 14),
        ("P", "Phosphorus", 15),
        ("S", "Sulfur", 16),
        ("Cl", "Chlorine", 17),
        ("Ar", "Argon", 18),
        ("K", "Potassium", 19),
        ("Ca", "Calcium", 20)

    ]

    cols = st.columns(5)

    for index, item in enumerate(
        elements
    ):

        symbol, name, number = item

        with cols[index % 5]:

            st.markdown(
                f"""
                <div class="feature-card">

                    <div class="feature-icon">
                        {symbol}
                    </div>

                    <div class="feature-title">
                        {name}
                    </div>

                    <div class="feature-description">
                        Atomic number {number}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# ADMIN PANEL
# =========================================================

def get_user_role():

    conn = get_conn()

    row = conn.execute(
        """
        SELECT role
        FROM users
        WHERE username=?
        """,
        (
            st.session_state.username,
        )
    ).fetchone()

    conn.close()

    if row:
        return row["role"]

    return "user"


def admin_panel():

    if get_user_role() != "admin":

        st.error(
            "🛑 Admin access required."
        )

        return

    st.markdown(
        '<div class="section-title">🛡️ Admin Panel</div>',
        unsafe_allow_html=True
    )

    st.success(
        f"Logged in as administrator: "
        f"{st.session_state.username}"
    )

    conn = get_conn()

    users = conn.execute(
        """
        SELECT
            username,
            role,
            prompts_count,
            created_at

        FROM users

        ORDER BY created_at ASC
        """
    ).fetchall()

    total_chats = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM chats
        """
    ).fetchone()["total"]

    conn.close()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Registered Users",
            len(users)
        )

    with col2:

        st.metric(
            "Total AI Interactions",
            total_chats
        )

    st.markdown(
        '<div class="section-title">👥 Users</div>',
        unsafe_allow_html=True
    )

    for user in users:

        st.markdown(
            f"""
            <div class="feature-card">

                <div class="feature-title">
                    👤 {html.escape(user["username"])}
                </div>

                <div class="feature-description">

                    Role:
                    <b>{html.escape(user["role"])}</b>

                    <br>

                    AI Prompts:
                    {user["prompts_count"]}

                    <br>

                    Created:
                    {html.escape(user["created_at"])}

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# OTHER AI TOOLS
# =========================================================

def other_tool(
    title,
    instruction
):

    generic_ai_tool(
        title,
        instruction
    )


# =========================================================
# TOOL ROUTER
# =========================================================

def open_tool(title):

    routes = {

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
            lambda:
            other_tool(
                "💡 Brainstorm",
                """
Generate creative and practical ideas
for the user's request.
"""
            ),

        "Exam Preparation":
            lambda:
            other_tool(
                "🎯 Exam Preparation",
                """
Create a realistic exam preparation plan
with topics, revision, practice and
time management.
"""
            ),

        "Periodic Table":
            periodic_table_page,

        "Daily Challenge":
            lambda:
            other_tool(
                "🏆 Daily Challenge",
                """
Create an interesting educational
daily challenge.
"""
            ),

        "Debate Coach":
            lambda:
            other_tool(
                "🗣️ Debate Coach",
                """
Prepare strong arguments,
counterarguments and rebuttals.
"""
            ),

        "Interview Coach":
            lambda:
            other_tool(
                "🎤 Interview Coach",
                """
Conduct realistic interview practice.
Ask questions and provide feedback.
"""
            ),

        "Career Roadmap":
            lambda:
            other_tool(
                "🧭 Career Roadmap",
                """
Create a step-by-step learning and
career roadmap.
"""
            ),

        "Project Builder":
            lambda:
            other_tool(
                "🚀 Project Builder",
                """
Turn the user's idea into a practical
project plan including features,
technology and steps.
"""
            ),

        "Presentation Maker":
            lambda:
            other_tool(
                "📊 Presentation Maker",
                """
Create a professional presentation
outline with slides and speaker notes.
"""
            ),

        "Memory Trainer":
            lambda:
            other_tool(
                "🧠 Memory Trainer",
                """
Create active recall and memory
training exercises.
"""
            ),

        "Vocabulary Builder":
            lambda:
            other_tool(
                "📘 Vocabulary Builder",
                """
Teach useful vocabulary with definitions,
examples and practice.
"""
            ),

        "Fact Checker":
            lambda:
            other_tool(
                "🔍 Fact Checker",
                """
Analyze a claim carefully.
Distinguish established facts,
uncertainty and unsupported claims.
"""
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
            assignment_helper_tool
    }

    function = routes.get(title)

    if function:

        function()

    else:

        st.error(
            f"Tool '{title}' is not available."
        )


# =========================================================
# AI TOOLS DIRECTORY
# =========================================================

def tools_page():

    st.markdown(
        '<div class="section-title">🧰 AI Tools</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Choose a tool below."
    )

    cols = st.columns(3)

    for index, item in enumerate(
        TOOLS
    ):

        icon, title, description = item

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
                        {description}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"Open {title}",
                key=f"tool_button_{index}",
                use_container_width=True
            ):

                st.session_state.selected_tool = title

                st.rerun()


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    role = get_user_role()

    st.sidebar.markdown(
        """
        <div style="
            text-align:center;
            padding:10px 0 18px;
        ">

            <div style="
                font-size:45px;
            ">
                🏔️
            </div>

            <div style="
                font-size:25px;
                font-weight:900;
            ">
                RockyAI
            </div>

            <div class="small-muted">
                v1-6 • AI Command Center
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    navigation = [

        "🏠 Dashboard",

        "🧰 AI Tools",

        "🕘 History",

        "📅 Planner",

        "📊 Analytics"
    ]

    if role == "admin":

        navigation.append(
            "🛡️ Admin Panel"
        )

    page = st.radio(
        "Navigation",
        navigation,
        key="navigation",
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        f"""
        👤 **{html.escape(
            st.session_state.username
        )}**
        """
    )

    st.sidebar.caption(
        f"Role: {role}"
    )

    st.sidebar.markdown(
        '<span class="status-online">● Online</span>',
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()

    return page


# =========================================================
# MAIN APPLICATION
# =========================================================

if not st.session_state.logged_in:

    restore_session()


if not st.session_state.logged_in:

    login_page()

    st.stop()


# =========================================================
# NAVIGATION
# =========================================================

page = sidebar()


# =========================================================
# PAGE ROUTING
# =========================================================

if page == "🏠 Dashboard":

    dashboard_page()


elif page == "🧰 AI Tools":

    if st.session_state.selected_tool:

        selected = (
            st.session_state.selected_tool
        )

        st.session_state.selected_tool = None

        open_tool(selected)

        if st.button(
            "← Back to AI Tools",
            key="back_tools"
        ):

            st.rerun()

    else:

        tools_page()


elif page == "🕘 History":

    history_page()


elif page == "📅 Planner":

    planner_page()


elif page == "📊 Analytics":

    analytics_page()


elif page == "🛡️ Admin Panel":

    admin_panel()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="rocky-footer">

        🏔️ RockyAI v1-6

        <br>

        AI learning • Coding • Productivity

    </div>
    """,
    unsafe_allow_html=True
)
