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
const DYNAMIC_OPERATION_SAVE_CONFIG = {
  CREATE_CROP_TYPE: {
    path: "/api/crop-types",
    fields: [
      "crop_name",
      "crop_group_text",
      "crop_code_suggestion",
      "days_to_harvest",
    ],
  },

  CREATE_SEASON: {
    path: "/api/seasons",
    fields: [
      "plot_text",
      "crop_text",
      "planting_date_text",
      "season_name",
      "expected_harvest_date_text",
      "plant_count",
      "expected_yield",
      "expected_yield_unit_text",
      "process_template_text",
    ],
  },

  CREATE_PLOT: {
    path: "/api/plots",
    fields: [
      "plot_name_or_code",
      "region_text",
      "boundary_required",
      "owner_text",
      "current_crop_text",
      "location_hint_text",
    ],
  },

  CREATE_TASK: {
    path: "/api/tasks",
    fields: [
      "season_text",
      "task_name",
      "task_type_text",
      "due_time_text",
      "assignee_text",
      "photo_required",
      "note",
    ],
  },

  CREATE_ISSUE_REPORT: {
    path: "/api/issue-reports",
    fields: [
      "plot_text",
      "issue_type_text",
      "severity_text",
      "description",
      "note",
    ],
    blocksPhotoRequirement: true,
  },

  CREATE_HARVEST: {
    path: "/api/harvests",
    fields: [
      "plot_text",
      "crop_text",
      "quantity",
      "unit_text",
      "harvest_date_text",
      "note",
    ],
    blocksPhotoRequirement: true,
  },
};

export async function saveDynamicOperation(
  operation,
  clientRecordId,
  fields
) {
  const normalizedOperation =
    String(operation || "").trim();

  const config =
    DYNAMIC_OPERATION_SAVE_CONFIG[
      normalizedOperation
    ];

  if (!config) {
    throw new IntegrationServiceError(
      "Operation does not have a configured Integration save endpoint."
    );
  }

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
    !fields ||
    typeof fields !== "object"
  ) {
    throw new IntegrationServiceError(
      "Dynamic form fields are required."
    );
  }

  if (
    config.blocksPhotoRequirement &&
    fields.photo_required === true
  ) {
    throw new IntegrationServiceError(
      "Nghiệp vụ đang yêu cầu ảnh nhưng frontend chưa có payload/API tải ảnh tương ứng."
    );
  }

  const payload = {
    client_record_id:
      normalizedId,
    confirmed: true,
  };

  config.fields.forEach(
    (fieldName) => {
      if (
        Object.prototype.hasOwnProperty.call(
          fields,
          fieldName
        )
      ) {
        payload[fieldName] =
          fields[fieldName];
      }
    }
  );

  return requestJson(
    `${INTEGRATION_API_BASE_URL}${config.path}`,
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
 * Trả về URL Integration Service hiện tại.
 *
 * Hữu ích khi debug local / tunnel.
 */
export function getIntegrationApiUrl() {
  return INTEGRATION_API_BASE_URL;
}
