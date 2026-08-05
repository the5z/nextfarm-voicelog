const API_URL = "http://localhost:8000/api/v1/audio/upload";

/**
 * Upload file ghi âm lên AI Service
 */
export async function uploadAudio(audioBlob) {
  const formData = new FormData();

  formData.append("file", audioBlob, "record.webm");

  const response = await fetch(API_URL, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Không thể kết nối AI Service.");
  }

  const result = await response.json();

  console.log("===== AI RESPONSE =====");
  console.log(result);

  if (!result.success) {
    throw new Error(result.message);
  }

  // Chỉ trả phần data
  return result.data;
}