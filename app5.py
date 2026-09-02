from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from google import genai
import sqlite3
import PyPDF2
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "306bfc52a357222048d4323e6861a38c653b899b5d920523f59a5add218ce43d"

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
DB_FILE = "rockyai.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL, role TEXT DEFAULT 'user', prompts_count INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, tool TEXT, prompt TEXT, response TEXT, timestamp TEXT)''')
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ("admin", "password123", "admin", 0))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

UNIFIED_STYLE = """
<style>
    body { background-color: #0c0c10; color: #00FFCC; font-family: 'Arial', sans-serif; margin: 0; padding: 20px; }
    .container { max-width: 1100px; margin: 0 auto; }
    .auth-card { max-width: 400px; margin: 60px auto; padding: 30px; background: #16161f; border: 1px solid #222; border-radius: 8px; text-align: center; }
    .headline { font-size: 26px; font-weight: bold; color: #00FFCC; margin-bottom: 15px; }
    .form-group { margin-bottom: 15px; text-align: left; }
    input, select, textarea { width: 100%; padding: 10px; background: #222; border: 1px solid #333; color: white; border-radius: 4px; box-sizing: border-box; }
    button, input[type="submit"] { background-color: #00FFCC; color: #000; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
    button:hover, input[type="submit"]:hover { background-color: #00b38f; }
    .alert { padding: 10px; background-color: #e74c3c; color: white; border-radius: 4px; margin-bottom: 15px; }
    .box { background: #16161f; padding: 20px; border-radius: 8px; border: 1px solid #222; margin-bottom: 20px; }
    .output-box { background: #16161f; padding: 20px; border-radius: 8px; border: 1px solid #222; white-space: pre-wrap; min-height: 180px; color: #fff; }
    .nav-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222; padding-bottom: 10px; margin-bottom: 20px; }
    .nav-links a { color: #00FFCC; text-decoration: none; margin-left: 15px; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #fff; }
    th, td { border: 1px solid #333; padding: 10px; text-align: left; }
    th { background: #222; color: #00FFCC; }
</style>
"""

AUTH_HTML = UNIFIED_STYLE + """
<div class="auth-card">
    <h2>{{ title }}</h2>
    {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="alert">{{m}}</div>{% endfor %}{% endif %}{% endwith %}
    <form method="POST">
        <div class="form-group"><label>Username</label><input type="text" name="username" required></div>
        <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
        <input type="submit" value="{{ btn_text }}" style="width: 100%;">
    </form>
    <p style="margin-top:20px;"><a href="{{ alt_link }}" style="color: #00FFCC; text-decoration: none;">{{ alt_text }}</a></p>
</div>
"""

DASHBOARD_HTML = UNIFIED_STYLE + """
<div class="container">
    <div class="nav-bar">
        <h1>RockyAI.net (Gemini 3.5 Flash Lite)</h1>
        <div class="nav-links">
            <span>{{ username }} (Prompts: {{ prompts_count }})</span>
            <a href="/dashboard">Dashboard</a>
            <a href="/history">History</a>
            {% if role == 'admin' %}<a href="/admin" style="color:#e74c3c;">Admin Panel</a>{% endif %}
            <a href="/logout">Log Out</a>
        </div>
    </div>
    
    <div class="headline">Workspace</div>
    <div class="box">
        <form method="POST" action="/run-feature" enctype="multipart/form-data">
            <div class="form-group" style="display: flex; gap: 10px;">
                <select name="tool" style="width: 30%;">
                    <option value="Ask AI">Ask AI</option>
                    <option value="PDF Reader">PDF Reader</option>
                    <option value="Generate Code">Generate Code</option>
                    <option value="Sample Paper">Sample Paper</option>
                    <option value="Text Mindmap">Text Mindmap</option>
                </select>
                <input type="text" name="query" placeholder="Enter your prompt or instructions..." value="{{ prev_query }}">
            </div>
            <div class="form-group">
                <label>Document Upload (PDF Optional):</label>
                <input type="file" name="doc_file" accept=".pdf">
            </div>
            <button type="submit">Execute Tool</button>
        </form>
    </div>
    
    <h3>Output Console</h3>
    <div class="output-box">{{ output_data | safe }}</div>
</div>
"""

HISTORY_HTML = UNIFIED_STYLE + """
<div class="container">
    <div class="nav-bar">
        <h1>Saved Chat History</h1>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/logout">Log Out</a>
        </div>
    </div>
    <div class="box">
        {% if chats %}
            {% for chat in chats %}
                <div style="border-bottom: 1px solid #333; margin-bottom: 15px; padding-bottom: 15px;">
                    <small style="color: #888;">[{{ chat[4] }}] Tool: <b>{{ chat[1] }}</b></small>
                    <p><b>Prompt:</b> {{ chat[2] }}</p>
                    <p style="color: #ddd;"><b>Response:</b> {{ chat[3] }}</p>
                </div>
            {% endfor %}
        {% else %}
            <p>No chat history found.</p>
        {% endif %}
    </div>
</div>
"""

ADMIN_HTML = UNIFIED_STYLE + """
<div class="container">
    <div class="nav-bar">
        <h1>Admin Panel - User Management</h1>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/logout">Log Out</a>
        </div>
    </div>
    <div class="box">
        <h3>Registered Users</h3>
        <table>
            <tr><th>Username</th><th>Role</th><th>Prompts Used</th><th>Actions</th></tr>
            {% for u in users %}
            <tr>
                <td>{{ u[0] }}</td>
                <td>{{ u[2] }}</td>
                <td>{{ u[3] }}</td>
                <td>
                    {% if u[0] != 'admin' %}
                    <a href="/admin/delete/{{ u[0] }}" style="color: #e74c3c; text-decoration: none; font-weight: bold;">Delete</a>
                    {% else %}
                    Protected
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</div>
"""

@app.route('/')
def home():
    return redirect(url_for('login') if 'username' not in session else 'dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (request.form['username'], request.form['password']))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'], session['role'] = user[0], user[1]
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.")
    return render_template_string(AUTH_HTML, title="RockyAI Login", btn_text="Log In", alt_text="Create Account", alt_link="/register")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role, prompts_count) VALUES (?, ?, 'user', 0)", 
                           (request.form['username'], request.form['password']))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            conn.close()
            flash("Username already exists.")
    return render_template_string(AUTH_HTML, title="Register RockyAI", btn_text="Register", alt_text="Back to Login", alt_link="/login")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session['username'],))
    row = cursor.fetchone()
    conn.close()
    count = row[0] if row else 0
    role = row[1] if row else 'user'
    default_msg = "Hello ! I am RockyAI, your personal AI assistant.Tell me what you want to do?"
    return render_template_string(DASHBOARD_HTML, username=session['username'], prompts_count=count, role=role, output_data=default_msg, prev_query="")

@app.route('/run-feature', methods=['POST'])
def run_feature():
    if 'username' not in session: return redirect(url_for('login'))
    
    tool = request.form.get('tool', 'Ask AI')
    query = request.form.get('query', '')
    file = request.files.get('doc_file')
    
    doc_text = ""
    if file and file.filename != '':
        if file.filename.lower().endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                doc_text += page.extract_text() or ""

    full_prompt = f"Tool: {tool}\nQuery: {query}\n\nDocument Context:\n{doc_text[:8000]}" if doc_text else f"Tool: {tool}\nQuery: {query}"
    
    # Updated model configuration to gemini-3.5-flash-lite
    if client:
        try:
            res = client.models.generate_content(
                model="gemini-3.5-flash-lite", 
                contents=full_prompt
            ).text
        except Exception as e:
            res = f"API Error: {str(e)}"
    else:
        res = "API Key missing."
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET prompts_count = prompts_count + 1 WHERE username = ?", (session['username'],))
    cursor.execute("INSERT INTO chats (username, tool, prompt, response, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (session['username'], tool, query, res, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session['username'],))
    row = cursor.fetchone()
    conn.close()

    return render_template_string(DASHBOARD_HTML, username=session['username'], prompts_count=row[0], role=row[1], output_data=res, prev_query=query)

@app.route('/history')
def history():
    if 'username' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT tool, prompt, response, timestamp, id FROM chats WHERE username = ? ORDER BY id DESC", (session['username'],))
    chats = cursor.fetchall()
    conn.close()
    return render_template_string(HISTORY_HTML, chats=chats)

@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, role, prompts_count FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, users=users)

@app.route('/admin/delete/<username>')
def admin_delete_user(username):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    if username != 'admin':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        cursor.execute("DELETE FROM chats WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=5000)
