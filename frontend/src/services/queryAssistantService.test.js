import {
  formatCultivationLog,
  handleQueryIntent,
} from "./queryAssistantService.js";


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


// Kiểm tra formatter cơ bản
// vẫn fallback được khi không truyền lookups.
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


// Query cây trồng chưa có nguồn dữ liệu.
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
// Lô B có những hoạt động gì?
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
// Có bao nhiêu lần bón phân?
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
// Lô A đã bón phân bao nhiêu lần?
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
// NPK đã được dùng ở lô nào?
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


console.log(
  "Query Assistant tests passed."
);