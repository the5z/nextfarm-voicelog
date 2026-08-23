import {
  getCultivationLogs,
  getLatestCultivationLog,
  getCultivationLogsByLotCode,
} from "./queryService.js";


function normalizeText(value) {
  return String(
    value ?? ""
  )
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}


function formatMaterial(
  material
) {
  if (!material) {
    return null;
  }

  const code =
    material.material_code || "";

  const quantity =
    material.quantity ?? "";

  const unit =
    material.unit_code || "";

  return [
    code,
    quantity,
    unit,
  ]
    .filter(
      (value) =>
        String(value).trim() !== ""
    )
    .join(" ");
}


export function formatCultivationLog(
  log,
  isVietnamese = true
) {
  if (!log) {
    return isVietnamese
      ? "Chưa có nhật ký canh tác nào được lưu."
      : "No cultivation logs have been saved yet.";
  }

  const materials =
    Array.isArray(log.materials)
      ? log.materials
          .map(formatMaterial)
          .filter(Boolean)
      : [];

  if (isVietnamese) {
    return [
      "📋 Nhật ký canh tác:",
      `• Mã bản ghi: ${log.client_record_id || "không có"}`,
      `• Lô: ${log.lot_code || "không có"}`,
      `• Công việc: ${log.activity_code || "không có"}`,
      `• Vật tư: ${
        materials.length > 0
          ? materials.join(", ")
          : "không có"
      }`,
      `• Thời gian: ${log.performed_at || "không có"}`,
      `• Trạng thái: ${log.status || "không có"}`,
    ].join("\n");
  }

  return [
    "📋 Cultivation log:",
    `• Record ID: ${log.client_record_id || "not available"}`,
    `• Plot: ${log.lot_code || "not available"}`,
    `• Activity: ${log.activity_code || "not available"}`,
    `• Materials: ${
      materials.length > 0
        ? materials.join(", ")
        : "none"
    }`,
    `• Performed at: ${log.performed_at || "not available"}`,
    `• Status: ${log.status || "not available"}`,
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
    text.includes("nhật ký") &&
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
      text.includes("trồng") ||
      text.includes("cây gì") ||
      text.includes("crop")
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
    const latestLog =
      await getLatestCultivationLog();

    return formatCultivationLog(
      latestLog,
      isVietnamese
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

    const logs =
      await getCultivationLogsByLotCode(
        lotCode
      );

    if (logs.length === 0) {
      return isVietnamese
        ? `Chưa tìm thấy nhật ký nào của ${lotCode}.`
        : `No cultivation logs were found for ${lotCode}.`;
    }

    return [
      isVietnamese
        ? `Tìm thấy ${logs.length} nhật ký của ${lotCode}. Nhật ký gần nhất:`
        : `Found ${logs.length} log(s) for ${lotCode}. Latest log:`,
      "",
      formatCultivationLog(
        logs[0],
        isVietnamese
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

  if (logs.length === 0) {
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