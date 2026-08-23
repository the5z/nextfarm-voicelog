import {
  getCultivationLogs,
  getLatestCultivationLog,
  getCultivationLogsByLotCode,
  getActivities,
  getLots,
  getMaterials,
  getUnits,
} from "./queryService.js";


function normalizeText(value) {
  return String(
    value ?? ""
  )
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}


function normalizeCode(value) {
  return String(
    value ?? ""
  )
    .trim()
    .toUpperCase();
}


function createCodeNameMap(
  items
) {
  const map =
    new Map();

  if (
    !Array.isArray(items)
  ) {
    return map;
  }

  for (
    const item of items
  ) {
    const code =
      normalizeCode(
        item?.code
      );

    const name =
      String(
        item?.name ?? ""
      ).trim();

    if (
      code &&
      name
    ) {
      map.set(
        code,
        name
      );
    }
  }

  return map;
}


async function loadMasterDataLookups() {
  const results =
    await Promise.allSettled([
      getActivities(),
      getLots(),
      getMaterials(),
      getUnits(),
    ]);

  const [
    activitiesResult,
    lotsResult,
    materialsResult,
    unitsResult,
  ] = results;

  const activities =
    activitiesResult.status ===
    "fulfilled"
      ? activitiesResult.value
      : [];

  const lots =
    lotsResult.status ===
    "fulfilled"
      ? lotsResult.value
      : [];

  const materials =
    materialsResult.status ===
    "fulfilled"
      ? materialsResult.value
      : [];

  const units =
    unitsResult.status ===
    "fulfilled"
      ? unitsResult.value
      : [];

  return {
    activities:
      createCodeNameMap(
        activities
      ),

    lots:
      createCodeNameMap(
        lots
      ),

    materials:
      createCodeNameMap(
        materials
      ),

    units:
      createCodeNameMap(
        units
      ),
  };
}


function getDisplayName(
  code,
  map
) {
  const normalizedCode =
    normalizeCode(
      code
    );

  if (!normalizedCode) {
    return "";
  }

  return (
    map?.get(
      normalizedCode
    ) ||
    code
  );
}


function formatMaterial(
  material,
  lookups = null,
  isVietnamese = true
) {
  if (!material) {
    return null;
  }

  const materialCode =
    material.material_code ||
    "";

  const quantity =
    material.quantity ??
    "";

  const unitCode =
    material.unit_code ||
    "";

  const materialName =
    isVietnamese
      ? getDisplayName(
          materialCode,
          lookups?.materials
        )
      : materialCode;

  const unitName =
    isVietnamese
      ? getDisplayName(
          unitCode,
          lookups?.units
        )
      : unitCode;

  return [
    materialName,
    quantity,
    unitName,
  ]
    .filter(
      (value) =>
        String(
          value
        ).trim() !== ""
    )
    .join(" ");
}


export function formatCultivationLog(
  log,
  isVietnamese = true,
  lookups = null
) {
  if (!log) {
    return isVietnamese
      ? "Chưa có nhật ký canh tác nào được lưu."
      : "No cultivation logs have been saved yet.";
  }

  const lotCode =
    log.lot_code ||
    "";

  const activityCode =
    log.activity_code ||
    "";

  const lotName =
    isVietnamese
      ? getDisplayName(
          lotCode,
          lookups?.lots
        )
      : lotCode;

  const activityName =
    isVietnamese
      ? getDisplayName(
          activityCode,
          lookups?.activities
        )
      : activityCode;

  const materials =
    Array.isArray(
      log.materials
    )
      ? log.materials
          .map(
            (material) =>
              formatMaterial(
                material,
                lookups,
                isVietnamese
              )
          )
          .filter(Boolean)
      : [];

  if (isVietnamese) {
    return [
      "📋 Nhật ký canh tác:",
      `• Mã bản ghi: ${
        log.client_record_id ||
        "không có"
      }`,
      `• Lô: ${
        lotName ||
        "không có"
      }`,
      `• Công việc: ${
        activityName ||
        "không có"
      }`,
      `• Vật tư: ${
        materials.length > 0
          ? materials.join(", ")
          : "không có"
      }`,
      `• Thời gian: ${
        log.performed_at ||
        "không có"
      }`,
      `• Trạng thái: ${
        log.status ||
        "không có"
      }`,
    ].join("\n");
  }

  return [
    "📋 Cultivation log:",
    `• Record ID: ${
      log.client_record_id ||
      "not available"
    }`,
    `• Plot: ${
      lotName ||
      "not available"
    }`,
    `• Activity: ${
      activityName ||
      "not available"
    }`,
    `• Materials: ${
      materials.length > 0
        ? materials.join(", ")
        : "none"
    }`,
    `• Performed at: ${
      log.performed_at ||
      "not available"
    }`,
    `• Status: ${
      log.status ||
      "not available"
    }`,
  ].join("\n");
}


function extractLotCode(
  message
) {
  const text =
    normalizeText(
      message
    );

  const match =
    text.match(
      /\blô\s+([a-z0-9_-]+)\b/i
    );

  if (!match) {
    return null;
  }

  const lotName =
    match[1]
      .trim()
      .toUpperCase();

  return `LO_${lotName}`;
}


function asksLatestLog(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    text.includes(
      "nhật ký gần nhất"
    ) ||
    text.includes(
      "nhật ký mới nhất"
    ) ||
    text.includes(
      "latest log"
    ) ||
    text.includes(
      "recent log"
    )
  );
}


function asksLogsByLot(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    text.includes(
      "nhật ký"
    ) &&
    /\blô\s+[a-z0-9_-]+\b/i.test(
      text
    )
  );
}


function asksCropByLot(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    /\blô\s+[a-z0-9_-]+\b/i.test(
      text
    ) &&
    (
      text.includes(
        "trồng"
      ) ||
      text.includes(
        "cây gì"
      ) ||
      text.includes(
        "crop"
      )
    )
  );
}


export async function handleQueryIntent({
  message,
  isVietnamese = true,
}) {
  if (
    asksLatestLog(
      message
    )
  ) {
    const [
      latestLog,
      lookups,
    ] =
      await Promise.all([
        getLatestCultivationLog(),
        loadMasterDataLookups(),
      ]);

    return formatCultivationLog(
      latestLog,
      isVietnamese,
      lookups
    );
  }


  if (
    asksLogsByLot(
      message
    )
  ) {
    const lotCode =
      extractLotCode(
        message
      );

    if (!lotCode) {
      return isVietnamese
        ? "Tôi chưa xác định được lô cần tra cứu."
        : "I could not determine which plot to query.";
    }

    const [
      logs,
      lookups,
    ] =
      await Promise.all([
        getCultivationLogsByLotCode(
          lotCode
        ),
        loadMasterDataLookups(),
      ]);

    const lotName =
      isVietnamese
        ? getDisplayName(
            lotCode,
            lookups.lots
          )
        : lotCode;

    if (
      logs.length === 0
    ) {
      return isVietnamese
        ? `Chưa tìm thấy nhật ký nào của ${lotName}.`
        : `No cultivation logs were found for ${lotCode}.`;
    }

    return [
      isVietnamese
        ? (
            `Tìm thấy ${logs.length} nhật ký của `
            + `${lotName}. Nhật ký gần nhất:`
          )
        : (
            `Found ${logs.length} log(s) for `
            + `${lotCode}. Latest log:`
          ),
      "",
      formatCultivationLog(
        logs[0],
        isVietnamese,
        lookups
      ),
    ].join("\n");
  }


  if (
    asksCropByLot(
      message
    )
  ) {
    return isVietnamese
      ? (
          "Hiện Integration Service chưa có nguồn dữ liệu "
          + "quan hệ giữa lô và cây trồng, nên tôi chưa thể "
          + "trả lời chính xác câu hỏi này."
        )
      : (
          "The Integration Service does not currently expose "
          + "plot-to-crop data, so I cannot answer this accurately yet."
        );
  }


  const logs =
    await getCultivationLogs();

  if (
    logs.length === 0
  ) {
    return isVietnamese
      ? "Chưa có nhật ký canh tác nào để tra cứu."
      : "There are no cultivation logs to query yet.";
  }

  return isVietnamese
    ? (
        `Hiện có ${logs.length} nhật ký canh tác đã lưu. `
        + "Bạn có thể hỏi “Cho tôi xem nhật ký gần nhất” "
        + "hoặc “Nhật ký của lô A”."
      )
    : (
        `There are currently ${logs.length} saved cultivation logs. `
        + 'You can ask "Show me the latest log" or '
        + '"Show me logs for plot A".'
      );
}