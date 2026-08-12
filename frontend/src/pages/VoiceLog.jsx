import { useState } from "react";

import Header from "../components/Header";
import WorkflowStepper from "../components/WorkflowStepper";
import RecordButton from "../components/RecordButton";
import TranscriptBox from "../components/TranscriptBox";
import AIForm from "../components/AIForm";
import ActionButtons from "../components/ActionButtons";
import AIAssistant from "../components/AIAssistant";

import { uploadAudio } from "../services/audioService";
import { TEXT } from "../constants/translations";

const EMPTY_AI_DATA = {
  lot: "",
  work: "",
  material: "",
  quantity: "",
  unit: "",
  time: "",
};

const DEV_VALID_DATA = {
  transcript:
    "Hôm nay tôi bón 20 kg phân NPK cho lô A01 lúc 8 giờ 30.",

  structuredData: {
    lot: "A01",
    work: "Bón phân",
    material: "Phân NPK",
    quantity: "20",
    unit: "kg",
    time: "08:30",
  },
};

const DEV_ERROR_DATA = {
  transcript:
    "Hôm nay tôi thực hiện công việc nhưng thông tin nhận dạng chưa đầy đủ.",

  structuredData: {
    lot: "",
    work: "",
    material: "Phân NPK",
    quantity: "0",
    unit: "",
    time: "",
  },
};

const DEV_WARNING_DATA = {
  transcript:
    "Hôm nay tôi kiểm tra lô A01.",

  structuredData: {
    lot: "A01",
    work: "Kiểm tra lô",
    material: "",
    quantity: "",
    unit: "",
    time: "",
  },
};

function VoiceLog() {
  const [language, setLanguage] =
    useState("vi");

  const t = TEXT[language];

  const isVietnamese =
    language === "vi";

  const [audioUrl, setAudioUrl] =
    useState(null);

  const [audioBlob, setAudioBlob] =
    useState(null);

  const [
    transcript,
    setTranscript,
  ] = useState("");

  const [aiData, setAiData] =
    useState(EMPTY_AI_DATA);

  const [
    isUploading,
    setIsUploading,
  ] = useState(false);

  const [
    isConfirmed,
    setIsConfirmed,
  ] = useState(false);

  const [
    hasAttemptedSubmit,
    setHasAttemptedSubmit,
  ] = useState(false);

  const [message, setMessage] =
    useState(null);

  const [
    currentStep,
    setCurrentStep,
  ] = useState(1);

  const isDevMode =
    import.meta.env.DEV;

  const showMessage = (
    type,
    text
  ) => {
    setMessage({
      type,
      text,
    });
  };

  const getMessageText = () => {
    if (!message) {
      return "";
    }

    if (
      typeof message === "string"
    ) {
      return message;
    }

    return message.text || "";
  };

  const getMessageType = () => {
    if (!message) {
      return "success";
    }

    if (
      typeof message === "object"
    ) {
      return (
        message.type ||
        "success"
      );
    }

    const errorKeywords = [
      "Không thể",
      "Vui lòng",
      "lỗi",
      "Unable",
      "Please",
      "error",
    ];

    return errorKeywords.some(
      (keyword) =>
        message.includes(keyword)
    )
      ? "error"
      : "success";
  };

  const validateAiData = (
    data
  ) => {
    const errors = {};
    const warnings = {};

    const lot =
      String(
        data?.lot || ""
      ).trim();

    const work =
      String(
        data?.work || ""
      ).trim();

    const material =
      String(
        data?.material || ""
      ).trim();

    const quantityRaw =
      String(
        data?.quantity ?? ""
      ).trim();

    const unit =
      String(
        data?.unit || ""
      ).trim();

    const time =
      String(
        data?.time || ""
      ).trim();

    if (!lot) {
      errors.lot =
        isVietnamese
          ? "Chưa có thông tin lô canh tác."
          : "Farm plot is required.";
    }

    if (!work) {
      errors.work =
        isVietnamese
          ? "Chưa có thông tin công việc."
          : "Farming task is required.";
    }

    if (quantityRaw) {
      const quantity =
        Number(quantityRaw);

      if (
        Number.isNaN(quantity)
      ) {
        errors.quantity =
          isVietnamese
            ? "Số lượng phải là một số hợp lệ."
            : "Quantity must be a valid number.";
      } else if (
        quantity <= 0
      ) {
        errors.quantity =
          isVietnamese
            ? "Số lượng phải lớn hơn 0."
            : "Quantity must be greater than 0.";
      }

      if (!unit) {
        errors.unit =
          isVietnamese
            ? "Có số lượng nhưng chưa có đơn vị."
            : "Unit is required when quantity is provided.";
      }
    }

    if (
      unit &&
      !quantityRaw
    ) {
      errors.quantity =
        isVietnamese
          ? "Có đơn vị nhưng chưa có số lượng."
          : "Quantity is required when a unit is provided.";
    }

    if (
      work &&
      !material
    ) {
      warnings.material =
        isVietnamese
          ? "Chưa có vật tư. Hãy kiểm tra xem công việc này có sử dụng vật tư hay không."
          : "No material detected. Check whether this task requires a material.";
    }

    if (!time) {
      warnings.time =
        isVietnamese
          ? "Chưa có thời gian thực hiện."
          : "No execution time was detected.";
    }

    return {
      errors,
      warnings,
      isValid:
        Object.keys(errors)
          .length === 0,
    };
  };

  const validation =
    validateAiData(aiData);

  const resetVoiceLog = () => {
    if (audioUrl) {
      URL.revokeObjectURL(
        audioUrl
      );
    }

    setAudioUrl(null);
    setAudioBlob(null);

    setTranscript("");
    setAiData(
      EMPTY_AI_DATA
    );

    setIsUploading(false);
    setIsConfirmed(false);

    setHasAttemptedSubmit(
      false
    );

    setMessage(null);
    setCurrentStep(1);
  };

  const handleDelete = () => {
    resetVoiceLog();
  };

  const handleCreateNew = () => {
    resetVoiceLog();
  };

  const loadDevTestData = (
    testData,
    testName
  ) => {
    if (audioUrl) {
      URL.revokeObjectURL(
        audioUrl
      );
    }

    setAudioUrl(null);
    setAudioBlob(null);

    setTranscript(
      testData.transcript
    );

    setAiData({
      ...EMPTY_AI_DATA,
      ...testData.structuredData,
    });

    setIsUploading(false);
    setIsConfirmed(false);

    setHasAttemptedSubmit(
      false
    );

    setCurrentStep(3);

    showMessage(
      "success",
      isVietnamese
        ? `🧪 Đã nạp dữ liệu DEV: ${testName}.`
        : `🧪 DEV test data loaded: ${testName}.`
    );
  };

  const handleLoadValidTest =
    () => {
      loadDevTestData(
        DEV_VALID_DATA,
        isVietnamese
          ? "Dữ liệu hợp lệ"
          : "Valid data"
      );
    };

  const handleLoadErrorTest =
    () => {
      loadDevTestData(
        DEV_ERROR_DATA,
        isVietnamese
          ? "Dữ liệu lỗi"
          : "Error data"
      );
    };

  const handleLoadWarningTest =
    () => {
      loadDevTestData(
        DEV_WARNING_DATA,
        isVietnamese
          ? "Dữ liệu cảnh báo"
          : "Warning data"
      );
    };

  const handleResetDevTest =
    () => {
      resetVoiceLog();

      showMessage(
        "success",
        isVietnamese
          ? "🧪 Đã reset dữ liệu DEV."
          : "🧪 DEV test data reset."
      );
    };

  const handleUpload =
    async () => {
      if (
        !audioBlob ||
        isUploading ||
        isConfirmed
      ) {
        return;
      }

      setCurrentStep(2);
      setIsUploading(true);

      setHasAttemptedSubmit(
        false
      );

      showMessage(
        "success",
        t.messages.sending
      );

      try {
        const data =
          await uploadAudio(
            audioBlob
          );

        setTranscript(
          data?.transcript ||
            ""
        );

        setAiData({
          ...EMPTY_AI_DATA,
          ...(data?.structured_data ||
            {}),
        });

        showMessage(
          "success",
          t.messages.processed
        );

        setCurrentStep(3);
      } catch (error) {
        console.error(
          "Upload audio error:",
          error
        );

        showMessage(
          "error",
          t.messages.backendError
        );

        setCurrentStep(1);
      } finally {
        setIsUploading(
          false
        );
      }
    };

  const handleConfirm = () => {
    setHasAttemptedSubmit(
      true
    );

    if (
      !transcript.trim()
    ) {
      showMessage(
        "error",
        t.messages
          .reviewBeforeConfirm
      );

      return;
    }

    const currentValidation =
      validateAiData(
        aiData
      );

    if (
      !currentValidation.isValid
    ) {
      showMessage(
        "error",
        isVietnamese
          ? "Chưa thể xác nhận nhật ký. Vui lòng kiểm tra các trường được đánh dấu."
          : "The log cannot be confirmed yet. Please review the highlighted fields."
      );

      setCurrentStep(3);

      return;
    }

    setIsConfirmed(true);
    setCurrentStep(4);

    showMessage(
      "success",
      t.messages.confirmed
    );
  };

  const messageText =
    getMessageText();

  const messageType =
    getMessageType();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            🌱
          </div>

          <div className="sidebar-brand-text">
            <strong>
              NextFarm
            </strong>

            <span>
              VoiceLog
            </span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            type="button"
            className="sidebar-item active"
          >
            <span className="sidebar-item-icon">
              🎙
            </span>

            <span>
              {isVietnamese
                ? "Tạo nhật ký"
                : "Create log"}
            </span>
          </button>

          <button
            type="button"
            className="sidebar-item"
          >
            <span className="sidebar-item-icon">
              📋
            </span>

            <span>
              {isVietnamese
                ? "Nhật ký của tôi"
                : "My logs"}
            </span>
          </button>

          <div className="sidebar-divider" />

          <button
            type="button"
            className="sidebar-item"
          >
            <span className="sidebar-item-icon">
              ⚙️
            </span>

            <span>
              {isVietnamese
                ? "Cài đặt"
                : "Settings"}
            </span>
          </button>
        </nav>
      </aside>

      <main className="workspace">
        <div className="workspace-container">
          <Header
            language={
              language
            }
            onLanguageChange={
              setLanguage
            }
            text={t}
          />

          <section className="workspace-hero">
            <div>
              <span className="workspace-eyebrow">
                NextFarm AI Workspace
              </span>

              <h2>
                {isVietnamese
                  ? "Tạo nhật ký canh tác bằng giọng nói"
                  : "Create farming logs with your voice"}
              </h2>

              <p>
                {isVietnamese
                  ? "Ghi âm, để AI xử lý và kiểm tra dữ liệu trước khi xác nhận."
                  : "Record your voice, let AI process it, then review the extracted data before confirming."}
              </p>
            </div>

            <div className="workspace-status">
              <span className="workspace-status-dot" />

              <span>
                {isVietnamese
                  ? "Hệ thống sẵn sàng"
                  : "System ready"}
              </span>
            </div>
          </section>

          {isDevMode && (
            <section className="dev-test-panel">
              <div className="dev-test-info">
                <span className="dev-test-icon">
                  🧪
                </span>

                <div>
                  <strong>
                    DEV Test Mode
                  </strong>

                  <span>
                    {isVietnamese
                      ? "Kiểm thử frontend không cần AI Service."
                      : "Test the frontend without the AI Service."}
                  </span>
                </div>
              </div>

              <div className="dev-test-actions">
                <button
                  type="button"
                  className="dev-test-btn valid"
                  onClick={
                    handleLoadValidTest
                  }
                >
                  ✅{" "}
                  {isVietnamese
                    ? "Hợp lệ"
                    : "Valid"}
                </button>

                <button
                  type="button"
                  className="dev-test-btn warning"
                  onClick={
                    handleLoadWarningTest
                  }
                >
                  ⚠️{" "}
                  {isVietnamese
                    ? "Cảnh báo"
                    : "Warning"}
                </button>

                <button
                  type="button"
                  className="dev-test-btn error"
                  onClick={
                    handleLoadErrorTest
                  }
                >
                  ❌{" "}
                  {isVietnamese
                    ? "Dữ liệu lỗi"
                    : "Error"}
                </button>

                <button
                  type="button"
                  className="dev-test-btn reset"
                  onClick={
                    handleResetDevTest
                  }
                >
                  ↺ Reset
                </button>
              </div>
            </section>
          )}

          <section className="workflow-card">
            <WorkflowStepper
              currentStep={
                currentStep
              }
              text={t}
            />
          </section>

          <section className="voice-workspace-grid">
            <div className="voice-primary-column">
              <div className="workspace-card record-card">
                <RecordButton
                  audioUrl={
                    audioUrl
                  }
                  setAudioUrl={
                    setAudioUrl
                  }
                  setAudioBlob={
                    setAudioBlob
                  }
                  setTranscript={
                    setTranscript
                  }
                  setAiData={
                    setAiData
                  }
                  setMessage={
                    setMessage
                  }
                  isConfirmed={
                    isConfirmed
                  }
                  text={t}
                />
              </div>

              <div className="workspace-card">
                <TranscriptBox
                  transcript={
                    transcript
                  }
                  onTranscriptChange={
                    setTranscript
                  }
                  isConfirmed={
                    isConfirmed
                  }
                  text={t}
                />
              </div>
            </div>

            <div className="voice-secondary-column">
              <div className="workspace-card ai-data-card">
                <AIForm
                  aiData={
                    aiData
                  }
                  onAiDataChange={
                    setAiData
                  }
                  isConfirmed={
                    isConfirmed
                  }
                  text={t}
                  language={
                    language
                  }
                  validation={
                    validation
                  }
                  showValidation={
                    hasAttemptedSubmit
                  }
                />

                <ActionButtons
                  hasAudio={
                    Boolean(audioBlob)
                  }
                  hasResult={
                    Boolean(
                      transcript.trim()
                    )
                  }
                  isUploading={
                    isUploading
                  }
                  isConfirmed={
                    isConfirmed
                  }
                  onRetry={
                    handleDelete
                  }
                  onUpload={
                    handleUpload
                  }
                  onConfirm={
                    handleConfirm
                  }
                  onCreateNew={
                    handleCreateNew
                  }
                  text={t}
                />
              </div>
            </div>
          </section>

          {messageText && (
            <div
              className={`app-toast ${messageType}`}
              role="status"
            >
              <span className="app-toast-icon">
                {messageType ===
                "error"
                  ? "⚠️"
                  : "✅"}
              </span>

              <span>
                {messageText}
              </span>
            </div>
          )}
        </div>
      </main>

      <AIAssistant
        language={language}
      />
    </div>
  );
}

export default VoiceLog;