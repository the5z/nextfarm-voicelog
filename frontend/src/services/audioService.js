const API_URL = "http://localhost:8000/api/v1/audio/upload";

// true: dùng dữ liệu giả để test frontend
// false: gọi backend thật
const USE_MOCK_AI = true;

const wait = (milliseconds) =>
  new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });

async function uploadAudioMock(audioBlob) {
  console.log("Mock audio received:", audioBlob);

  // Giả lập AI xử lý trong 1,5 giây
  await wait(1500);

  return {
    transcript:
      "Hôm nay tôi bón 20 kg phân NPK cho lô A01 vào lúc 08 giờ 30.",

    structured_data: {
      lot: "A01",
      work: "Bón phân",
      material: "Phân NPK",
      quantity: "20",
      unit: "kg",
      time: "08:30",
    },
  };
}

async function uploadAudioReal(audioBlob) {
  const formData = new FormData();

  formData.append("file", audioBlob, "record.webm");

  const response = await fetch(API_URL, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = "Upload audio thất bại.";

    try {
      const errorData = await response.json();
      message = errorData.message || message;
    } catch {
      // Backend không trả JSON thì giữ thông báo mặc định.
    }

    throw new Error(message);
  }

  const result = await response.json();

  if (result.success === false) {
    throw new Error(
      result.message || "AI Service xử lý thất bại."
    );
  }

  // Hỗ trợ cả response { data: {...} }
  // và response trả trực tiếp dữ liệu.
  return result.data || result;
}

export async function uploadAudio(audioBlob) {
  if (!(audioBlob instanceof Blob) || audioBlob.size === 0) {
    throw new Error("Bản ghi âm không hợp lệ.");
  }

  if (USE_MOCK_AI) {
    return uploadAudioMock(audioBlob);
  }

  return uploadAudioReal(audioBlob);
}