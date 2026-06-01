import psutil
import requests
import time
import socket

SERVER_URL = "http://127.0.0.1:5000/status"

while True:
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent

    data = {
        "cpu": cpu,
        "ram": ram,
        "disk": psutil.disk_usage("C:\\").percent,
        "hostname": socket.gethostname()
    }

    try:
        requests.post(SERVER_URL, json=data, timeout=5)
        print("Sent:", data)

    except Exception as e:
        print("Server unavailable:", e)

    time.sleep(10)