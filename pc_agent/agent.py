import os
import subprocess

from flask import Flask, jsonify, request

app = Flask(__name__)

CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "troque-este-token")
SHUTDOWN_DELAY_SECONDS = int(os.getenv("SHUTDOWN_DELAY_SECONDS", "5"))


def require_token():
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {CONTROL_TOKEN}"
    return auth == expected


@app.get("/")
def home():
    return jsonify({"status": "online", "service": "pc_agent"})


@app.post("/desligar")
@app.get("/desligar")
def desligar():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    subprocess.Popen(
        ["shutdown", "/s", "/t", str(SHUTDOWN_DELAY_SECONDS)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return jsonify(
        {
            "status": "ok",
            "message": f"PC vai desligar em {SHUTDOWN_DELAY_SECONDS} segundos",
        }
    )


@app.post("/cancelar-desligamento")
@app.get("/cancelar-desligamento")
def cancelar_desligamento():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    subprocess.Popen(
        ["shutdown", "/a"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return jsonify({"status": "ok", "message": "Desligamento cancelado"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5051")))
