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


// Giai đoạn 5:
// Query hoạt động theo lô.
expectIntent(
  {
    message:
      "Lô B có những hoạt động gì?",
  },
  ASSISTANT_INTENT
    .QUERY
);


// Giai đoạn 5:
// Đếm hoạt động.
expectIntent(
  {
    message:
      "Có bao nhiêu lần bón phân?",
  },
  ASSISTANT_INTENT
    .QUERY
);


// Giai đoạn 5:
// Kết hợp lô + hoạt động + đếm.
expectIntent(
  {
    message:
      "Lô A đã bón phân bao nhiêu lần?",
  },
  ASSISTANT_INTENT
    .QUERY
);


// Giai đoạn 5:
// Tra cứu vật tư theo lô.
expectIntent(
  {
    message:
      "NPK đã được dùng ở lô nào?",
  },
  ASSISTANT_INTENT
    .QUERY
);


// Giai đoạn 6:
// Query hoạt động hôm nay.
expectIntent(
  {
    message:
      "Hôm nay có những hoạt động gì?",
  },
  ASSISTANT_INTENT
    .QUERY
);


// Giai đoạn 6:
// Query nhật ký hôm nay.
expectIntent(
  {
    message:
      "Cho tôi xem nhật ký hôm nay",
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


// Giai doan 8:
// Query hoat dong trong 7 ngay gan day.
expectIntent(
  {
    message:
      "7 ng\u00e0y g\u1ea7n \u0111\u00e2y c\u00f3 nh\u1eefng ho\u1ea1t \u0111\u1ed9ng g\u00ec?",
  },
  ASSISTANT_INTENT
    .QUERY
);


// Giai doan 8:
// Query nhat ky trong 7 ngay gan day.
expectIntent(
  {
    message:
      "Cho t\u00f4i xem nh\u1eadt k\u00fd 7 ng\u00e0y g\u1ea7n \u0111\u00e2y",
  },
  ASSISTANT_INTENT
    .QUERY
);


console.log(
  "Intent Router tests passed."
);
