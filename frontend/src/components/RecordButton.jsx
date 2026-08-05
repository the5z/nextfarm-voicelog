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

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
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

      mediaRecorder.onstop = () => {
        const mimeType =
          mediaRecorder.mimeType || "audio/webm;codecs=opus";

        const recordedBlob = new Blob(audioChunksRef.current, {
          type: mimeType,
        });

        const recordedUrl = URL.createObjectURL(recordedBlob);

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
        setRecordTime((previousTime) => previousTime + 1);
      }, 1000);
    } catch (error) {
      console.error("Microphone error:", error);
      setRecordStatus("Không thể truy cập microphone");
      setMessage("Vui lòng cấp quyền sử dụng microphone.");
    }
  };

  const stopRecording = () => {
    const mediaRecorder = mediaRecorderRef.current;

    if (!mediaRecorder || mediaRecorder.state !== "recording") return;

    stopTimer();
    mediaRecorder.stop();
    setIsRecording(false);
  };

  const handleRecord = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTime = (seconds) => {
    const minutes = String(Math.floor(seconds / 60)).padStart(2, "0");
    const remainingSeconds = String(seconds % 60).padStart(2, "0");

    return `${minutes}:${remainingSeconds}`;
  };

  return (
    <div className="record-section">
      <button
        type="button"
        className={`record-btn ${isRecording ? "recording" : ""}`}
        onClick={handleRecord}
        aria-label={isRecording ? "Dừng ghi âm" : "Bắt đầu ghi âm"}
      >
        {isRecording ? "⏹" : "🎤"}
      </button>

      <div className="record-status">
        <span>{recordStatus}</span>

        {isRecording && (
          <strong>{formatTime(recordTime)}</strong>
        )}
      </div>

      <AudioPlayer audioUrl={audioUrl} />
    </div>
  );
}

export default RecordButton;