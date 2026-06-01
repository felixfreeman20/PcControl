import os
from flask import Flask, request, jsonify, redirect, session
from datetime import datetime
from collections import deque

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

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
file_list = []


# ===== LOGIN =====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect("/")

    return """
    <html>
    <body style="background:#0f172a;color:white;text-align:center;padding-top:100px;font-family:Arial;">
        <h2>Login</h2>
        <form method="POST">
            <input name="password" type="password" placeholder="Password">
            <button>Login</button>
        </form>
    </body>
    </html>
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
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ background:#0f172a; color:white; font-family:Arial; padding:20px; }}
        .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:15px; }}
        .card {{ background:#1e293b; padding:15px; border-radius:12px; }}
        .title {{ color:#94a3b8; font-size:12px; }}
        .value {{ font-size:22px; margin-top:10px; }}
        .online {{ color:#22c55e; }}
        .offline {{ color:#ef4444; }}
    </style>
    </head>

    <body>
    <h2>🖥️ PC Dashboard</h2>

    <a href="/logout">Logout</a>

    <div class="grid">

        <div class="card">
            <div class="title">Computer</div>
            <div class="value">{pc_status["hostname"]}</div>
        </div>

        <div class="card">
            <div class="title">Status</div>
            <div class="value">{'🟢 Online' if pc_status['online'] else '🔴 Offline'}</div>
        </div>

        <div class="card">
            <div class="title">CPU</div>
            <div class="value">{pc_status["cpu"]}%</div>
        </div>

        <div class="card">
            <div class="title">RAM</div>
            <div class="value">{pc_status["ram"]}%</div>
        </div>

        <div class="card">
            <div class="title">Disk</div>
            <div class="value">{pc_status["disk"]}%</div>
        </div>

        <div class="card">
            <div class="title">Last Seen</div>
            <div class="value">{pc_status["last_seen"]}</div>
        </div>

    </div>

    <h3>📸 Screenshots</h3>
    <ul>
        {''.join([f"<li>{s}</li>" for s in screenshots])}
    </ul>

    <h3>⚙️ Top Processes</h3>
    <ul>
        {''.join([f"<li>{p['name']} - {p['cpu_percent']}%</li>" for p in process_data])}
    </ul>

    </body>
    </html>
    """


# ===== STATUS UPDATE =====
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
    if not session.get("logged_in"):
        return jsonify({"command": None})

    if command_queue:
        return jsonify({"command": command_queue.popleft()})

    return jsonify({"command": None})


@app.route("/lock")
def lock():
    command_queue.append("lock")
    return redirect("/")


@app.route("/screenshot_cmd")
def screenshot_cmd():
    command_queue.append("screenshot")
    return redirect("/")


# ===== UPLOADS =====
@app.route("/upload_screenshot", methods=["POST"])
def upload_screenshot():
    file = request.files["file"]
    name = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
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
