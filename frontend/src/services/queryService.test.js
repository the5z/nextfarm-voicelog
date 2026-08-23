import {
  getCultivationLogs,
  getLatestCultivationLog,
  getCultivationLogsByLotCode,
} from "./queryService.js";


const sampleLogs = [
  {
    client_record_id: "log-002",
    lot_code: "LO_B",
    activity_code: "TUOI_NUOC",
    materials: [],
    performed_at:
      "2026-08-21T09:00:00",
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


const logs =
  await getCultivationLogs();

if (logs.length !== 2) {
  throw new Error(
    "getCultivationLogs failed."
  );
}


const latest =
  await getLatestCultivationLog();

if (
  latest?.client_record_id !==
  "log-002"
) {
  throw new Error(
    "getLatestCultivationLog failed."
  );
}


const lotALogs =
  await getCultivationLogsByLotCode(
    "LO_A"
  );

if (
  lotALogs.length !== 1 ||
  lotALogs[0]
    ?.client_record_id !==
    "log-001"
) {
  throw new Error(
    "getCultivationLogsByLotCode failed."
  );
}


console.log(
  "Query Service tests passed."
);