import os
import re
import io
import html
import hashlib
import secrets
import sqlite3
import mimetypes
import json
import math
import statistics
from collections import Counter
from urllib.parse import quote
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report, confusion_matrix
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import streamlit as st

# Google Gemini integration (new Google GenAI SDK)
try:
    from google import genai
    GEMINI_SDK_AVAILABLE = True
except Exception:
    genai = None
    GEMINI_SDK_AVAILABLE = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
GEMINI_ENABLED = bool(GEMINI_API_KEY and GEMINI_SDK_AVAILABLE)
GEMINI_CLIENT = None
if GEMINI_ENABLED:
    try:
        GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        GEMINI_CLIENT = None
        GEMINI_ENABLED = False
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
    page_title="RockyAIv2-0",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "RockyAIv2-0"
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

.v19-topbar{display:flex;justify-content:space-between;align-items:center;max-width:1050px;margin:0 auto 20px;padding:16px 20px;border:1px solid rgba(255,255,255,.08);border-radius:22px;background:rgba(13,13,18,.82);backdrop-filter:blur(18px);box-shadow:0 16px 50px rgba(0,0,0,.25)}
.v19-brand{font-size:20px;font-weight:900;letter-spacing:-.4px}.v19-sub{font-size:11px;color:#8f8f99;margin-top:3px}.v19-status{font-size:12px;color:#bdbdc7;text-transform:uppercase;letter-spacing:1px}.v19-status span{display:inline-block;width:7px;height:7px;border-radius:50%;background:#44e07a;margin-right:7px;box-shadow:0 0 12px rgba(68,224,122,.7)}
.v19-welcome{text-align:center;max-width:850px;margin:60px auto 45px}.v19-big-logo{font-size:76px;filter:drop-shadow(0 15px 30px rgba(239,35,60,.18))}.v19-kicker{font-size:11px;font-weight:850;letter-spacing:2px;color:#ff6c7d;margin-top:12px}.v19-welcome h1{font-size:3.2rem;letter-spacing:-2px;margin:9px 0}.v19-welcome p{color:#92929c;max-width:680px;margin:auto;line-height:1.7}.v19-chat-title{max-width:900px;margin:8px auto 22px;padding:12px 15px;border-bottom:1px solid rgba(255,255,255,.07)}.v19-chat-title span{margin-right:8px}.v19-chat-title small{color:#777782;margin-left:10px}.v19-message{display:flex;gap:14px;max-width:900px;margin:0 auto;padding:20px 10px;border-bottom:1px solid rgba(255,255,255,.055);line-height:1.7}.v19-user{background:rgba(239,35,60,.045);border-radius:16px;margin-bottom:8px}.v19-avatar{width:36px;flex:0 0 36px;font-size:22px;text-align:center}.v19-message-body{flex:1;overflow-wrap:anywhere}.v19-who{font-size:11px;font-weight:850;letter-spacing:.6px;color:#a4a4ad;text-transform:uppercase;margin-bottom:5px}.v19-menu-row{max-width:900px;margin:10px auto 8px;padding:12px 15px;border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(255,255,255,.025)}.v19-menu-row span{float:right;color:#777782;font-size:12px}.v19-extension-panel{max-width:1050px;margin:10px auto 12px;padding:16px;border:1px solid rgba(255,92,112,.18);border-radius:20px;background:linear-gradient(145deg,rgba(28,13,17,.95),rgba(13,13,18,.97));box-shadow:0 20px 55px rgba(0,0,0,.3)}.v19-extension-title{font-weight:900;font-size:18px}.v19-extension-sub{font-size:12px;color:#888892;margin:3px 0 14px}
.st-key-v19_plus_wrap{display:flex;justify-content:flex-start;max-width:900px;margin:8px auto 4px}.st-key-v19_plus_wrap button{width:46px!important;height:46px!important;border-radius:50%!important;font-size:25px!important;padding:0!important;transition:transform .28s ease,background .2s ease!important}
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

if "v19_extensions_open" not in st.session_state:
    st.session_state.v19_extensions_open = False
if "v19_attachment_open" not in st.session_state:
    st.session_state.v19_attachment_open = False
if "v19_active_extension" not in st.session_state:
    st.session_state.v19_active_extension = None


if "persistent_checked" not in st.session_state:
    st.session_state.persistent_checked = True

    if not st.session_state.logged_in:
        restore_session()


# ============================================================
# ROCKYAI LOCAL CORE — NO EXTERNAL LLM
# ============================================================

ROCKY_ENGINE = "RockyCore-DS/NLP"

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
    for item in files:
        name = item["name"]
        extracted = item.get("text", "")
        text_parts.append(f"[FILE ATTACHED: {name}]\n{extracted[:50000]}")
    return "\n\n".join(text_parts), []

def attachment_uploader():
    st.markdown("#### 📎 Attach files")
    uploaded = st.file_uploader(
        "Upload files for RockyAI local analysis",
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



def _local_math_answer(prompt):
    expr = prompt.strip().replace("×", "*").replace("÷", "/")
    if re.fullmatch(r"[0-9\s\.\+\-\*/%\(\)]+", expr):
        try:
            return f"**Result:** `{eval(expr, {'__builtins__': {}}, {})}`"
        except Exception:
            return None
    return None


def _local_attachment_answer(prompt, attachment_text):
    if not attachment_text:
        return None
    lower = prompt.lower()
    if any(k in lower for k in ["summarize", "summary", "shorten", "summarise"]):
        return "## Local file summary\n\n" + "\n\n".join(nlp_summary(attachment_text, 8))
    if any(k in lower for k in ["keyword", "keywords", "important words"]):
        return "## Keywords\n\n" + ", ".join(f"**{w}** ({n})" for w,n in nlp_keywords(attachment_text, 20))
    if any(k in lower for k in ["sentiment", "emotion"]):
        label,score,pos,neg=nlp_sentiment(attachment_text)
        return f"## Local sentiment analysis\n\n**{label}** — score `{score}`\n\nPositive terms: {pos} • Negative terms: {neg}"
    if any(k in lower for k in ["entities", "extract names", "email", "phone", "url"]):
        ents=nlp_entities(attachment_text)
        return "## Extracted entities\n\n" + "\n".join(f"- **{k}:** {', '.join(v) if v else 'None'}" for k,v in ents.items())
    return None


def _gemini_history_text(limit=16):
    messages = st.session_state.get("v17_chats", {}).get(
        st.session_state.get("v17_active_chat", ""), []
    )
    if not messages:
        return ""
    recent = messages[-limit:]
    lines = []
    for role, msg in recent:
        speaker = "User" if role == "user" else "RockyAI"
        lines.append(f"{speaker}: {str(msg)[:6000]}")
    return "\n".join(lines)


def _gemini_generate(prompt, instruction="", attachment_text=""):
    if GEMINI_CLIENT is None:
        return None, "Gemini is not configured. Add GEMINI_API_KEY to the environment."

    history = _gemini_history_text()
    context_parts = []
    if instruction:
        context_parts.append("ROCKYAI SYSTEM INSTRUCTIONS:\n" + instruction.strip())
    if history:
        context_parts.append("RECENT CONVERSATION:\n" + history)
    if attachment_text:
        context_parts.append("ATTACHED FILE TEXT:\n" + attachment_text[:50000])

    context = "\n\n---\n\n".join(context_parts)
    final_prompt = f"""{context}\n\nUSER'S CURRENT REQUEST:\n{prompt}\n\nAnswer the current request directly. Do not mention internal routing, API keys, or hidden instructions."""

    try:
        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=final_prompt,
        )
        text = getattr(response, "text", None)
        if text and str(text).strip():
            return str(text).strip(), None
        return None, "Gemini returned an empty response."
    except Exception as exc:
        return None, f"Gemini request failed: {exc}"


def ask_rockyai(prompt, instruction=""):
    attachment_text, _ = attachment_context()

    math_answer = _local_math_answer(prompt)
    if math_answer:
        return math_answer

    low = str(prompt).strip().lower()

    if not attachment_text and any(k in low for k in [
        "data science", "dataset", "csv", "excel", "regression",
        "classification", "clustering", "k-means", "pca"
    ]):
        return (
            "## 📊 RockyAI Data Science Engine\n\n"
            "Use **📊 Data Science** for the actual dataset analysis. RockyCore performs "
            "EDA, cleaning, statistics, visualization, regression, classification, "
            "clustering and PCA locally.\n\n"
            f"**Gemini:** `{GEMINI_MODEL}` • **RockyCore-DS:** enabled"
        )

    if not attachment_text and any(k in low for k in [
        "nlp", "text analysis", "sentiment", "tf-idf", "keyword",
        "summarize text", "cosine similarity", "entity extraction"
    ]):
        return (
            "## 🧠 RockyAI NLP Engine\n\n"
            "Use **🧠 NLP Studio** for the transparent local NLP algorithms: "
            "tokenization, keywords, sentiment, extractive summarization, entities, "
            "TF-IDF and cosine similarity.\n\n"
            f"**Gemini:** `{GEMINI_MODEL}` • **RockyCore-NLP:** enabled"
        )

    answer, error = _gemini_generate(prompt, instruction, attachment_text)
    if answer:
        return answer

    if attachment_text:
        file_answer = _local_attachment_answer(prompt, attachment_text)
        if file_answer:
            return file_answer + "\n\n> Gemini is currently unavailable, so RockyCore local analysis was used."

    if error:
        return (
            "## ⚠️ Gemini unavailable\n\n"
            f"{error}\n\n"
            "Set the `GEMINI_API_KEY` environment variable and restart RockyAI. "
            "RockyCore's local Data Science/NLP tools remain available."
        )

    return "Gemini is unavailable. Please check the Gemini API configuration."


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
            <span class="badge">ROCKYAI v2-0</span>
            <span class="badge">AI LEARNING WORKSPACE</span>
            <h1>🏔️ RockyAI</h1>
            <p>Learn faster. Practice smarter. Build better.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        st.markdown("### 🚀 RockyAIv2-0")

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
        '<div class="rocky-footer">RockyAIv2-0 • AI-powered learning workspace</div>',
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
# ROCKYAI v1-9 — NEW CHAT WORKSPACE SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("# 🏔️ RockyAIv2-0")
    st.caption("AI powered personal workspace")
    role_label = "Administrator" if st.session_state.role == "admin" else "User"
    st.markdown(f"**{html.escape(st.session_state.username)}** — **{role_label}**")
    st.divider()

    def v19_nav(label, target):
        active = st.session_state.v18_page == target
        if st.button(("● " if active else "") + label,
                     key="v19_nav_" + re.sub(r"[^A-Za-z0-9]", "_", label),
                     use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.v18_page = target
            st.rerun()

    v19_nav("⏰ Scheduled", "⏰ Scheduled")
    v19_nav("🧩 Plugins", "🧩 Plugins")
    v19_nav("📁 Project", "📁 Project")
    v19_nav("💻 Coder", "💻 Coder")
    v19_nav("📊 Data Science", "📊 Data Science")
    v19_nav("🧠 NLP Studio", "🧠 NLP Studio")

    with st.expander("… More", expanded=False):
        v19_nav("📚 Study Tools", "📚 Study Tools")
        v19_nav("📦 File Studio", "📦 File Studio")
        v19_nav("🕘 History", "🕘 History")
        v19_nav("📊 Analytics", "📊 Analytics")
        if st.session_state.role == "admin":
            v19_nav("🛡️ Admin Panel", "🛡️ Admin Panel")

    st.divider()
    st.markdown("### 📌 Pinned Chat")
    pinned = [x for x in st.session_state.v18_pinned_chats if x in st.session_state.v17_chats]
    st.session_state.v18_pinned_chats = pinned
    if pinned:
        for idx, name in enumerate(pinned):
            c1, c2, c3 = st.columns([5, 1, 1])
            suffix = hashlib.md5(name.encode()).hexdigest()[:8]
            with c1:
                if st.button("📌 " + name, key=f"v19_pin_open_{idx}_{suffix}", use_container_width=True):
                    st.session_state.v17_active_chat = name
                    st.session_state.v18_page = "🏠 Workspace"
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"v19_pin_del_{idx}_{suffix}", help="Delete this chat"):
                    st.session_state.v18_delete_confirm = name
                    st.rerun()
            with c3:
                if st.button("↩️", key=f"v19_unpin_{idx}_{suffix}", help="Unpin chat"):
                    st.session_state.v18_pinned_chats.remove(name)
                    st.rerun()
    else:
        st.caption("No pinned chats")

    st.markdown("### 🕘 Recent Chat")
    recent = [x for x in st.session_state.v17_chats.keys() if x not in st.session_state.v18_pinned_chats]
    if recent:
        for idx, name in enumerate(recent[-12:][::-1]):
            c1, c2, c3 = st.columns([5, 1, 1])
            suffix = hashlib.md5(name.encode()).hexdigest()[:8]
            with c1:
                if st.button(("● " if name == st.session_state.v17_active_chat else "") + name,
                             key=f"v19_recent_open_{idx}_{suffix}", use_container_width=True):
                    st.session_state.v17_active_chat = name
                    st.session_state.v18_page = "🏠 Workspace"
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"v19_recent_del_{idx}_{suffix}", help="Delete this chat"):
                    st.session_state.v18_delete_confirm = name
                    st.rerun()
            with c3:
                if st.button("📌", key=f"v19_pin_add_{idx}_{suffix}", help="Pin chat"):
                    if name not in st.session_state.v18_pinned_chats:
                        st.session_state.v18_pinned_chats.append(name)
                    st.rerun()
    else:
        st.caption("No recent chats")

    st.divider()
    if st.button("✚ New Chat", type="primary", use_container_width=True, key="v19_new_chat_sidebar"):
        v17_new_chat()
        st.session_state.v18_page = "🏠 Workspace"
        st.rerun()

    if st.session_state.v18_delete_confirm:
        delete_name = st.session_state.v18_delete_confirm
        st.warning(f"Delete **{delete_name}** permanently from this session?")
        d1, d2 = st.columns(2)
        with d1:
            if st.button("Delete", type="primary", use_container_width=True, key="v19_confirm_delete"):
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
            if st.button("Cancel", use_container_width=True, key="v19_cancel_delete"):
                st.session_state.v18_delete_confirm = None
                st.rerun()

    if st.button("🚪 Logout", use_container_width=True, key="v19_logout"):
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


def v19_extension_prompts():
    return {
        "🎓 AI Tutor": "Act as my personal tutor. Teach my topic step by step, adapt to my level, ask practice questions and explain mistakes.",
        "🧩 Question Solver": "Solve the question I provide step by step. Explain the reasoning clearly and give the final answer.",
        "📖 PDF Study": "Study the attached PDF or document and answer questions from it using the source as the primary basis.",
        "📄 PDF Generator": "Create a polished PDF document for my request and prepare it as a downloadable PDF.",
        "📝 Quiz Generator": "Create a quiz on my requested topic with answers and explanations.",
        "📚 Sample Paper": "Create a complete sample paper with marks, sections, difficulty balance and answer key.",
        "💻 Code Generator": "Act as my coding assistant. Write complete, correct, copy-paste-ready code and debug it when needed.",
        "🧠 Mind Map": "Create a clear hierarchical text mind map followed by key takeaways.",
        "🃏 Flashcards": "Create revision flashcards with concise questions and answers.",
        "📅 Study Planner": "Create a realistic study plan with daily tasks, revision and progress checkpoints.",
        "✂️ Smart Summarizer": "Summarize my supplied material into clear notes while preserving important facts.",
        "🌐 Translator": "Translate the material I provide accurately and naturally while preserving structure and meaning.",
        "💡 Brainstorm": "Brainstorm practical, creative ideas for my topic and organize them into useful next steps.",
        "🎯 Exam Preparation": "Create an exam-preparation strategy with topics, revision schedule, practice and a final checklist.",
        "🧪 Periodic Table": "Help me study the periodic table, including names, symbols, atomic numbers, groups, periods and trends.",
        "🏆 Daily Challenge": "Give me a daily learning challenge with a question, hint, answer and follow-up task.",
        "🗣️ Debate Coach": "Coach me for a debate by building both sides, arguments, evidence needs and rebuttals.",
        "🎤 Interview Coach": "Run a realistic interview practice and give constructive feedback on my answers.",
        "🧭 Career Roadmap": "Create a career roadmap based on my interests, current level, skills and next steps.",
        "🚀 Project Builder": "Turn my project idea into requirements, architecture, milestones, tasks, code and documentation.",
        "📊 Presentation Maker": "Create slide-by-slide presentation content with speaker notes and a clear structure.",
        "🧠 Memory Trainer": "Create an active-recall memory workout using mnemonics, chunking and retrieval practice.",
        "🎯 Goal Coach": "Turn my goal into measurable milestones, weekly actions and progress checks.",
        "📘 Vocabulary Builder": "Build a vocabulary lesson with meanings, examples, memory clues and a short test.",
        "🔍 Fact Checker": "Analyze my claim carefully, separate established facts from uncertainty, and explain what needs verification.",
        "📄 DOCX": "Create a professional DOCX document from my request and make it downloadable.",
        "📊 XLSX": "Create a structured XLSX spreadsheet from my request and make it downloadable.",
        "📽️ PPTX": "Create a PPTX presentation from my request and make it downloadable.",
        "📃 TXT / CSV": "Create the requested TXT or CSV file and make it downloadable.",
        "📝 Markdown": "Create a clean Markdown document from my request and make it downloadable.",
        "🌐 HTML / CSS": "Create clean HTML/CSS for my request and make the requested files downloadable.",
        "⚙️ JavaScript": "Create complete JavaScript code for my request, ready to copy and use.",
        "🐍 Python": "Create complete Python code for my request, ready to copy and run.",
        "☕ Java": "Create complete Java code for my request, ready to compile.",
        "🔧 C / C++": "Create complete C or C++ code for my request, ready to compile.",
        "🤖 Arduino": "Create complete Arduino code for my hardware/project request, including clear setup guidance.",
        "🗄️ SQL": "Create SQL queries or database scripts for my request.",
        "🧾 JSON / XML / YAML": "Create valid structured JSON, XML or YAML for my request.",
        "📦 RTF / Text": "Create a clean RTF or text document from my request and make it downloadable.",
    }


def v19_extensions_panel():
    tools = v19_extension_prompts()
    st.markdown("<div class='v19-extension-panel'><div class='v19-extension-title'>Extensions</div><div class='v19-extension-sub'>Choose a RockyAI capability. Everything runs inside this chat.</div></div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (label, prompt) in enumerate(tools.items()):
        with cols[i % 4]:
            if st.button(label, use_container_width=True, key=f"v19_ext_{i}"):
                st.session_state.v18_prefill = prompt
                st.session_state.v19_active_extension = label
                st.session_state.v19_extensions_open = False
                st.rerun()


def _slash_command(prompt):
    p = prompt.strip()
    if not p.startswith('/'):
        return p, ''
    cmd, _, rest = p[1:].partition(' ')
    shortcuts = {'code':'CODE','python':'CODE_PYTHON','javascript':'CODE_JAVASCRIPT','js':'CODE_JAVASCRIPT','java':'CODE_JAVA','cpp':'CODE_CPP','c++':'CODE_CPP','arduino':'CODE_ARDUINO','mindmap':'MINDMAP','quiz':'QUIZ','summary':'SUMMARY','summarize':'SUMMARY','flashcards':'FLASHCARDS','translate':'TRANSLATE','explain':'EXPLAIN','study':'STUDY','pdf':'PDF'}
    return rest.strip(), shortcuts.get(cmd.lower().strip(), '')


def _render_code_block(code, language='text', block_index=0):
    lang=(language or 'text').strip().lower()
    ext={'python':'.py','py':'.py','javascript':'.js','js':'.js','java':'.java','cpp':'.cpp','c++':'.cpp','c':'.c','arduino':'.ino','ino':'.ino','sql':'.sql','html':'.html','css':'.css','json':'.json','xml':'.xml','yaml':'.yaml','yml':'.yml','bash':'.sh','shell':'.sh','markdown':'.md','md':'.md','text':'.txt','txt':'.txt'}.get(lang,'.txt')
    c1,c2=st.columns([1,1])
    with c1: st.caption(f'Programming language: **{language or "Text"}**')
    with c2: st.download_button('⬇️ Download',data=code,file_name=f'RockyAI_code_{block_index}{ext}',mime='text/plain',key=f'code_dl_{hashlib.md5((code+str(block_index)).encode()).hexdigest()}',use_container_width=True)
    st.code(code,language=lang if lang!='text' else None)


def _render_mindmap(text, block_index=0):
    c1,c2=st.columns([1,1])
    with c1: st.caption('Mind map')
    with c2: st.download_button('⬇️ Download',data=text,file_name='RockyAI_mindmap.txt',mime='text/plain',key=f'mindmap_dl_{hashlib.md5((text+str(block_index)).encode()).hexdigest()}',use_container_width=True)
    st.code(text,language='text')


def _render_assistant_message(answer, prompt=''):
    if not answer: return
    pattern=re.compile(r'```([A-Za-z0-9_+#./-]*)\s*\n?(.*?)```',re.S)
    pos=0; found=False; idx=0
    for m in pattern.finditer(answer):
        found=True
        before=answer[pos:m.start()].strip()
        if before: st.markdown(before)
        _render_code_block(m.group(2).strip('\n'),m.group(1).strip() or 'text',idx)
        idx+=1; pos=m.end()
    tail=answer[pos:].strip()
    if tail:
        if ('Main topic--|' in tail or 'Main topic --|' in tail) and '```' not in tail: _render_mindmap(tail,idx)
        else: st.markdown(tail)
    if not found and not tail and answer.strip(): st.markdown(answer)


def _v19_render_message(role, msg):
    avatar = "👤" if role == "user" else "🏔️"
    who = "You" if role == "user" else "RockyAI"
    cls = "v19-message v19-user" if role == "user" else "v19-message"
    safe = html.escape(str(msg)).replace("\n", "<br>")
    st.markdown(
        f"<div class='{cls}'><div class='v19-avatar'>{avatar}</div><div class='v19-message-body'><div class='v19-who'>{who}</div><div>{safe}</div></div></div>",
        unsafe_allow_html=True,
    )


def v19_chat_ui():
    name=st.session_state.v17_active_chat
    messages=st.session_state.v17_chats[name]
    st.markdown(f"<div class='v19-topbar'><div><div class='v19-brand'>🏔️ RockyAIv2-0</div><div class='v19-sub'>AI powered personal workspace</div></div><div class='v19-status'><span></span> Online</div></div>",unsafe_allow_html=True)
    if not messages:
        st.markdown("<div class='v19-welcome'><div class='v19-big-logo'>🏔️️</div><div class='v19-kicker'>YOUR PERSONAL AI WORKSPACE</div><h1>What are we building today?</h1><p>Ask anything, study, code, work with files, create documents, plan projects or use any RockyAI extension — all from one conversation.</p></div>",unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='v19-chat-title'><span>🏔️</span><strong>{html.escape(name)}</strong><small>Unified conversation</small></div>",unsafe_allow_html=True)
    for role,msg in messages:
        avatar='👤' if role=='user' else '🏔️'; who='You' if role=='user' else 'RockyAI'; cls='v19-message v19-user' if role=='user' else 'v19-message'
        st.markdown(f"<div class='{cls}'><div class='v19-avatar'>{avatar}</div><div class='v19-message-body'><div class='v19-who'>{who}</div>",unsafe_allow_html=True)
        _render_assistant_message(msg) if role=='assistant' else st.markdown(msg)
        st.markdown('</div></div>',unsafe_allow_html=True)
    if st.session_state.v19_extensions_open:
        st.markdown("<style>.st-key-v19_plus_wrap button{transform:rotate(45deg)!important;background:linear-gradient(135deg,#ef233c,#b7092b)!important}</style>",unsafe_allow_html=True)
    with st.container(key='v19_plus_wrap'):
        if st.button('＋',key='v19_plus_button',help='Open RockyAI extensions'):
            st.session_state.v19_extensions_open=not st.session_state.v19_extensions_open; st.rerun()
    if st.session_state.v19_extensions_open:
        st.markdown("<div class='v19-menu-row'><b>Extensions</b><span>Optional shortcuts — normal chat works without them.</span></div>",unsafe_allow_html=True)
        if st.button('📎 Attachments',key='v19_show_attachments',use_container_width=True):
            st.session_state.v19_attachment_open=not st.session_state.v19_attachment_open; st.rerun()
        if st.session_state.v19_attachment_open: v19_extensions_panel()
        if st.button('📁 Add File',key='v19_add_file',use_container_width=True):
            st.session_state.v19_attachment_open=True; st.session_state.v19_extensions_open=True; st.rerun()
    if st.session_state.v19_attachment_open: attachment_uploader()
    attached=st.session_state.get('rockyai_attachments',[])
    if attached:
        labels=' • '.join(html.escape(x['name']) for x in attached)
        st.markdown(f"<div class='attachment-strip'><b>📎 Ready for this chat:</b> {labels}<br><span class='small-muted'>Ask naturally — you do not need to describe the file first.</span></div>",unsafe_allow_html=True)
    prefill=st.session_state.pop('v18_prefill','')
    prompt=st.chat_input('Message RockyAI…',key='v19_input')
    if prefill and not prompt: prompt=prefill
    if prompt and prompt.strip():
        original=prompt.strip(); prompt,shortcut=_slash_command(original); prompt=prompt or original
        messages.append(('user',original))

        _v19_render_message('user', original)
        if name.startswith('New chat') and len(messages)==1:
            title=re.sub(r'\s+',' ',prompt)[:45].strip() or name
            if title!=name:
                st.session_state.v17_chats[title]=st.session_state.v17_chats.pop(name)
                st.session_state.v18_pinned_chats=[title if x==name else x for x in st.session_state.v18_pinned_chats]
                st.session_state.v17_active_chat=title; name=title; messages=st.session_state.v17_chats[name]
        shortcut_instruction=''
        if shortcut=='CODE': shortcut_instruction='Return complete code in exactly one fenced code block with the programming language identifier. Infer the language if possible.'
        elif shortcut.startswith('CODE_'):
            language=shortcut.replace('CODE_','').lower(); language={'cpp':'C++','javascript':'JavaScript','arduino':'Arduino','python':'Python','java':'Java'}.get(language,language)
            shortcut_instruction=f'Use programming language {language}. Return complete copy-paste-ready code in exactly one fenced code block tagged {language.lower()}.'
        elif shortcut=='MINDMAP': shortcut_instruction='Create a monospaced text mind map using exactly this style: Main topic--|\n            |-{Topic one}\n            |  ├─ {Subtopic}: {description}\n            |  └─ {Subtopic}: {description}\n            |-{Topic two}\n            |  ├─ {Subtopic}: {description}. Do not use Mermaid.'
        elif shortcut=='QUIZ': shortcut_instruction='Create a complete quiz with answers and explanations.'
        elif shortcut=='SUMMARY': shortcut_instruction='Summarize the supplied material; if an attachment exists, use it as the primary source.'
        elif shortcut=='FLASHCARDS': shortcut_instruction='Create concise question/answer flashcards from the topic or attachment.'
        elif shortcut=='TRANSLATE': shortcut_instruction='Translate the supplied text naturally while preserving structure and meaning.'
        elif shortcut=='EXPLAIN': shortcut_instruction='Explain the requested topic clearly at the user level.'
        elif shortcut=='STUDY': shortcut_instruction='Act as a study tutor and build an appropriate lesson and practice sequence.'
        instruction="""You are RockyAIv2-0, a unified all-in-one personal AI workspace chatbot powered by Gemini, with RockyCore Data Science/NLP tools.
Normal natural-language conversation is always supported. Do NOT require a slash command and do NOT require the user to describe an attachment before using it.
If files are attached, treat them as available context. When the user says 'this', 'the PDF', 'the file', 'the document', 'it', 'page 3', etc., use the attached material when it supports the request. Do not invent source-specific facts.
If the user asks for code, provide complete copy-paste-ready code in a fenced code block with a language identifier.
If the user asks for a mind map, use this branch style and do not use Mermaid:
Main topic--|
            |-{Topic one}
            |  ├─ {Subtopic}: {description}
            |  └─ {Subtopic}: {description}
            |-{Topic two}
            |  ├─ {Subtopic}: {description}
All capabilities can be requested directly in normal language. Slash commands are optional shortcuts only."""
        if shortcut_instruction: instruction+='\nOPTIONAL SHORTCUT INSTRUCTION:\n'+shortcut_instruction
        with st.spinner('RockyAI is thinking…'):
            answer=ask_rockyai(prompt,instruction)
        messages.append(('assistant',answer)); save_chat('Unified Chat',original,answer); st.rerun()
    if messages:
        last_user=next((m for r,m in reversed(messages) if r=='user'),''); last_answer=next((m for r,m in reversed(messages) if r=='assistant'),'')
        if last_answer: v18_make_download(last_answer,last_user)

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
    st.caption(f"Gemini-powered chat with RockyCore Data Science/NLP tools. Model: {GEMINI_MODEL}.")
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
    v19_chat_ui()

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
# ROCKYAI v2-0 — CUSTOM DATA SCIENCE ENGINE
# ============================================================

def _numeric_columns(df):
    return df.select_dtypes(include=np.number).columns.tolist()


def _clean_dataframe(df):
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].apply(lambda x: x.strip() if isinstance(x, str) else x)
    return out


def _fig_download(fig, name):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    buf.seek(0)
    st.download_button("⬇️ Download chart", buf, file_name=name, mime="image/png", key="dl_" + name)


def data_science_page():
    st.markdown("# 📊 RockyAI Data Science")
    st.caption("A local Data Science engine for datasets, statistics, machine learning and visual analytics.")

    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"], key="ds_upload")
    if not uploaded:
        st.info("Upload a CSV/Excel file to start. No external AI service is required for the analysis engine.")
        st.markdown("### Included modules")
        st.write("EDA • cleaning • missing values • outliers • statistics • correlation • charts • regression • classification • clustering • PCA • export")
        return

    try:
        if uploaded.name.lower().endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
        df = _clean_dataframe(df)
    except Exception as e:
        st.error(f"Could not read the dataset: {e}")
        return

    st.session_state["rocky_ds_df"] = df
    st.success(f"Loaded {len(df):,} rows × {len(df.columns):,} columns")

    tabs = st.tabs(["🔎 Overview", "🧹 Clean", "📈 Statistics", "📊 Visualize", "🤖 ML", "🧩 Clustering", "⬇️ Export"])
    nums = _numeric_columns(df)

    with tabs[0]:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Rows", f"{len(df):,}")
        c2.metric("Columns", f"{len(df.columns):,}")
        c3.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")
        c4.metric("Duplicates", f"{int(df.duplicated().sum()):,}")
        st.dataframe(df.head(100), use_container_width=True)
        st.markdown("#### Column profile")
        profile = pd.DataFrame({"column":df.columns,"dtype":[str(x) for x in df.dtypes],"missing":df.isna().sum().values,"unique":df.nunique().values})
        st.dataframe(profile, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.markdown("#### Missing values")
        missing = df.isna().sum().sort_values(ascending=False)
        st.dataframe(missing[missing>0].rename("missing").to_frame(), use_container_width=True)
        numeric_fill = st.selectbox("Numeric missing-value strategy", ["Keep", "Mean", "Median", "Zero"])
        categorical_fill = st.selectbox("Text missing-value strategy", ["Keep", "Mode", "Unknown"])
        drop_duplicates = st.checkbox("Remove duplicate rows")
        if st.button("🧹 Apply cleaning", type="primary"):
            cleaned = df.copy()
            for c in cleaned.columns:
                if pd.api.types.is_numeric_dtype(cleaned[c]):
                    if numeric_fill == "Mean": cleaned[c] = cleaned[c].fillna(cleaned[c].mean())
                    elif numeric_fill == "Median": cleaned[c] = cleaned[c].fillna(cleaned[c].median())
                    elif numeric_fill == "Zero": cleaned[c] = cleaned[c].fillna(0)
                elif categorical_fill == "Mode" and not cleaned[c].mode().empty:
                    cleaned[c] = cleaned[c].fillna(cleaned[c].mode().iloc[0])
                elif categorical_fill == "Unknown": cleaned[c] = cleaned[c].fillna("Unknown")
            if drop_duplicates: cleaned = cleaned.drop_duplicates()
            st.session_state["rocky_ds_df"] = cleaned
            st.success("Cleaning applied. Reload this page selection if you want to analyze the updated dataframe.")
            st.dataframe(cleaned.head(50), use_container_width=True)

        if nums:
            c = st.selectbox("Outlier column", nums, key="out_col")
            q1,q3 = df[c].quantile([.25,.75]); iqr=q3-q1
            lo,hi=q1-1.5*iqr,q3+1.5*iqr
            out=df[(df[c]<lo)|(df[c]>hi)]
            st.write(f"IQR bounds: **{lo:.4g}** to **{hi:.4g}** • outliers: **{len(out):,}**")
            if len(out): st.dataframe(out.head(100), use_container_width=True)

    with tabs[2]:
        if not nums: st.warning("No numeric columns found.")
        else:
            st.dataframe(df[nums].describe().T, use_container_width=True)
            corr=df[nums].corr()
            st.markdown("#### Correlation matrix")
            st.dataframe(corr, use_container_width=True)
            st.markdown("#### Strongest correlations")
            pairs=[]
            for i,a in enumerate(nums):
                for b in nums[i+1:]: pairs.append((a,b,corr.loc[a,b]))
            pairs=sorted(pairs,key=lambda x:abs(x[2]),reverse=True)[:10]
            for a,b,v in pairs: st.write(f"**{a} ↔ {b}**: {v:.3f}")

    with tabs[3]:
        if not nums:
            st.warning("No numeric columns found.")
        else:
            chart_type = st.selectbox("Chart type", ["Scatter", "Histogram", "Line", "Box", "Correlation Heatmap"])
            x_col = st.selectbox("X column", df.columns, key="ds_x")
            y_col = st.selectbox("Y column", nums, key="ds_y")
            fig, ax = plt.subplots(figsize=(8, 5))
            if chart_type == "Scatter":
                ax.scatter(df[x_col], df[y_col], alpha=0.7, color="#ef233c")
                ax.set_xlabel(x_col); ax.set_ylabel(y_col)
            elif chart_type == "Histogram":
                ax.hist(df[y_col].dropna(), bins=20, color="#ef233c", edgecolor="black")
                ax.set_xlabel(y_col)
            elif chart_type == "Line":
                ax.plot(df[x_col], df[y_col], color="#ef233c")
                ax.set_xlabel(x_col); ax.set_ylabel(y_col)
            elif chart_type == "Box":
                ax.boxplot(df[y_col].dropna())
                ax.set_ylabel(y_col)
            elif chart_type == "Correlation Heatmap":
                fig, ax = plt.subplots(figsize=(6, 6))
                cax = ax.matshow(df[nums].corr(), cmap="coolwarm")
                fig.colorbar(cax)
                ax.set_xticks(range(len(nums)))
                ax.set_yticks(range(len(nums)))
                ax.set_xticklabels(nums, rotation=90)
                ax.set_yticklabels(nums)
            st.pyplot(fig)
            _fig_download(fig, "rockyai_chart.png")

    with tabs[4]:
        st.markdown("#### Machine Learning Models")
        ml_type = st.selectbox("Task type", ["Regression", "Classification"])
        target_col = st.selectbox("Target column", df.columns, key="ml_target")
        feature_cols = st.multiselect("Feature columns", [c for c in nums if c != target_col], default=[c for c in nums if c != target_col][:3])
        if st.button("🚀 Train Model", type="primary"):
            if not feature_cols:
                st.warning("Select at least one feature column.")
            else:
                try:
                    X = df[feature_cols].dropna()
                    y = df.loc[X.index, target_col]
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                    if ml_type == "Regression":
                        model = LinearRegression()
                        model.fit(X_train, y_train)
                        preds = model.predict(X_test)
                        mse = mean_squared_error(y_test, preds)
                        r2 = r2_score(y_test, preds)
                        st.success(f"Model trained successfully! • MSE: `{mse:.4f}` • R²: `{r2:.4f}`")
                        st.write("Coefficients:", dict(zip(feature_cols, model.coef_)))
                    else:
                        model = LogisticRegression(max_iter=1000)
                        model.fit(X_train, y_train)
                        preds = model.predict(X_test)
                        acc = accuracy_score(y_test, preds)
                        st.success(f"Model trained successfully! • Accuracy: `{acc:.4f}`")
                        st.text(classification_report(y_test, preds))
                except Exception as e:
                    st.error(f"Training failed: {e}")

    with tabs[5]:
        st.markdown("#### K-Means Clustering")
        cluster_features = st.multiselect("Clustering features (numeric)", nums, default=nums[:2] if len(nums)>=2 else nums)
        k = st.slider("Clusters (K)", 2, 8, 3)
        if st.button("🧩 Run Clustering", type="primary"):
            if len(cluster_features) < 2:
                st.warning("Select at least 2 numeric features.")
            else:
                try:
                    sub = df[cluster_features].dropna()
                    scaler = StandardScaler()
                    scaled = scaler.fit_transform(sub)
                    kmeans = KMeans(n_init=10, n_clusters=k, random_state=42)
                    labels = kmeans.fit_predict(scaled)
                    sub["Cluster"] = labels
                    st.success(f"Clustering complete with {k} clusters.")
                    st.dataframe(sub.head(100), use_container_width=True)
                    fig, ax = plt.subplots(figsize=(8, 5))
                    scatter = ax.scatter(sub.iloc[:, 0], sub.iloc[:, 1], c=labels, cmap="viridis", alpha=0.8)
                    ax.set_xlabel(cluster_features[0])
                    ax.set_ylabel(cluster_features[1])
                    fig.colorbar(scatter)
                    st.pyplot(fig)
                    _fig_download(fig, "clusters.png")
                except Exception as e:
                    st.error(f"Clustering failed: {e}")

    with tabs[6]:
        st.markdown("#### Export Cleaned Dataset")
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv_data, file_name="rockyai_cleaned_dataset.csv", mime="text/csv", use_container_width=True)
