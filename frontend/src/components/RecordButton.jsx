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
  text,
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordTime, setRecordTime] = useState(0);

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

  const getCurrentStatus = () => {
    if (isConfirmed) {
      return text.record.confirmed;
    }

    if (isRecording) {
      return text.record.recording;
    }

    if (audioUrl) {
      return text.record.recorded;
    }

    return text.record.ready;
  };

  const startRecording = async () => {
    if (isConfirmed) {
      setMessage({
        type: "error",
        text: text.record.confirmedMessage,
      });

      return;
    }

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          text.record.browserUnsupported
        );
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: getAudioConstraints(),
        });

      mediaStreamRef.current = stream;

      const mediaRecorder =
        new MediaRecorder(stream);

      mediaRecorderRef.current =
        mediaRecorder;

      audioChunksRef.current = [];

      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }

      setAudioUrl(null);
      setAudioBlob(null);
      setTranscript("");
      setAiData(EMPTY_AI_DATA);
      setMessage(null);

      mediaRecorder.ondataavailable = (
        event
      ) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(
            event.data
          );
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error(
          "MediaRecorder error:",
          event.error
        );

        stopTimer();
        stopMicrophone();

        setIsRecording(false);

        setMessage({
          type: "error",
          text:
            text.record
              .recordingErrorMessage,
        });
      };

      mediaRecorder.onstop = () => {
        const mimeType =
          mediaRecorder.mimeType ||
          "audio/webm;codecs=opus";

        const recordedBlob = new Blob(
          audioChunksRef.current,
          {
            type: mimeType,
          }
        );

        if (recordedBlob.size === 0) {
          setMessage({
            type: "error",
            text:
              text.record
                .emptyAudioMessage,
          });

          stopMicrophone();
          return;
        }

        const recordedUrl =
          URL.createObjectURL(
            recordedBlob
          );

        setAudioBlob(recordedBlob);
        setAudioUrl(recordedUrl);

        setMessage({
          type: "success",
          text: text.record.audioReady,
        });

        stopMicrophone();

        console.log(
          "Recorded audio:",
          recordedBlob
        );
      };

      mediaRecorder.start();

      setRecordTime(0);
      setIsRecording(true);

      timerRef.current = setInterval(
        () => {
          setRecordTime(
            (previousTime) =>
              previousTime + 1
          );
        },
        1000
      );
    } catch (error) {
      console.error(
        "Microphone error:",
        error
      );

      stopTimer();
      stopMicrophone();

      setIsRecording(false);

      if (
        error.name === "NotAllowedError"
      ) {
        setMessage({
          type: "error",
          text:
            text.record
              .microphoneDeniedMessage,
        });
      } else if (
        error.name === "NotFoundError"
      ) {
        setMessage({
          type: "error",
          text:
            text.record
              .microphoneNotFoundMessage,
        });
      } else {
        setMessage({
          type: "error",
          text:
            error.message ||
            text.record
              .microphoneUnavailableMessage,
        });
      }
    }
  };

  const stopRecording = () => {
    const mediaRecorder =
      mediaRecorderRef.current;

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
    if (isConfirmed) {
      return;
    }

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

  return (
    <div className="record-section">
      <button
        type="button"
        className={`record-btn ${
          isRecording
            ? "recording"
            : ""
        }`}
        onClick={handleRecord}
        disabled={isConfirmed}
        aria-label={
          isConfirmed
            ? text.record.confirmedLabel
            : isRecording
              ? text.record.stopLabel
              : text.record.startLabel
        }
        aria-pressed={isRecording}
      >
        {isRecording ? "⏹" : "🎤"}
      </button>

      <div className="record-status">
        <span>
          {getCurrentStatus()}
        </span>

        {isRecording && (
          <strong>
            {formatTime(recordTime)}
          </strong>
        )}
      </div>

      <AudioPlayer
        audioUrl={audioUrl}
        text={text}
      />
    </div>
  );
}

export default RecordButton;