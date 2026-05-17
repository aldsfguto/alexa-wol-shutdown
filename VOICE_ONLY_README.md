# Modo somente Alexa, sem celular e sem outro PC

Este e o modo que voce pediu:

```text
Alexa -> AWS Lambda -> Railway -> seu roteador -> PC
```

Ele nao usa celular nem outro PC ligado. Mas depende do seu roteador aceitar Wake-on-LAN vindo da internet.

## Limite importante

Wake-on-LAN e um pacote de rede local. Para a Alexa ligar o PC sem outro dispositivo dentro da sua casa, o roteador precisa encaminhar um pacote UDP da internet para a rede interna.

Funciona se o roteador permitir uma destas opcoes:

- encaminhar UDP porta `9` para broadcast `192.168.1.255`;
- encaminhar UDP porta `9` para o IP fixo do PC `192.168.1.4` e manter ARP/static DHCP;
- ter recurso proprio de Wake-on-LAN;
- aceitar regra de static ARP/IP-MAC.

Se o roteador bloquear isso, nao existe arquivo Python que resolva sozinho. A alternativa sem outro PC e usar um roteador com WoL, firmware tipo OpenWrt, ou tomada inteligente com BIOS configurada para ligar ao voltar energia.

## Arquivos deste modo

- `voice_only_railway/app.py`: Railway manda WoL direto para seu IP publico.
- `pc_agent/agent.py`: roda no PC alvo para desligar o Windows.
- `lambda/index.js`: Lambda da Alexa.
- `alexa/interaction-model.json`: intents da Alexa.

## 1. Fixar o IP do PC no roteador

No roteador, reserve este IP para o MAC do PC:

```text
IP: 192.168.1.4
MAC: 22:23:5C:04:00:D8
```

Procure por algo como:

- DHCP Reservation
- Reserva DHCP
- Address Reservation
- Static Lease

## 2. Configurar port forwarding para ligar

No roteador, crie uma regra:

```text
Protocolo: UDP
Porta externa: 9
Destino interno preferido: 192.168.1.255
Porta interna: 9
```

Se o roteador nao aceitar `192.168.1.255`, tente:

```text
Protocolo: UDP
Porta externa: 9
Destino interno: 192.168.1.4
Porta interna: 9
```

## 3. Configurar port forwarding para desligar

No roteador, crie outra regra:

```text
Protocolo: TCP
Porta externa: 5051
Destino interno: 192.168.1.4
Porta interna: 5051
```

Esta porta so funciona quando o PC esta ligado, porque ela chama o agente local de desligamento.

## 4. Rodar o agente no PC alvo

No PC que sera desligado pela Alexa:

```powershell
cd C:\Users\Augusto\Documents\Codex\2026-05-16\files-mentioned-by-the-user-test\alexa-wol-shutdown\pc_agent
python -m pip install -r requirements.txt
set CONTROL_TOKEN=troque-este-token
python agent.py
```

Libere no firewall:

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

Depois coloque o `agent.py` para iniciar com o Windows pelo Agendador de Tarefas.

## 5. Descobrir seu IP publico ou criar DDNS

Voce precisa de um destino fixo para o Railway.

Opcoes:

- IP publico atual do seu roteador;
- DDNS do roteador, tipo `meunome.ddns.net`;
- dominio apontando para sua casa.

Se seu IP publico muda, use DDNS.

## 6. Subir o Railway

Publique a pasta:

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

Teste pelo PowerShell:

```powershell
curl.exe -X POST https://SEU-APP.up.railway.app/ligar -H "Authorization: Bearer troque-este-token"
curl.exe -X POST https://SEU-APP.up.railway.app/desligar -H "Authorization: Bearer troque-este-token"
```

## 7. Configurar AWS Lambda

Crie uma Lambda Node.js 18 ou Node.js 20.

Cole o conteudo de:

```text
lambda/index.js
```

Variaveis da Lambda:

```text
RAILWAY_BASE_URL=https://SEU-APP.up.railway.app
CONTROL_TOKEN=troque-este-token
```

## 8. Configurar Alexa

No Alexa Developer Console:

1. Crie uma Custom Skill.
2. Invocation name: `meu computador`.
3. Crie `LigarComputadorIntent`.
4. Crie `DesligarComputadorIntent`.
5. Use `alexa/interaction-model.json`.
6. Endpoint: ARN da Lambda.
7. Build Model.

Comandos de voz:

```text
Alexa, abrir meu computador
ligar computador
```

```text
Alexa, abrir meu computador
desligar computador
```

## 9. Se ligar local mas nao ligar pela Alexa

Se o comando local funcionou, mas pelo Railway/Alexa nao, o problema esta no roteador.

Teste estas possibilidades:

- trocar port forwarding de `192.168.1.255` para `192.168.1.4`;
- garantir reserva DHCP do PC em `192.168.1.4`;
- procurar no roteador por `Wake on LAN`, `Static ARP`, `IP & MAC Binding`;
- usar DDNS se o IP publico mudou;
- verificar se voce esta atras de CGNAT. Se estiver, port forwarding nao funciona.

Para saber se tem CGNAT, compare o IP WAN mostrado no roteador com o IP publico mostrado em sites de "meu IP". Se forem diferentes, provavelmente e CGNAT.
