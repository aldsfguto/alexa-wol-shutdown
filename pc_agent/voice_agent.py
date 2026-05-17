import os
import subprocess
import time
import webbrowser

import requests

RAILWAY_BASE_URL = os.getenv("RAILWAY_BASE_URL", "https://seu-app.up.railway.app").rstrip("/")
COMMAND_TOKEN = os.getenv("COMMAND_TOKEN", "troque-este-token")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "2"))
SHUTDOWN_DELAY_SECONDS = int(os.getenv("SHUTDOWN_DELAY_SECONDS", "5"))
RESTART_DELAY_SECONDS = int(os.getenv("RESTART_DELAY_SECONDS", "5"))
GAME_COMMAND = os.getenv("GAME_COMMAND", "")
STEAM_COMMAND = os.getenv("STEAM_COMMAND", "steam://open/main")
CHROME_COMMAND = os.getenv("CHROME_COMMAND", "chrome")


def auth_headers():
    return {"Authorization": f"Bearer {COMMAND_TOKEN}"}


def run_detached(command):
    subprocess.Popen(
        command,
        shell=isinstance(command, str),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def open_target(command):
    if command.startswith(("http://", "https://", "steam://")):
        webbrowser.open(command)
        return

    run_detached(command)


def execute(action):
    if action == "shutdown":
        run_detached(["shutdown", "/s", "/t", str(SHUTDOWN_DELAY_SECONDS)])
        return "Desligamento iniciado"

    if action == "restart":
        run_detached(["shutdown", "/r", "/t", str(RESTART_DELAY_SECONDS)])
        return "Reinicio iniciado"

    if action == "lock":
        run_detached(["rundll32.exe", "user32.dll,LockWorkStation"])
        return "Tela bloqueada"

    if action == "open_steam":
        open_target(STEAM_COMMAND)
        return f"Steam aberta com {STEAM_COMMAND}"

    if action == "open_chrome":
        open_target(CHROME_COMMAND)
        return f"Chrome aberto com {CHROME_COMMAND}"

    if action == "open_game":
        if not GAME_COMMAND:
            raise RuntimeError("GAME_COMMAND nao foi configurado")
        open_target(GAME_COMMAND)
        return f"Jogo aberto com {GAME_COMMAND}"

    raise RuntimeError(f"Comando desconhecido: {action}")


def report(command_id, action, ok, message):
    try:
        requests.post(
            f"{RAILWAY_BASE_URL}/commands/result",
            headers=auth_headers(),
            json={
                "command_id": command_id,
                "action": action,
                "ok": ok,
                "message": message,
            },
            timeout=10,
        )
    except requests.RequestException:
        pass


def main():
    print("Agente Alexa do PC iniciado")
    print(f"Railway: {RAILWAY_BASE_URL}")

    while True:
        try:
            response = requests.get(
                f"{RAILWAY_BASE_URL}/commands/next",
                headers=auth_headers(),
                timeout=15,
            )

            if response.status_code == 401:
                print("Token recusado pelo Railway. Confira COMMAND_TOKEN.")
                time.sleep(10)
                continue

            response.raise_for_status()
            data = response.json()
            command = data.get("command")

            if not command:
                time.sleep(POLL_SECONDS)
                continue

            command_id = command.get("id")
            action = command.get("action")
            print(f"Executando comando: {action}")

            try:
                message = execute(action)
                print(message)
                report(command_id, action, True, message)
            except Exception as error:
                message = str(error)
                print(f"Erro: {message}")
                report(command_id, action, False, message)

        except requests.RequestException as error:
            print(f"Erro falando com Railway: {error}")
            time.sleep(10)


if __name__ == "__main__":
    main()
