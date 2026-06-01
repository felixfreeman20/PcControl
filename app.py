import os
from flask import Flask, request, jsonify, redirect, session
from datetime import datetime
from collections import deque
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

PASSWORD = os.environ.get("APP_PASSWORD")
os.makedirs("screenshots", exist_ok=True)
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

@app.route("/screenshots/<filename>")
def get_screenshot(filename):
    return send_from_directory("screenshots", filename)

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
    <!DOCTYPE html>
    <html>
    <head>
        <title>PC Control</title>

        <style>
            * {{
                margin:0;
                padding:0;
                box-sizing:border-box;
                font-family:Arial;
            }}

            body {{
                display:flex;
                background:#0f172a;
                color:white;
                height:100vh;
            }}

            /* SIDEBAR */
            .sidebar {{
                width:220px;
                background:#111827;
                padding:20px;
            }}

            .sidebar h2 {{
                font-size:18px;
                margin-bottom:20px;
            }}

            .btn {{
                display:block;
                padding:10px;
                margin-bottom:10px;
                border-radius:8px;
                text-decoration:none;
                color:white;
                background:#1f2937;
            }}

            .btn:hover {{
                background:#374151;
            }}

            .danger {{
                background:#ef4444;
            }}

            .danger:hover {{
                background:#dc2626;
            }}

            .main {{
                flex:1;
                padding:20px;
                overflow:auto;
            }}

            /* GRID */
            .grid {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
                gap:15px;
            }}

            .card {{
                background:#1e293b;
                padding:15px;
                border-radius:12px;
            }}

            .title {{
                color:#94a3b8;
                font-size:12px;
            }}

            .value {{
                font-size:20px;
                margin-top:10px;
            }}

            .section {{
                margin-top:20px;
            }}

            img {{
                width:100%;
                border-radius:10px;
                margin-top:10px;
            }}

        </style>
    </head>

    <body>

        <!-- SIDEBAR -->
        <div class="sidebar">
            <h2>🖥️ Control</h2>

            <a class="btn" href="/">Dashboard</a>
            <a class="btn" href="/screenshot_cmd">📸 Screenshot</a>
            <a class="btn" href="/lock">🔒 Lock PC</a>

            <a class="btn danger" href="/logout">Logout</a>
        </div>

        <!-- MAIN -->
        <div class="main">

            <h1>PC Dashboard</h1>

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

            <!-- SCREENSHOTS -->
            <div class="section">
                <h2>📸 Screenshots</h2>
                {"".join([f'<img src="/screenshots/{s}">' for s in screenshots])}
            </div>

            <!-- PROCESSES -->
            <div class="section">
                <h2>⚙️ Top Processes</h2>
                {"".join([f"<div class='card'>{p['name']} - {p['cpu_percent']}%</div>" for p in process_data])}
            </div>

        </div>

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
