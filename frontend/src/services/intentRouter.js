export const ASSISTANT_INTENT = {
  VOICELOG_CONTEXT:
    "voicelog_context",

  VOICELOG_COMMAND:
    "voicelog_command",

  QUERY:
    "query",

  GENERAL:
    "general",
};


function normalizeMessage(
  message
) {
  return String(
    message ?? ""
  )
    .trim()
    .toLowerCase()
    .replace(
      /\s+/g,
      " "
    );
}


function isCurrentLogCommand(
  message
) {
  const text =
    normalizeMessage(
      message
    );

  return (
    text.includes(
      "dữ liệu hiện tại"
    ) ||
    text.includes(
      "nhật ký hiện tại"
    ) ||
    text.includes(
      "form hiện tại"
    ) ||
    text.includes(
      "đang có gì"
    ) ||
    text.includes(
      "đã có gì"
    ) ||
    text.includes(
      "đọc dữ liệu"
    ) ||
    text.includes(
      "current log"
    ) ||
    text.includes(
      "current form"
    ) ||
    text.includes(
      "current data"
    )
  );
}


function isUndoCommand(
  message
) {
  const text =
    normalizeMessage(
      message
    );

  return (
    text === "undo" ||
    text.includes(
      "hoàn tác"
    ) ||
    text.includes(
      "quay lại thay đổi trước"
    ) ||
    text.includes(
      "khôi phục thay đổi trước"
    ) ||
    text.includes(
      "undo last change"
    )
  );
}


function isEditCommand(
  message
) {
  const text =
    normalizeMessage(
      message
    );

  const editPrefixes = [
    "đổi ",
    "sửa ",
    "cập nhật ",
    "change ",
  ];

  return editPrefixes.some(
    (prefix) =>
      text.startsWith(
        prefix
      )
  );
}


export function isQueryIntent(
  message
) {
  const text =
    normalizeMessage(
      message
    );

  const queryPatterns = [
    // Query cây trồng / trạng thái lô.
    /lô\s+.+\s+(?:trồng|đang trồng|có cây|tình trạng)/i,

    // Tra cứu nhật ký nói chung.
    /(?:cho tôi|xem|tìm|tra cứu).*(?:nhật ký|lịch sử)/i,

    // Nhật ký gần nhất / theo thời gian.
    /nhật ký\s+(?:gần nhất|mới nhất|hôm nay|hôm qua)/i,

    // Giai đoạn 6:
    // Query hoạt động / công việc / nhật ký theo ngày.
    /(?:hôm nay|hôm qua).*(?:hoạt động|công việc|nhật ký|đã làm|làm gì)/i,

    // Giai doan 8:
    // Query trong 7 ngay gan day.
    /(?:7 ng\u00e0y g\u1ea7n \u0111\u00e2y|7 ng\u00e0y qua|trong 7 ng\u00e0y).*(?:ho\u1ea1t \u0111\u1ed9ng|c\u00f4ng vi\u1ec7c|nh\u1eadt k\u00fd|\u0111\u00e3 l\u00e0m|l\u00e0m g\u00ec)/i,

    // Nhật ký theo lô.
    /nhật ký.*\blô\s+[a-z0-9_-]+\b/i,

    // Thông tin lô.
    /(?:thông tin|trạng thái|diện tích)\s+lô/i,

    // Hoạt động của một lô.
    /\blô\s+[a-z0-9_-]+\b.*(?:hoạt động|công việc|đã làm|làm gì)/i,

    // Query hoạt động cụ thể trên một lô.
    /\blô\s+[a-z0-9_-]+\b.*(?:bón phân|tưới nước|làm cỏ|phun thuốc|thu hoạch|cho bò ăn)/i,

    // Đếm số lần thực hiện hoạt động.
    /(?:bao nhiêu|mấy)\s+lần.*(?:bón phân|tưới nước|làm cỏ|phun thuốc|thu hoạch|cho bò ăn)/i,

    // Câu đảo: hoạt động ... bao nhiêu lần.
    /(?:bón phân|tưới nước|làm cỏ|phun thuốc|thu hoạch|cho bò ăn).*(?:bao nhiêu|mấy)\s+lần/i,

    // Tra cứu vật tư đã sử dụng.
    /(?:cây|vật tư).*(?:đã dùng|đang dùng|sử dụng)/i,

    // Tên vật tư + hành động sử dụng.
    /\b(?:npk|urê|ure|cám)\b.*(?:đã|được|dùng|sử dụng).*(?:lô|ở đâu|nào)/i,

    // Hỏi lô nào đã dùng vật tư.
    /(?:lô|ở đâu).*(?:dùng|sử dụng).*\b(?:npk|urê|ure|cám)\b/i,

    // English query patterns.
    /(?:latest|recent)\s+(?:log|farming log)/i,

    /(?:plot|field).*(?:crop|status|area)/i,

    /(?:how many|count).*(?:fertilize|water|weed|spray|harvest)/i,

    /(?:npk|urea|feed).*(?:used|use).*(?:plot|field|where)/i,
  ];

  return queryPatterns.some(
    (pattern) =>
      pattern.test(
        text
      )
  );
}


export function routeAssistantIntent({
  message,
  hasCollectingSession = false,
  expectedField = null,
  isContextReply = false,
}) {
  // VoiceLog contextual answer always has highest priority.
  if (
    hasCollectingSession &&
    expectedField &&
    isContextReply
  ) {
    return ASSISTANT_INTENT
      .VOICELOG_CONTEXT;
  }

  // Explicit commands for the current VoiceLog form.
  if (
    isUndoCommand(
      message
    ) ||
    isEditCommand(
      message
    ) ||
    isCurrentLogCommand(
      message
    )
  ) {
    return ASSISTANT_INTENT
      .VOICELOG_COMMAND;
  }

  // Historical / reporting / farm-data queries.
  if (
    isQueryIntent(
      message
    )
  ) {
    return ASSISTANT_INTENT
      .QUERY;
  }

  return ASSISTANT_INTENT
    .GENERAL;
}
