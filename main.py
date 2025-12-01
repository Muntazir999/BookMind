# main.py - BookMind PRO: Final Edition (Book hides when chat opens)
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os, glob, markdown

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
BOOK_DIR = "book"
BOOK_IMAGE = "/static/book.png"

MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.0-flash", "gemini-3.0-pro"]

def load_book():
    chapters = []
    files = sorted(glob.glob(f"{BOOK_DIR}/*.md") + glob.glob(f"{BOOK_DIR}/*.txt"))
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            title = os.path.basename(file).split('.')[0].replace('_', ' ').title()
            html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
            chapters.append({"title": title, "content": content, "html": html_content})
    return chapters

book_chapters = load_book()

def get_model():
    for name in MODELS:
        try:
            model = genai.GenerativeModel(name, generation_config={"temperature": 0.4})
            model.generate_content("hi")
            return model
        except: continue
    return None

def ask_book(question):
    context = "\n\n".join([f"Chapter: {ch['title']}\n{ch['content']}" for ch in book_chapters])
    prompt = f"""You are a wise AI assistant inside a living book about Physical AI and Humanoid Robotics.
Answer using only the book's knowledge. Be eloquent and kind.

Book content:
{context}

Question: {question}

Answer wisely:"""
    model = get_model()
    if not model:
        return "The book is resting quietly tonight. Please try again soon."
    try:
        return model.generate_content(prompt).text.strip()
    except Exception as e:
        return f"The pages whisper softly... (temporary silence)"

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BookMind: Physical AI & Humanoid Robotics</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --bg:#0d1117; --sidebar:#161b22; --card:#1a1f2c; --accent:#00ff9d; --text:#e6edf3; --border:#30363d; }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Segoe UI',sans-serif; background:var(--bg); color:var(--text); height:100vh; display:flex; overflow:hidden; }
        #sidebar { width:300px; background:var(--sidebar); border-right:1px solid var(--border); padding:20px; overflow-y:auto; }
        #sidebar h1 { color:var(--accent); text-align:center; font-size:1.8em; margin-bottom:30px; text-shadow:0 0 10px #00ff9d33; }
        .chapter { padding:14px; margin:8px 0; background:#21262d; border-radius:10px; cursor:pointer; transition:all .2s; }
        .chapter:hover { background:#30363d; border-color:var(--accent); transform:translateX(4px); }
        .chapter.active { background:#0d3a2c; border-left:4px solid var(--accent); font-weight:bold; }

        #main-area { flex:1; display:flex; position:relative; }
        #content { flex:1; padding:40px; overflow-y:auto; background:var(--card); margin:20px; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.6); }
        #content h1 { color:var(--accent); }

        #chat-panel { width:380px; background:var(--sidebar); border-left:1px solid var(--border); display:flex; flex-direction:column; transition:width .4s ease; }
        #chat-header { padding:16px; text-align:center; border-bottom:1px solid var(--border); color:var(--accent); font-weight:bold; cursor:pointer; }
        #messages { flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:12px; }
        .msg { max-width:85%; padding:10px 14px; border-radius:18px; line-height:1.5; }
        .user { background:var(--accent); color:black; align-self:flex-end; border-bottom-right-radius:4px; }
        .ai { background:#30363d; color:#ccffdd; align-self:flex-start; border-bottom-left-radius:4px; }
        #chat-input { padding:16px; border-top:1px solid var(--border); display:flex; gap:10px; }
        #chat-input input { flex:1; padding:12px 16px; background:#0d1117; border:1px solid var(--border); border-radius:24px; color:white; outline:none; }
        #chat-input input:focus { border-color:var(--accent); box-shadow:0 0 0 2px #00ff9d33; }

        #floating-book {
            position:fixed; bottom:20px; right:20px; width:140px; cursor:pointer;
            animation:float 6s ease-in-out infinite; filter:drop-shadow(0 0 20px #00ff9d44); z-index:100;
            transition:opacity .5s ease, transform .5s ease;
        }
        @keyframes float { 0%,100%{transform:translateY(0) rotate(2deg)} 50%{transform:translateY(-16px) rotate(-2deg)} }

        .resize-handle { width:6px; background:#30363d; cursor:col-resize; }
        .resize-handle:hover { background:var(--accent); }

        @media (max-width:900px) {
            body { flex-direction:column; }
            #sidebar { width:100%; max-height:30vh; }
            #chat-panel { width:100%; height:50vh; border-left:none; border-top:1px solid var(--border); }
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <h1>BookMind</h1>
        {% for ch in chapters %}
        <div class="chapter" onclick="loadChapter({{ loop.index0 }})">{{ ch.title }}</div>
        {% endfor %}
    </div>

    <div id="main-area">
        <div id="content">
            <h1>Physical AI & Humanoid Robotics</h1>
            <p><strong>BookMind</strong> — An AI-powered living book on the future of embodied intelligence.</p>
            <p style="color:var(--accent);margin-top:20px;">Open the assistant to speak with the book.</p>
        </div>

        <div class="resize-handle" id="chat-resize"></div>

        <div id="chat-panel">
            <div id="chat-header" onclick="toggleChat()">Ask the Book <i class="fas fa-chevron-left" id="chevron"></i></div>
            <div id="messages"></div>
            <div id="chat-input">
                <input type="text" placeholder="Ask about Optimus, Figure, VLA models..." onkeypress="if(event.key==='Enter')send()">
            </div>
        </div>
    </div>

    <img src="{{ book_image }}" id="floating-book" onclick="toggleChat()" title="Open AI Assistant">

    <script>
        const chapters = {{ chapters|tojson }};
        let chatOpen = false;

        function toggleChat() {
            chatOpen = !chatOpen;
            const panel = document.getElementById('chat-panel');
            const book = document.getElementById('floating-book');
            const chevron = document.getElementById('chevron');

            if (chatOpen) {
                panel.style.width = '380px';
                book.style.opacity = '0';
                book.style.pointerEvents = 'none';
                chevron.className = 'fas fa-chevron-right';
            } else {
                panel.style.width = '0';
                book.style.opacity = '1';
                book.style.pointerEvents = 'auto';
                chevron.className = 'fas fa-chevron-left';
            }
        }

        function loadChapter(i) {
            document.querySelectorAll('.chapter').forEach(c=>c.classList.remove('active'));
            document.querySelectorAll('.chapter')[i].classList.add('active');
            document.getElementById('content').innerHTML = `<h1>${chapters[i].title}</h1>${chapters[i].html}`;
        }

        function addMessage(text, type) {
            const div = document.createElement('div');
            div.className = 'msg ' + type;
            div.innerHTML = text.replace(/\\n/g, '<br>');
            document.getElementById('messages').appendChild(div);
            div.scrollIntoView({behavior:'smooth'});
        }

        function send() {
            const input = document.querySelector('#chat-input input');
            const q = input.value.trim();
            if (!q) return;
            addMessage(q, 'user');
            input.value = '';
            fetch('/ask', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:q})})
                .then(r=>r.json()).then(d=>addMessage(d.answer,'ai'))
                .catch(()=>addMessage("The book is dreaming...",'ai'));
        }

        // Resizable
        document.getElementById('chat-resize').addEventListener('mousedown', e=>{
            e.preventDefault();
            const move = e=>{ let w = window.innerWidth - e.clientX; if(w>280&&w<600) document.getElementById('chat-panel').style.width = w+'px'; }
            const up = ()=>{ document.removeEventListener('mousemove',move); document.removeEventListener('mouseup',up); }
            document.addEventListener('mousemove',move);
            document.addEventListener('mouseup',up);
        });

        if (chapters.length > 0) loadChapter(0);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, chapters=book_chapters, book_image=BOOK_IMAGE)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    answer = ask_book(data.get('question', ''))
    return jsonify({"answer": answer})

if __name__ == '__main__':
    print("BookMind PRO is ALIVE! → http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)