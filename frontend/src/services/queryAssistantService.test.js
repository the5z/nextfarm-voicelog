import {
  formatCultivationLog,
  handleQueryIntent,
} from "./queryAssistantService.js";


const VIETNAM_UTC_OFFSET_MS =
  7 * 60 * 60 * 1000;


function createVietnamTodayIso(
  hour = 12
) {
  const vietnamNow =
    new Date(
      Date.now() +
        VIETNAM_UTC_OFFSET_MS
    );

  const dateKey =
    vietnamNow
      .toISOString()
      .slice(0, 10);

  const hourText =
    String(hour)
      .padStart(2, "0");

  return new Date(
    `${dateKey}T${hourText}:00:00+07:00`
  ).toISOString();
}


const sampleLogs = [
  {
    client_record_id: "log-003",
    lot_code: "LO_B",
    activity_code: "LAM_CO",
    materials: [],
    performed_at:
      "2026-08-21T10:00:00",
    status: "saved",
  },

  {
    client_record_id: "log-002",
    lot_code: "LO_B",
    activity_code: "TUOI_NUOC",
    materials: [],
    performed_at:
      "2026-08-21T09:00:00",
    status: "saved",
  },

  {
    client_record_id: "log-001",
    lot_code: "LO_A",
    activity_code: "BON_PHAN",
    materials: [
      {
        material_code: "NPK",
        quantity: 20,
        unit_code: "KG",
      },
    ],
    performed_at:
      "2026-08-21T08:00:00",
    status: "saved",
  },

  {
    client_record_id: "log-000",
    lot_code: "LO_A",
    activity_code: "BON_PHAN",
    materials: [
      {
        material_code: "NPK",
        quantity: 10,
        unit_code: "KG",
      },
    ],
    performed_at:
      "2026-08-20T08:00:00",
    status: "saved",
  },

  // Giai đoạn 6:
  // Hai log thuộc "hôm nay" theo UTC+7.
  // Dùng LO_C để không làm thay đổi
  // các kết quả test Giai đoạn 5.
  {
    client_record_id:
      "today-log-002",
    lot_code: "LO_C",
    activity_code:
      "THU_HOACH",
    materials: [],
    performed_at:
      createVietnamTodayIso(
        12
      ),
    status: "saved",
  },

  {
    client_record_id:
      "today-log-001",
    lot_code: "LO_C",
    activity_code:
      "PHUN_THUOC",
    materials: [],
    performed_at:
      createVietnamTodayIso(
        11
      ),
    status: "saved",
  },
];


const activities = [
  {
    code: "BON_PHAN",
    name: "Bón phân",
    aliases: [
      "bón phân",
      "rải phân",
    ],
  },

  {
    code: "TUOI_NUOC",
    name: "Tưới nước",
    aliases: [
      "tưới",
      "tưới nước",
    ],
  },

  {
    code: "LAM_CO",
    name: "Làm cỏ",
    aliases: [
      "làm cỏ",
      "nhổ cỏ",
    ],
  },

  {
    code: "PHUN_THUOC",
    name: "Phun thuốc",
    aliases: [
      "phun thuốc",
      "xịt thuốc",
    ],
  },

  {
    code: "THU_HOACH",
    name: "Thu hoạch",
    aliases: [
      "thu hoạch",
      "hái",
    ],
  },
];


const lots = [
  {
    code: "LO_A",
    name: "Lô A",
    aliases: [
      "lô a",
    ],
  },

  {
    code: "LO_B",
    name: "Lô B",
    aliases: [
      "lô b",
    ],
  },

  {
    code: "LO_C",
    name: "Lô C",
    aliases: [
      "lô c",
    ],
  },
];


const materials = [
  {
    code: "NPK",
    name: "Phân NPK",
    aliases: [
      "npk",
      "phân npk",
    ],
  },
];


const units = [
  {
    code: "KG",
    name: "Kilôgam",
    aliases: [
      "kg",
      "kilogram",
    ],
  },
];


function createResponse(
  data
) {
  return {
    ok: true,

    async json() {
      return data;
    },
  };
}


globalThis.fetch =
  async (url) => {
    const requestUrl =
      String(url);

    if (
      requestUrl.endsWith(
        "/cultivation-logs"
      )
    ) {
      return createResponse({
        success: true,
        data: sampleLogs,
      });
    }

    if (
      requestUrl.endsWith(
        "/master-data/activities"
      )
    ) {
      return createResponse(
        activities
      );
    }

    if (
      requestUrl.endsWith(
        "/master-data/lots"
      )
    ) {
      return createResponse(
        lots
      );
    }

    if (
      requestUrl.endsWith(
        "/master-data/materials"
      )
    ) {
      return createResponse(
        materials
      );
    }

    if (
      requestUrl.endsWith(
        "/master-data/units"
      )
    ) {
      return createResponse(
        units
      );
    }

    throw new Error(
      `Unexpected URL: ${requestUrl}`
    );
  };


function expectIncludes(
  value,
  expected,
  label
) {
  if (
    !value.includes(
      expected
    )
  ) {
    throw new Error(
      `${label} failed. Expected "${expected}" in:\n${value}`
    );
  }
}


// Formatter fallback.
const formatted =
  formatCultivationLog(
    sampleLogs[2],
    true
  );

expectIncludes(
  formatted,
  "LO_A",
  "formatCultivationLog lot"
);

expectIncludes(
  formatted,
  "BON_PHAN",
  "formatCultivationLog activity"
);

expectIncludes(
  formatted,
  "NPK 20 KG",
  "formatCultivationLog material"
);


// Query nhật ký gần nhất.
const latestReply =
  await handleQueryIntent({
    message:
      "Cho tôi xem nhật ký gần nhất",
    isVietnamese: true,
  });

expectIncludes(
  latestReply,
  "log-003",
  "Latest log query"
);

expectIncludes(
  latestReply,
  "Lô B",
  "Latest log master-data lot mapping"
);

expectIncludes(
  latestReply,
  "Làm cỏ",
  "Latest log master-data activity mapping"
);


// Query nhật ký theo lô.
const lotReply =
  await handleQueryIntent({
    message:
      "Cho tôi xem nhật ký của lô A",
    isVietnamese: true,
  });

expectIncludes(
  lotReply,
  "Lô A",
  "Lot query"
);

expectIncludes(
  lotReply,
  "log-001",
  "Lot query latest matching log"
);


// Query cây trồng chưa có nguồn.
const cropReply =
  await handleQueryIntent({
    message:
      "Lô A đang trồng cây gì?",
    isVietnamese: true,
  });

expectIncludes(
  cropReply,
  "chưa có nguồn dữ liệu",
  "Unsupported crop query"
);


// Giai đoạn 5:
// Hoạt động theo lô.
const activitiesByLotReply =
  await handleQueryIntent({
    message:
      "Lô B có những hoạt động gì?",
    isVietnamese: true,
  });

expectIncludes(
  activitiesByLotReply,
  "Lô B",
  "Activities-by-lot query lot"
);

expectIncludes(
  activitiesByLotReply,
  "Tưới nước",
  "Activities-by-lot query watering"
);

expectIncludes(
  activitiesByLotReply,
  "Làm cỏ",
  "Activities-by-lot query weeding"
);

expectIncludes(
  activitiesByLotReply,
  "2 loại hoạt động",
  "Activities-by-lot query count"
);


// Giai đoạn 5:
// Đếm hoạt động.
const activityCountReply =
  await handleQueryIntent({
    message:
      "Có bao nhiêu lần bón phân?",
    isVietnamese: true,
  });

expectIncludes(
  activityCountReply,
  "2 lần",
  "Activity count query"
);

expectIncludes(
  activityCountReply,
  "bón phân",
  "Activity count query activity"
);


// Giai đoạn 5:
// Lô + hoạt động + đếm.
const lotActivityCountReply =
  await handleQueryIntent({
    message:
      "Lô A đã bón phân bao nhiêu lần?",
    isVietnamese: true,
  });

expectIncludes(
  lotActivityCountReply,
  "Lô A",
  "Lot activity count query lot"
);

expectIncludes(
  lotActivityCountReply,
  "2 lần",
  "Lot activity count query count"
);

expectIncludes(
  lotActivityCountReply,
  "bón phân",
  "Lot activity count query activity"
);


// Giai đoạn 5:
// Vật tư đã sử dụng ở lô nào.
const materialUsageReply =
  await handleQueryIntent({
    message:
      "NPK đã được dùng ở lô nào?",
    isVietnamese: true,
  });

expectIncludes(
  materialUsageReply,
  "Phân NPK",
  "Material usage query material"
);

expectIncludes(
  materialUsageReply,
  "2 nhật ký",
  "Material usage query count"
);

expectIncludes(
  materialUsageReply,
  "Lô A",
  "Material usage query lot"
);


// Giai đoạn 6:
// Hoạt động hôm nay theo UTC+7.
const todayActivitiesReply =
  await handleQueryIntent({
    message:
      "Hôm nay có những hoạt động gì?",
    isVietnamese: true,
  });

expectIncludes(
  todayActivitiesReply,
  "Hôm nay có 2 nhật ký",
  "Today activities log count"
);

expectIncludes(
  todayActivitiesReply,
  "2 loại hoạt động",
  "Today activities type count"
);

expectIncludes(
  todayActivitiesReply,
  "Phun thuốc",
  "Today activities spraying"
);

expectIncludes(
  todayActivitiesReply,
  "Thu hoạch",
  "Today activities harvesting"
);


// Giai đoạn 6:
// Nhật ký hôm nay.
const todayLogsReply =
  await handleQueryIntent({
    message:
      "Cho tôi xem nhật ký hôm nay",
    isVietnamese: true,
  });

expectIncludes(
  todayLogsReply,
  "Hôm nay có 2 nhật ký",
  "Today logs count"
);

expectIncludes(
  todayLogsReply,
  "today-log-002",
  "Today latest log"
);

expectIncludes(
  todayLogsReply,
  "Lô C",
  "Today latest log lot mapping"
);

expectIncludes(
  todayLogsReply,
  "Thu hoạch",
  "Today latest log activity mapping"
);


// Giai doan 8:
// Hoat dong trong 7 ngay gan day.
const recentActivitiesReply =
  await handleQueryIntent({
    message:
      "7 ng\u00e0y g\u1ea7n \u0111\u00e2y c\u00f3 nh\u1eefng ho\u1ea1t \u0111\u1ed9ng g\u00ec?",
    isVietnamese: true,
  });

expectIncludes(
  recentActivitiesReply,
  "7 ng\u00e0y g\u1ea7n \u0111\u00e2y c\u00f3",
  "Recent activities heading"
);

expectIncludes(
  recentActivitiesReply,
  "Phun thu\u1ed1c",
  "Recent activities spraying"
);

expectIncludes(
  recentActivitiesReply,
  "Thu ho\u1ea1ch",
  "Recent activities harvesting"
);


// Giai doan 8:
// Nhat ky trong 7 ngay gan day.
const recentLogsReply =
  await handleQueryIntent({
    message:
      "Cho t\u00f4i xem nh\u1eadt k\u00fd 7 ng\u00e0y g\u1ea7n \u0111\u00e2y",
    isVietnamese: true,
  });

expectIncludes(
  recentLogsReply,
  "7 ng\u00e0y g\u1ea7n \u0111\u00e2y c\u00f3",
  "Recent logs heading"
);

expectIncludes(
  recentLogsReply,
  "today-log-002",
  "Recent latest log"
);

expectIncludes(
  recentLogsReply,
  "L\u00f4 C",
  "Recent latest lot mapping"
);

expectIncludes(
  recentLogsReply,
  "Thu ho\u1ea1ch",
  "Recent latest activity mapping"
);


console.log(
  "Query Assistant tests passed."
);
