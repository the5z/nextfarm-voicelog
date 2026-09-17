const API_URL =
  import.meta.env.VITE_AI_API_URL ||
  "http://localhost:8000/api/v1/audio/upload";

// true: dùng dữ liệu giả để test frontend
// false: gọi backend thật
const USE_MOCK_AI = false;

const DEFAULT_OPERATION = "CREATE_WORK_LOG";

const wait = (milliseconds) =>
  new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });

function normalizeOptions(options = {}) {
  const {
    operation = DEFAULT_OPERATION,
    currentFields = {},
    context = {},
    useNoiseReduction = false,
  } = options;

  return {
    operation,
    currentFields:
      currentFields && typeof currentFields === "object"
        ? currentFields
        : {},
    context:
      context && typeof context === "object"
        ? context
        : {},
    useNoiseReduction: Boolean(useNoiseReduction),
  };
}

function normalizeAudioResponse(result) {
  const data = result?.data || result;

  if (!data || typeof data !== "object") {
    throw new Error("AI Service trả về dữ liệu không hợp lệ.");
  }

  if (!data.dynamic_form || typeof data.dynamic_form !== "object") {
    throw new Error(
      "AI Service không trả về dynamic_form theo Contract V3.1."
    );
  }

  return {
    ...data,
    transcript:
      typeof data.transcript === "string"
        ? data.transcript
        : "",
    dynamic_form: data.dynamic_form,
  };
}

async function uploadAudioMock(audioBlob, options) {
  console.log("Mock audio received:", audioBlob);

  await wait(1500);

  const { operation, currentFields } = normalizeOptions(options);

  if (operation !== DEFAULT_OPERATION) {
    throw new Error(
      "Mock AI currently only supports " + DEFAULT_OPERATION + "."
    );
  }

  const mockFields = {
    ...currentFields,
    result_status: currentFields.result_status || "completed",
    plot_text: currentFields.plot_text || "A01",
    activity_text: currentFields.activity_text || "Bón phân",
    performed_time_text:
      currentFields.performed_time_text || "08:30",
    materials:
      Array.isArray(currentFields.materials) &&
      currentFields.materials.length > 0
        ? currentFields.materials
        : [
            {
              material_text: "Phân NPK",
              quantity: 20,
              unit_text: "kg",
            },
          ],
    photo_required:
      currentFields.photo_required ?? false,
    material_batch_text:
      currentFields.material_batch_text ?? null,
    note: currentFields.note ?? null,
  };

  return {
    transcript:
      "Hôm nay tôi bón 20 kg phân NPK cho lô A01 vào lúc 08 giờ 30, đã hoàn thành.",
    dynamic_form: {
      contract_version: "3.1",
      operation,
      template_id: "work_log",
      fields: mockFields,
      missing_fields: [],
      warnings: [],
      field_confidence: {
        result_status: 0.98,
        plot_text: 0.95,
        activity_text: 0.96,
        performed_time_text: 0.93,
        "materials[0].material_text": 0.97,
        "materials[0].quantity": 0.98,
        "materials[0].unit_text": 0.98,
      },
      requires_confirmation: false,
      next_question: null,
    },
  };
}

async function uploadAudioReal(audioBlob, options) {
  const {
    operation,
    currentFields,
    context,
    useNoiseReduction,
  } = normalizeOptions(options);

  const formData = new FormData();

  formData.append(
    "file",
    audioBlob,
    "record.webm"
  );

  formData.append(
    "operation",
    operation
  );

  formData.append(
    "current_fields",
    JSON.stringify(currentFields)
  );

  formData.append(
    "context",
    JSON.stringify(context)
  );

  formData.append(
    "use_noise_reduction",
    String(useNoiseReduction)
  );

  const response = await fetch(API_URL, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = "Upload audio thất bại.";

    try {
      const errorData = await response.json();

      message =
        errorData?.message ||
        errorData?.detail ||
        errorData?.error ||
        message;

      if (typeof message !== "string") {
        message = JSON.stringify(message);
      }
    } catch {
      // Backend không trả JSON.
    }

    throw new Error(message);
  }

  const result = await response.json();

  if (result?.success === false) {
    throw new Error(
      result.message ||
        "AI Service xử lý thất bại."
    );
  }

  return normalizeAudioResponse(result);
}

export async function uploadAudio(
  audioBlob,
  options = {}
) {
  if (
    !(audioBlob instanceof Blob) ||
    audioBlob.size === 0
  ) {
    throw new Error(
      "Bản ghi âm không hợp lệ."
    );
  }

  if (USE_MOCK_AI) {
    return uploadAudioMock(
      audioBlob,
      options
    );
  }

  return uploadAudioReal(
    audioBlob,
    options
  );
}

export function getAiApiUrl() {
  return API_URL;
}
