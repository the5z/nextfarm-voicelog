const INTEGRATION_API_BASE_URL = "http://127.0.0.1:8002";

const RESOLVE_API_URL =
  `${INTEGRATION_API_BASE_URL}/api/master-data/resolve`;

const VALIDATE_LOG_API_URL =
  `${INTEGRATION_API_BASE_URL}/api/cultivation-logs/validate`;

const SAVE_LOG_API_URL =
  `${INTEGRATION_API_BASE_URL}/api/cultivation-logs`;

export async function resolveMasterData(dataType, text) {
  if (!text || !text.trim()) {
    return {
      matched: false,
      code: null,
      name: null,
      requires_confirmation: true,
    };
  }

  const response = await fetch(RESOLVE_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      data_type: dataType,
      text: text.trim(),
    }),
  });

  if (!response.ok) {
    throw new Error(
      `Integration Service resolve error: ${response.status}`
    );
  }

  return response.json();
}

export async function validateCultivationLog(payload) {
  const response = await fetch(VALIDATE_LOG_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    console.error(
      "Cultivation log validation error:",
      errorData
    );

    throw new Error(
      `Integration Service validate error: ${response.status}`
    );
  }

  return response.json();
}

export async function saveCultivationLog(payload) {
  const response = await fetch(SAVE_LOG_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    console.error(
      "Cultivation log save error:",
      errorData
    );

    throw new Error(
      `Integration Service save error: ${response.status}`
    );
  }

  return response.json();
}