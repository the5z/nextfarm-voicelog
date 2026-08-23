import {
  ASSISTANT_INTENT,
  routeAssistantIntent,
} from "./intentRouter.js";


function expectIntent(
  input,
  expected
) {
  const actual =
    routeAssistantIntent(
      input
    );

  if (actual !== expected) {
    throw new Error(
      `Expected "${expected}" but received "${actual}".`
    );
  }
}


expectIntent(
  {
    message: "8 giờ",
    hasCollectingSession: true,
    expectedField: "time_text",
    isContextReply: true,
  },
  ASSISTANT_INTENT
    .VOICELOG_CONTEXT
);


expectIntent(
  {
    message: "20 kg",
    hasCollectingSession: true,
    expectedField:
      "materials.quantity",
    isContextReply: true,
  },
  ASSISTANT_INTENT
    .VOICELOG_CONTEXT
);


expectIntent(
  {
    message:
      "Đổi thời gian thành 8 giờ",
  },
  ASSISTANT_INTENT
    .VOICELOG_COMMAND
);


expectIntent(
  {
    message:
      "Dữ liệu hiện tại có gì?",
  },
  ASSISTANT_INTENT
    .VOICELOG_COMMAND
);


expectIntent(
  {
    message:
      "Hoàn tác thay đổi trước",
  },
  ASSISTANT_INTENT
    .VOICELOG_COMMAND
);


expectIntent(
  {
    message:
      "Lô A đang trồng cây gì?",
  },
  ASSISTANT_INTENT
    .QUERY
);


expectIntent(
  {
    message:
      "Cho tôi xem nhật ký gần nhất",
  },
  ASSISTANT_INTENT
    .QUERY
);


expectIntent(
  {
    message:
      "Thông tin diện tích lô A",
  },
  ASSISTANT_INTENT
    .QUERY
);


expectIntent(
  {
    message:
      "Xin chào",
  },
  ASSISTANT_INTENT
    .GENERAL
);


expectIntent(
  {
    message:
      "Lô A đang trồng cây gì?",
    hasCollectingSession: true,
    expectedField: "time_text",
    isContextReply: false,
  },
  ASSISTANT_INTENT
    .QUERY
);


console.log(
  "Intent Router tests passed."
);