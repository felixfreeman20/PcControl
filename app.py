import os
from flask import Flask, request, jsonify, redirect, session, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

PASSWORD = os.environ.get("APP_PASSWORD")

pc_status = {
    "online": False,
    "cpu": 0,
    "ram": 0,
    "disk": 0,
    "hostname": "Unknown",
    "last_seen": "Never"
}

pending_command = None
process_list = []
SCREENSHOT_PATH = "latest.png"


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        return "Wrong password"

    return """
    <html>
    <body style="background:#0f172a;color:white;text-align:center;padding-top:100px;font-family:Arial;">
        <h1>Login</h1>
        <form method="POST">
            <input type="password" name="password"/>
            <button>Login</button>
        </form>
    </body>
    </html>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- COMMANDS ----------------
@app.route("/command")
def get_command():
    global pending_command
    cmd = pending_command
    pending_command = None
    return jsonify({"command": cmd})


@app.route("/screenshot_command")
def screenshot_command():
    global pending_command

    if not session.get("logged_in"):
        return redirect("/login")

    pending_command = "screenshot"
    return redirect("/")


@app.route("/processes_command")
def processes_command():
    global pending_command

    if not session.get("logged_in"):
        return redirect("/login")

    pending_command = "processes"
    return redirect("/")


# ---------------- DATA RECEIVERS ----------------
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


@app.route("/processes", methods=["POST"])
def processes():
    global process_list
    process_list = request.json.get("processes", [])
    return jsonify({"ok": True})


@app.route("/upload_screenshot", methods=["POST"])
def upload_screenshot():
    file = request.files["file"]
    file.save(SCREENSHOT_PATH)
    return jsonify({"ok": True})


@app.route("/latest_screenshot")
def latest_screenshot():
    return send_from_directory(".", SCREENSHOT_PATH)


# ---------------- DASHBOARD ----------------
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
        .card {{ background:#1e293b; padding:15px; margin:10px; border-radius:10px; }}
        .btn {{ padding:10px 15px; background:#2563eb; color:white; text-decoration:none; margin:5px; border-radius:8px; }}
        .danger {{ background:#ef4444; }}
    </style>
    </head>

    <body>

    <h1>PC Control Panel</h1>

    <a class="btn" href="/screenshot_command">📸 Screenshot</a>
    <a class="btn" href="/processes_command">⚙️ Processes</a>
    <a class="btn danger" href="/logout">Logout</a>

    <div class="card">PC: {pc_status["hostname"]}</div>
    <div class="card">CPU: {pc_status["cpu"]}%</div>
    <div class="card">RAM: {pc_status["ram"]}%</div>
    <div class="card">Disk: {pc_status["disk"]}%</div>
    <div class="card">Last Seen: {pc_status["last_seen"]}</div>

    <h2>Screenshot</h2>
    <img src="/latest_screenshot" width="600"/>

    <h2>Top Processes</h2>
    <pre>{process_list[:10]}</pre>

    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
