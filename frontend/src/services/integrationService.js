const INTEGRATION_API_URL =
  "http://127.0.0.1:8002/api/master-data/resolve";

export async function resolveMasterData(dataType, text) {
  if (!text || !text.trim()) {
    return {
      matched: false,
      code: null,
      name: null,
      requires_confirmation: true,
    };
  }

  const response = await fetch(INTEGRATION_API_URL, {
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
      `Integration Service error: ${response.status}`
    );
  }

  return response.json();
}