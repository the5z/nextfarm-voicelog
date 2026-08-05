import { useState } from "react";
import Header from "../components/Header";
import WorkflowStepper from "../components/WorkflowStepper";
import RecordButton from "../components/RecordButton";
import TranscriptBox from "../components/TranscriptBox";
import AIForm from "../components/AIForm";
import ActionButtons from "../components/ActionButtons";
import { uploadAudio } from "../services/audioService";

const EMPTY_AI_DATA = {
  lot: "",
  work: "",
  material: "",
  quantity: "",
  unit: "",
  time: "",
};

function VoiceLog() {
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);

  const [transcript, setTranscript] = useState("");
  const [aiData, setAiData] = useState(EMPTY_AI_DATA);

  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");

  // 1: Ghi âm
  // 2: AI xử lý
  // 3: Kiểm tra và chỉnh sửa
  // 4: Xác nhận
  const [currentStep, setCurrentStep] = useState(1);

  const handleDelete = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }

    setAudioUrl(null);
    setAudioBlob(null);
    setTranscript("");
    setAiData(EMPTY_AI_DATA);
    setMessage("");

    // Quay lại bước ghi âm
    setCurrentStep(1);
  };

  const handleUpload = async () => {
    if (!audioBlob || isUploading) return;

    // Chuyển sang bước AI xử lý
    setCurrentStep(2);
    setIsUploading(true);
    setMessage("Đang gửi bản ghi đến AI Service...");

    try {
      const data = await uploadAudio(audioBlob);

      setTranscript(data?.transcript || "");

      setAiData({
        ...EMPTY_AI_DATA,
        ...(data?.structured_data || {}),
      });

      setMessage("Xử lý bản ghi thành công.");

      // Có kết quả thì chuyển sang bước kiểm tra
      setCurrentStep(3);
    } catch (error) {
      console.error("Upload audio error:", error);

      setMessage(
        "Không thể kết nối AI Service. Hãy kiểm tra backend tại cổng 8000."
      );

      // Xử lý thất bại nhưng vẫn giữ bản ghi để người dùng gửi lại
      setCurrentStep(1);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="container">
      <Header />

      <WorkflowStepper currentStep={currentStep} />

      <RecordButton
        audioUrl={audioUrl}
        setAudioUrl={setAudioUrl}
        setAudioBlob={setAudioBlob}
        setTranscript={setTranscript}
        setAiData={setAiData}
        setMessage={setMessage}
      />

      <TranscriptBox transcript={transcript} />

      <AIForm aiData={aiData} />

      <ActionButtons
        hasAudio={Boolean(audioBlob)}
        isUploading={isUploading}
        onRetry={handleDelete}
        onUpload={handleUpload}
      />

      {message && (
        <p
          className={`app-message ${
            message.includes("Không thể") ? "error" : ""
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}

export default VoiceLog;