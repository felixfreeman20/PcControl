import os
from flask import Flask, request, jsonify, redirect, session, send_from_directory
from datetime import datetime

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

pending_command = None
screenshots = []
process_data = []

# ===== SCREENSHOT FILE ACCESS =====
os.makedirs("screenshots", exist_ok=True)

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

# ===== LOGOUT =====
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
    <body style="background:#0f172a;color:white;font-family:Arial;padding:20px;">
        <h1>PC Dashboard</h1>

        <a href="/screenshot_cmd">📸 Screenshot</a> |
        <a href="/lock">🔒 Lock</a> |
        <a href="/logout">Logout</a>

        <hr>

        <p><b>PC:</b> {pc_status["hostname"]}</p>
        <p><b>Status:</b> {'🟢 Online' if pc_status['online'] else '🔴 Offline'}</p>
        <p><b>CPU:</b> {pc_status["cpu"]}%</p>
        <p><b>RAM:</b> {pc_status["ram"]}%</p>
        <p><b>Disk:</b> {pc_status["disk"]}%</p>
        <p><b>Last:</b> {pc_status["last_seen"]}</p>

        <h3>Screenshots</h3>
        {''.join([f'<img src="/screenshots/{s}" width="300"><br>' for s in screenshots])}

        <h3>Processes</h3>
        {''.join([f"<div>{p['name']} - {p['cpu_percent']}%</div>" for p in process_data])}
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

# ===== COMMAND SYSTEM (FIXED) =====
@app.route("/command")
def command():
    global pending_command

    cmd = pending_command
    pending_command = None

    return jsonify({"command": cmd})

@app.route("/screenshot_cmd")
def screenshot_cmd():
    global pending_command
    pending_command = "screenshot"
    return redirect("/")

@app.route("/lock")
def lock():
    global pending_command
    pending_command = "lock"
    return redirect("/")

# ===== UPLOAD SCREENSHOT =====
@app.route("/upload_screenshot", methods=["POST"])
def upload_screenshot():
    file = request.files["file"]

    name = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
    path = f"screenshots/{name}"
    file.save(path)

    screenshots.append(name)

    return jsonify({"ok": True})

# ===== PROCESS LIST =====
@app.route("/processes", methods=["POST"])
def processes():
    global process_data
    process_data = request.json.get("processes", [])
    return jsonify({"ok": True})

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
