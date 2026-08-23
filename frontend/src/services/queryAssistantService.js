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


const VIETNAM_UTC_OFFSET_MS =
  7 * 60 * 60 * 1000;


function getVietnamDateKey(
  value
) {
  const date =
    value instanceof Date
      ? value
      : new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return null;
  }

  return new Date(
    date.getTime() +
      VIETNAM_UTC_OFFSET_MS
  )
    .toISOString()
    .slice(0, 10);
}


function getTodayVietnamDateKey() {
  return getVietnamDateKey(
    new Date()
  );
}


function getYesterdayVietnamDateKey() {
  const yesterday =
    new Date(
      Date.now() -
      24 * 60 * 60 * 1000
    );

  return getVietnamDateKey(
    yesterday
  );
}


function isLogInRecentVietnamDays(
  log,
  days
) {
  if (
    !log?.performed_at ||
    !Number.isInteger(days) ||
    days <= 0
  ) {
    return false;
  }

  const logDateKey =
    getVietnamDateKey(
      log.performed_at
    );

  const todayKey =
    getTodayVietnamDateKey();

  if (
    !logDateKey ||
    !todayKey
  ) {
    return false;
  }

  const logDate =
    new Date(
      `${logDateKey}T00:00:00Z`
    );

  const todayDate =
    new Date(
      `${todayKey}T00:00:00Z`
    );

  const diffDays =
    Math.floor(
      (
        todayDate.getTime() -
        logDate.getTime()
      ) /
      (24 * 60 * 60 * 1000)
    );

  return (
    diffDays >= 0 &&
    diffDays < days
  );
}


function isLogOnVietnamDate(
  log,
  dateKey
) {
  if (
    !log?.performed_at ||
    !dateKey
  ) {
    return false;
  }

  return (
    getVietnamDateKey(
      log.performed_at
    ) === dateKey
  );
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

    activityItems:
      activities,

    lotItems:
      lots,

    materialItems:
      materials,

    unitItems:
      units,
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


function getSearchTerms(
  item
) {
  const terms = [
    item?.name,
    ...(Array.isArray(
      item?.aliases
    )
      ? item.aliases
      : []),
  ];

  return terms
    .map(
      normalizeText
    )
    .filter(Boolean)
    .sort(
      (a, b) =>
        b.length -
        a.length
    );
}


function findMentionedCode(
  message,
  items
) {
  const text =
    normalizeText(
      message
    );

  if (
    !text ||
    !Array.isArray(items)
  ) {
    return null;
  }

  for (
    const item of items
  ) {
    const code =
      normalizeCode(
        item?.code
      );

    if (!code) {
      continue;
    }

    const terms =
      getSearchTerms(
        item
      );

    if (
      terms.some(
        (term) =>
          text.includes(
            term
          )
      )
    ) {
      return code;
    }

    if (
      text.includes(
        code.toLowerCase()
      )
    ) {
      return code;
    }
  }

  return null;
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


function asksTodayQuery(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    text.includes(
      "hôm nay"
    ) ||
    text.includes(
      "today"
    )
  );
}


function asksRecent7DaysQuery(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    text.includes(
      "7 ng\u00e0y g\u1ea7n \u0111\u00e2y"
    ) ||
    text.includes(
      "7 ng\u00e0y qua"
    ) ||
    text.includes(
      "trong 7 ng\u00e0y"
    )
  );
}


function asksRecent7DaysActivities(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    asksRecent7DaysQuery(
      message
    ) &&
    (
      text.includes(
        "ho\u1ea1t \u0111\u1ed9ng"
      ) ||
      text.includes(
        "c\u00f4ng vi\u1ec7c"
      ) ||
      text.includes(
        "\u0111\u00e3 l\u00e0m"
      ) ||
      text.includes(
        "l\u00e0m g\u00ec"
      ) ||
      text.includes(
        "activity"
      ) ||
      text.includes(
        "activities"
      )
    )
  );
}


function asksRecent7DaysLogs(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    asksRecent7DaysQuery(
      message
    ) &&
    (
      text.includes(
        "nh\u1eadt k\u00fd"
      ) ||
      text.includes(
        "log"
      )
    )
  );
}


function asksYesterdayQuery(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    text.includes(
      "h\u00f4m qua"
    ) ||
    text.includes(
      "yesterday"
    )
  );
}


function asksYesterdayActivities(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    asksYesterdayQuery(
      message
    ) &&
    (
      text.includes(
        "ho\u1ea1t \u0111\u1ed9ng"
      ) ||
      text.includes(
        "c\u00f4ng vi\u1ec7c"
      ) ||
      text.includes(
        "\u0111\u00e3 l\u00e0m"
      ) ||
      text.includes(
        "l\u00e0m g\u00ec"
      ) ||
      text.includes(
        "activity"
      ) ||
      text.includes(
        "activities"
      )
    )
  );
}


function asksYesterdayLogs(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    asksYesterdayQuery(
      message
    ) &&
    (
      text.includes(
        "nh\u1eadt k\u00fd"
      ) ||
      text.includes(
        "log"
      )
    )
  );
}


function asksTodayActivities(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    asksTodayQuery(
      message
    ) &&
    (
      text.includes(
        "hoạt động"
      ) ||
      text.includes(
        "công việc"
      ) ||
      text.includes(
        "đã làm"
      ) ||
      text.includes(
        "làm gì"
      ) ||
      text.includes(
        "activity"
      ) ||
      text.includes(
        "activities"
      )
    )
  );
}


function asksTodayLogs(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    asksTodayQuery(
      message
    ) &&
    (
      text.includes(
        "nhật ký"
      ) ||
      text.includes(
        "log"
      )
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


function asksActivitiesByLot(
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
        "hoạt động"
      ) ||
      text.includes(
        "công việc"
      ) ||
      text.includes(
        "đã làm"
      ) ||
      text.includes(
        "làm gì"
      )
    )
  );
}


function asksCount(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    text.includes(
      "bao nhiêu lần"
    ) ||
    text.includes(
      "mấy lần"
    ) ||
    text.includes(
      "how many"
    ) ||
    text.includes(
      "count"
    )
  );
}


function asksMaterialUsageByLot(
  message
) {
  const text =
    normalizeText(
      message
    );

  return (
    (
      text.includes(
        "dùng"
      ) ||
      text.includes(
        "sử dụng"
      ) ||
      text.includes(
        "used"
      )
    ) &&
    (
      text.includes(
        "lô nào"
      ) ||
      text.includes(
        "ở lô"
      ) ||
      text.includes(
        "ở đâu"
      ) ||
      text.includes(
        "which plot"
      ) ||
      text.includes(
        "which field"
      )
    )
  );
}


function getUniqueCodes(
  values
) {
  return [
    ...new Set(
      values
        .map(
          normalizeCode
        )
        .filter(Boolean)
    ),
  ];
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


  const [
    logs,
    lookups,
  ] =
    await Promise.all([
      getCultivationLogs(),
      loadMasterDataLookups(),
    ]);


  if (
    asksRecent7DaysActivities(
      message
    ) ||
    asksRecent7DaysLogs(
      message
    )
  ) {
    const lotCode =
      extractLotCode(
        message
      );

    let recentLogs =
      logs
        .filter(
          (log) =>
            isLogInRecentVietnamDays(
              log,
              7
            )
        );

    if (lotCode) {
      recentLogs =
        recentLogs.filter(
          (log) =>
            normalizeCode(
              log?.lot_code
            ) ===
            normalizeCode(
              lotCode
            )
        );
    }

    recentLogs =
      recentLogs.sort(
        (a, b) =>
          new Date(
            b?.performed_at ?? 0
          ).getTime() -
          new Date(
            a?.performed_at ?? 0
          ).getTime()
      );

    if (
      recentLogs.length === 0
    ) {
      return isVietnamese
        ? "7 ng\u00e0y g\u1ea7n \u0111\u00e2y ch\u01b0a c\u00f3 nh\u1eadt k\u00fd canh t\u00e1c n\u00e0o."
        : "There are no cultivation logs in the last 7 days.";
    }

    if (
      asksRecent7DaysActivities(
        message
      )
    ) {
      const activityCodes =
        getUniqueCodes(
          recentLogs.map(
            (log) =>
              log?.activity_code
          )
        );

      const activityNames =
        activityCodes.map(
          (code) =>
            getDisplayName(
              code,
              lookups.activities
            )
        );

      return isVietnamese
        ? (
            `7 ng\u00e0y g\u1ea7n \u0111\u00e2y c\u00f3 ${recentLogs.length} nh\u1eadt k\u00fd v\u1edbi `
            + `${activityCodes.length} lo\u1ea1i ho\u1ea1t \u0111\u1ed9ng: `
            + `${activityNames.join(", ")}.`
          )
        : (
            `In the last 7 days there are ${recentLogs.length} log(s) with `
            + `${activityCodes.length} activity type(s): `
            + `${activityNames.join(", ")}.`
          );
    }

    return [
      isVietnamese
        ? (
            `7 ng\u00e0y g\u1ea7n \u0111\u00e2y c\u00f3 ${recentLogs.length} nh\u1eadt k\u00fd. `
            + "Nh\u1eadt k\u00fd g\u1ea7n nh\u1ea5t:"
          )
        : (
            `There are ${recentLogs.length} log(s) in the last 7 days. `
            + "Latest log:"
          ),
      "",
      formatCultivationLog(
        recentLogs[0],
        isVietnamese,
        lookups
      ),
    ].join("\n");
  }


  if (
    asksYesterdayActivities(
      message
    ) ||
    asksYesterdayLogs(
      message
    )
  ) {
    const yesterdayKey =
      getYesterdayVietnamDateKey();

    const yesterdayLogs =
      logs.filter(
        (log) =>
          isLogOnVietnamDate(
            log,
            yesterdayKey
          )
      );

    if (
      yesterdayLogs.length === 0
    ) {
      return isVietnamese
        ? "H\u00f4m qua ch\u01b0a c\u00f3 nh\u1eadt k\u00fd canh t\u00e1c n\u00e0o."
        : "There are no cultivation logs for yesterday.";
    }

    if (
      asksYesterdayActivities(
        message
      )
    ) {
      const activityCodes =
        getUniqueCodes(
          yesterdayLogs.map(
            (log) =>
              log?.activity_code
          )
        );

      const activityNames =
        activityCodes.map(
          (code) =>
            getDisplayName(
              code,
              lookups.activities
            )
        );

      return isVietnamese
        ? (
            `H\u00f4m qua c\u00f3 ${yesterdayLogs.length} nh\u1eadt k\u00fd v\u1edbi `
            + `${activityCodes.length} lo\u1ea1i ho\u1ea1t \u0111\u1ed9ng: `
            + `${activityNames.join(", ")}.`
          )
        : (
            `Yesterday there were ${yesterdayLogs.length} log(s) with `
            + `${activityCodes.length} activity type(s): `
            + `${activityNames.join(", ")}.`
          );
    }

    return [
      isVietnamese
        ? (
            `H\u00f4m qua c\u00f3 ${yesterdayLogs.length} nh\u1eadt k\u00fd. `
            + "Nh\u1eadt k\u00fd g\u1ea7n nh\u1ea5t:"
          )
        : (
            `There were ${yesterdayLogs.length} log(s) yesterday. `
            + "Latest log:"
          ),
      "",
      formatCultivationLog(
        yesterdayLogs[0],
        isVietnamese,
        lookups
      ),
    ].join("\n");
  }


  if (
    asksTodayActivities(
      message
    ) ||
    asksTodayLogs(
      message
    )
  ) {
    const todayKey =
      getTodayVietnamDateKey();

    const todayLogs =
      logs.filter(
        (log) =>
          isLogOnVietnamDate(
            log,
            todayKey
          )
      );

    if (
      todayLogs.length === 0
    ) {
      return isVietnamese
        ? "Hôm nay chưa có nhật ký canh tác nào."
        : "There are no cultivation logs for today.";
    }

    if (
      asksTodayActivities(
        message
      )
    ) {
      const activityCodes =
        getUniqueCodes(
          todayLogs.map(
            (log) =>
              log?.activity_code
          )
        );

      const activityNames =
        activityCodes.map(
          (code) =>
            getDisplayName(
              code,
              lookups.activities
            )
        );

      return isVietnamese
        ? (
            `Hôm nay có ${todayLogs.length} nhật ký với `
            + `${activityCodes.length} loại hoạt động: `
            + `${activityNames.join(", ")}.`
          )
        : (
            `Today there are ${todayLogs.length} log(s) with `
            + `${activityCodes.length} activity type(s): `
            + `${activityNames.join(", ")}.`
          );
    }

    return [
      isVietnamese
        ? (
            `Hôm nay có ${todayLogs.length} nhật ký. `
            + "Nhật ký gần nhất:"
          )
        : (
            `There are ${todayLogs.length} log(s) today. `
            + "Latest log:"
          ),
      "",
      formatCultivationLog(
        todayLogs[0],
        isVietnamese,
        lookups
      ),
    ].join("\n");
  }


  if (
    logs.length === 0
  ) {
    return isVietnamese
      ? "Chưa có nhật ký canh tác nào để tra cứu."
      : "There are no cultivation logs to query yet.";
  }


  if (
    asksActivitiesByLot(
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

    const lotLogs =
      logs.filter(
        (log) =>
          normalizeCode(
            log?.lot_code
          ) ===
          normalizeCode(
            lotCode
          )
      );

    const lotName =
      getDisplayName(
        lotCode,
        lookups.lots
      );

    if (
      lotLogs.length === 0
    ) {
      return isVietnamese
        ? `Chưa tìm thấy nhật ký nào của ${lotName}.`
        : `No cultivation logs were found for ${lotCode}.`;
    }

    const activityCodes =
      getUniqueCodes(
        lotLogs.map(
          (log) =>
            log?.activity_code
        )
      );

    const activityNames =
      activityCodes.map(
        (code) =>
          getDisplayName(
            code,
            lookups.activities
          )
      );

    return isVietnamese
      ? (
          `${lotName} có ${activityCodes.length} loại hoạt động `
          + `trong ${lotLogs.length} nhật ký: `
          + `${activityNames.join(", ")}.`
        )
      : (
          `${lotCode} has ${activityCodes.length} activity type(s) `
          + `across ${lotLogs.length} log(s): `
          + `${activityNames.join(", ")}.`
        );
  }


  if (
    asksCount(
      message
    )
  ) {
    const lotCode =
      extractLotCode(
        message
      );

    const activityCode =
      findMentionedCode(
        message,
        lookups.activityItems
      );

    if (!activityCode) {
      return isVietnamese
        ? "Tôi chưa xác định được hoạt động cần thống kê."
        : "I could not determine which activity to count.";
    }

    let matchedLogs =
      logs.filter(
        (log) =>
          normalizeCode(
            log?.activity_code
          ) ===
          normalizeCode(
            activityCode
          )
      );

    if (
      asksRecent7DaysQuery(
        message
      )
    ) {
      matchedLogs =
        matchedLogs.filter(
          (log) =>
            isLogInRecentVietnamDays(
              log,
              7
            )
        );
    }

    if (lotCode) {
      matchedLogs =
        matchedLogs.filter(
          (log) =>
            normalizeCode(
              log?.lot_code
            ) ===
            normalizeCode(
              lotCode
            )
        );
    }

    const activityName =
      getDisplayName(
        activityCode,
        lookups.activities
      );

    const isRecent7Days =
      asksRecent7DaysQuery(
        message
      );

    if (lotCode) {
      const lotName =
        getDisplayName(
          lotCode,
          lookups.lots
        );

      return isVietnamese
        ? (
            isRecent7Days
              ? (
                  `Trong 7 ng\u00e0y g\u1ea7n \u0111\u00e2y, ${lotName} c\u00f3 `
                  + `${matchedLogs.length} l\u1ea7n `
                  + `${activityName.toLowerCase()}.`
                )
              : (
                  `${lotName} c\u00f3 ${matchedLogs.length} l\u1ea7n `
                  + `${activityName.toLowerCase()} trong d\u1eef li\u1ec7u \u0111\u00e3 l\u01b0u.`
                )
          )
        : (
            `${lotCode} has ${matchedLogs.length} `
            + `${activityName} log(s).`
          );
    }

    return isVietnamese
      ? (
          isRecent7Days
            ? (
                `Trong 7 ng\u00e0y g\u1ea7n \u0111\u00e2y c\u00f3 `
                + `${matchedLogs.length} l\u1ea7n `
                + `${activityName.toLowerCase()}.`
              )
            : (
                `C\u00f3 ${matchedLogs.length} l\u1ea7n `
                + `${activityName.toLowerCase()} trong d\u1eef li\u1ec7u \u0111\u00e3 l\u01b0u.`
              )
        )
      : (
          `There are ${matchedLogs.length} `
          + `${activityName} log(s).`
        );


  }


  if (
    asksMaterialUsageByLot(
      message
    )
  ) {
    const materialCode =
      findMentionedCode(
        message,
        lookups.materialItems
      );

    if (!materialCode) {
      return isVietnamese
        ? "T\u00f4i ch\u01b0a x\u00e1c \u0111\u1ecbnh \u0111\u01b0\u1ee3c v\u1eadt t\u01b0 c\u1ea7n tra c\u1ee9u."
        : "I could not determine which material to query.";
    }

    let matchedLogs =
      logs.filter(
        (log) =>
          Array.isArray(
            log?.materials
          ) &&
          log.materials.some(
            (material) =>
              normalizeCode(
                material?.material_code
              ) ===
              normalizeCode(
                materialCode
              )
          )
      );

    const isRecent7Days =
      asksRecent7DaysQuery(
        message
      );

    if (isRecent7Days) {
      matchedLogs =
        matchedLogs.filter(
          (log) =>
            isLogInRecentVietnamDays(
              log,
              7
            )
        );
    }

    const lotCodes =
      getUniqueCodes(
        matchedLogs.map(
          (log) =>
            log?.lot_code
        )
      );

    const materialName =
      getDisplayName(
        materialCode,
        lookups.materials
      );

    if (
      lotCodes.length === 0
    ) {
      return isVietnamese
        ? (
            isRecent7Days
              ? `Trong 7 ng\u00e0y g\u1ea7n \u0111\u00e2y ch\u01b0a t\u00ecm th\u1ea5y nh\u1eadt k\u00fd n\u00e0o s\u1eed d\u1ee5ng ${materialName}.`
              : `Ch\u01b0a t\u00ecm th\u1ea5y nh\u1eadt k\u00fd n\u00e0o s\u1eed d\u1ee5ng ${materialName}.`
          )
        : `No logs were found using ${materialCode}.`;
    }

    const lotNames =
      lotCodes.map(
        (code) =>
          getDisplayName(
            code,
            lookups.lots
          )
      );

    return isVietnamese
      ? (
          isRecent7Days
            ? (
                `Trong 7 ng\u00e0y g\u1ea7n \u0111\u00e2y, ${materialName} `
                + `\u0111\u00e3 \u0111\u01b0\u1ee3c s\u1eed d\u1ee5ng trong `
                + `${matchedLogs.length} nh\u1eadt k\u00fd, t\u1ea1i: `
                + `${lotNames.join(", ")}.`
              )
            : (
                `${materialName} \u0111\u00e3 \u0111\u01b0\u1ee3c s\u1eed d\u1ee5ng trong `
                + `${matchedLogs.length} nh\u1eadt k\u00fd, t\u1ea1i: `
                + `${lotNames.join(", ")}.`
              )
        )
      : (
          `${materialCode} was used in ${matchedLogs.length} log(s), `
          + `at: ${lotNames.join(", ")}.`
        );
  }


  const activityCode =
    findMentionedCode(
      message,
      lookups.activityItems
    );

  const lotCode =
    extractLotCode(
      message
    );

  if (
    activityCode &&
    lotCode
  ) {
    const matchedLogs =
      logs.filter(
        (log) =>
          normalizeCode(
            log?.activity_code
          ) ===
            normalizeCode(
              activityCode
            ) &&
          normalizeCode(
            log?.lot_code
          ) ===
            normalizeCode(
              lotCode
            )
      );

    const activityName =
      getDisplayName(
        activityCode,
        lookups.activities
      );

    const lotName =
      getDisplayName(
        lotCode,
        lookups.lots
      );

    if (
      matchedLogs.length === 0
    ) {
      return isVietnamese
        ? (
            `Chưa tìm thấy nhật ký ${activityName.toLowerCase()} `
            + `của ${lotName}.`
          )
        : (
            `No ${activityName} logs were found for ${lotCode}.`
          );
    }

    return [
      isVietnamese
        ? (
            `Tìm thấy ${matchedLogs.length} nhật ký `
            + `${activityName.toLowerCase()} của ${lotName}. `
            + "Nhật ký gần nhất:"
          )
        : (
            `Found ${matchedLogs.length} ${activityName} log(s) `
            + `for ${lotCode}. Latest log:`
          ),
      "",
      formatCultivationLog(
        matchedLogs[0],
        isVietnamese,
        lookups
      ),
    ].join("\n");
  }


  return isVietnamese
    ? (
        `Hiện có ${logs.length} nhật ký canh tác đã lưu. `
        + "Bạn có thể hỏi về nhật ký gần nhất, hoạt động theo lô, "
        + "số lần thực hiện công việc hoặc vật tư đã sử dụng."
      )
    : (
        `There are currently ${logs.length} saved cultivation logs. `
        + "You can ask about the latest log, activities by plot, "
        + "activity counts, or material usage."
      );
}
