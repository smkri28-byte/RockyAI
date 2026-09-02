from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from google import genai
import sqlite3
import PyPDF2
import os

app = Flask(__name__)
app.secret_key = "2473f200f4c64bc97c21bc3802a88a566b0779b14a4404f5fab1025cf0a9ba00"

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
DB_FILE = "rockyaipro.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL, role TEXT DEFAULT 'user', prompts_count INTEGER DEFAULT 0)''')
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ("admin", "password123", "admin", 0))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

PRO_STYLE = """
<style>
    body { background-color: #0b0b0f; color: #f1c40f; font-family: 'Arial', sans-serif; margin: 0; padding: 20px; }
    .auth-container { max-width: 400px; margin: 50px auto; padding: 30px; background-color: #16161d; border: 1px solid #f1c40f; border-radius: 8px; text-align: center; }
    .dashboard-container { max-width: 1200px; margin: 0 auto; }
    .headline { font-size: 32px; font-weight: bold; color: #f39c12; margin-bottom: 20px; }
    .form-group { margin-bottom: 15px; text-align: left; }
    input, select, textarea { width: 100%; padding: 10px; background: #222; border: 1px solid #444; color: white; border-radius: 4px; box-sizing: border-box; }
    button, input[type="submit"] { background-color: #f39c12; color: black; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
    .alert { padding: 10px; background-color: #e74c3c; color: white; border-radius: 4px; margin-bottom: 15px; }
    .upgrade-alert { padding: 20px; background-color: #27ae60; border: 2px solid #ffd700; color: white; border-radius: 8px; margin-bottom: 20px; text-align: center; }
    .menu-box { background: #16161d; padding: 20px; border-radius: 8px; border: 1px solid #333; margin-bottom: 20px; }
    .output-box { background: #16161d; padding: 20px; border-radius: 8px; border: 1px solid #333; white-space: pre-wrap; color: #fff; min-height: 200px; }
    .nav-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
</style>
"""

PRO_LOGIN = PRO_STYLE + """
<div class="auth-container">
    <h2>💰 RockyAIPro Login</h2>
    {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="alert">{{m}}</div>{% endfor %}{% endif %}{% endwith %}
    <form method="POST" action="/login">
        <div class="form-group"><label>Username</label><input type="text" name="username" required></div>
        <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
        <input type="submit" value="Log In Pro" style="width: 100%;">
    </form>
</div>
"""

ACCESS_DENIED_HTML = PRO_STYLE + """
<div class="auth-container" style="border-color: #e74c3c; max-width: 600px;">
    <h2 style="color: #e74c3c;">Access Denied Please unlock by completing prompts !!</h2>
    <p>You must complete the required prompt limit on RockAIPlus to unlock and access RockyAIPro.</p>
    <a href="https://rock-ai-plus.onrender.com" class="btn-upgrade" style="background-color: #e74c3c !important; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; margin-top: 10px;">Return to RockAIPlus</a>
</div>
"""

PRO_DASHBOARD = PRO_STYLE + """
<div class="dashboard-container">
    <div class="nav-bar">
        <h1>💰 RockyAIPro Dashboard</h1>
        <div><a href="/logout"><button>Log Out</button></a></div>
    </div>
    
    {% if upgrade_msg %}
    <div class="upgrade-alert">
        <h2>🎉 Hurray!! You have Reached Max Pro Tier</h2>
        <p>You have successfully completed all prompt requirements on RockyAIPro!</p>
    </div>
    {% endif %}

    <div class="headline">Welcome Pro User: {{ username }} [Prompts Used: {{ prompts_count }}/250] {% if role == 'admin' %}<span style="color:#e74c3c;">(ADMIN ACCESS KEY ACTIVE)</span>{% endif %}</div>
    <div class="menu-box">
        <form method="POST" action="/run-feature" enctype="multipart/form-data">
            <div class="form-group" style="display: flex; gap: 10px;">
                <select name="feature" style="width: 30%;">
                    <option value="ask_ai">Ask Pro AI</option>
                </select>
                <input type="text" name="query" placeholder="Type query..." value="{{ prev_query }}">
            </div>
            <div class="form-group">
                <label>Document Upload (PDF Only):</label>
                <input type="file" name="doc_file" accept=".pdf">
            </div>
            <button type="submit">Execute Pro Feature</button>
        </form>
    </div>
    <div class="output-box">{{ output_data | safe }}</div>
</div>
"""

@app.route('/')
def home():
    if request.args.get('unlocked') == 'rockaiplus_passed' or session.get('role') == 'admin':
        session['unlocked'] = True
    if not session.get('unlocked'):
        return render_template_string(ACCESS_DENIED_HTML)
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
            if user[1] == 'admin':
                session['unlocked'] = True
            return redirect(url_for('dashboard'))
        flash("Invalid login.")
    
    if session.get('role') == 'admin':
        session['unlocked'] = True

    if not session.get('unlocked'):
        return render_template_string(ACCESS_DENIED_HTML)
        
    return render_template_string(PRO_LOGIN)

@app.route('/dashboard')
def dashboard():
    if session.get('role') == 'admin':
        session['unlocked'] = True

    if not session.get('unlocked'):
        return render_template_string(ACCESS_DENIED_HTML)
        
    if 'username' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session['username'],))
    row = cursor.fetchone()
    count = row[0] if row else 0
    role = row[1] if row else 'user'
    conn.close()
    return render_template_string(PRO_DASHBOARD, username=session['username'], prompts_count=count, role=role, upgrade_msg=(count >= 250 or role == 'admin'), output_data="Pro Console Ready.", prev_query="")

@app.route('/run-feature', methods=['POST'])
def run_feature():
    if session.get('role') == 'admin':
        session['unlocked'] = True
    if not session.get('unlocked'): return render_template_string(ACCESS_DENIED_HTML)
    if 'username' not in session: return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session['username'],))
    row = cursor.fetchone()
    count = row[0] + 1
    role = row[1]
    cursor.execute("UPDATE users SET prompts_count = ? WHERE username = ?", (count, session['username']))
    conn.commit()
    conn.close()

    upgrade_msg = (count >= 250 or role == 'admin')
    query = request.form.get('query', '')
    
    file = request.files.get('doc_file')
    doc_text = ""
    if file and file.filename != '':
        filename = file.filename.lower()
        if filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                doc_text += page.extract_text() or ""

    full_prompt = f"{query}\n\nDocument Context:\n{doc_text[:8000]}" if doc_text else query
    res = client.models.generate_content(model="gemini-2.5-flash", contents=full_prompt).text if client else "API Missing."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session['username'],))
    row_val = cursor.fetchone()
    c_val = row_val[0]
    r_val = row_val[1]
    conn.close()

    return render_template_string(PRO_DASHBOARD, username=session['username'], prompts_count=c_val, role=r_val, upgrade_msg=(c_val >= 250 or r_val == 'admin'), output_data=res, prev_query=query)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=5001)
