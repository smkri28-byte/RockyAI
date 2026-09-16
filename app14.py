import os
import re
import io
import html
import hashlib
import secrets
import sqlite3
import mimetypes
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
# ROCKYAI v1-8 — PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RockyAIv1-8",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "RockyAIv1-8"
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
# ROCKYAI v1-7 — PREMIUM MOUNTAIN UI
# ============================================================

st.markdown(
    """
<style>
:root {
    --red: #ef233c;
    --red2: #ff5c70;
    --red3: #b7092b;
    --bg: #070709;
    --panel: #101014;
    --panel2: #17171d;
    --line: rgba(255,255,255,.09);
    --text: #fafafa;
    --muted: #a7a7b0;
}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(239,35,60,.18), transparent 27%),
        radial-gradient(circle at 92% 8%, rgba(255,92,112,.10), transparent 24%),
        linear-gradient(180deg,#060608 0%,#0b0b10 55%,#070709 100%);
    color: var(--text);
}

.block-container {
    max-width: 1500px;
    padding-top: 1.1rem;
    padding-bottom: 3rem;
}

section[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 50% 0%, rgba(239,35,60,.14), transparent 28%),
        linear-gradient(180deg,#0d0d11,#08080b);
    border-right: 1px solid rgba(239,35,60,.18);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.2rem;
}

.rocky-hero {
    position: relative;
    overflow: hidden;
    padding: 38px;
    border-radius: 30px;
    border: 1px solid rgba(255,92,112,.25);
    background:
        radial-gradient(circle at 85% 25%, rgba(239,35,60,.22), transparent 30%),
        linear-gradient(135deg,rgba(35,8,14,.97),rgba(13,13,18,.98) 58%,rgba(25,8,13,.97));
    box-shadow: 0 28px 90px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.04);
    margin-bottom: 24px;
}

.rocky-hero:after {
    content:"🏔️";
    position:absolute;
    right:30px;
    bottom:-35px;
    font-size:9rem;
    opacity:.12;
    filter: grayscale(.15);
}

.rocky-hero h1 {
    margin: 8px 0 5px;
    font-size: 3rem;
    line-height: 1.05;
    letter-spacing: -1.8px;
}

.rocky-hero p {
    color:#c7c7cf;
    font-size:1.06rem;
    max-width:720px;
}

.rocky-card, .metric-card {
    border: 1px solid var(--line);
    background: linear-gradient(145deg,rgba(25,25,31,.90),rgba(13,13,17,.94));
    box-shadow: 0 12px 35px rgba(0,0,0,.20);
}

.rocky-card {
    padding:20px;
    border-radius:20px;
    margin:8px 0;
}

.metric-card {
    padding:20px;
    border-radius:20px;
}

.metric-number {
    font-size:1.9rem;
    font-weight:850;
    color:#fff;
}

.metric-label {
    color:#a8a8b2;
    font-size:.88rem;
}

.badge {
    display:inline-block;
    padding:6px 11px;
    border-radius:999px;
    background:rgba(239,35,60,.10);
    border:1px solid rgba(255,92,112,.26);
    color:#ffd5da;
    margin-right:6px;
    font-size:.76rem;
    font-weight:800;
    letter-spacing:.45px;
}

.small-muted { color:#a1a1aa; }

.attachment-strip {
    padding:13px 16px;
    border-radius:16px;
    border:1px solid rgba(255,92,112,.18);
    background:rgba(239,35,60,.055);
    margin:10px 0 18px;
}

.attachment-chip {
    display:inline-block;
    padding:6px 10px;
    margin:3px;
    border-radius:999px;
    background:#18181e;
    border:1px solid rgba(255,255,255,.08);
    color:#e7e7ec;
    font-size:.78rem;
}

.rocky-footer {
    text-align:center;
    color:#71717a;
    padding:34px 0 8px;
    font-size:.84rem;
}

div[data-testid="stButton"] > button {
    border-radius:13px;
    border:1px solid rgba(255,255,255,.09);
    font-weight:750;
    background:linear-gradient(180deg,#1b1b21,#111116);
    transition:.18s ease;
}

div[data-testid="stButton"] > button:hover {
    border-color:#ff5c70;
    box-shadow:0 0 25px rgba(239,35,60,.16);
    transform:translateY(-1px);
}

button[kind="primary"] {
    background:linear-gradient(135deg,#ef233c,#b7092b) !important;
    border-color:#ff5c70 !important;
    box-shadow:0 8px 25px rgba(239,35,60,.15);
}

[data-testid="stMetricValue"] { color:#fff; }
.stTabs [data-baseweb="tab"] { font-weight:750; }
.stTabs [aria-selected="true"] { color:#ff5c70 !important; }
div[data-baseweb="select"] > div,
textarea, input {
    border-radius:12px !important;
}

.v17-head{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;margin:10px auto 16px;max-width:950px;border:1px solid rgba(255,255,255,.08);border-radius:18px;background:rgba(15,15,19,.92)}
.v17-title{font-size:20px;font-weight:850}.v17-sub{font-size:11px;opacity:.55}.v17-welcome{text-align:center;padding:55px 20px 35px}.v17-logo{font-size:64px}.v17-welcome h1{font-size:2.3rem}.v17-welcome p{opacity:.6}.v17-msg{display:flex;gap:14px;max-width:900px;margin:auto;padding:18px;border-bottom:1px solid rgba(255,255,255,.06);line-height:1.65}.v17-user{background:rgba(239,35,60,.06);border-radius:16px}.v17-avatar{font-size:23px;width:34px;flex:0 0 34px;text-align:center}.v17-who{font-size:12px;font-weight:800;opacity:.6;margin-bottom:5px}.v17-body{flex:1;overflow-wrap:anywhere}
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

if "rockyai_attachments" not in st.session_state:
    st.session_state.rockyai_attachments = []
if "v17_chats" not in st.session_state:
    st.session_state.v17_chats = {"New chat": []}
if "v17_active_chat" not in st.session_state:
    st.session_state.v17_active_chat = "New chat"

if "v18_pinned_chats" not in st.session_state:
    st.session_state.v18_pinned_chats = []
if "v18_delete_confirm" not in st.session_state:
    st.session_state.v18_delete_confirm = None
if "v18_page" not in st.session_state:
    st.session_state.v18_page = "🏠 Workspace"


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


# ============================================================
# UNIVERSAL FILE ATTACHMENTS
# ============================================================

ATTACHMENT_TYPES = [
    "pdf", "txt", "md", "csv", "json", "xml", "html", "css", "js",
    "py", "java", "c", "cpp", "h", "ino", "sql", "yaml", "yml",
    "docx", "xlsx", "pptx",
    "png", "jpg", "jpeg", "webp", "gif"
]

def _read_attachment_text(uploaded_file):
    """Extract readable text from common document/code formats."""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    try:
        if name.endswith(".pdf"):
            return extract_pdf(io.BytesIO(data))

        if name.endswith((".txt", ".md", ".csv", ".json", ".xml", ".html",
                           ".css", ".js", ".py", ".java", ".c", ".cpp",
                           ".h", ".ino", ".sql", ".yaml", ".yml")):
            return data.decode("utf-8", errors="replace")

        if name.endswith(".docx"):
            from docx import Document
            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)

        if name.endswith(".xlsx"):
            from openpyxl import load_workbook
            wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            chunks = []
            for ws in wb.worksheets:
                chunks.append(f"[SHEET: {ws.title}]")
                for row in ws.iter_rows(values_only=True):
                    chunks.append(" | ".join("" if v is None else str(v) for v in row))
            return "\n".join(chunks)

        if name.endswith(".pptx"):
            from pptx import Presentation
            prs = Presentation(io.BytesIO(data))
            chunks = []
            for i, slide in enumerate(prs.slides, 1):
                chunks.append(f"[SLIDE {i}]")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        chunks.append(shape.text)
            return "\n".join(chunks)
    except Exception as error:
        return f"[Could not extract text: {error}]"

    return ""

def attachment_context():
    files = st.session_state.get("rockyai_attachments", [])
    if not files:
        return "", []

    text_parts = []
    multimodal_parts = []

    for item in files:
        data = item["data"]
        mime = item["mime"]
        name = item["name"]

        # Images are sent directly to Gemini as multimodal bytes.
        if mime.startswith("image/"):
            try:
                multimodal_parts.append(
                    genai.types.Part.from_bytes(data=data, mime_type=mime)
                )
                text_parts.append(f"[IMAGE ATTACHED: {name}]")
            except Exception:
                text_parts.append(f"[IMAGE ATTACHED: {name} — image could not be sent]")

        # PDFs can be sent directly as PDF bytes.
        elif mime == "application/pdf":
            try:
                multimodal_parts.append(
                    genai.types.Part.from_bytes(data=data, mime_type=mime)
                )
                text_parts.append(f"[PDF ATTACHED: {name}]")
            except Exception:
                extracted = item.get("text", "")
                text_parts.append(f"[PDF: {name}]\n{extracted[:50000]}")

        else:
            extracted = item.get("text", "")
            text_parts.append(
                f"[FILE ATTACHED: {name}]\n{extracted[:50000]}"
            )

    return "\n\n".join(text_parts), multimodal_parts

def attachment_uploader():
    st.markdown("#### 📎 Attach files")
    uploaded = st.file_uploader(
        "Upload files for RockyAI to read, analyze or use",
        type=ATTACHMENT_TYPES,
        accept_multiple_files=True,
        key="universal_attachment_uploader",
        help=(
            "Supports PDFs, Word, Excel, PowerPoint, images, text, CSV, JSON, "
            "web files and common programming files."
        ),
    )

    if uploaded:
        st.session_state.rockyai_attachments = []
        for file in uploaded:
            mime = file.type or mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            data = file.getvalue()
            st.session_state.rockyai_attachments.append({
                "name": file.name,
                "mime": mime,
                "data": data,
                "text": _read_attachment_text(file),
            })

    files = st.session_state.get("rockyai_attachments", [])
    if files:
        chips = "".join(
            f'<span class="attachment-chip">📎 {html.escape(f["name"])}</span>'
            for f in files
        )
        st.markdown(
            f'<div class="attachment-strip"><b>Attached:</b><br>{chips}</div>',
            unsafe_allow_html=True,
        )

        if st.button("🗑️ Clear attachments", key="clear_attachments"):
            st.session_state.rockyai_attachments = []
            st.rerun()



def ask_rockyai(prompt, instruction=""):
    if gemini is None:
        return (
            "⚠️ Gemini is not connected.\n\n"
            "Add your **GEMINI_API_KEY** to your environment variables "
            "or Render Environment settings."
        )

    attachment_text, attachment_parts = attachment_context()

    final_prompt = f"""
You are RockyAIv1-8, a professional educational AI assistant.

IMPORTANT:
- Be accurate and clear.
- Explain difficult ideas in student-friendly language.
- Do not invent information.
- Use headings, bullets and examples when useful.
- If a question is ambiguous, state the assumption you made.
- When files are attached, use them as the primary source for file-related questions.
- For images, inspect the visible content carefully.
- For code files, explain or modify the actual supplied code rather than inventing a different project.

SPECIAL INSTRUCTION:
{instruction}

USER REQUEST:
{prompt}

ATTACHED FILE CONTEXT:
{attachment_text if attachment_text else "No files attached."}
"""

    try:
        contents = [*attachment_parts, final_prompt]
        response = gemini.models.generate_content(
            model=MODEL,
            contents=contents,
        )

        text = getattr(response, "text", None)
        if text:
            return text.strip()

        return "RockyAI returned an empty response."

    except Exception as error:
        # Some Gemini configurations may reject a binary attachment.
        # Fall back to extracted text so the text/document workflow still works.
        if attachment_text and attachment_parts:
            try:
                fallback_prompt = final_prompt + "\n\nPlease answer using the extracted attachment text above."
                response = gemini.models.generate_content(
                    model=MODEL,
                    contents=fallback_prompt,
                )
                text = getattr(response, "text", None)
                if text:
                    return text.strip()
            except Exception:
                pass

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
            <span class="badge">ROCKYAI v1-7</span>
            <span class="badge">AI LEARNING WORKSPACE</span>
            <h1>🏔️ RockyAI</h1>
            <p>Learn faster. Practice smarter. Build better.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        st.markdown("### 🚀 RockyAIv1-8")

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
        '<div class="rocky-footer">RockyAIv1-8 • AI-powered learning workspace</div>',
        unsafe_allow_html=True,
    )


if not st.session_state.logged_in:
    login_page()
    st.stop()


def v18_chat_action(label, prompt):
    if st.button(label, use_container_width=True, key="v18_action_" + re.sub(r"[^A-Za-z0-9]", "_", label)):
        st.session_state.v18_prefill = prompt
        st.session_state.v18_page = "🏠 Workspace"
        st.rerun()


# ============================================================
# ROCKYAI v1-8 — CHATGPT-STYLE SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("# 🏔️ RockyAIv1-8")
    st.caption("AI powered personal workspace")

    role_label = "Administrator" if st.session_state.role == "admin" else "User"
    st.markdown(f"**{html.escape(st.session_state.username)}**  \n`{role_label}`")
    st.divider()

    def side_nav(label, target):
        active = st.session_state.v18_page == target
        if st.button(("● " if active else "") + label,
                     key="v18_nav_" + re.sub(r"[^A-Za-z0-9]", "_", label),
                     use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.v18_page = target
            st.rerun()

    v18_chat_action("⏰ Scheduled", "Help me create or review a schedule for my study, work or personal tasks. Ask for any missing details you need.")
    v18_chat_action("🧩 Plugins", "Show me all RockyAI built-in capabilities and explain how I can use each one directly in this chat.")
    v18_chat_action("📁 Project", "Help me build my project from idea to completion: requirements, architecture, folder structure, tasks, code, documentation and presentation.")
    v18_chat_action("💻 Coder", "Act as my coding assistant. Help me write, debug, explain, improve or package code. Ask for the language only if needed.")

    with st.expander("… More", expanded=False):
        v18_chat_action("📚 Study Tools", "Open an all-in-one study session: tutor me, solve questions, summarize material, make quizzes, flashcards, a mind map and an exam plan as appropriate.")
        v18_chat_action("📦 File Studio", "Help me create a downloadable file. Ask what format I want if I have not specified one. Supported: PDF, DOCX, XLSX, PPTX, TXT, CSV, JSON, Markdown, HTML, CSS, JS, Python, Java, C, C++, Arduino, SQL, XML, YAML and RTF. No images.")
        v18_chat_action("🕘 History", "Show me how to review my saved RockyAI conversations and organize them.")
        v18_chat_action("📊 Analytics", "Help me understand my RockyAI usage and study activity.")
        if st.session_state.role == "admin":
            v18_chat_action("🛡️ Admin Panel", "Explain the administrator capabilities available in RockyAI.")

    st.divider()
    st.markdown("### 📌 Pinned Chat")
    pinned = [x for x in st.session_state.v18_pinned_chats if x in st.session_state.v17_chats]
    st.session_state.v18_pinned_chats = pinned
    if pinned:
        for name in pinned:
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                if st.button("📌 " + name, key="v18_pin_open_" + name, use_container_width=True):
                    st.session_state.v17_active_chat = name
                    st.session_state.v18_page = "🏠 Workspace"
                    st.rerun()
            with c2:
                if st.button("🗑️", key="v18_pin_del_" + name, help="Delete this chat"):
                    st.session_state.v18_delete_confirm = name
                    st.rerun()
            with c3:
                if st.button("📍", key="v18_unpin_" + name, help="Unpin chat"):
                    st.session_state.v18_pinned_chats.remove(name)
                    st.rerun()
    else:
        st.caption("No pinned chats")

    st.markdown("### 🕘 Recent Chat")
    recent = [x for x in st.session_state.v17_chats.keys() if x not in st.session_state.v18_pinned_chats]
    if recent:
        for name in recent[-12:][::-1]:
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                if st.button(("● " if name == st.session_state.v17_active_chat else "") + name,
                             key="v18_recent_open_" + name, use_container_width=True):
                    st.session_state.v17_active_chat = name
                    st.session_state.v18_page = "🏠 Workspace"
                    st.rerun()
            with c2:
                if st.button("🗑️", key="v18_recent_del_" + name, help="Delete this chat"):
                    st.session_state.v18_delete_confirm = name
                    st.rerun()
            with c3:
                if st.button("📌", key="v18_pin_add_" + name, help="Pin chat"):
                    st.session_state.v18_pinned_chats.append(name)
                    st.rerun()
    else:
        st.caption("No recent chats")

    st.divider()
    if st.button("✚ New Chat", type="primary", use_container_width=True, key="v18_new_chat_sidebar"):
        i = 1
        while True:
            new_name = "New chat" if i == 1 else f"New chat {i}"
            if new_name not in st.session_state.v17_chats:
                break
            i += 1
        st.session_state.v17_chats[new_name] = []
        st.session_state.v17_active_chat = new_name
        st.session_state.rockyai_attachments = []
        st.session_state.v18_page = "🏠 Workspace"
        st.rerun()

    if st.session_state.v18_delete_confirm:
        delete_name = st.session_state.v18_delete_confirm
        st.warning(f"Delete **{delete_name}**?")
        d1, d2 = st.columns(2)
        with d1:
            if st.button("Delete", type="primary", use_container_width=True, key="v18_confirm_delete"):
                st.session_state.v17_chats.pop(delete_name, None)
                if delete_name in st.session_state.v18_pinned_chats:
                    st.session_state.v18_pinned_chats.remove(delete_name)
                if not st.session_state.v17_chats:
                    st.session_state.v17_chats["New chat"] = []
                if st.session_state.v17_active_chat == delete_name:
                    st.session_state.v17_active_chat = next(iter(st.session_state.v17_chats))
                st.session_state.v18_delete_confirm = None
                st.session_state.rockyai_attachments = []
                st.rerun()
        with d2:
            if st.button("Cancel", use_container_width=True, key="v18_cancel_delete"):
                st.session_state.v18_delete_confirm = None
                st.rerun()

    st.divider()
    if st.button("🚪 Logout", use_container_width=True, key="v18_logout"):
        logout()

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
# ROCKYAI v1-7 — CHATGPT-STYLE NEW CHAT
# ============================================================

def v17_new_chat():
    i = 1
    while True:
        name = "New chat" if i == 1 else f"New chat {i}"
        if name not in st.session_state.v17_chats:
            break
        i += 1
    st.session_state.v17_chats[name] = []
    st.session_state.v17_active_chat = name
    st.session_state.rockyai_attachments = []


def v18_detect_file_request(prompt):
    p = prompt.lower()
    mapping = {
        "pdf": ("PDF", ".pdf"), "docx": ("DOCX", ".docx"), "word": ("DOCX", ".docx"), "document": ("DOCX", ".docx"),
        "xlsx": ("XLSX", ".xlsx"), "excel": ("XLSX", ".xlsx"), "spreadsheet": ("XLSX", ".xlsx"), "pptx": ("PPTX", ".pptx"),
        "powerpoint": ("PPTX", ".pptx"), "presentation": ("PPTX", ".pptx"), "csv": ("CSV", ".csv"), "json": ("JSON", ".json"),
        "markdown": ("Markdown", ".md"), "md file": ("Markdown", ".md"), "html": ("HTML", ".html"),
        "css": ("CSS", ".css"), "javascript": ("JavaScript", ".js"), "js file": ("JavaScript", ".js"),
        "python": ("Python", ".py"), "python file": ("Python", ".py"), "java": ("Java", ".java"),
        "c++": ("C++", ".cpp"), "cpp": ("C++", ".cpp"), "arduino": ("Arduino", ".ino"),
        "c code": ("C", ".c"), "sql": ("SQL", ".sql"), "xml": ("XML", ".xml"),
        "yaml": ("YAML", ".yaml"), "yml": ("YAML", ".yml"), "txt": ("TXT", ".txt"),
        "text file": ("TXT", ".txt"), "rtf": ("RTF", ".rtf"),
    }
    # Prefer explicit file/download/create/export wording so normal questions about a PDF don't trigger a download.
    if not any(x in p for x in ["create", "generate", "make", "download", "export", "save as", "file"]):
        return None
    for key, value in mapping.items():
        if key in p:
            return value
    return None


def v18_file_bytes(file_type, title, content):
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", title).strip("_") or "RockyAI_File"
    if file_type == "PDF":
        return create_pdf(title, content), "application/pdf", safe_name + ".pdf"
    if file_type == "DOCX":
        from docx import Document
        bio = io.BytesIO(); doc = Document(); doc.add_heading(title, 0)
        for para in content.splitlines() or [content]: doc.add_paragraph(para)
        doc.save(bio)
        return bio.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", safe_name + ".docx"
    if file_type == "XLSX":
        from openpyxl import Workbook
        bio = io.BytesIO(); wb = Workbook(); ws = wb.active; ws.title = "RockyAI"
        for r, line in enumerate(content.splitlines() or [content], 1):
            for c, value in enumerate(line.split(","), 1): ws.cell(r, c, value.strip())
        wb.save(bio)
        return bio.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", safe_name + ".xlsx"
    if file_type == "PPTX":
        from pptx import Presentation
        prs = Presentation()
        chunks = [x.strip() for x in re.split(r"\n\s*\n", content) if x.strip()] or [content]
        for i, chunk in enumerate(chunks[:20]):
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = title if i == 0 else f"{title} — {i+1}"
            slide.placeholders[1].text = chunk[:5000]
        bio = io.BytesIO(); prs.save(bio)
        return bio.getvalue(), "application/vnd.openxmlformats-officedocument.presentationml.presentation", safe_name + ".pptx"
    if file_type == "JSON":
        import json
        try: obj = json.loads(content)
        except Exception: obj = {"content": content}
        return json.dumps(obj, indent=2, ensure_ascii=False), "application/json", safe_name + ".json"
    mime = {
        "CSV":"text/csv", "Markdown":"text/markdown", "HTML":"text/html", "CSS":"text/css",
        "JavaScript":"text/javascript", "Python":"text/x-python", "Java":"text/x-java-source",
        "C":"text/x-c", "C++":"text/x-c++src", "Arduino":"text/plain", "SQL":"application/sql",
        "XML":"application/xml", "YAML":"application/yaml", "TXT":"text/plain", "RTF":"application/rtf",
    }.get(file_type, "text/plain")
    ext = {"CSV":".csv","Markdown":".md","HTML":".html","CSS":".css","JavaScript":".js","Python":".py","Java":".java","C":".c","C++":".cpp","Arduino":".ino","SQL":".sql","XML":".xml","YAML":".yaml","TXT":".txt","RTF":".rtf"}[file_type]
    return content, mime, safe_name + ext


def v18_make_download(answer, prompt):
    req = v18_detect_file_request(prompt)
    if not req:
        return
    file_type, _ = req
    # Ask the model to return only the file body for code/data formats, while normal prose is used for documents.
    content = answer
    if file_type in {"Python","JavaScript","Java","C","C++","Arduino","CSS","HTML","SQL","XML","YAML","JSON"}:
        content = clean_code(answer)
    title_match = re.search(r"(?:called|named|name)\s+['\"]?([A-Za-z0-9_-]+)", prompt, re.I)
    title = title_match.group(1) if title_match else "RockyAI_Generated"
    try:
        data, mime, filename = v18_file_bytes(file_type, title, content)
        st.download_button("⬇️ Download generated " + file_type, data=data, file_name=filename, mime=mime, use_container_width=True, key="v18_download_" + hashlib.md5((prompt+answer).encode()).hexdigest())
        st.caption("Generated in chat • Image generation is not included.")
    except Exception as e:
        st.error(f"File generation failed: {e}")


def v18_chat_ui():
    name = st.session_state.v17_active_chat
    messages = st.session_state.v17_chats[name]

    st.markdown(f'''<div class="v17-head"><div><div class="v17-title">🏔️ {html.escape(name)}</div><div class="v17-sub">RockyAIv1-8 • AI-powered personal workspace</div></div><div>● ONLINE</div></div>''', unsafe_allow_html=True)

    # One-chat command bar: every capability is available without leaving the chatbot.
    with st.expander("✨ All-in-one tools", expanded=not messages):
        cols = st.columns(4)
        quick = [
            ("🎓 Study", "Act as my personal tutor. Teach me my topic step by step, adapt to my level, ask practice questions and explain mistakes."),
            ("📝 Quiz", "Create an interactive-style quiz on my topic with questions, answers and explanations."),
            ("📄 Create PDF", "Create a polished PDF document for me. Include a title, sections, useful formatting and complete content. Then prepare it as a downloadable PDF."),
            ("💻 Code", "Act as my coding assistant. Write complete working code, explain it, debug errors, and give copy-paste-ready files when requested."),
            ("🧠 Mind Map", "Create a clear hierarchical text mind map for my topic, followed by key takeaways."),
            ("🃏 Flashcards", "Create revision flashcards with questions on one side and concise answers on the other."),
            ("📅 Study Plan", "Create a realistic study plan with daily tasks, revision, practice and progress checkpoints."),
            ("🚀 Project", "Act as my project builder. Turn my idea into requirements, architecture, milestones, code, documentation and presentation content."),
            ("📊 Presentation", "Create a complete slide-by-slide presentation with titles, bullet points, speaker notes and design suggestions."),
            ("✂️ Summarize", "Summarize my attached or pasted material into clear revision notes without losing important facts."),
            ("🌐 Translate", "Translate the material I provide accurately and naturally. Preserve meaning and structure."),
            ("🎯 Exam Prep", "Create an exam preparation strategy including topics, revision schedule, practice questions and last-day checklist."),
            ("🧪 Science", "Help me with science study, including concepts, experiments, definitions, diagrams described in text and exam questions."),
            ("📚 Sample Paper", "Create a complete school sample paper on my requested subject and topics, with sections, marks and an answer key."),
            ("🏆 Daily Challenge", "Give me a daily learning challenge with a question, hint, answer and a small follow-up task."),
            ("💡 Brainstorm", "Brainstorm practical, creative and realistic ideas for my topic, then organize them into categories and next steps."),
            ("🧪 Periodic Table", "Help me study the periodic table, including element names, symbols, atomic numbers, groups, periods and useful trends."),
            ("📘 Vocabulary", "Build a vocabulary lesson with meanings, examples, memory clues and a short test."),
            ("🧠 Memory", "Create an active-recall and memory-training session using mnemonics, chunking and retrieval practice."),
            ("🔍 Fact Check", "Analyze the claim I provide, separate established facts from uncertainty, and explain what would need verification."),
            ("🎤 Interview", "Act as an interview coach. Ask realistic questions, evaluate my answers constructively and suggest improvements."),
            ("🗣️ Debate", "Act as a debate coach. Help me understand both sides, build arguments and practice rebuttals."),
            ("🧭 Career", "Create a career roadmap based on my interests, current level, skills to build, projects and next steps."),
            ("🎯 Goal", "Act as my goal coach. Turn my goal into measurable milestones, weekly actions and progress checks."),
            ("📦 DOCX", "Create a professional DOCX document from my request and make it downloadable."),
            ("📊 XLSX", "Create a structured XLSX spreadsheet from my request and make it downloadable."),
            ("📽️ PPTX", "Create a PPTX presentation from my request and make it downloadable."),
            ("📄 TXT/CSV", "Create the requested TXT or CSV file from my content and make it downloadable."),
        ]
        for i, (label, prompt) in enumerate(quick):
            with cols[i % 4]:
                if st.button(label, use_container_width=True, key="v18_quick_" + str(i)):
                    st.session_state.v18_prefill = prompt
                    st.rerun()

    if not messages:
        st.markdown('''<div class="v17-welcome"><div class="v17-logo">🏔️</div><h1>How can I help you today?</h1><p>Everything is in one chat — study, coding, projects, files, research-style explanations, planning, practice and document creation.</p></div>''', unsafe_allow_html=True)

    for role, msg in messages:
        avatar = "👤" if role == "user" else "🏔️"
        who = "You" if role == "user" else "RockyAI"
        cls = "v17-msg v17-user" if role == "user" else "v17-msg"
        safe = html.escape(msg).replace("\n", "<br>")
        st.markdown(f'<div class="{cls}"><div class="v17-avatar">{avatar}</div><div class="v17-body"><div class="v17-who">{who}</div>{safe}</div></div>', unsafe_allow_html=True)

    # Files can be attached directly to the one conversation.
    attachment_uploader()

    prefill = st.session_state.pop("v18_prefill", "")
    prompt = st.chat_input("Message RockyAI — ask, study, code, create a file, plan, solve...", key="v18_input")
    if prefill and not prompt:
        prompt = prefill

    if prompt and prompt.strip():
        prompt = prompt.strip()
        messages.append(("user", prompt))
        if name.startswith("New chat") and len(messages) == 1:
            title = re.sub(r"\s+", " ", prompt)[:45].strip() or name
            if title != name:
                st.session_state.v17_chats[title] = st.session_state.v17_chats.pop(name)
                st.session_state.v18_pinned_chats = [title if x == name else x for x in st.session_state.v18_pinned_chats]
                st.session_state.v17_active_chat = title
                name = title
                messages = st.session_state.v17_chats[name]

        instruction = '''
You are RockyAIv1-8, a unified all-in-one personal AI workspace chatbot. Never force the user to select a separate tool.
Handle the request directly and naturally. You are simultaneously a general assistant, personal tutor, question solver, PDF/file study assistant, quiz generator, sample-paper creator, coding assistant, debugger, mind-map creator, flashcard maker, study planner, summarizer, translator, brainstorm partner, exam-preparation coach, periodic-table/science helper, daily-challenge coach, debate coach, interview coach, career-roadmap coach, project builder, presentation maker, memory trainer, goal coach, vocabulary builder and fact-checking assistant.
For attached files, use the attachment as the primary source when the user asks about it. Do not invent information that is not in the source when source-only work is requested.
When the user asks for a file, produce complete, clean content suitable for that file. Supported downloadable formats include PDF, DOCX, XLSX, PPTX, TXT, CSV, JSON, Markdown, HTML, CSS, JavaScript, Python, Java, C, C++, Arduino, SQL, XML, YAML and RTF. Image generation is NOT supported.
For code, give complete copy-paste-ready code and avoid wrapping code in unnecessary explanations when the user asks for a file. Never claim a file was generated unless the application provides a download button.
Adapt explanations to the user's requested level, including school grades. For educational answers, be clear and structured. For coding, prioritize correctness and runnable code.
'''
        with st.spinner("RockyAI is thinking..."):
            answer = ask_rockyai(prompt, instruction)
        messages.append(("assistant", answer))
        save_chat("Unified Chat", prompt, answer)
        st.rerun()

    # Show a download control for explicit file-generation requests after the current response.
    if messages:
        last_user = next((m for r, m in reversed(messages) if r == "user"), "")
        last_answer = next((m for r, m in reversed(messages) if r == "assistant"), "")
        if last_answer:
            v18_make_download(last_answer, last_user)


def file_studio():
    st.markdown("## 📦 File Studio")
    st.caption("Create downloadable files from your content. Image generation is not included.")
    file_type = st.selectbox("File type", ["PDF", "DOCX", "XLSX", "PPTX", "TXT", "CSV", "JSON", "Markdown", "HTML", "Python", "JavaScript", "C++", "Arduino"])
    title = st.text_input("File name / title", "RockyAI_Document")
    content = st.text_area("Content", height=300, placeholder="Paste or write the content you want to turn into a file...")
    if st.button("✨ Generate File", type="primary", use_container_width=True):
        if not content.strip():
            st.warning("Enter some content first.")
            return
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", title).strip("_") or "RockyAI_Document"
        data, mime, ext = content, "text/plain", ".txt"
        try:
            if file_type == "PDF":
                data = create_pdf(title, content); mime = "application/pdf"; ext = ".pdf"
            elif file_type == "DOCX":
                from docx import Document
                bio = io.BytesIO(); doc = Document(); doc.add_heading(title, 0)
                for para in content.split("\n"): doc.add_paragraph(para)
                doc.save(bio); data = bio.getvalue(); mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"; ext = ".docx"
            elif file_type == "XLSX":
                from openpyxl import Workbook
                bio = io.BytesIO(); wb = Workbook(); ws = wb.active; ws.title = "RockyAI"
                for r, line in enumerate(content.splitlines() or [content], 1):
                    for c, value in enumerate(line.split(","), 1): ws.cell(r, c, value.strip())
                wb.save(bio); data = bio.getvalue(); mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"; ext = ".xlsx"
            elif file_type == "PPTX":
                from pptx import Presentation
                bio = io.BytesIO(); prs = Presentation(); slide = prs.slides.add_slide(prs.slide_layouts[1]); slide.shapes.title.text = title; slide.placeholders[1].text = content[:5000]; prs.save(bio)
                data = bio.getvalue(); mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"; ext = ".pptx"
            elif file_type == "CSV":
                mime, ext = "text/csv", ".csv"
            elif file_type == "JSON":
                import json
                try: obj = json.loads(content)
                except Exception: obj = {"content": content}
                data = json.dumps(obj, indent=2, ensure_ascii=False); mime, ext = "application/json", ".json"
            elif file_type == "Markdown": mime, ext = "text/markdown", ".md"
            elif file_type == "HTML":
                if "<html" not in content.lower(): data = f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title></head><body><pre>{html.escape(content)}</pre></body></html>"
                mime, ext = "text/html", ".html"
            else:
                ext = {"Python":".py", "JavaScript":".js", "C++":".cpp", "Arduino":".ino"}[file_type]
            st.download_button("⬇️ Download " + file_type, data=data, file_name=safe_name + ext, mime=mime, use_container_width=True)
        except Exception as e:
            st.error(f"Could not create the file: {e}")


def unified_project_page():
    st.markdown("## 📁 Project")
    st.info("Use the main chat to describe your project. RockyAI can turn the idea into requirements, architecture, tasks, code, documentation and presentation content.")
    cols = st.columns(3)
    for col, label, prompt in [(cols[0], "🚀 Start Project", "Create a complete project plan with objectives, features, tech stack, milestones and risks."), (cols[1], "🧱 Architecture", "Design the architecture and folder structure for my project."), (cols[2], "📊 Presentation", "Create a presentation outline for my project with slide-by-slide content.")]:
        with col:
            if st.button(label, use_container_width=True, key="v18_proj_" + label):
                st.session_state.v18_prefill = prompt; st.session_state.v18_page = "🏠 Workspace"; st.rerun()


def coder_page():
    st.markdown("## 💻 Coder")
    language = st.selectbox("Preferred language", ["Python", "JavaScript", "HTML/CSS/JS", "C", "C++", "Java", "Arduino"])
    request = st.text_area("What should RockyAI code?", height=180)
    if st.button("💻 Send to RockyAI", type="primary", use_container_width=True) and request.strip():
        st.session_state.v18_prefill = f"Using {language}, {request}"; st.session_state.v18_page = "🏠 Workspace"; st.rerun()


def plugins_page():
    st.markdown("## 🧩 Plugins")
    st.caption("RockyAI's built-in capabilities are available directly in the unified chatbot.")
    for tool in TOOLS: st.markdown(f"• {tool}")


def scheduled_page():
    st.markdown("## ⏰ Scheduled")
    st.info("Scheduling interface is available for scheduled AI tasks. Your chats remain available in the sidebar.")


def study_tools_page():
    st.markdown("## 📚 Study Tools")
    st.caption("All study tools work through the main chatbot.")
    cols = st.columns(3)
    prompts = [("🎓 AI Tutor", "Teach me a topic step by step at my grade level."), ("📝 Quiz", "Create a quiz on my topic with answers and explanations."), ("🃏 Flashcards", "Create revision flashcards for my topic."), ("📅 Study Plan", "Make a study plan for my exams."), ("✂️ Summary", "Summarize the attached material into revision notes."), ("🧠 Mind Map", "Create a clear text mind map for this topic.")]
    for i, (label, prompt) in enumerate(prompts):
        with cols[i % 3]:
            if st.button(label, use_container_width=True, key="v18_study_" + label):
                st.session_state.v18_prefill = prompt; st.session_state.v18_page = "🏠 Workspace"; st.rerun()


def workspace():
    v18_chat_ui()

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

page = st.session_state.get("v18_page", "🏠 Workspace")
if page == "🏠 Workspace": workspace()
elif page == "⏰ Scheduled": scheduled_page()
elif page == "🧩 Plugins": plugins_page()
elif page == "📁 Project": unified_project_page()
elif page == "💻 Coder": coder_page()
elif page == "📚 Study Tools": study_tools_page()
elif page == "📦 File Studio": file_studio()
elif page == "🕘 History": history_page()
elif page == "📊 Analytics": analytics_page()
elif page == "🛡️ Admin Panel": admin_page()

st.markdown('<div class="rocky-footer">RockyAIv1-8 • Learn • Practice • Create • Build</div>', unsafe_allow_html=True)
