# Alexa sem AWS Lambda

Este e o jeito mais simples sem usar AWS Lambda:

```text
Alexa Skill -> Railway -> seu roteador -> PC
```

Voce continua usando a Alexa por comando de voz, mas o endpoint da Skill aponta direto para o Railway.

## O que voce vai usar

- Railway: hospeda o servidor.
- Alexa Developer Console: cria a Skill.
- Roteador: encaminha portas para ligar/desligar o PC.
- PC Windows: roda um agente pequeno apenas para desligar.

## Arquivos usados

- `voice_only_railway/app.py`: servidor principal no Railway, com endpoint `/alexa`.
- `pc_agent/agent.py`: agente local para desligar o Windows.
- `alexa/interaction-model.json`: intents da Alexa.

Nao precisa mais de:

- AWS Lambda;
- pasta `lambda`;
- outro PC ligado;
- celular para acionar.

## 1. Configurar o roteador

Reserve o IP do PC:

```text
IP: 192.168.1.4
MAC: 22:23:5C:04:00:D8
```

Crie port forwarding para ligar:

```text
UDP 9 -> 192.168.1.255:9
```

Se o roteador nao aceitar `192.168.1.255`, tente:

```text
UDP 9 -> 192.168.1.4:9
```

Crie port forwarding para desligar:

```text
TCP 5051 -> 192.168.1.4:5051
```

## 2. Rodar o agente de desligamento no PC

No PC que vai desligar:

```powershell
cd C:\Users\Augusto\Documents\Codex\2026-05-16\files-mentioned-by-the-user-test\alexa-wol-shutdown\pc_agent
python -m pip install -r requirements.txt
set CONTROL_TOKEN=troque-este-token
python agent.py
```

Libere a porta no Firewall:

```powershell
netsh advfirewall firewall add rule name="PC Shutdown Agent 5051" dir=in action=allow protocol=TCP localport=5051
```

Teste local:

```powershell
curl.exe -X POST http://127.0.0.1:5051/desligar -H "Authorization: Bearer troque-este-token"
```

Para cancelar:

```powershell
shutdown /a
```

Depois, coloque o `agent.py` para iniciar com o Windows pelo Agendador de Tarefas.

## 3. Subir o servidor no Railway

Suba esta pasta no Railway:

```text
alexa-wol-shutdown/voice_only_railway
```

Variaveis no Railway:

```text
CONTROL_TOKEN=troque-este-token
TARGET_MAC=22:23:5C:04:00:D8
WOL_IP_ADDRESS=SEU_IP_PUBLICO_OU_DDNS
WOL_PORT=9
SHUTDOWN_URL=http://SEU_IP_PUBLICO_OU_DDNS:5051/desligar
SHUTDOWN_TOKEN=troque-este-token
```

Depois que criar a Skill, voce tambem pode adicionar:

```text
ALEXA_SKILL_ID=amzn1.ask.skill.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Deixe vazio no primeiro teste se quiser simplificar.

Teste manual:

```powershell
curl.exe -X POST https://SEU-APP.up.railway.app/ligar -H "Authorization: Bearer troque-este-token"
curl.exe -X POST https://SEU-APP.up.railway.app/desligar -H "Authorization: Bearer troque-este-token"
```

## 4. Criar Skill Alexa sem Lambda

No Alexa Developer Console:

1. Crie uma `Custom Skill`.
2. Nome pode ser `Meu Computador`.
3. Invocation name: `meu computador`.
4. Em `Interaction Model`, use o arquivo:

```text
alexa/interaction-model.json
```

5. Em `Endpoint`, escolha `HTTPS`.
6. Default Region:

```text
https://SEU-APP.up.railway.app/alexa
```

7. SSL certificate type:

```text
My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority
```

ou a opcao equivalente de certificado valido por autoridade confiavel.

8. Clique em `Save Endpoints`.
9. Clique em `Build Model`.
10. Va em `Test` e habilite teste da skill.

## 5. Comandos de voz

Use assim:

```text
Alexa, abrir meu computador
ligar computador
```

Ou:

```text
Alexa, abrir meu computador
desligar computador
```

Dependendo da configuracao da Skill, tambem pode funcionar:

```text
Alexa, pedir para meu computador ligar computador
```

```text
Alexa, pedir para meu computador desligar computador
```

## 6. Se nao ligar pela Alexa

Se o comando local de Wake-on-LAN funcionou, mas pela Alexa nao funciona, o problema quase sempre e um destes:

- o roteador nao encaminha UDP para broadcast;
- o IP publico mudou e voce precisa de DDNS;
- a operadora usa CGNAT;
- o encaminhamento UDP 9 esta indo para o IP errado;
- o PC nao manteve o IP `192.168.1.4`.

CGNAT e o mais chato: se o IP WAN do roteador for diferente do IP visto em sites de "meu IP", port forwarding nao vai funcionar direto.
