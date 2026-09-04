import streamlit as st
from google import genai
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
import PyPDF2
import json
import os
import io
import html

from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors


# ============================================================
# ROCKYAI v1-3
# AI-POWERED LEARNING WORKSPACE
# ============================================================


# ============================================================
# 1. STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="RockyAI v1-3",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.stApp {

    background:
        radial-gradient(
            circle at top left,
            #14213d 0%,
            #070b14 42%,
            #03050a 100%
        );

    color: #f8fafc;
}


/* SIDEBAR */

[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            #07101f,
            #030712
        );

    border-right:
        1px solid
        rgba(99,216,255,0.12);
}


/* LOGO */

.rocky-logo {

    font-size: 34px;

    font-weight: 900;

    background:
        linear-gradient(
            90deg,
            #62e6ff,
            #7c8cff
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

    margin-bottom: 5px;
}


.rocky-version {

    color: #63d8ff;

    font-size: 13px;

    font-weight: 700;

    letter-spacing: 1px;
}


.rocky-subtitle {

    color: #94a3b8;

    font-size: 14px;

    margin-bottom: 25px;
}


/* HERO */

.hero {

    padding: 30px;

    border-radius: 22px;

    background:
        linear-gradient(
            135deg,
            rgba(15,23,42,0.95),
            rgba(8,15,30,0.85)
        );

    border:
        1px solid
        rgba(99,216,255,0.15);

    margin-bottom: 25px;

    box-shadow:
        0 20px 60px
        rgba(0,0,0,0.25);
}


.hero h1 {

    font-size:
        clamp(
            30px,
            5vw,
            46px
        );

    margin:
        5px 0 8px;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #63d8ff
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;
}


.hero p {

    color: #94a3b8;

    font-size: 16px;
}


/* FEATURE CARDS */

.feature-card {

    padding: 20px;

    border-radius: 17px;

    background:
        rgba(
            15,
            23,
            42,
            0.82
        );

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.07
        );

    min-height: 145px;

    transition: 0.2s;
}


.feature-icon {

    font-size: 28px;
}


.feature-title {

    font-size: 17px;

    font-weight: 800;

    margin-top: 8px;
}


.feature-text {

    color: #94a3b8;

    font-size: 13px;

    margin-top: 5px;
}


/* OUTPUT */

.output-box {

    padding: 22px;

    border-radius: 17px;

    background: #050a13;

    border:
        1px solid
        #1e293b;

    margin-top: 20px;

    line-height: 1.7;
}


/* PDF */

.pdf-ready {

    padding: 25px;

    border-radius: 18px;

    background:
        rgba(
            99,
            216,
            255,
            0.05
        );

    border:
        1px solid
        rgba(
            99,
            216,
            255,
            0.25
        );
}


/* STATUS */

.online {

    color: #4ade80;

    font-weight: 700;
}


/* FOOTER */

.footer {

    text-align: center;

    color: #64748b;

    padding: 35px;

    font-size: 12px;
}


/* BUTTON */

.stButton > button {

    border-radius: 12px;

    font-weight: 700;
}


/* FILE UPLOADER */

[data-testid="stFileUploader"] {

    border-radius: 14px;
}


/* MOBILE */

@media(max-width: 700px) {

    .hero {

        padding: 22px;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. DATABASE
# ============================================================

DB_FILE = os.environ.get(
    "DB_FILE",
    "rockyai_v1_3.db"
)


def get_db():

    conn = sqlite3.connect(
        DB_FILE
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            username TEXT PRIMARY KEY,

            password_hash TEXT NOT NULL,

            role TEXT DEFAULT 'user',

            prompts_count INTEGER DEFAULT 0,

            created_at TEXT

        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL,

            tool TEXT,

            prompt TEXT,

            response TEXT,

            timestamp TEXT

        )
    """)


    conn.commit()

    conn.close()


init_db()


# ============================================================
# 4. ADMIN ACCOUNT
# ============================================================

def create_admin():

    username = os.environ.get(
        "ADMIN_USERNAME"
    )

    password = os.environ.get(
        "ADMIN_PASSWORD"
    )


    if not username or not password:

        return


    conn = get_db()


    existing = conn.execute(
        """
        SELECT username
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    if not existing:

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
            VALUES (?, ?, 'admin', 0, ?)
            """,
            (
                username,
                generate_password_hash(
                    password
                ),
                datetime.now().isoformat()
            )
        )

        conn.commit()


    conn.close()


create_admin()


# ============================================================
# 5. GEMINI
# ============================================================

API_KEY = os.environ.get(
    "GEMINI_API_KEY"
)


if API_KEY:

    client = genai.Client(
        api_key=API_KEY
    )

else:

    client = None


def ask_gemini(prompt):

    if not client:

        return (
            "⚠️ Gemini API is not configured.\n\n"
            "Please add GEMINI_API_KEY "
            "to your Render Environment Variables."
        )


    try:

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt

        )


        if response and response.text:

            return response.text.strip()


        return (
            "RockyAI did not receive a response."
        )


    except Exception:

        return (
            "⚠️ RockyAI could not process "
            "your request right now."
        )


# ============================================================
# 6. LOGIN
# ============================================================

def login_user(
    username,
    password
):

    conn = get_db()


    user = conn.execute(
        """
        SELECT
            username,
            password_hash,
            role
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    conn.close()


    if not user:

        return None


    if check_password_hash(
        user["password_hash"],
        password
    ):

        return {

            "username": user["username"],

            "role": user["role"]

        }


    return None


# ============================================================
# 7. SAVE CHAT
# ============================================================

def save_chat(
    username,
    tool,
    prompt,
    response
):

    conn = get_db()


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
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username,
            tool,
            prompt,
            response,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        )
    )


    conn.execute(
        """
        UPDATE users

        SET prompts_count =
            prompts_count + 1

        WHERE username = ?
        """,
        (username,)
    )


    conn.commit()

    conn.close()


# ============================================================
# 8. PDF GENERATOR
# ============================================================

def create_pdf(
    title,
    content
):

    buffer = io.BytesIO()


    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(

        "RockyTitle",

        parent=styles["Title"],

        fontName="Helvetica-Bold",

        fontSize=22,

        leading=28,

        alignment=TA_CENTER,

        spaceAfter=20,

        textColor=colors.HexColor(
            "#145A7A"
        )
    )


    heading_style = ParagraphStyle(

        "RockyHeading",

        parent=styles["Heading2"],

        fontName="Helvetica-Bold",

        fontSize=15,

        leading=20,

        spaceBefore=12,

        spaceAfter=8,

        textColor=colors.HexColor(
            "#145A7A"
        )
    )


    body_style = ParagraphStyle(

        "RockyBody",

        parent=styles["BodyText"],

        fontName="Helvetica",

        fontSize=10.5,

        leading=16,

        spaceAfter=8
    )


    bullet_style = ParagraphStyle(

        "RockyBullet",

        parent=body_style,

        leftIndent=18,

        firstLineIndent=-8,

        spaceAfter=5
    )


    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=45,

        leftMargin=45,

        topMargin=50,

        bottomMargin=50
    )


    story = []


    story.append(
        Paragraph(
            "ROCKYAI v1-3",
            title_style
        )
    )


    story.append(
        Paragraph(
            html.escape(
                title
            ),
            heading_style
        )
    )


    story.append(
        Spacer(
            1,
            10
        )
    )


    for raw_line in content.split(
        "\n"
    ):

        line = raw_line.strip()


        if not line:

            story.append(
                Spacer(
                    1,
                    5
                )
            )

            continue


        if line.startswith(
            "###"
        ):

            text = line.replace(
                "###",
                "",
                1
            ).strip()


            story.append(
                Paragraph(
                    html.escape(text),
                    heading_style
                )
            )


        elif line.startswith(
            "##"
        ):

            text = line.replace(
                "##",
                "",
                1
            ).strip()


            story.append(
                Paragraph(
                    html.escape(text),
                    heading_style
                )
            )


        elif line.startswith(
            "#"
        ):

            text = line.replace(
                "#",
                "",
                1
            ).strip()


            story.append(
                Paragraph(
                    html.escape(text),
                    heading_style
                )
            )


        elif (
            line.startswith("-")
            or line.startswith("*")
        ):

            text = line[1:].strip()


            story.append(
                Paragraph(
                    "• " + html.escape(text),
                    bullet_style
                )
            )


        else:

            story.append(
                Paragraph(
                    html.escape(line),
                    body_style
                )
            )


    story.append(
        Spacer(
            1,
            20
        )
    )


    story.append(
        Paragraph(
            "Generated by RockyAI v1-3",
            ParagraphStyle(
                "Footer",
                parent=body_style,
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
        )
    )


    document.build(
        story
    )


    buffer.seek(0)

    return buffer


# ============================================================
# 9. LOGIN PAGE
# ============================================================

def login_page():

    st.markdown(
        """
        <div class="hero">

            <div class="rocky-logo">
                ROCKYAI
            </div>

            <div class="rocky-version">
                VERSION 1-3
            </div>

            <h1>
                Your AI Learning Workspace 🚀
            </h1>

            <p>
                Learn • Practice • Create • Understand
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    login_tab, register_tab = st.tabs(
        [
            "🔐 Login",
            "✨ Create Account"
        ]
    )


    # ========================================================
    # LOGIN
    # ========================================================

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
            "🚀 Sign In",
            use_container_width=True
        ):

            user = login_user(
                username.strip(),
                password
            )


            if user:

                st.session_state.logged_in = True

                st.session_state.username = (
                    user["username"]
                )

                st.session_state.role = (
                    user["role"]
                )

                st.rerun()


            else:

                st.error(
                    "Invalid username or password."
                )


    # ========================================================
    # REGISTER
    # ========================================================

    with register_tab:

        username = st.text_input(
            "New username",
            key="register_username"
        )


        password = st.text_input(
            "New password",
            type="password",
            key="register_password"
        )


        confirm = st.text_input(
            "Confirm password",
            type="password",
            key="register_confirm"
        )


        if st.button(
            "✨ Create Account",
            use_container_width=True
        ):

            username = username.strip()


            if len(username) < 3:

                st.error(
                    "Username must contain "
                    "at least 3 characters."
                )


            elif len(password) < 8:

                st.error(
                    "Password must contain "
                    "at least 8 characters."
                )


            elif password != confirm:

                st.error(
                    "Passwords do not match."
                )


            else:

                conn = get_db()


                try:

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
                        VALUES
                        (?, ?, 'user', 0, ?)
                        """,
                        (
                            username,
                            generate_password_hash(
                                password
                            ),
                            datetime.now().isoformat()
                        )
                    )


                    conn.commit()


                    st.success(
                        "Account created successfully!"
                    )


                except sqlite3.IntegrityError:

                    st.error(
                        "That username already exists."
                    )


                finally:

                    conn.close()


# ============================================================
# 10. SIDEBAR
# ============================================================

def show_sidebar():

    with st.sidebar:

        st.markdown(
            '<div class="rocky-logo">'
            'ROCKYAI'
            '</div>',
            unsafe_allow_html=True
        )


        st.markdown(
            '<div class="rocky-version">'
            'VERSION 1-3'
            '</div>',
            unsafe_allow_html=True
        )


        st.markdown(
            '<div class="rocky-subtitle">'
            'AI-Powered Learning Workspace'
            '</div>',
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            👤 **{st.session_state.username}**

            <span class="online">
            ● Online
            </span>
            """,
            unsafe_allow_html=True
        )


        st.divider()


        page = st.radio(

            "Navigation",

            [
                "🏠 Workspace",
                "💬 History",
                "📊 Analytics"
            ]

        )


        if st.session_state.role == "admin":

            st.divider()


            admin_option = st.radio(
                "Administration",
                ["👑 Admin Panel"]
            )


            if admin_option:

                if st.session_state.role == "admin":

                    page = admin_option


        st.divider()


        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.session_state.clear()

            st.rerun()


        return page


# ============================================================
# 11. WORKSPACE
# ============================================================

def workspace():

    conn = get_db()


    user = conn.execute(
        """
        SELECT prompts_count
        FROM users
        WHERE username = ?
        """,
        (st.session_state.username,)
    ).fetchone()


    conn.close()


    prompts_count = (
        user["prompts_count"]
        if user
        else 0
    )


    # ========================================================
    # HERO
    # ========================================================

    st.markdown(
        """
        <div class="hero">

            <div class="rocky-logo">
                ROCKYAI
            </div>

            <div class="rocky-version">
                VERSION 1-3
            </div>

            <h1>
                Your AI Learning Workspace 🚀
            </h1>

            <p>
                Learn. Create. Practice. Build.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # STATS
    # ========================================================

    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "AI Requests",
            prompts_count
        )


    with c2:

        st.metric(
            "AI Tools",
            "8"
        )


    with c3:

        st.metric(
            "PDF Generator",
            "ON"
        )


    with c4:

        st.metric(
            "Status",
            "🟢 Online"
        )


    st.divider()


    # ========================================================
    # FEATURES
    # ========================================================

    cards = [

        (
            "🤖",
            "Ask RockyAI",
            "Ask questions and get intelligent answers."
        ),

        (
            "📖",
            "PDF Study",
            "Upload study material and ask questions."
        ),

        (
            "📄",
            "PDF Generator",
            "Create printable AI documents."
        ),

        (
            "📝",
            "Quiz Generator",
            "Create practice questions."
        ),

        (
            "📚",
            "Sample Paper",
            "Generate exam papers."
        ),

        (
            "💻",
            "Code Generator",
            "Create programming solutions."
        ),

        (
            "🧠",
            "Mind Map",
            "Organize complex topics."
        ),

        (
            "🧪",
            "Science Tools",
            "Explore chemistry information."
        )

    ]


    cols = st.columns(4)


    for index, card in enumerate(cards):

        icon, title, description = card


        with cols[index % 4]:

            st.markdown(
                f"""
                <div class="feature-card">

                    <div class="feature-icon">
                        {icon}
                    </div>

                    <div class="feature-title">
                        {title}
                    </div>

                    <div class="feature-text">
                        {description}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


    st.write("")


    # ========================================================
    # TOOL SELECTOR
    # ========================================================

    st.markdown(
        "## 🛠️ RockyAI Workspace"
    )


    tool = st.selectbox(

        "Choose a tool",

        [
            "🤖 Ask RockyAI",
            "📖 PDF Study",
            "📄 PDF Generator",
            "📝 Quiz Generator",
            "📚 Sample Paper",
            "💻 Code Generator",
            "🧠 Mind Map",
            "🧪 Periodic Table"
        ]

    )


    # ========================================================
    # PDF UPLOAD
    # ========================================================

    uploaded_pdf = None


    if tool == "📖 PDF Study":

        uploaded_pdf = st.file_uploader(

            "📎 Upload your study PDF",

            type=["pdf"]

        )


    # ========================================================
    # USER INPUT
    # ========================================================

    query = st.text_area(

        "What do you want RockyAI to do?",

        height=150,

        placeholder=(
            "Example: Explain photosynthesis "
            "for a Class 7 student."
        )

    )


    # ========================================================
    # RUN
    # ========================================================

    if st.button(

        "🚀 Run RockyAI",

        type="primary",

        use_container_width=True

    ):

        if tool == "📖 PDF Study":

            if uploaded_pdf is None:

                st.warning(
                    "Please upload a PDF first."
                )

                return


        if not query.strip():

            st.warning(
                "Please enter a request."
            )

            return


        # ====================================================
        # ASK AI
        # ====================================================

        if tool == "🤖 Ask RockyAI":

            prompt = f"""

You are RockyAI v1-3,
an AI-powered learning assistant.

Answer the following request
clearly and accurately.

Use headings and bullet points
when helpful.

User request:

{query}

"""


            with st.spinner(
                "RockyAI is thinking..."
            ):

                result = ask_gemini(
                    prompt
                )


            save_chat(
                st.session_state.username,
                "Ask AI",
                query,
                result
            )


            st.markdown(
                "### 🤖 RockyAI"
            )


            st.markdown(
                f"""
                <div class="output-box">

                {result}

                </div>
                """,
                unsafe_allow_html=True
            )


        # ====================================================
        # PDF STUDY
        # ====================================================

        elif tool == "📖 PDF Study":

            try:

                reader = PyPDF2.PdfReader(
                    uploaded_pdf
                )


                text = ""


                for page in reader.pages:

                    text += (
                        page.extract_text()
                        or ""
                    )


                if not text.strip():

                    st.error(
                        "No readable text was found."
                    )

                    return


                prompt = f"""

You are RockyAI v1-3.

Answer the user's question
using the uploaded document.

If the answer cannot be found
in the document, say so clearly.

Question:

{query}

Document:

{text[:12000]}

"""


                with st.spinner(
                    "RockyAI is reading your PDF..."
                ):

                    result = ask_gemini(
                        prompt
                    )


                save_chat(
                    st.session_state.username,
                    "PDF Study",
                    query,
                    result
                )


                st.markdown(
                    "### 📖 PDF Study Result"
                )


                st.markdown(
                    f"""
                    <div class="output-box">

                    {result}

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            except Exception:

                st.error(
                    "Unable to process this PDF."
                )


        # ====================================================
        # PDF GENERATOR
        # ====================================================

        elif tool == "📄 PDF Generator":

            prompt = f"""

You are RockyAI v1-3,
an educational document generator.

Create professional,
printable content for a PDF.

User request:

{query}

Requirements:

- Clear title
- Headings
- Organized sections
- Bullet points
- Student-friendly language
- Printable format
- Useful educational content

Return only the document content.

"""


            with st.spinner(
                "RockyAI is generating your PDF..."
            ):

                result = ask_gemini(
                    prompt
                )


            save_chat(
                st.session_state.username,
                "PDF Generator",
                query,
                result
            )


            st.markdown(
                """
                <div class="pdf-ready">

                    <h2>
                        📄 PDF Ready!
                    </h2>

                    <p>
                        RockyAI v1-3 created your document.
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )


            pdf = create_pdf(
                query[:80],
                result
            )


            st.download_button(

                "⬇️ Download RockyAI PDF",

                data=pdf,

                file_name=(
                    "RockyAI_v1-3_Generated.pdf"
                ),

                mime="application/pdf",

                use_container_width=True

            )


            with st.expander(
                "👀 Preview Document"
            ):

                st.write(result)


        # ====================================================
        # QUIZ
        # ====================================================

        elif tool == "📝 Quiz Generator":

            prompt = f"""

Create exactly 5 multiple-choice questions
about:

{query}

Return ONLY valid JSON.

Format:

[
  {{
    "question": "Question",
    "options": [
      "A) Option",
      "B) Option",
      "C) Option",
      "D) Option"
    ],
    "answer": "A"
  }}
]

Do not include Markdown.

"""


            with st.spinner(
                "Creating your quiz..."
            ):

                raw = ask_gemini(
                    prompt
                )


            raw = (
                raw
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```",
                    ""
                )
                .strip()
            )


            try:

                questions = json.loads(
                    raw
                )


                st.markdown(
                    "### 📝 RockyAI Quiz"
                )


                answers = []


                for i, question in enumerate(
                    questions
                ):

                    st.markdown(
                        f"""
                        **Q{i + 1}.**
                        {question["question"]}
                        """
                    )


                    selected = st.radio(

                        "Select an answer",

                        question["options"],

                        key=f"quiz_{i}"

                    )


                    answers.append(
                        selected
                    )


                if st.button(
                    "🏆 Check My Score"
                ):

                    score = 0


                    for i, question in enumerate(
                        questions
                    ):

                        if answers[i].startswith(
                            question["answer"]
                        ):

                            score += 1


                    percentage = int(
                        (
                            score /
                            len(questions)
                        ) * 100
                    )


                    if percentage == 100:

                        st.balloons()

                        message = (
                            "🏆 Perfect score!"
                        )

                    elif percentage >= 60:

                        message = (
                            "🔥 Great job!"
                        )

                    else:

                        message = (
                            "📚 Keep practicing!"
                        )


                    st.success(
                        f"Score: {score}/"
                        f"{len(questions)} "
                        f"({percentage}%)\n\n"
                        f"{message}"
                    )


                    save_chat(
                        st.session_state.username,
                        "Quiz Generator",
                        query,
                        f"Score: {score}/"
                        f"{len(questions)}"
                    )


            except Exception:

                st.error(
                    "The quiz could not be generated. "
                    "Please try again."
                )


        # ====================================================
        # SAMPLE PAPER
        # ====================================================

        elif tool == "📚 Sample Paper":

            prompt = f"""

You are RockyAI v1-3.

Create a professional educational
sample question paper.

Requirements:

{query}

Include:

- Title
- Instructions
- Sections
- Questions
- Marks
- Different question types
- Appropriate difficulty

"""


            with st.spinner(
                "Creating sample paper..."
            ):

                result = ask_gemini(
                    prompt
                )


            save_chat(
                st.session_state.username,
                "Sample Paper",
                query,
                result
            )


            st.markdown(
                "### 📚 Sample Paper"
            )


            st.markdown(
                f"""
                <div class="output-box">

                {result}

                </div>
                """,
                unsafe_allow_html=True
            )


            pdf = create_pdf(
                "RockyAI v1-3 Sample Paper",
                result
            )


            st.download_button(

                "⬇️ Download Sample Paper PDF",

                data=pdf,

                file_name=(
                    "RockyAI_v1-3_Sample_Paper.pdf"
                ),

                mime="application/pdf"

            )


        # ====================================================
        # CODE GENERATOR
        # ====================================================

        elif tool == "💻 Code Generator":

            prompt = f"""

You are RockyAI v1-3,
a programming assistant.

Generate clean,
commented and understandable code.

User requirement:

{query}

After the code,
explain the important parts.

"""


            with st.spinner(
                "Writing your code..."
            ):

                result = ask_gemini(
                    prompt
                )


            save_chat(
                st.session_state.username,
                "Code Generator",
                query,
                result
            )


            st.markdown(
                "### 💻 Generated Code"
            )


            st.code(
                result
            )


        # ====================================================
        # MIND MAP
        # ====================================================

        elif tool == "🧠 Mind Map":

            prompt = f"""

Create a concise text mind map
for:

{query}

Use:

MAIN TOPIC
├── Branch
│   ├── Subtopic
│   └── Subtopic
└── Branch
    ├── Subtopic
    └── Subtopic

"""


            with st.spinner(
                "Building your mind map..."
            ):

                result = ask_gemini(
                    prompt
                )


            save_chat(
                st.session_state.username,
                "Mind Map",
                query,
                result
            )


            st.markdown(
                "### 🧠 Mind Map"
            )


            st.code(
                result
            )


        # ====================================================
        # PERIODIC TABLE
        # ====================================================

        elif tool == "🧪 Periodic Table":

            elements = {

                "H": "Hydrogen",

                "He": "Helium",

                "Li": "Lithium",

                "Be": "Beryllium",

                "B": "Boron",

                "C": "Carbon",

                "N": "Nitrogen",

                "O": "Oxygen",

                "F": "Fluorine",

                "Ne": "Neon",

                "Na": "Sodium",

                "Mg": "Magnesium",

                "Al": "Aluminium",

                "Si": "Silicon",

                "P": "Phosphorus",

                "S": "Sulfur",

                "Cl": "Chlorine",

                "Ar": "Argon"

            }


            st.markdown(
                "### 🧪 Element Reference"
            )


            for symbol, name in elements.items():

                st.write(
                    f"**{symbol}** — {name}"
                )


# ============================================================
# 12. HISTORY
# ============================================================

def history_page():

    st.title(
        "💬 RockyAI v1-3 History"
    )


    conn = get_db()


    chats = conn.execute(
        """
        SELECT
            tool,
            prompt,
            response,
            timestamp
        FROM chats
        WHERE username = ?
        ORDER BY id DESC
        """,
        (st.session_state.username,)
    ).fetchall()


    conn.close()


    if not chats:

        st.info(
            "No AI activity yet."
        )

        return


    for chat in chats:

        with st.expander(
            f"{chat['tool']} • "
            f"{chat['timestamp']}"
        ):

            st.markdown(
                "**You:**"
            )

            st.write(
                chat["prompt"]
            )


            st.markdown(
                "**RockyAI:**"
            )

            st.write(
                chat["response"]
            )


# ============================================================
# 13. ANALYTICS
# ============================================================

def analytics_page():

    st.title(
        "📊 RockyAI v1-3 Analytics"
    )


    conn = get_db()


    user = conn.execute(
        """
        SELECT prompts_count
        FROM users
        WHERE username = ?
        """,
        (st.session_state.username,)
    ).fetchone()


    tools = conn.execute(
        """
        SELECT
            tool,
            COUNT(*) AS count
        FROM chats
        WHERE username = ?
        GROUP BY tool
        ORDER BY count DESC
        """,
        (st.session_state.username,)
    ).fetchall()


    conn.close()


    requests = (
        user["prompts_count"]
        if user
        else 0
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Total AI Requests",
            requests
        )


    with col2:

        st.metric(
            "Available Tools",
            8
        )


    st.subheader(
        "Tool Usage"
    )


    if tools:

        for tool in tools:

            st.write(
                f"**{tool['tool']}** — "
                f"{tool['count']} requests"
            )

    else:

        st.info(
            "No usage data yet."
        )


# ============================================================
# 14. ADMIN PANEL
# ============================================================

def admin_page():

    st.title(
        "👑 RockyAI v1-3 Admin Panel"
    )


    conn = get_db()


    users = conn.execute(
        """
        SELECT
            username,
            role,
            prompts_count,
            created_at
        FROM users
        ORDER BY created_at DESC
        """
    ).fetchall()


    conn.close()


    st.subheader(
        "Registered Users"
    )


    for user in users:

        col1, col2, col3, col4 = st.columns(
            [3, 2, 2, 2]
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

            if (
                user["username"]
                != st.session_state.username
            ):

                if st.button(
                    "Delete",
                    key=(
                        "delete_"
                        + user["username"]
                    )
                ):

                    conn = get_db()


                    conn.execute(
                        """
                        DELETE FROM chats
                        WHERE username = ?
                        """,
                        (user["username"],)
                    )


                    conn.execute(
                        """
                        DELETE FROM users
                        WHERE username = ?
                        """,
                        (user["username"],)
                    )


                    conn.commit()

                    conn.close()


                    st.success(
                        "User deleted."
                    )

                    st.rerun()


    st.divider()


    st.subheader(
        "System Information"
    )


    st.info(
        "RockyAI v1-3\n\n"
        "AI Engine: Gemini 2.5 Flash\n\n"
        "Framework: Streamlit\n\n"
        "Database: SQLite\n\n"
        "PDF Engine: ReportLab\n\n"
        "Image Generation: Removed"
    )


# ============================================================
# 15. INITIALIZE SESSION
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


# ============================================================
# 16. APPLICATION
# ============================================================

if not st.session_state.logged_in:

    login_page()

else:

    page = show_sidebar()


    if page == "🏠 Workspace":

        workspace()


    elif page == "💬 History":

        history_page()


    elif page == "📊 Analytics":

        analytics_page()


    elif page == "👑 Admin Panel":

        if st.session_state.role == "admin":

            admin_page()

        else:

            st.error(
                "Access denied."
            )


    st.markdown(
        """
        <div class="footer">

        <strong>
        RockyAI v1-3
        </strong>

        <br>

        AI-Powered Learning Workspace

        <br><br>

        Learn smarter. Build faster. 🚀

        </div>
        """,
        unsafe_allow_html=True
    )
