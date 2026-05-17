import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "troque-este-token")
HOME_SERVER_URL = os.getenv("HOME_SERVER_URL", "https://seu-servidor-local-exposto.example.com")
HOME_SERVER_TOKEN = os.getenv("HOME_SERVER_TOKEN", CONTROL_TOKEN)


def require_token():
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {CONTROL_TOKEN}"
    return auth == expected


def call_home_server(path):
    response = requests.post(
        f"{HOME_SERVER_URL.rstrip('/')}/{path.lstrip('/')}",
        headers={"Authorization": f"Bearer {HOME_SERVER_TOKEN}"},
        timeout=15,
    )
    return response


@app.get("/")
def home():
    return jsonify({"status": "online", "service": "railway_relay"})


@app.post("/ligar")
@app.get("/ligar")
def ligar():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    response = call_home_server("/ligar")
    return jsonify(
        {
            "status": "ok",
            "message": "Comando de ligar encaminhado",
            "home_status_code": response.status_code,
            "home_response": response.text,
        }
    )


@app.post("/desligar")
@app.get("/desligar")
def desligar():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    response = call_home_server("/desligar")
    return jsonify(
        {
            "status": "ok",
            "message": "Comando de desligar encaminhado",
            "home_status_code": response.status_code,
            "home_response": response.text,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
