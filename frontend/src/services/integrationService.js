const INTEGRATION_API_BASE_URL =
  String(
    import.meta.env.VITE_INTEGRATION_API_URL ||
      "http://127.0.0.1:8002"
  ).replace(/\/+$/, "");

const RESOLVE_API_URL =
  `${INTEGRATION_API_BASE_URL}/api/master-data/resolve`;

const VALIDATE_LOG_API_URL =
  `${INTEGRATION_API_BASE_URL}/api/cultivation-logs/validate`;

const SAVE_LOG_API_URL =
  `${INTEGRATION_API_BASE_URL}/api/cultivation-logs`;

export class IntegrationServiceError extends Error {
  constructor(
    message,
    {
      status = 0,
      data = null,
      cause = null,
    } = {}
  ) {
    super(message);

    this.name =
      "IntegrationServiceError";

    this.status =
      status;

    this.data =
      data;

    if (cause) {
      this.cause =
        cause;
    }
  }
}

async function parseJsonSafe(
  response
) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function requestJson(
  url,
  options = {}
) {
  let response;

  try {
    response = await fetch(
      url,
      options
    );
  } catch (error) {
    throw new IntegrationServiceError(
      "Không thể kết nối Integration Service.",
      {
        status: 0,
        cause: error,
      }
    );
  }

  const data =
    await parseJsonSafe(
      response
    );

  if (!response.ok) {
    const message =
      data?.message ||
      data?.detail ||
      `Integration Service error: ${response.status}`;

    throw new IntegrationServiceError(
      typeof message === "string"
        ? message
        : JSON.stringify(message),
      {
        status:
          response.status,
        data,
      }
    );
  }

  return data;
}

/**
 * Resolve text sang master-data code.
 *
 * Ví dụ:
 *   "Bón phân" -> BON_PHAN
 *   "NPK"      -> NPK
 *   "kg"       -> KG
 *
 * Backend là nơi quyết định:
 *   - matched
 *   - code
 *   - requires_confirmation
 *   - các thông tin resolve khác
 */
export async function resolveMasterData(
  dataType,
  text
) {
  const normalizedType =
    String(
      dataType || ""
    ).trim();

  const normalizedText =
    String(
      text || ""
    ).trim();

  if (!normalizedType) {
    throw new IntegrationServiceError(
      "Master-data type is required."
    );
  }

  if (!normalizedText) {
    return {
      matched: false,
      code: null,
      text: normalizedText,
      requires_confirmation: false,
    };
  }

  return requestJson(
    RESOLVE_API_URL,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        data_type:
          normalizedType,

        text:
          normalizedText,
      }),
    }
  );
}

/**
 * Validate cultivation log.
 *
 * Integration Service là source of truth cho business validation.
 *
 * Response có thể gồm:
 *   valid
 *   errors
 *   warnings
 *   requires_confirmation
 *   rule_version
 */
export async function validateCultivationLog(
  payload
) {
  if (
    !payload ||
    typeof payload !== "object"
  ) {
    throw new IntegrationServiceError(
      "Cultivation log payload is required."
    );
  }

  return requestJson(
    VALIDATE_LOG_API_URL,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify(
          payload
        ),
    }
  );
}

/**
 * Save cultivation log.
 *
 * Frontend không được giả định dữ liệu đã hợp lệ.
 * Backend vẫn phải tự validate trước khi lưu.
 */
export async function saveCultivationLog(
  payload
) {
  if (
    !payload ||
    typeof payload !== "object"
  ) {
    throw new IntegrationServiceError(
      "Cultivation log payload is required."
    );
  }

  return requestJson(
    SAVE_LOG_API_URL,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify(
          payload
        ),
    }
  );
}

/**
 * Get saved cultivation logs.
 *
 * Dùng cho My Logs hoặc các flow cần đọc
 * dữ liệu từ Integration Service.
 */
export async function getCultivationLogs() {
  return requestJson(
    `${INTEGRATION_API_BASE_URL}/api/cultivation-logs`,
    {
      method: "GET",
    }
  );
}

/**
 * Get one cultivation log by client_record_id.
 */
export async function getCultivationLog(
  clientRecordId
) {
  const normalizedId =
    String(
      clientRecordId || ""
    ).trim();

  if (!normalizedId) {
    throw new IntegrationServiceError(
      "client_record_id is required."
    );
  }

  return requestJson(
    `${
      INTEGRATION_API_BASE_URL
    }/api/cultivation-logs/${encodeURIComponent(
      normalizedId
    )}`,
    {
      method: "GET",
    }
  );
}
/**
 * Update one cultivation log by client_record_id.
 */
export async function updateCultivationLog(
  clientRecordId,
  payload
) {
  const normalizedId =
    String(
      clientRecordId || ""
    ).trim();

  if (!normalizedId) {
    throw new IntegrationServiceError(
      "client_record_id is required."
    );
  }

  if (
    !payload ||
    typeof payload !== "object"
  ) {
    throw new IntegrationServiceError(
      "Cultivation log payload is required."
    );
  }

  return requestJson(
    `${
      INTEGRATION_API_BASE_URL
    }/api/cultivation-logs/${encodeURIComponent(
      normalizedId
    )}`,
    {
      method: "PUT",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify(
          payload
        ),
    }
  );
}
/**
 * Trả về URL Integration Service hiện tại.
 *
 * Hữu ích khi debug local / tunnel.
 */
export function getIntegrationApiUrl() {
  return INTEGRATION_API_BASE_URL;
}
