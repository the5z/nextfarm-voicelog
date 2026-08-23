import {
  formatCultivationLog,
  handleQueryIntent,
} from "./queryAssistantService.js";


const sampleLogs = [
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
];


globalThis.fetch = async () => ({
  ok: true,

  async json() {
    return {
      success: true,
      data: sampleLogs,
    };
  },
});


const formatted =
  formatCultivationLog(
    sampleLogs[1],
    true
  );

if (
  !formatted.includes("LO_A") ||
  !formatted.includes("BON_PHAN") ||
  !formatted.includes("NPK 20 KG")
) {
  throw new Error(
    "formatCultivationLog failed."
  );
}


const latestReply =
  await handleQueryIntent({
    message:
      "Cho tôi xem nhật ký gần nhất",
    isVietnamese: true,
  });

if (
  !latestReply.includes(
    "log-002"
  ) ||
  !latestReply.includes(
    "LO_B"
  )
) {
  throw new Error(
    "Latest log query failed."
  );
}


const lotReply =
  await handleQueryIntent({
    message:
      "Cho tôi xem nhật ký của lô A",
    isVietnamese: true,
  });

if (
  !lotReply.includes(
    "LO_A"
  ) ||
  !lotReply.includes(
    "log-001"
  )
) {
  throw new Error(
    "Lot log query failed."
  );
}


const cropReply =
  await handleQueryIntent({
    message:
      "Lô A đang trồng cây gì?",
    isVietnamese: true,
  });

if (
  !cropReply.includes(
    "chưa có nguồn dữ liệu"
  )
) {
  throw new Error(
    "Unsupported crop query handling failed."
  );
}


console.log(
  "Query Assistant tests passed."
);