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


function isQueryIntent(
  message
) {
  const text =
    normalizeMessage(
      message
    );

  const queryPatterns = [
    /lô\s+.+\s+(?:trồng|đang trồng|có cây|tình trạng)/i,

    /(?:cho tôi|xem|tìm|tra cứu).*(?:nhật ký|lịch sử)/i,

    /nhật ký\s+(?:gần nhất|mới nhất|hôm nay|hôm qua)/i,

    /(?:thông tin|trạng thái|diện tích)\s+lô/i,

    /(?:cây|vật tư).*(?:đã dùng|đang dùng|sử dụng)/i,

    /(?:latest|recent)\s+(?:log|farming log)/i,

    /(?:plot|field).*(?:crop|status|area)/i,
  ];

  return queryPatterns.some(
    (pattern) =>
      pattern.test(text)
  );
}


export function routeAssistantIntent({
  message,
  hasCollectingSession = false,
  expectedField = null,
  isContextReply = false,
}) {
  if (
    hasCollectingSession &&
    expectedField &&
    isContextReply
  ) {
    return ASSISTANT_INTENT
      .VOICELOG_CONTEXT;
  }

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