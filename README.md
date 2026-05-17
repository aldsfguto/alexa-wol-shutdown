# Alexa Wake-on-LAN + Desligar PC

Este projeto liga e desliga um PC Windows pela Alexa.

## Arquitetura

Use assim:

```text
Alexa -> AWS Lambda -> Railway -> servidor local -> PC
```

O Railway nao consegue enviar Wake-on-LAN direto para sua rede. Por isso o `home_server`
precisa rodar em um PC auxiliar, notebook, mini PC, Raspberry Pi ou outro dispositivo que
fique ligado dentro da sua casa.

Para desligar o PC, o `pc_agent` roda no PC alvo enquanto ele estiver ligado.

## Pastas

- `home_server`: roda dentro da sua rede e envia Wake-on-LAN.
- `pc_agent`: roda no PC alvo e executa o comando de desligar.
- `railway_relay`: roda no Railway e repassa comandos para o `home_server`.
- `lambda`: codigo da AWS Lambda.
- `alexa`: modelo de intents da Alexa.

## Valores do seu caso

- MAC Ethernet: `22:23:5C:04:00:D8`
- IP do PC alvo: `192.168.1.4`
- Broadcast da rede: `192.168.1.255`
- Gateway: `192.168.1.1`

## 1. Preparar token

Escolha um token secreto. Exemplo:

```text
minha-senha-grande-aqui-123
```

Use o mesmo token em todos os lugares abaixo.

## 2. PC alvo: instalar o agente de desligamento

No PC que sera ligado/desligado:

```powershell
cd caminho\para\alexa-wol-shutdown\pc_agent
python -m pip install -r requirements.txt
set CONTROL_TOKEN=minha-senha-grande-aqui-123
python agent.py
```

Teste no proprio PC alvo:

```powershell
curl.exe -X POST http://127.0.0.1:5051/desligar -H "Authorization: Bearer minha-senha-grande-aqui-123"
```

Se quiser cancelar rapidamente:

```powershell
shutdown /a
```

Libere a porta no Firewall do Windows:

```powershell
netsh advfirewall firewall add rule name="PC Shutdown Agent 5051" dir=in action=allow protocol=TCP localport=5051
```

Depois coloque o `agent.py` para iniciar com o Windows usando Agendador de Tarefas.

## 3. PC auxiliar: instalar o servidor local

No PC que fica ligado dentro da sua rede:

```powershell
cd caminho\para\alexa-wol-shutdown\home_server
python -m pip install -r requirements.txt
set TARGET_MAC=22:23:5C:04:00:D8
set BROADCAST_IP=192.168.1.255
set WOL_PORT=9
set CONTROL_TOKEN=minha-senha-grande-aqui-123
set PC_AGENT_URL=http://192.168.1.4:5051
set PC_AGENT_TOKEN=minha-senha-grande-aqui-123
python app.py
```

Teste ligar:

```powershell
curl.exe -X POST http://127.0.0.1:5050/ligar -H "Authorization: Bearer minha-senha-grande-aqui-123"
```

Teste desligar:

```powershell
curl.exe -X POST http://127.0.0.1:5050/desligar -H "Authorization: Bearer minha-senha-grande-aqui-123"
```

## 4. Expor o servidor local

Voce precisa dar uma URL publica ao `home_server`.

Opcoes:

- Cloudflare Tunnel
- ngrok
- Tailscale Funnel
- port forwarding no roteador

Exemplo de URL final:

```text
https://seu-servidor-local-exposto.example.com
```

Essa URL vai entrar no Railway como `HOME_SERVER_URL`.

## 5. Railway: publicar o relay

Publique a pasta `railway_relay` no Railway.

Variaveis no Railway:

```text
CONTROL_TOKEN=minha-senha-grande-aqui-123
HOME_SERVER_URL=https://seu-servidor-local-exposto.example.com
HOME_SERVER_TOKEN=minha-senha-grande-aqui-123
```

Teste:

```powershell
curl.exe -X POST https://SEU-APP.up.railway.app/ligar -H "Authorization: Bearer minha-senha-grande-aqui-123"
curl.exe -X POST https://SEU-APP.up.railway.app/desligar -H "Authorization: Bearer minha-senha-grande-aqui-123"
```

## 6. AWS Lambda

Crie uma Lambda Node.js 18 ou Node.js 20.

Cole o codigo de `lambda/index.js`.

Variaveis da Lambda:

```text
RAILWAY_BASE_URL=https://SEU-APP.up.railway.app
CONTROL_TOKEN=minha-senha-grande-aqui-123
```

## 7. Alexa Skill

No Alexa Developer Console:

1. Crie uma Custom Skill.
2. Invocation name: `meu computador`.
3. Crie as intents:
   - `LigarComputadorIntent`
   - `DesligarComputadorIntent`
4. Use o conteudo de `alexa/interaction-model.json` como modelo.
5. Em Endpoint, selecione AWS Lambda e cole o ARN da sua Lambda.
6. Build Model.
7. Teste com:

```text
Alexa, abrir meu computador
ligar computador
```

ou:

```text
Alexa, abrir meu computador
desligar computador
```

## 8. Checklist de Wake-on-LAN

No PC alvo:

- Cabo Ethernet conectado.
- LED da porta Ethernet aceso com o PC desligado.
- BIOS com Wake-on-LAN ativado.
- Windows com `Wake on Magic Packet` ativado.
- Inicializacao rapida desativada:

```powershell
powercfg /h off
```

Se o comando local `send_magic_packet` ja ligou o PC, esta parte esta pronta.
