const API_URL = "http://localhost:8000/api/v1/audio/upload";

// true: dùng dữ liệu giả để test frontend
// false: gọi backend thật
const USE_MOCK_AI = false;

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
      lot_text: "A01",

      activity_text:
        "Bón phân",

      materials: [
        {
          material_text:
            "Phân NPK",

          quantity: 20,

          unit_text: "kg",
        },
      ],

      time_text: "08:30",
    },
  };
}

async function uploadAudioReal(
  audioBlob
) {
  const formData =
    new FormData();

  formData.append(
    "file",
    audioBlob,
    "record.webm"
  );

  /*
    Tạm tắt noise reduction
    để A/B test Whisper với
    audio gốc.
  */
  formData.append(
    "use_noise_reduction",
    "false"
  );

  const response =
    await fetch(
      API_URL,
      {
        method: "POST",
        body: formData,
      }
    );

  if (!response.ok) {
    let message =
      "Upload audio thất bại.";

    try {
      const errorData =
        await response.json();

      message =
        errorData.message ||
        errorData.detail ||
        message;
    } catch {
      // Backend không trả JSON.
    }

    throw new Error(
      message
    );
  }

  const result =
    await response.json();

  if (
    result.success === false
  ) {
    throw new Error(
      result.message ||
        "AI Service xử lý thất bại."
    );
  }

  return (
    result.data ||
    result
  );
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