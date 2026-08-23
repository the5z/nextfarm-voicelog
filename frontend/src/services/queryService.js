const INTEGRATION_API_URL =
  "http://127.0.0.1:8002/api";


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
      `Integration API error: ${response.status}`;

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


export async function getCultivationLogs() {
  const response =
    await fetch(
      `${INTEGRATION_API_URL}/cultivation-logs`
    );

  const result =
    await parseResponse(
      response
    );

  return Array.isArray(
    result?.data
  )
    ? result.data
    : [];
}


export async function getLatestCultivationLog() {
  const logs =
    await getCultivationLogs();

  return logs[0] || null;
}


export async function getCultivationLogsByLotCode(
  lotCode
) {
  const normalizedLotCode =
    String(
      lotCode ?? ""
    )
      .trim()
      .toUpperCase();

  if (!normalizedLotCode) {
    return [];
  }

  const logs =
    await getCultivationLogs();

  return logs.filter(
    (log) =>
      String(
        log?.lot_code ?? ""
      )
        .trim()
        .toUpperCase() ===
      normalizedLotCode
  );
}


export async function getMasterData(
  type
) {
  const response =
    await fetch(
      `${INTEGRATION_API_URL}/master-data/${type}`
    );

  const result =
    await parseResponse(
      response
    );

  return Array.isArray(result)
    ? result
    : [];
}


export async function getActivities() {
  return getMasterData(
    "activities"
  );
}


export async function getLots() {
  return getMasterData(
    "lots"
  );
}


export async function getMaterials() {
  return getMasterData(
    "materials"
  );
}


export async function getUnits() {
  return getMasterData(
    "units"
  );
}