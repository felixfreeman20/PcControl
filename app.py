import os
from flask import Flask, request, jsonify, redirect, session, send_from_directory
from datetime import datetime
from collections import deque

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

PASSWORD = os.environ.get("APP_PASSWORD", "1234")

pc_status = {
    "online": False,
    "cpu": 0,
    "ram": 0,
    "disk": 0,
    "hostname": "Unknown",
    "last_seen": "Never"
}

command_queue = deque()
screenshots = []
process_data = []

os.makedirs("screenshots", exist_ok=True)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect("/")
    return """
    <body style="background:#0f172a;color:white;font-family:Arial;text-align:center;padding-top:100px;">
        <h2>Login</h2>
        <form method="POST">
            <input name="password" type="password">
            <button>Login</button>
        </form>
    </body>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- DASHBOARD ----------------
@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect("/login")

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ margin:0;font-family:Arial;background:#0f172a;color:white; }}
        .top {{ padding:15px;background:#111827;display:flex;justify-content:space-between; }}
        .grid {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;padding:10px; }}
        .card {{ background:#1e293b;padding:10px;border-radius:10px; }}
        a {{ color:white;text-decoration:none;margin-right:10px; }}
        img {{ width:100%;border-radius:10px;margin-top:10px; }}
    </style>
    </head>

    <body>

    <div class="top">
        <div>🖥️ PC Control</div>
        <div>
            <a href="/cmd/screenshot">📸 Screenshot</a>
            <a href="/cmd/lock">🔒 Lock</a>
            <a href="/logout">Logout</a>
        </div>
    </div>

    <div class="grid">
        <div class="card">CPU: {pc_status["cpu"]}%</div>
        <div class="card">RAM: {pc_status["ram"]}%</div>
        <div class="card">Disk: {pc_status["disk"]}%</div>
        <div class="card">PC: {pc_status["hostname"]}</div>
        <div class="card">Last: {pc_status["last_seen"]}</div>
    </div>

    <div style="padding:10px;">
        <h3>📸 Screenshots</h3>
        {''.join([f'<img src="/screenshots/{s}">' for s in screenshots])}

        <h3>⚙️ Processes</h3>
        {''.join([f"<div class='card'>{p['name']} - {p['cpu']}%</div>" for p in process_data])}
    </div>

    </body>
    </html>
    """

# ---------------- COMMANDS ----------------
@app.route("/cmd/<action>")
def cmd(action):
    if not session.get("logged_in"):
        return redirect("/login")

    command_queue.append(action)
    return redirect("/")

@app.route("/command")
def get_command():
    if command_queue:
        return jsonify({"cmd": command_queue.popleft()})
    return jsonify({"cmd": None})

# ---------------- STATUS ----------------
@app.route("/status", methods=["POST"])
def status():
    data = request.json

    pc_status.update({
        "online": True,
        "cpu": data.get("cpu", 0),
        "ram": data.get("ram", 0),
        "disk": data.get("disk", 0),
        "hostname": data.get("hostname", "Unknown"),
        "last_seen": datetime.now().strftime("%H:%M:%S")
    })

    return jsonify({"ok": True})

# ---------------- SCREENSHOT UPLOAD ----------------
@app.route("/upload_screenshot", methods=["POST"])
def upload_screenshot():
    file = request.files["file"]
    name = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
    path = os.path.join("screenshots", name)
    file.save(path)
    screenshots.append(name)
    return jsonify({"ok": True})

# ---------------- PROCESS LIST ----------------
@app.route("/processes", methods=["POST"])
def processes():
    global process_data
    process_data = request.json.get("processes", [])
    return jsonify({"ok": True})

# ---------------- FILES ----------------
@app.route("/screenshots/<name>")
def get_screenshot(name):
    return send_from_directory("screenshots", name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
