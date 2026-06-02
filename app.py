import os
from flask import Flask, request, jsonify, redirect, session, send_from_directory
from datetime import datetime
from collections import deque

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

PASSWORD = os.environ.get("APP_PASSWORD")

# ===== STATE =====
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

# ===== SCREENSHOT FILES =====
os.makedirs("screenshots", exist_ok=True)

@app.route("/screenshots/<path:name>")
def get_screenshot(name):
    return send_from_directory("screenshots", name)


# ===== LOGIN =====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect("/")
    return """
    <body style="background:#0f172a;color:white;text-align:center;padding-top:100px;">
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


# ===== DASHBOARD =====
@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect("/login")

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {{ background:#0b1220; color:white; font-family:Arial; padding:15px; }}
        .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }}
        .card {{ background:#1e293b; padding:12px; border-radius:10px; }}
        .btn {{ padding:10px; margin:5px; background:#2563eb; color:white; border-radius:8px; text-decoration:none; display:inline-block; }}
        .danger {{ background:#ef4444; }}
        img {{ width:100%; border-radius:10px; margin-top:10px; }}
    </style>
    </head>

    <body>

    <h2>🖥️ PC Control</h2>

    <a class="btn" href="/cmd/screenshot">📸 Screenshot</a>
    <a class="btn" href="/cmd/lock">🔒 Lock</a>
    <a class="btn danger" href="/logout">Logout</a>

    <div class="grid">
        <div class="card">CPU<br>{pc_status["cpu"]}%</div>
        <div class="card">RAM<br>{pc_status["ram"]}%</div>
        <div class="card">Disk<br>{pc_status["disk"]}%</div>
        <div class="card">PC<br>{pc_status["hostname"]}</div>
        <div class="card">Last<br>{pc_status["last_seen"]}</div>
    </div>

    <h3>📸 Screenshots</h3>
    {''.join([f'<img src="/screenshots/{s}">' for s in screenshots])}

    <h3>⚙️ Processes</h3>
    {''.join([f"<div>{p['name']} - {p['cpu']}%</div>" for p in process_data])}

    </body>
    </html>
    """


# ===== STATUS =====
@app.route("/status", methods=["POST"])
def status():
    global pc_status

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


# ===== COMMAND SYSTEM =====
@app.route("/command")
def command():
    if command_queue:
        return jsonify({"cmd": command_queue.popleft()})
    return jsonify({"cmd": None})


@app.route("/cmd/<action>")
def add_cmd(action):
    command_queue.append(action)
    return redirect("/")


# ===== UPLOADS =====
@app.route("/upload_screenshot", methods=["POST"])
def upload_screenshot():
    file = request.files["file"]
    name = datetime.now().strftime("%H%M%S") + ".png"
    file.save(f"screenshots/{name}")
    screenshots.append(name)
    return jsonify({"ok": True})


@app.route("/processes", methods=["POST"])
def processes():
    global process_data
    process_data = request.json.get("processes", [])
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
