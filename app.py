import os
from flask import Flask, request, jsonify, redirect, session, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

PASSWORD = os.environ.get("APP_PASSWORD")
CLIENT_KEY = os.environ.get("CLIENT_KEY", "client123")

os.makedirs("screenshots", exist_ok=True)

# ===== STATE =====
state = {
    "online": False,
    "cpu": 0,
    "ram": 0,
    "disk": 0,
    "hostname": "Unknown",
    "last_seen": "Never"
}

command = None
screenshots = []
processes = []
files = []

# ===== AUTH =====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["ok"] = True
            return redirect("/")
    return """
    <body style="background:#0b1220;color:white;font-family:Arial;text-align:center;padding-top:100px">
        <h2>Login</h2>
        <form method="POST">
            <input name="password" type="password" />
            <button>Login</button>
        </form>
    </body>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ===== DASHBOARD =====
@app.route("/")
def home():
    if not session.get("ok"):
        return redirect("/login")

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin:0;
            font-family:Arial;
            background:#0b1220;
            color:white;
        }}

        .top {{
            padding:15px;
            display:flex;
            justify-content:space-between;
            background:#111a2e;
        }}

        .grid {{
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
            gap:10px;
            padding:10px;
        }}

        .card {{
            background:#16213a;
            padding:12px;
            border-radius:12px;
        }}

        .btn {{
            display:inline-block;
            padding:10px;
            margin:5px;
            background:#2b3a67;
            color:white;
            text-decoration:none;
            border-radius:8px;
        }}

        .danger {{ background:#d33; }}

        img {{
            width:100%;
            border-radius:10px;
            margin-top:10px;
        }}
    </style>
    </head>

    <body>

    <div class="top">
        <div>🖥️ PC Control</div>
        <a class="btn danger" href="/logout">Logout</a>
    </div>

    <div style="padding:10px;">
        <a class="btn" href="/cmd/screenshot">📸 Screenshot</a>
        <a class="btn" href="/cmd/lock">🔒 Lock</a>
        <a class="btn" href="/cmd/files">📁 Files</a>
    </div>

    <div class="grid">
        <div class="card">PC: {state["hostname"]}</div>
        <div class="card">CPU: {state["cpu"]}%</div>
        <div class="card">RAM: {state["ram"]}%</div>
        <div class="card">Disk: {state["disk"]}%</div>
        <div class="card">Status: {'🟢' if state['online'] else '🔴'}</div>
        <div class="card">Last: {state["last_seen"]}</div>
    </div>

    <div style="padding:10px;">
        <h3>Screenshots</h3>
        {''.join([f'<img src="/screenshots/{s}">' for s in screenshots])}

        <h3>Processes</h3>
        {''.join([f"<div class='card'>{p['name']} - {p['cpu']}%</div>" for p in processes])}

        <h3>Files</h3>
        {''.join([f"<div class='card'>{f}</div>" for f in files])}
    </div>

    </body>
    </html>
    """

# ===== COMMANDS =====
@app.route("/cmd/<c>")
def set_cmd(c):
    global command
    command = c
    return redirect("/")

@app.route("/api/command")
def get_cmd():
    global command
    c = command
    command = None
    return jsonify({"command": c})

# ===== STATUS =====
@app.route("/api/status", methods=["POST"])
def status():
    global state
    data = request.json

    state.update({
        "online": True,
        "cpu": data.get("cpu", 0),
        "ram": data.get("ram", 0),
        "disk": data.get("disk", 0),
        "hostname": data.get("hostname", "Unknown"),
        "last_seen": datetime.now().strftime("%H:%M:%S")
    })

    return {"ok": True}

# ===== SCREENSHOT UPLOAD =====
@app.route("/api/screenshot", methods=["POST"])
def upload():
    f = request.files["file"]
    name = datetime.now().strftime("%H%M%S") + ".png"
    f.save(f"screenshots/{name}")
    screenshots.append(name)
    return {"ok": True}

# ===== DATA UPDATES =====
@app.route("/api/processes", methods=["POST"])
def procs():
    global processes
    processes = request.json.get("processes", [])
    return {"ok": True}

@app.route("/api/files", methods=["POST"])
def file_update():
    global files
    files = request.json.get("files", [])
    return {"ok": True}

@app.route("/screenshots/<name>")
def img(name):
    return send_from_directory("screenshots", name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
