import {
  getActivities,
  getCultivationLogs,
  getLots,
  getMaterials,
  getUnits,
} from "./queryService";


const STORAGE_KEY =
  "nextfarm-farming-logs";


function normalizeCode(
  value
) {
  return String(
    value ?? ""
  )
    .trim()
    .toUpperCase();
}


function createNameMap(
  records
) {
  const map =
    new Map();

  if (
    !Array.isArray(
      records
    )
  ) {
    return map;
  }

  records.forEach(
    (record) => {
      const code =
        normalizeCode(
          record?.code
        );

      if (!code) {
        return;
      }

      map.set(
        code,
        record?.name ||
          record?.label ||
          code
      );
    }
  );

  return map;
}


function getDisplayName(
  code,
  nameMap
) {
  const normalized =
    normalizeCode(code);

  if (!normalized) {
    return "";
  }

  return (
    nameMap.get(
      normalized
    ) ||
    normalized
  );
}


function formatDateTime(
  value
) {
  if (!value) {
    return {
      date: "",
      time: "",
    };
  }

  const parsed =
    new Date(value);

  if (
    Number.isNaN(
      parsed.getTime()
    )
  ) {
    return {
      date: "",
      time: "",
    };
  }

  const day =
    String(
      parsed.getDate()
    ).padStart(
      2,
      "0"
    );

  const month =
    String(
      parsed.getMonth() +
        1
    ).padStart(
      2,
      "0"
    );

  const year =
    parsed.getFullYear();

  const hours =
    String(
      parsed.getHours()
    ).padStart(
      2,
      "0"
    );

  const minutes =
    String(
      parsed.getMinutes()
    ).padStart(
      2,
      "0"
    );

  return {
    date:
      `${day}/${month}/${year}`,
    time:
      `${hours}:${minutes}`,
  };
}


function normalizeStatus(
  status,
  confirmed
) {
  const normalized =
    String(
      status ?? ""
    )
      .trim()
      .toLowerCase();

  if (
    normalized ===
      "saved" ||
    normalized ===
      "completed"
  ) {
    return "completed";
  }

  if (
    normalized ===
    "draft"
  ) {
    return "draft";
  }

  if (
    normalized ===
    "review"
  ) {
    return "review";
  }

  return confirmed
    ? "completed"
    : "review";
}


function normalizeBackendLog(
  log,
  lookups
) {
  const performed =
    formatDateTime(
      log?.performed_at
    );

  const lotCode =
    normalizeCode(
      log?.lot_code
    );

  const activityCode =
    normalizeCode(
      log?.activity_code
    );

  const rawMaterials =
    Array.isArray(
      log?.materials
    )
      ? log.materials
      : [];

  const materials =
    rawMaterials.map(
      (item) => {
        const materialCode =
          normalizeCode(
            item?.material_code
          );

        const unitCode =
          normalizeCode(
            item?.unit_code
          );

        return {
          material:
            getDisplayName(
              materialCode,
              lookups.materials
            ),

          materialCode,

          quantity:
            item?.quantity ??
            "",

          unit:
            getDisplayName(
              unitCode,
              lookups.units
            ),

          unitCode,
        };
      }
    );

  const firstMaterial =
    materials[0] || {
      material: "",
      quantity: "",
      unit: "",
    };

  const clientRecordId =
    String(
      log?.client_record_id ??
        log?.id ??
        ""
    );

  return {
    /*
      UI fields
    */

    id:
      clientRecordId,

    lot:
      getDisplayName(
        lotCode,
        lookups.lots
      ),

    work:
      getDisplayName(
        activityCode,
        lookups.activities
      ),

    materials,

    /*
      Compatibility với UI cũ.
      Các component cũ vẫn có thể
      đọc vật tư đầu tiên.
    */

    material:
      firstMaterial.material,

    quantity:
      firstMaterial.quantity,

    unit:
      firstMaterial.unit,

    date:
      performed.date,

    time:
      performed.time,

    status:
      normalizeStatus(
        log?.status,
        log?.confirmed
      ),

    transcript:
      log?.transcript ??
      "",

    createdAt:
      log?.created_at ??
      log?.performed_at ??
      "",

    updatedAt:
      log?.updated_at ??
      log?.created_at ??
      log?.performed_at ??
      "",

    /*
      Giữ raw/canonical fields
      để edit hoặc integration
      không bị mất code.
    */

    clientRecordId,
    client_record_id:
      clientRecordId,

    lotCode,
    lot_code:
      lotCode,

    activityCode,
    activity_code:
      activityCode,

    performedAt:
      log?.performed_at ??
      "",

    performed_at:
      log?.performed_at ??
      "",

    performerCode:
      log?.performer_code ??
      null,

    performer_code:
      log?.performer_code ??
      null,

    notes:
      log?.notes ??
      null,

    source:
      log?.source ??
      "voice",

    confirmed:
      Boolean(
        log?.confirmed
      ),

    backendStatus:
      log?.status ??
      "",
  };
}


async function safeLoad(
  loader
) {
  try {
    const result =
      await loader();

    return Array.isArray(
      result
    )
      ? result
      : [];
  } catch (error) {
    console.warn(
      "Master data load error:",
      error
    );

    return [];
  }
}


export async function loadBackendLogs() {
  /*
    Cultivation logs là dữ liệu chính.

    Master data chỉ phục vụ
    đổi code -> tên hiển thị.
  */

  const backendLogs =
    await getCultivationLogs();

  const [
    activities,
    lots,
    materials,
    units,
  ] =
    await Promise.all([
      safeLoad(
        getActivities
      ),
      safeLoad(
        getLots
      ),
      safeLoad(
        getMaterials
      ),
      safeLoad(
        getUnits
      ),
    ]);

  const lookups = {
    activities:
      createNameMap(
        activities
      ),

    lots:
      createNameMap(
        lots
      ),

    materials:
      createNameMap(
        materials
      ),

    units:
      createNameMap(
        units
      ),
  };

  return backendLogs.map(
    (log) =>
      normalizeBackendLog(
        log,
        lookups
      )
  );
}


export function loadLogs() {
  /*
    Local storage chỉ còn là
    fallback/cache.

    Không tự tạo sample logs nữa.
  */

  try {
    const saved =
      localStorage.getItem(
        STORAGE_KEY
      );

    if (!saved) {
      return [];
    }

    const parsed =
      JSON.parse(saved);

    return Array.isArray(
      parsed
    )
      ? parsed
      : [];
  } catch (error) {
    console.error(
      "Load local logs error:",
      error
    );

    return [];
  }
}


export function persistLogs(
  logs
) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(
        Array.isArray(logs)
          ? logs
          : []
      )
    );
  } catch (error) {
    console.error(
      "Save local logs error:",
      error
    );
  }
}


export function resetLogs() {
  localStorage.removeItem(
    STORAGE_KEY
  );

  return [];
}