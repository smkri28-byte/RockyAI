from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from google import genai
from google.genai import types
import sqlite3
import PyPDF2
import json
from datetime import datetime
import graphviz
import base64
import os

app = Flask(__name__)

# Fetch the secret key safely from the hosting environment
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "306bfc52a357222048d4323e6861a38c653b899b5d920523f59a5add218ce43d")

# Fetch your Gemini API key safely from the hosting environment
API_KEY = os.environ.get("GEMINI_API_KEY")

# Fallback check to avoid server crashes if you forget to add the key to Render
if not API_KEY:
    client = None
else:
    client = genai.Client(api_key=API_KEY)

DB_FILE = "users_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            prompts_count INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            tool TEXT,
            prompt TEXT,
            response TEXT,
            timestamp TEXT
        )
    ''')
    try:
        cursor.execute("INSERT INTO users (username, password, role, prompts_count) VALUES (?, ?, ?, ?)", ("admin", "password123", "admin", 0))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

def get_ai_response(prompt):
    if not client:
        return "Error: Gemini API Key is missing. Please add it to your Environment Variables."
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error connecting to Gemini AI: {str(e)}"

BASE_STYLE = """
<style>
    body { background-color: #0c0c10; color: #00FFCC; font-family: 'Arial', sans-serif; margin: 0; padding: 20px; }
    .auth-container { max-width: 400px; margin: 60px auto; padding: 30px; background: #16161f; border: 1px solid #222; border-radius: 8px; text-align: center; }
    .dashboard-container { max-width: 1100px; margin: 0 auto; }
    h1 { color: #00FFCC; font-weight: bold; }
    .headline { font-size: 26px; font-weight: bold; color: #00FFCC; margin-bottom: 20px; }
    .form-group { margin-bottom: 15px; text-align: left; }
    label { display: block; margin-bottom: 5px; font-weight: bold; color: #00FFCC; }
    input[type="text"], input[type="password"], textarea, select { width: 100%; padding: 10px; background: #222; border: 1px solid #333; color: white; border-radius: 4px; box-sizing: border-box; }
    button, input[type="submit"] { background-color: #00FFCC; color: #000; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
    button:hover, input[type="submit"]:hover { background-color: #00b38f; }
    .btn-green { background-color: #00FFCC !important; color: #000 !important; }
    .btn-green:hover { background-color: #00b38f !important; }
    .alert { padding: 10px; background-color: #e74c3c; color: white; border-radius: 4px; margin-bottom: 15px; font-size: 14px; }
    .menu-box { background: #16161f; padding: 20px; border-radius: 8px; border: 1px solid #222222; margin-bottom: 20px; }
    .output-box { background: #16161f; padding: 20px; border-radius: 8px; border: 1px solid #222222; white-space: pre-wrap; min-height: 180px; color: #fff; }
    .nav-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222222; padding-bottom: 10px; margin-bottom: 20px; }
    .nav-links { display: flex; align-items: center; gap: 15px; }
    .nav-links a { color: #00FFCC; text-decoration: none; font-weight: bold; }
    .quiz-option { display: block; margin: 10px 0; background: #222; padding: 10px; border-radius: 4px; color: #fff; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #fff; }
    th, td { border: 1px solid #333; padding: 10px; text-align: left; }
    th { background: #222; color: #00FFCC; }
</style>
"""

LOGIN_HTML = BASE_STYLE + """
<div class="auth-container">
    <h2>RockyAI - v1.2 Login</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="alert">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST" action="/login">
        <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
        </div>
        <input type="submit" value="Log In" style="width: 100%;">
    </form>
    <p style="margin-top:20px; font-size:14px;">
        <a href="/register" style="color: #00FFCC; text-decoration: none;">Create New Account</a>
    </p>
</div>
"""

REGISTER_HTML = BASE_STYLE + """
<div class="auth-container">
    <h2>Register RockyAI - v1.2</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="alert">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST" action="/register">
        <div class="form-group">
            <label>Choose Username</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Choose Password</label>
            <input type="password" name="password" required>
        </div>
        <input type="submit" value="Register" style="width: 100%;">
    </form>
    <p style="margin-top:20px; font-size:14px;">
        <a href="/login" style="color: #00FFCC; text-decoration: none;">Back to Login</a>
    </p>
</div>
"""

DASHBOARD_HTML = BASE_STYLE + """
<div class="dashboard-container">
    <div class="nav-bar">
        <h1>RockyAI - v1.2</h1>
        <div class="nav-links">
            <span>{{ username }} (Prompts: {{ prompts_count }})</span>
            <a href="/dashboard">Dashboard</a>
            <a href="/history">History</a>
            {% if role == 'admin' %}
                <a href="/admin" style="color:#e74c3c;">Admin Panel</a>
            {% endif %}
            <a href="/logout"><button>Log Out</button></a>
        </div>
    </div>
    
    <div class="headline">Workspace</div>

    <div class="menu-box">
        <form method="POST" action="/run-feature" enctype="multipart/form-data">
            <div class="form-group" style="display: flex; gap: 10px;">
                <select name="feature" style="width: 30%;">
                    <option value="ask_ai" {% if selected_tool == 'ask_ai' %}selected{% endif %}>Ask AI</option>
                    <option value="generate_image" {% if selected_tool == 'generate_image' %}selected{% endif %}>Generate Image (Nano Banana)</option>
                    <option value="pdf_reader" {% if selected_tool == 'pdf_reader' %}selected{% endif %}>PDF Reader</option>
                    <option value="generate_quiz" {% if selected_tool == 'generate_quiz' %}selected{% endif %}>Generate Quiz</option>
                    <option value="sample_paper" {% if selected_tool == 'sample_paper' %}selected{% endif %}>Sample Paper</option>
                    <option value="generate_code" {% if selected_tool == 'generate_code' %}selected{% endif %}>Generate Code</option>
                    <option value="mind_map" {% if selected_tool == 'mind_map' %}selected{% endif %}>Text Mindmap</option>
                    <option value="periodic_table" {% if selected_tool == 'periodic_table' %}selected{% endif %}>Periodic Table</option>
                    <option value="analytics" {% if selected_tool == 'analytics' %}selected{% endif %}>Analytics</option>
                </select>
                <input type="text" name="query" placeholder="Enter your prompt, question, or image description..." value="{{ prev_query }}">
            </div>
            
            <div class="form-group">
                <label>Document Upload (PDF Optional):</label>
                <input type="file" name="pdf_file" accept=".pdf">
            </div>
            
            <button type="submit">Execute Tool</button>
        </form>
    </div>

    <h3>Output Console</h3>
    <div class="output-box">
        {% if feature_type == "text" %}
            {{ output_data | safe }}
        {% elif feature_type == "image" %}
            <img src="data:image/png;base64,{{ output_data }}" style="max-width: 100%; border-radius: 8px;">
        {% elif feature_type == "quiz" %}
            <form method="POST" action="/evaluate-quiz">
                <h4>Interactive Quiz Questions:</h4>
                {% for q in output_data %}
                    <div style="margin-bottom: 20px;">
                        <p><b>Q{{ loop.index }}: {{ q.question }}</b></p>
                        <input type="hidden" name="ans_{{ loop.index0 }}" value="{{ q.answer }}">
                        {% for opt in q.options %}
                            <label class="quiz-option">
                                <input type="radio" name="user_ans_{{ loop.index0 }}" value="{{ opt }}"> {{ opt }}
                            </label>
                        {% endfor %}
                    </div>
                {% endfor %}
                <button type="submit">Submit Quiz Answers</button>
            </form>
        {% else %}
            Hello! I am RockyAI, your personal AI assistant. Tell me what you want to do?
        {% endif %}
    </div>
</div>
"""

HISTORY_HTML = BASE_STYLE + """
<div class="dashboard-container">
    <div class="nav-bar">
        <h1>Saved Chat History</h1>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/logout"><button>Log Out</button></a>
        </div>
    </div>
    <div class="menu-box">
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

ADMIN_HTML = BASE_STYLE + """
<div class="dashboard-container">
    <div class="nav-bar">
        <h1>Admin Panel - User Management</h1>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/logout"><button>Log Out</button></a>
        </div>
    </div>
    <div class="menu-box">
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
    if "username" in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (username, password))
        user_found = cursor.fetchone()
        conn.close()
        
        if user_found:
            session['username'] = user_found[0]
            session['role'] = user_found[1]
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.")
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash("Fields cannot be empty.")
            return render_template_string(REGISTER_HTML)
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role, prompts_count) VALUES (?, ?, 'user', 0)", (username, password))
            conn.commit()
            flash("Account created successfully! Please log in.")
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
        finally:
            conn.close()
            
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if "username" not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session['username'],))
    row = cursor.fetchone()
    conn.close()
    
    prompts_count = row[0] if row else 0
    role = row[1] if row else 'user'
    
    return render_template_string(DASHBOARD_HTML, username=session['username'], role=role, prompts_count=prompts_count, feature_type="none", prev_query="")

@app.route('/run-feature', methods=['POST'])
def run_feature():
    if "username" not in session:
        return redirect(url_for('login'))
    
    feature = request.form.get('feature')
    query = request.form.get('query', '').strip()
    feature_type = "text"
    output_data = ""

    if feature == "ask_ai":
        if not query: 
            output_data = "Error: Question required"
        else:
            prompt = f"System Instruction: You are RockyAI, a custom AI assistant. Whenever greeted or asked about your origin, identify yourself explicitly as RockyAI. User Request: {query}"
            output_data = get_ai_response(prompt)
            
    elif feature == "generate_image":
        if not query:
            output_data = "Error: Please enter a prompt description for image generation."
        else:
            if not client:
                output_data = "Error: Gemini API Key is missing."
            else:
                try:
                    result = client.models.generate_images(
                        model='imagen-3.0-generate-002',
                        prompt=query,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            output_mime_type="image/png",
                            aspect_ratio="1:1"
                        )
                    )
                    for generated_image in result.generated_images:
                        img_bytes = generated_image.image.image_bytes
                        output_data = base64.b64encode(img_bytes).decode('utf-8')
                        feature_type = "image"
                except Exception as e:
                    output_data = f"Image Generation Failed: {str(e)}"
                    feature_type = "text"

    elif feature == "pdf_reader":
        file = request.files.get('pdf_file')
        doc_text = ""
        if file and file.filename != '':
            try:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    doc_text += page.extract_text() or ""
            except Exception as e:
                doc_text = f"Error reading PDF: {str(e)}"
        
        full_prompt = f"System Instruction: You are RockyAI. Tool: PDF Reader\nQuery: {query}\n\nDocument Context:\n{doc_text[:8000]}"
        output_data = get_ai_response(full_prompt)
                
    elif feature == "generate_quiz":
        if not query: 
            output_data = "Error: Topic required"
        else:
            prompt = f"""Create a quiz on '{query}' with exactly 3 multiple-choice questions. Return strictly valid JSON array format.
            Format: [{{"question": "...", "options": ["A) ..", "B) .."], "answer": "B"}}]"""
            raw = get_ai_response(prompt).replace("```json", "").replace("```", "").strip()
            try:
                output_data = json.loads(raw)
                feature_type = "quiz"
            except Exception:
                output_data = "Failed to compile structured quiz format. Try again."
                
    elif feature == "sample_paper":
        if not query: 
            output_data = "Error: Subject required"
        else:
            output_data = get_ai_response(f"System Instruction: You are RockyAI. Create a Sample Paper for {query}. Include markings and sections.")
            
    elif feature == "generate_code":
        if not query: 
            output_data = "Error: Code concept required"
        else:
            output_data = get_ai_response(f'System Instruction: You are RockyAI. Generate clean code for: {query}')
            
    elif feature == "mind_map":
        if not query: 
            output_data = "Error: Map topic required"
        else:
            output_data = get_ai_response(f"System Instruction: You are RockyAI. Create a short structural hierarchy text mindmap overview for: {query}.")
            feature_type = "text"
                
    elif feature == "periodic_table":
        periodic_table = {"H": "Hydrogen", "He": "Helium", "Li": "Lithium", "Be": "Beryllium", "B": "Boron", "C": "Carbon"}
        output_data = "🧪 Fast Chemical Elements Reference (RockyAI)\n\n"
        for k, v in periodic_table.items():
            output_data += f"{k}: {v}\n"
            
    elif feature == "analytics":
        output_data = "📊 Study Logs Counter\nDatabase connectivity: Connected to SQLite. Account registries are permanently active."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET prompts_count = prompts_count + 1 WHERE username = ?", (session['username'],))
    cursor.execute("INSERT INTO chats (username, tool, prompt, response, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (session['username'], feature, query, str(output_data) if feature_type != "image" else "[Generated Image]", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session['username'],))
    row = cursor.fetchone()
    conn.close()
    
    prompts_count = row[0] if row else 0
    role = row[1] if row else 'user'

    return render_template_string(DASHBOARD_HTML, username=session['username'], role=role, prompts_count=prompts_count, feature_type=feature_type, output_data=output_data, prev_query=query, selected_tool=feature)

@app.route('/evaluate-quiz', methods=['POST'])
def evaluate_quiz():
    score = 0
    total = 3
    for idx in range(total):
        correct = request.form.get(f'ans_{idx}')
        user_choice = request.form.get(f'user_ans_{idx}')
        if user_choice and user_choice.startswith(correct):
            score += 1
    result = f"🏁 Quiz Evaluation Complete\nYou answered {score} out of {total} questions correctly!"
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompts_count, role FROM users WHERE username = ?", (session.get('username'),))
    row = cursor.fetchone()
    conn.close()
    
    prompts_count = row[0] if row else 0
    role = row[1] if row else 'user'

    return render_template_string(DASHBOARD_HTML, username=session.get('username', 'Student'), role=role, prompts_count=prompts_count, feature_type="text", output_data=result, prev_query="")

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
