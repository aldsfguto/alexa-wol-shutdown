const BASE_URL = process.env.RAILWAY_BASE_URL;
const CONTROL_TOKEN = process.env.CONTROL_TOKEN;

async function callServer(path) {
  const response = await fetch(`${BASE_URL.replace(/\/$/, "")}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${CONTROL_TOKEN}`,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Servidor respondeu ${response.status}: ${body}`);
  }
}

function alexaResponse(text) {
  return {
    version: "1.0",
    response: {
      outputSpeech: {
        type: "PlainText",
        text,
      },
      shouldEndSession: true,
    },
  };
}

exports.handler = async (event) => {
  const intentName = event?.request?.intent?.name;

  try {
    if (intentName === "LigarComputadorIntent") {
      await callServer("/ligar");
      return alexaResponse("Ligando o computador");
    }

    if (intentName === "DesligarComputadorIntent") {
      await callServer("/desligar");
      return alexaResponse("Desligando o computador");
    }

    if (event?.request?.type === "LaunchRequest") {
      return alexaResponse("Pode falar ligar computador ou desligar computador");
    }

    return alexaResponse("Não entendi o comando");
  } catch (error) {
    console.error(error);
    return alexaResponse("Não consegui falar com o servidor do computador");
  }
};
