import { useRef, useState } from "react";
import AudioPlayer from "./AudioPlayer";

const EMPTY_AI_DATA = {
  lot: "",
  work: "",
  material: "",
  quantity: "",
  unit: "",
  time: "",
};

function RecordButton({
  audioUrl,
  setAudioUrl,
  setAudioBlob,
  setTranscript,
  setAiData,
  setMessage,
  isConfirmed = false,
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordTime, setRecordTime] = useState(0);
  const [recordStatus, setRecordStatus] = useState("Nhấn để ghi âm");

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const stopMicrophone = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current
        .getTracks()
        .forEach((track) => track.stop());

      mediaStreamRef.current = null;
    }
  };

  const getAudioConstraints = () => {
    const supported =
      navigator.mediaDevices.getSupportedConstraints?.() || {};

    const audioConstraints = {};

    if (supported.echoCancellation) {
      audioConstraints.echoCancellation = true;
    }

    if (supported.noiseSuppression) {
      audioConstraints.noiseSuppression = true;
    }

    if (supported.autoGainControl) {
      audioConstraints.autoGainControl = true;
    }

    if (supported.channelCount) {
      audioConstraints.channelCount = 1;
    }

    return Object.keys(audioConstraints).length > 0
      ? audioConstraints
      : true;
  };

  const startRecording = async () => {
    if (isConfirmed) {
      setMessage(
        "Nhật ký đã được xác nhận. Hãy chọn Tạo nhật ký mới để tiếp tục."
      );
      return;
    }

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Trình duyệt không hỗ trợ chức năng ghi âm."
        );
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: getAudioConstraints(),
      });

      mediaStreamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }

      setAudioUrl(null);
      setAudioBlob(null);
      setTranscript("");
      setAiData(EMPTY_AI_DATA);
      setMessage("");

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error("MediaRecorder error:", event.error);

        stopTimer();
        stopMicrophone();

        setIsRecording(false);
        setRecordStatus("Ghi âm bị lỗi");
        setMessage(
          "Không thể tiếp tục ghi âm. Vui lòng thử lại."
        );
      };

      mediaRecorder.onstop = () => {
        const mimeType =
          mediaRecorder.mimeType || "audio/webm;codecs=opus";

        const recordedBlob = new Blob(
          audioChunksRef.current,
          {
            type: mimeType,
          }
        );

        if (recordedBlob.size === 0) {
          setRecordStatus("Không thu được âm thanh");
          setMessage(
            "Bản ghi không có dữ liệu. Vui lòng thử lại và nói gần microphone hơn."
          );

          stopMicrophone();
          return;
        }

        const recordedUrl =
          URL.createObjectURL(recordedBlob);

        setAudioBlob(recordedBlob);
        setAudioUrl(recordedUrl);
        setRecordStatus("Đã ghi âm");
        setMessage("Bản ghi đã sẵn sàng để gửi AI.");

        stopMicrophone();

        console.log("Recorded audio:", recordedBlob);
      };

      mediaRecorder.start();

      setRecordTime(0);
      setRecordStatus("Đang ghi âm...");
      setIsRecording(true);

      timerRef.current = setInterval(() => {
        setRecordTime(
          (previousTime) => previousTime + 1
        );
      }, 1000);
    } catch (error) {
      console.error("Microphone error:", error);

      stopTimer();
      stopMicrophone();

      setIsRecording(false);

      if (error.name === "NotAllowedError") {
        setRecordStatus("Chưa được cấp quyền microphone");
        setMessage(
          "Vui lòng cho phép trình duyệt sử dụng microphone."
        );
      } else if (error.name === "NotFoundError") {
        setRecordStatus("Không tìm thấy microphone");
        setMessage(
          "Thiết bị không có microphone hoặc microphone đang không khả dụng."
        );
      } else {
        setRecordStatus("Không thể truy cập microphone");
        setMessage(
          error.message ||
            "Không thể sử dụng microphone. Vui lòng thử lại."
        );
      }
    }
  };

  const stopRecording = () => {
    const mediaRecorder = mediaRecorderRef.current;

    if (
      !mediaRecorder ||
      mediaRecorder.state !== "recording"
    ) {
      return;
    }

    stopTimer();
    mediaRecorder.stop();
    setIsRecording(false);
  };

  const handleRecord = () => {
    if (isConfirmed) return;

    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTime = (seconds) => {
    const minutes = String(
      Math.floor(seconds / 60)
    ).padStart(2, "0");

    const remainingSeconds = String(
      seconds % 60
    ).padStart(2, "0");

    return `${minutes}:${remainingSeconds}`;
  };

  const displayedStatus = isConfirmed
    ? "Nhật ký đã được xác nhận"
    : recordStatus;

  return (
    <div className="record-section">
      <button
        type="button"
        className={`record-btn ${
          isRecording ? "recording" : ""
        }`}
        onClick={handleRecord}
        disabled={isConfirmed}
        aria-label={
          isConfirmed
            ? "Nhật ký đã được xác nhận"
            : isRecording
              ? "Dừng ghi âm"
              : "Bắt đầu ghi âm"
        }
        aria-pressed={isRecording}
      >
        {isRecording ? "⏹" : "🎤"}
      </button>

      <div className="record-status">
        <span>{displayedStatus}</span>

        {isRecording && (
          <strong>{formatTime(recordTime)}</strong>
        )}
      </div>

      <AudioPlayer audioUrl={audioUrl} />
    </div>
  );
}

export default RecordButton;