import { useRef, useState } from "react";

function RecordButton() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleRecord = async () => {
  if (!isRecording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;

      // Reset mảng lưu dữ liệu âm thanh
      audioChunksRef.current = [];

      // Khi có dữ liệu âm thanh thì lưu lại
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
            type: "audio/webm",
        });

        const url = URL.createObjectURL(audioBlob);

        setAudioUrl(url);

        console.log(audioBlob);
      };

      mediaRecorder.start();

      console.log(mediaRecorder);
 
      console.log(stream);

      setIsRecording(true);
    } catch (error) {
      alert("Không thể truy cập microphone!");
      console.error(error);
    }
  } else {
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  }
};

  return (
    <div className="record-section">
      <button
        className={`record-btn ${isRecording ? "recording" : ""}`}
        onClick={handleRecord}
      >
        {isRecording ? "⏹" : "🎤"}
      </button>

      <p>
        {isRecording
          ? "Đang ghi âm..."
          : "Nhấn để ghi âm"}
      </p>

      {audioUrl && (
        <div style={{ marginTop: "20px" }}>
            <audio controls src={audioUrl}></audio>
        </div>
      )}
    </div>
  );
}

export default RecordButton;