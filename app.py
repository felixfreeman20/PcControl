import os

PASSWORD = os.environ.get("APP_PASSWORD")
from flask import Flask, request, jsonify
from datetime import datetime
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

pc_status = {
    "online": False,
    "cpu": 0,
    "ram": 0,
    "disk": 0,
    "hostname": "Unknown",
    "last_seen": "Never"
}

@app.route("/")
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PC Control Dashboard</title>
        <meta http-equiv="refresh" content="5">

        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: white;
                margin: 0;
                padding: 30px;
            }}

            h1 {{
                text-align: center;
                margin-bottom: 30px;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }}

            .card {{
                background: #1e293b;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
            }}

            .title {{
                font-size: 14px;
                color: #94a3b8;
            }}

            .value {{
                font-size: 30px;
                font-weight: bold;
                margin-top: 10px;
            }}

            .online {{
                color: #22c55e;
            }}

            .offline {{
                color: #ef4444;
            }}

            .footer {{
                margin-top: 30px;
                text-align: center;
                color: #94a3b8;
            }}
        </style>
    </head>

    <body>

        <h1>🖥️ PC Control Dashboard</h1>

        <div class="grid">

            <div class="card">
                <div class="title">Computer</div>
                <div class="value">{pc_status["hostname"]}</div>
            </div>

            <div class="card">
                <div class="title">Status</div>
                <div class="value {'online' if pc_status['online'] else 'offline'}">
                    {'🟢 Online' if pc_status['online'] else '🔴 Offline'}
                </div>
            </div>

            <div class="card">
                <div class="title">CPU Usage</div>
                <div class="value">{pc_status["cpu"]}%</div>
            </div>

            <div class="card">
                <div class="title">RAM Usage</div>
                <div class="value">{pc_status["ram"]}%</div>
            </div>

            <div class="card">
                <div class="title">Disk Usage</div>
                <div class="value">{pc_status["disk"]}%</div>
            </div>

            <div class="card">
                <div class="title">Last Seen</div>
                <div class="value" style="font-size:22px;">
                    {pc_status["last_seen"]}
                </div>
            </div>

        </div>

        <div class="footer">
            Auto-refreshes every 5 seconds
        </div>

    </body>
    </html>
    """

@app.route("/status", methods=["POST"])
def status():
    global pc_status

    data = request.json

    pc_status["online"] = True
    pc_status["cpu"] = data.get("cpu", 0)
    pc_status["ram"] = data.get("ram", 0)
    pc_status["disk"] = data.get("disk", 0)
    pc_status["hostname"] = data.get("hostname", "Unknown")
    pc_status["last_seen"] = datetime.now().strftime("%H:%M:%S")

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
