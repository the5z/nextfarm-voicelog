const STORAGE_KEY =
  "nextfarm-farming-logs";

const INITIAL_LOGS = [
  {
    id: "log-001",
    lot: "A01",
    work: "Bón phân",
    material: "Phân NPK",
    quantity: "20",
    unit: "kg",
    time: "08:30",
    date: "13/08/2026",
    status: "completed",
    transcript:
      "Hôm nay tôi bón 20 kg phân NPK cho lô A01 lúc 8 giờ 30.",
    createdAt:
      "2026-08-13T08:30:00",
    updatedAt:
      "2026-08-13T08:30:00",
  },

  {
    id: "log-002",
    lot: "B02",
    work: "Tưới nước",
    material: "",
    quantity: "",
    unit: "",
    time: "",
    date: "13/08/2026",
    status: "draft",
    transcript:
      "Hôm nay tôi tưới nước cho lô B02.",
    createdAt:
      "2026-08-13T09:10:00",
    updatedAt:
      "2026-08-13T09:10:00",
  },

  {
    id: "log-003",
    lot: "C03",
    work: "Phun thuốc",
    material: "Thuốc BVTV",
    quantity: "5",
    unit: "",
    time: "15:20",
    date: "12/08/2026",
    status: "review",
    transcript:
      "Phun 5 thuốc bảo vệ thực vật cho lô C03 lúc 15 giờ 20.",
    warning:
      "Có số lượng nhưng chưa có đơn vị.",
    createdAt:
      "2026-08-12T15:20:00",
    updatedAt:
      "2026-08-12T15:20:00",
  },

  {
    id: "log-004",
    lot: "A05",
    work: "Kiểm tra sâu bệnh",
    material: "",
    quantity: "",
    unit: "",
    time: "09:10",
    date: "11/08/2026",
    status: "completed",
    transcript:
      "Kiểm tra sâu bệnh tại lô A05 lúc 9 giờ 10.",
    createdAt:
      "2026-08-11T09:10:00",
    updatedAt:
      "2026-08-11T09:10:00",
  },

  {
    id: "log-005",
    lot: "D01",
    work: "Bón phân",
    material: "Phân hữu cơ",
    quantity: "15",
    unit: "kg",
    time: "07:45",
    date: "10/08/2026",
    status: "completed",
    transcript:
      "Bón 15 kg phân hữu cơ cho lô D01 lúc 7 giờ 45.",
    createdAt:
      "2026-08-10T07:45:00",
    updatedAt:
      "2026-08-10T07:45:00",
  },
];

export function loadLogs() {
  try {
    const saved =
      localStorage.getItem(
        STORAGE_KEY
      );

    if (!saved) {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(
          INITIAL_LOGS
        )
      );

      return INITIAL_LOGS;
    }

    const parsed =
      JSON.parse(saved);

    if (!Array.isArray(parsed)) {
      return INITIAL_LOGS;
    }

    return parsed;
  } catch (error) {
    console.error(
      "Load logs error:",
      error
    );

    return INITIAL_LOGS;
  }
}

export function persistLogs(
  logs
) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(logs)
    );
  } catch (error) {
    console.error(
      "Save logs error:",
      error
    );
  }
}

export function resetLogs() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(INITIAL_LOGS)
  );

  return INITIAL_LOGS;
}