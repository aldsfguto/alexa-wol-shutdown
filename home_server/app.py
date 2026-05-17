import os

import requests
from flask import Flask, jsonify, request
from wakeonlan import send_magic_packet

app = Flask(__name__)

TARGET_MAC = os.getenv("TARGET_MAC", "22:23:5C:04:00:D8")
BROADCAST_IP = os.getenv("BROADCAST_IP", "192.168.1.255")
WOL_PORT = int(os.getenv("WOL_PORT", "9"))

CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "troque-este-token")
PC_AGENT_URL = os.getenv("PC_AGENT_URL", "http://192.168.1.4:5051")
PC_AGENT_TOKEN = os.getenv("PC_AGENT_TOKEN", CONTROL_TOKEN)


def require_token():
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {CONTROL_TOKEN}"
    return auth == expected


@app.get("/")
def home():
    return jsonify({"status": "online", "service": "home_server"})


@app.post("/ligar")
@app.get("/ligar")
def ligar():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    send_magic_packet(TARGET_MAC, ip_address=BROADCAST_IP, port=WOL_PORT)
    return jsonify(
        {
            "status": "ok",
            "message": "Pacote Wake-on-LAN enviado",
            "mac": TARGET_MAC,
            "broadcast": BROADCAST_IP,
            "port": WOL_PORT,
        }
    )


@app.post("/desligar")
@app.get("/desligar")
def desligar():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    response = requests.post(
        f"{PC_AGENT_URL.rstrip('/')}/desligar",
        headers={"Authorization": f"Bearer {PC_AGENT_TOKEN}"},
        timeout=10,
    )
    return jsonify(
        {
            "status": "ok",
            "message": "Comando de desligar enviado ao PC",
            "agent_status_code": response.status_code,
            "agent_response": response.text,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5050")))
