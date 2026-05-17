import os

import requests
from flask import Flask, jsonify, request
from wakeonlan import send_magic_packet

app = Flask(__name__)

CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "troque-este-token")
ALEXA_SKILL_ID = os.getenv("ALEXA_SKILL_ID", "")

TARGET_MAC = os.getenv("TARGET_MAC", "22:23:5C:04:00:D8")
WOL_IP_ADDRESS = os.getenv("WOL_IP_ADDRESS", "seu-ip-publico-ou-ddns")
WOL_PORT = int(os.getenv("WOL_PORT", "9"))

SHUTDOWN_URL = os.getenv("SHUTDOWN_URL", "http://seu-ip-publico-ou-ddns:5051/desligar")
SHUTDOWN_TOKEN = os.getenv("SHUTDOWN_TOKEN", CONTROL_TOKEN)


def require_token():
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {CONTROL_TOKEN}"


def alexa_response(text):
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text,
            },
            "shouldEndSession": True,
        },
    }


def get_alexa_application_id(payload):
    session_app_id = (
        payload.get("session", {})
        .get("application", {})
        .get("applicationId")
    )
    context_app_id = (
        payload.get("context", {})
        .get("System", {})
        .get("application", {})
        .get("applicationId")
    )
    return session_app_id or context_app_id or ""


def send_wol():
    send_magic_packet(TARGET_MAC, ip_address=WOL_IP_ADDRESS, port=WOL_PORT)


def send_shutdown():
    return requests.post(
        SHUTDOWN_URL,
        headers={"Authorization": f"Bearer {SHUTDOWN_TOKEN}"},
        timeout=15,
    )


@app.get("/")
def home():
    return jsonify({"status": "online", "service": "voice_only_railway"})


@app.get("/debug-config")
def debug_config():
    return jsonify(
        {
            "control_token_is_default": CONTROL_TOKEN == "troque-este-token",
            "has_control_token": bool(CONTROL_TOKEN),
            "target_mac": TARGET_MAC,
            "wol_ip_address": WOL_IP_ADDRESS,
            "wol_ip_is_default": WOL_IP_ADDRESS == "seu-ip-publico-ou-ddns",
            "wol_port": WOL_PORT,
            "shutdown_url": SHUTDOWN_URL,
            "shutdown_token_is_default": SHUTDOWN_TOKEN == "troque-este-token",
        }
    )


@app.post("/alexa")
def alexa():
    payload = request.get_json(silent=True) or {}

    if ALEXA_SKILL_ID:
        application_id = get_alexa_application_id(payload)
        if application_id != ALEXA_SKILL_ID:
            return jsonify(alexa_response("Skill nao autorizada")), 403

    request_type = payload.get("request", {}).get("type")
    intent_name = (
        payload.get("request", {})
        .get("intent", {})
        .get("name")
    )

    try:
        if request_type == "LaunchRequest":
            return jsonify(alexa_response("Pode falar ligar computador ou desligar computador"))

        if intent_name == "LigarComputadorIntent":
            send_wol()
            return jsonify(alexa_response("Ligando o computador"))

        if intent_name == "DesligarComputadorIntent":
            send_shutdown()
            return jsonify(alexa_response("Desligando o computador"))

        if intent_name in ("AMAZON.CancelIntent", "AMAZON.StopIntent"):
            return jsonify(alexa_response("Tudo bem"))

        if intent_name == "AMAZON.HelpIntent":
            return jsonify(alexa_response("Fale ligar computador ou desligar computador"))

        return jsonify(alexa_response("Nao entendi o comando"))
    except Exception as error:
        print(error)
        return jsonify(alexa_response("Nao consegui falar com o computador"))


@app.post("/ligar")
@app.get("/ligar")
def ligar():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    send_wol()
    return jsonify(
        {
            "status": "ok",
            "message": "Pacote Wake-on-LAN enviado pela internet",
            "mac": TARGET_MAC,
            "ip_address": WOL_IP_ADDRESS,
            "port": WOL_PORT,
        }
    )


@app.post("/desligar")
@app.get("/desligar")
def desligar():
    if not require_token():
        return jsonify({"status": "error", "message": "unauthorized"}), 401

    response = send_shutdown()
    return jsonify(
        {
            "status": "ok",
            "message": "Comando de desligar enviado",
            "shutdown_status_code": response.status_code,
            "shutdown_response": response.text,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
