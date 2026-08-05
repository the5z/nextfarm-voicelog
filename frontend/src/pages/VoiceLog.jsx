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
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [message, setMessage] = useState("");

  // 1: Ghi âm
  // 2: AI xử lý
  // 3: Kiểm tra và chỉnh sửa
  // 4: Xác nhận
  const [currentStep, setCurrentStep] = useState(1);

  const resetVoiceLog = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }

    setAudioUrl(null);
    setAudioBlob(null);
    setTranscript("");
    setAiData(EMPTY_AI_DATA);
    setIsUploading(false);
    setIsConfirmed(false);
    setMessage("");
    setCurrentStep(1);
  };

  const handleDelete = () => {
    resetVoiceLog();
  };

  const handleCreateNew = () => {
    resetVoiceLog();
  };

  const handleUpload = async () => {
    if (!audioBlob || isUploading || isConfirmed) return;

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
      setCurrentStep(3);
    } catch (error) {
      console.error("Upload audio error:", error);

      setMessage(
        "Không thể kết nối AI Service. Hãy kiểm tra backend tại cổng 8000."
      );

      setCurrentStep(1);
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirm = () => {
    if (!transcript.trim()) {
      setMessage("Vui lòng kiểm tra nội dung ghi âm trước khi xác nhận.");
      return;
    }

    setIsConfirmed(true);
    setCurrentStep(4);
    setMessage("Nhật ký đã được xác nhận.");
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
        isConfirmed={isConfirmed}
      />

      <TranscriptBox
        transcript={transcript}
        onTranscriptChange={setTranscript}
        isConfirmed={isConfirmed}
      />

      <AIForm
        aiData={aiData}
        onAiDataChange={setAiData}
        isConfirmed={isConfirmed}
      />

      <ActionButtons
        hasAudio={Boolean(audioBlob)}
        hasResult={Boolean(transcript.trim())}
        isUploading={isUploading}
        isConfirmed={isConfirmed}
        onRetry={handleDelete}
        onUpload={handleUpload}
        onConfirm={handleConfirm}
        onCreateNew={handleCreateNew}
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