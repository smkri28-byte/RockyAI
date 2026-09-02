from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from google import genai
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "rockyaipromax_unique_secret_key_321"

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
DB_FILE = "rockyaipromax.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL, role TEXT DEFAULT 'promax')''')
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", "password123", "promax"))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

MAX_STYLE = """
<style>
    body { background-color: #0c0910; color: #ffd700; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
    .auth-container { max-width: 400px; margin: 50px auto; padding: 30px; background-color: #1a1423; border: 2px solid #ffd700; border-radius: 12px; text-align: center; box-shadow: 0 0 20px rgba(255, 215, 0, 0.2); }
    .dashboard-container { max-width: 1200px; margin: 0 auto; }
    .headline { font-size: 36px; font-weight: bold; color: #ffdf00; text-shadow: 0 0 10px rgba(255,223,0,0.4); margin-bottom: 20px; }
    .form-group { margin-bottom: 15px; text-align: left; }
    input, select, textarea { width: 100%; padding: 12px; background: #251d33; border: 1px solid #ffd700; color: white; border-radius: 6px; box-sizing: border-box; }
    button, input[type="submit"] { background: linear-gradient(45deg, #ffd700, #ff8c00); color: black; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; width: 100%; }
    .btn-upgrade { background: linear-gradient(45deg, #ffd700, #ff8c00) !important; color: black; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; margin-top: 10px; }
    .alert { padding: 10px; background-color: #e74c3c; color: white; border-radius: 4px; margin-bottom: 15px; }
    .menu-box { background: #1a1423; padding: 25px; border-radius: 12px; border: 1px solid #ffd700; margin-bottom: 20px; box-shadow: 0 0 15px rgba(255, 215, 0, 0.1); }
    .output-box { background: #1a1423; padding: 25px; border-radius: 12px; border: 1px solid #ffd700; white-space: pre-wrap; color: #fff; min-height: 250px; }
    .nav-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ffd700; padding-bottom: 15px; margin-bottom: 20px; }
    .grid-files { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-bottom: 15px; }
    .file-card { background: #251d33; padding: 12px; border: 1px dashed #ffd700; border-radius: 6px; }
</style>
"""

MAX_LOGIN = MAX_STYLE + """
<div class="auth-container">
    <h2>👑 RockyAIProMax Portal</h2>
    {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="alert">{{m}}</div>{% endfor %}{% endif %}{% endwith %}
    <form method="POST" action="/login">
        <div class="form-group"><label>Username</label><input type="text" name="username" required></div>
        <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
        <input type="submit" value="Enter Ultra Portal">
    </form>
</div>
"""

ACCESS_DENIED_MAX = MAX_STYLE + """
<div class="auth-container" style="border-color: #e74c3c; max-width: 600px;">
    <h2 style="color: #e74c3c;">Access Denied Please unlock by completing prompts !!</h2>
    <p>You must complete the required prompt limit on RockyAIPro to unlock and access RockyAIProMax.</p>
    <a href="https://rockyai-pro-net.onrender.com" class="btn-upgrade" style="background: #e74c3c !important; color: white;">Return to RockyAIPro</a>
</div>
"""

MAX_DASHBOARD = MAX_STYLE + """
<div class="dashboard-container">
    <div class="nav-bar">
        <h1>👑 RockyAIProMax Ultimate Edition</h1>
        <div><a href="/logout"><button style="width: auto; padding: 8px 16px;">Log Out</button></a></div>
    </div>
    <div class="headline">Welcome Supreme User: {{ username }}</div>
    <div class="menu-box">
        <form method="POST" action="/run-feature" enctype="multipart/form-data">
            <div class="form-group">
                <label>Prompt / Query:</label>
                <input type="text" name="query" placeholder="Ask anything about your attachments..." value="{{ prev_query }}">
            </div>
            
            <label style="font-weight: bold; display: block; margin-bottom: 10px;">📂 Dedicated Attachment Types:</label>
            <div class="grid-files">
                <div class="file-card">
                    <label>🖼️ Image Attachment:</label>
                    <input type="file" name="image_file" accept="image/*">
                </div>
                <div class="file-card">
                    <label>📄 Document (PDF/DOCX/TXT):</label>
                    <input type="file" name="doc_file" accept=".pdf,.docx,.txt">
                </div>
                <div class="file-card">
                    <label>🎵 Audio / 🎬 Video File:</label>
                    <input type="file" name="media_file" accept="audio/*,video/*">
                </div>
            </div>

            <button type="submit">Analyze with ProMax Multimodal Intelligence</button>
        </form>
    </div>
    <div class="output-box">{{ output_data | safe }}</div>
</div>
"""

@app.route('/')
def home():
    if request.args.get('unlocked') == 'rockyaipro_passed':
        session['unlocked'] = True
    if not session.get('unlocked'):
        return render_template_string(ACCESS_DENIED_MAX)
    return redirect(url_for('login') if 'username' not in session else 'dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.args.get('unlocked') == 'rockyaipro_passed':
        session['unlocked'] = True
    if not session.get('unlocked'):
        return render_template_string(ACCESS_DENIED_MAX)

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
    return render_template_string(MAX_LOGIN)

@app.route('/dashboard')
def dashboard():
    if request.args.get('unlocked') == 'rockyaipro_passed':
        session['unlocked'] = True
    if not session.get('unlocked'):
        return render_template_string(ACCESS_DENIED_MAX)

    if 'username' not in session: return redirect(url_for('login'))
    return render_template_string(MAX_DASHBOARD, username=session['username'], output_data="ProMax System Online. Attach any combination of files above.", prev_query="")

@app.route('/run-feature', methods=['POST'])
def run_feature():
    if not session.get('unlocked'): return render_template_string(ACCESS_DENIED_MAX)
    if 'username' not in session: return redirect(url_for('login'))
    
    query = request.form.get('query', 'Analyze these attachments')
    contents = [query]
    
    # Check each file attachment type independently
    for field_name in ['image_file', 'doc_file', 'media_file']:
        file = request.files.get(field_name)
        if file and file.filename != '':
            file_bytes = file.read()
            uploaded_file = client.files.upload(file=file_bytes, config=dict(mime_type=file.content_type))
            contents.append(uploaded_file)

    res = client.models.generate_content(model="gemini-2.5-flash", contents=contents).text if client else "API Client missing."
    return render_template_string(MAX_DASHBOARD, username=session['username'], output_data=res, prev_query=query)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=5002)
