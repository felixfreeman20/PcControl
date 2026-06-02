import os
from flask import Flask, request, jsonify, redirect, session, send_from_directory
from datetime import datetime
from collections import deque

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

PASSWORD = os.environ.get("APP_PASSWORD")

pc_status = {
    "online": False,
    "cpu": 0,
    "ram": 0,
    "disk": 0,
    "hostname": "Unknown",
    "last_seen": "Never"
}

commands = deque()
screenshots = []
processes = []

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["ok"] = True
            return redirect("/")
    return """
    <body style="background:#111;color:white;text-align:center;padding-top:100px;font-family:Arial">
        <h2>Login</h2>
        <form method="POST">
            <input name="password" type="password">
            <button>Enter</button>
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
    if not session.get("ok"):
        return redirect("/login")

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family:Arial; background:#0f172a; color:white; margin:0; }}
        .top {{ padding:15px; background:#111827; display:flex; justify-content:space-between; }}
        .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; padding:10px; }}
        .card {{ background:#1e293b; padding:12px; border-radius:10px; }}
        a {{ color:white; text-decoration:none; margin-right:10px; }}
        button {{ padding:8px; border:none; border-radius:6px; }}
        .btn {{ background:#2563eb; color:white; }}
        .danger {{ background:#ef4444; }}
        img {{ width:100%; border-radius:10px; margin-top:10px; }}
    </style>
    </head>

    <body>

    <div class="top">
        <div>🖥 PC Control</div>
        <div>
            <a href="/screenshot">📸 Screenshot</a>
            <a href="/lock">🔒 Lock</a>
            <a href="/logout">Logout</a>
        </div>
    </div>

    <div class="grid">
        <div class="card">CPU<br>{pc_status["cpu"]}%</div>
        <div class="card">RAM<br>{pc_status["ram"]}%</div>
        <div class="card">Disk<br>{pc_status["disk"]}%</div>
        <div class="card">Status<br>{pc_status["online"]}</div>
        <div class="card">PC<br>{pc_status["hostname"]}</div>
        <div class="card">Last<br>{pc_status["last_seen"]}</div>
    </div>

    <h3 style="padding:10px">Screenshots</h3>
    {"".join([f'<img src="/shots/{s}">' for s in screenshots])}

    <h3 style="padding:10px">Processes</h3>
    {"".join([f"<div class='card'>{p['name']} - {p['cpu']}%</div>" for p in processes])}

    </body>
    </html>
    """

# ---------------- API ----------------
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

@app.route("/command")
def command():
    if not session.get("ok"):
        return jsonify({"cmd": None})

    if commands:
        return jsonify({"cmd": commands.popleft()})

    return jsonify({"cmd": None})

@app.route("/lock")
def lock():
    commands.append("lock")
    return redirect("/")

@app.route("/screenshot")
def screenshot():
    commands.append("screenshot")
    return redirect("/")

@app.route("/upload_screenshot", methods=["POST"])
def upload():
    f = request.files["file"]
    name = datetime.now().strftime("%H%M%S") + ".png"
    f.save("screenshots/" + name)
    screenshots.append(name)
    return jsonify({"ok": True})

@app.route("/shots/<name>")
def shots(name):
    return send_from_directory("screenshots", name)

@app.route("/processes", methods=["POST"])
def proc():
    global processes
    processes = request.json.get("processes", [])
    return jsonify({"ok": True})

if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
