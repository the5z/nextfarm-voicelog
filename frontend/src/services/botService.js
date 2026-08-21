const BOT_API_URL =
  "http://127.0.0.1:8000/api/v1/bot";


function normalizeText(value) {
  const text =
    String(value ?? "").trim();

  return text || null;
}


function normalizeQuantity(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }

  const quantity =
    Number(value);

  if (Number.isNaN(quantity)) {
    return null;
  }

  return quantity;
}


export function buildActivityPayload(
  aiData = {}
) {
  const materialText =
    normalizeText(
      aiData.material
    );

  const quantity =
    normalizeQuantity(
      aiData.quantity
    );

  const unitText =
    normalizeText(
      aiData.unit
    );

  const materials =
    materialText ||
    quantity !== null ||
    unitText
      ? [
          {
            material_text:
              materialText,

            quantity,

            unit_text:
              unitText,
          },
        ]
      : [];

  return {
    activity_text:
      normalizeText(
        aiData.work
      ),

    lot_text:
      normalizeText(
        aiData.lot
      ),

    materials,

    time_text:
      normalizeText(
        aiData.time
      ),

    missing_fields: [],

    warnings: [],

    requires_confirmation:
      false,
  };
}


async function parseResponse(
  response
) {
  let data = null;

  try {
    data =
      await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail =
      data?.detail ||
      `Voice Bot API error: ${response.status}`;

    throw new Error(
      typeof detail === "string"
        ? detail
        : JSON.stringify(
            detail
          )
    );
  }

  return data;
}


export async function createBotSession(
  aiData
) {
  const response =
    await fetch(
      `${BOT_API_URL}/sessions`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify(
          buildActivityPayload(
            aiData
          )
        ),
      }
    );

  return parseResponse(
    response
  );
}


export async function getBotSession(
  sessionId
) {
  const response =
    await fetch(
      `${BOT_API_URL}/sessions/${sessionId}`
    );

  return parseResponse(
    response
  );
}


export async function updateBotSession(
  sessionId,
  aiData
) {
  const response =
    await fetch(
      `${BOT_API_URL}/sessions/${sessionId}`,
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify(
          buildActivityPayload(
            aiData
          )
        ),
      }
    );

  return parseResponse(
    response
  );
}


export async function sendBotMessage(
  sessionId,
  message
) {
  const normalizedMessage =
    String(
      message ?? ""
    ).trim();

  if (!normalizedMessage) {
    throw new Error(
      "Voice Bot message is empty."
    );
  }

  const response =
    await fetch(
      `${BOT_API_URL}/sessions/${sessionId}/messages`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          message:
            normalizedMessage,
        }),
      }
    );

  return parseResponse(
    response
  );
}