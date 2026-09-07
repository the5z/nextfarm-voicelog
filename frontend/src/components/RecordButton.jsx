import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  chooseSupportedMimeType,
  createSilenceDetector,
  getRecordingErrorMessage,
  requestMicrophoneStream,
  stopMediaStream,
} from "../utils/audioRecording";

/*
 * Auto-stop tuning. These mirror how a chatbot voice mic behaves: tap once
 * to start, keep listening while you talk, and stop on their own shortly
 * after you go quiet. MAX_RECORDING_MS is a hard safety net in case VAD is
 * unavailable (unsupported browser) or the mic picks up continuous noise.
 */
const SILENCE_STOP_MS = 1400;
const MIN_SPEECH_MS = 250;
const MAX_RECORDING_MS = 120000;

const EMPTY_AI_DATA = {
  lot: "",
  work: "",
  material: "",
  quantity: "",
  unit: "",
  time: "",
};

function formatDuration(totalSeconds) {
  const safeSeconds = Math.max(
    0,
    Number(totalSeconds) || 0
  );

  const minutes = Math.floor(
    safeSeconds / 60
  );

  const seconds =
    safeSeconds % 60;

  return `${String(minutes).padStart(
    2,
    "0"
  )}:${String(seconds).padStart(
    2,
    "0"
  )}`;
}

function RecordButton({
  audioUrl,
  setAudioUrl,
  setAudioBlob,
  setTranscript,
  setAiData,
  setMessage,
  isConfirmed = false,
  text,
  language = "vi",
}) {
  const isVietnamese =
    language === "vi";

  const [
    isRecording,
    setIsRecording,
  ] = useState(false);

  /*
   * Visual state for immediate push-to-talk feedback.
   * This is intentionally separate from MediaRecorder state:
   * pointerdown should update the UI instantly, even while the stream
   * is still being prepared asynchronously.
   */
  const [
    isHolding,
    setIsHolding,
  ] = useState(false);

  const [
    elapsedSeconds,
    setElapsedSeconds,
  ] = useState(0);

  const [
    isPreparingPermission,
    setIsPreparingPermission,
  ] = useState(false);

  const elapsedSecondsRef =
    useRef(0);

  const recorderRef =
    useRef(null);

  const streamRef =
    useRef(null);

  const chunksRef =
    useRef([]);

  const timerRef =
    useRef(null);

  const recordingStartedAtRef =
    useRef(null);

  const ownedAudioUrlRef =
    useRef(null);

  const mountedRef =
    useRef(true);

  /*
   * `microphoneReadyRef` means the browser has already granted microphone
   * permission during this page session, or Permissions API reported granted.
   */
  const microphoneReadyRef =
    useRef(false);

  const permissionInFlightRef =
    useRef(false);

  /*
   * Push-to-talk state.
   *
   * We intentionally do NOT stop based on pointercancel/lostPointerCapture.
   * Some browsers can emit those events while microphone UI changes.
   *
   * `releaseRequestedRef` handles the edge case where the user releases
   * before getUserMedia() / MediaRecorder finishes starting.
   */
  const pressActiveRef =
    useRef(false);

  const releaseRequestedRef =
    useRef(false);

  const startingRecordingRef =
    useRef(false);

  const keyboardPressRef =
    useRef(false);

  /*
   * Voice Activity Detection: watches the live stream and auto-stops the
   * recording once the user goes quiet, so the mic behaves like tap-to-talk
   * instead of press-and-hold.
   */
  const silenceDetectorRef =
    useRef(null);

  const maxDurationTimerRef =
    useRef(null);

  const clearMaxDurationTimer =
    () => {
      if (
        maxDurationTimerRef.current
      ) {
        window.clearTimeout(
          maxDurationTimerRef.current
        );

        maxDurationTimerRef.current =
          null;
      }
    };

  const destroySilenceDetector =
    () => {
      silenceDetectorRef.current?.destroy();

      silenceDetectorRef.current =
        null;
    };

  const showMessage = (
    type,
    messageText
  ) => {
    setMessage?.({
      type,
      text: messageText,
    });
  };

  const clearTimer = () => {
    if (!timerRef.current) {
      return;
    }

    window.clearInterval(
      timerRef.current
    );

    timerRef.current = null;
  };

  const cleanupStream = () => {
    destroySilenceDetector();
    clearMaxDurationTimer();

    stopMediaStream(
      streamRef.current
    );

    streamRef.current = null;
  };

  const releaseRecorder = () => {
    recorderRef.current = null;
    chunksRef.current = [];
  };

  const revokeOwnedAudioUrl =
    () => {
      const url =
        ownedAudioUrlRef.current;

      if (!url) {
        return;
      }

      try {
        URL.revokeObjectURL(
          url
        );
      } catch {
        // Ignore cleanup error.
      }

      ownedAudioUrlRef.current =
        null;
    };

  const resetResultForNewRecording =
    () => {
      revokeOwnedAudioUrl();

      setAudioUrl?.(null);
      setAudioBlob?.(null);
      setTranscript?.("");

      setAiData?.({
        ...EMPTY_AI_DATA,
      });
    };

  const resetRecordingUi = () => {
    clearTimer();

    elapsedSecondsRef.current =
      0;

    recordingStartedAtRef.current =
      null;

    if (mountedRef.current) {
      setElapsedSeconds(0);
      setIsRecording(false);
      setIsHolding(false);
    }
  };

  const finishRecording = (
    recorder,
    recordedSeconds
  ) => {
    const chunks =
      chunksRef.current.filter(
        (chunk) =>
          chunk &&
          chunk.size > 0
      );

    resetRecordingUi();
    cleanupStream();

    startingRecordingRef.current =
      false;

    pressActiveRef.current =
      false;

    releaseRequestedRef.current =
      false;

    if (
      chunks.length === 0
    ) {
      releaseRecorder();

      showMessage(
        "error",
        isVietnamese
          ? "Không nhận được dữ liệu âm thanh. Hãy nhấn giữ micro lâu hơn một chút rồi thử lại."
          : "No audio data was captured. Hold the microphone a little longer and try again."
      );

      return;
    }

    const mimeType =
      recorder?.mimeType ||
      chunks[0]?.type ||
      "audio/webm";

    const blob =
      new Blob(chunks, {
        type: mimeType,
      });

    const url =
      URL.createObjectURL(
        blob
      );

    ownedAudioUrlRef.current =
      url;

    setAudioBlob?.(blob);
    setAudioUrl?.(url);

    releaseRecorder();

    showMessage(
      "success",
      isVietnamese
        ? `✅ Đã ghi âm ${formatDuration(
            recordedSeconds
          )}. Bạn có thể nghe lại hoặc gửi bản ghi cho AI.`
        : `✅ Recorded ${formatDuration(
            recordedSeconds
          )}. You can play it back or send it to AI.`
    );
  };

  const stopRecording = () => {
    const recorder =
      recorderRef.current;

    /*
     * If MediaRecorder is still starting, remember that the user released.
     * startRecording() will stop immediately after recorder.start().
     */
    if (
      !recorder ||
      recorder.state ===
        "inactive"
    ) {
      if (
        startingRecordingRef.current
      ) {
        releaseRequestedRef.current =
          true;

        return;
      }

      resetRecordingUi();
      cleanupStream();

      return;
    }

    try {
      if (
        typeof recorder.requestData ===
        "function"
      ) {
        try {
          recorder.requestData();
        } catch {
          // requestData can fail if recorder is already stopping.
        }
      }

      recorder.stop();
    } catch (error) {
      console.error(
        "Stop recording error:",
        error
      );

      resetRecordingUi();
      cleanupStream();
      releaseRecorder();

      startingRecordingRef.current =
        false;

      showMessage(
        "error",
        isVietnamese
          ? "Không thể kết thúc bản ghi đúng cách. Hãy thử ghi lại."
          : "The recording could not be stopped correctly. Please record again."
      );
    }
  };

  /*
   * First interaction only:
   * ask for permission, immediately close the temporary stream,
   * and return to the idle UI.
   */
  const prepareMicrophonePermission =
    async () => {
      if (
        permissionInFlightRef.current ||
        microphoneReadyRef.current ||
        isConfirmed
      ) {
        return;
      }

      permissionInFlightRef.current =
        true;

      if (mountedRef.current) {
        setIsPreparingPermission(
          true
        );
      }

      try {
        if (
          typeof window.MediaRecorder ===
          "undefined"
        ) {
          throw new Error(
            "MEDIA_RECORDER_UNAVAILABLE"
          );
        }

        const permissionStream =
          await requestMicrophoneStream();

        stopMediaStream(
          permissionStream
        );

        microphoneReadyRef.current =
          true;

        showMessage(
          "success",
          isVietnamese
            ? "✅ Microphone đã sẵn sàng. Từ lần tiếp theo, nhấn giữ để ghi và thả để dừng."
            : "✅ Microphone is ready. From the next press, hold to record and release to stop."
        );
      } catch (error) {
        microphoneReadyRef.current =
          false;

        showMessage(
          "error",
          getRecordingErrorMessage(
            error,
            language
          )
        );
      } finally {
        permissionInFlightRef.current =
          false;

        pressActiveRef.current =
          false;

        releaseRequestedRef.current =
          false;

        if (mountedRef.current) {
          setIsPreparingPermission(
            false
          );
          setIsHolding(false);
        }
      }
    };

  const startRecording =
    async () => {
      if (
        startingRecordingRef.current ||
        recorderRef.current ||
        isConfirmed
      ) {
        return;
      }

      startingRecordingRef.current =
        true;

      releaseRequestedRef.current =
        false;

      /*
       * UX requirement:
       * change to "Đang ghi âm" immediately on press.
       * Permission was already granted, so getUserMedia should usually resolve
       * very quickly; if it fails we roll the UI back.
       */
      if (mountedRef.current) {
        setIsHolding(true);
        setIsRecording(true);
        setElapsedSeconds(0);
      }

      elapsedSecondsRef.current =
        0;

      try {
        if (
          typeof window.MediaRecorder ===
          "undefined"
        ) {
          throw new Error(
            "MEDIA_RECORDER_UNAVAILABLE"
          );
        }

        const stream =
          await requestMicrophoneStream();

        streamRef.current =
          stream;

        const mimeType =
          chooseSupportedMimeType();

        let recorder;

        try {
          recorder =
            mimeType
              ? new MediaRecorder(
                  stream,
                  {
                    mimeType,
                  }
                )
              : new MediaRecorder(
                  stream
                );
        } catch {
          recorder =
            new MediaRecorder(
              stream
            );
        }

        recorderRef.current =
          recorder;

        chunksRef.current = [];

        recorder.ondataavailable =
          (event) => {
            if (
              event.data &&
              event.data.size > 0
            ) {
              chunksRef.current.push(
                event.data
              );
            }
          };

        recorder.onerror =
          (event) => {
            console.error(
              "MediaRecorder error:",
              event?.error ||
                event
            );

            showMessage(
              "error",
              isVietnamese
                ? "Đã xảy ra lỗi trong lúc ghi âm. Hãy thử lại."
                : "An error occurred while recording. Please try again."
            );
          };

        recorder.onstop = () => {
          const recordedSeconds =
            recordingStartedAtRef.current
              ? Math.max(
                  0,
                  Math.floor(
                    (Date.now() -
                      recordingStartedAtRef.current) /
                      1000
                  )
                )
              : elapsedSecondsRef.current;

          finishRecording(
            recorder,
            recordedSeconds
          );
        };

        resetResultForNewRecording();

        recorder.start(250);

        recordingStartedAtRef.current =
          Date.now();

        elapsedSecondsRef.current =
          0;

        if (mountedRef.current) {
          setElapsedSeconds(0);
          setIsHolding(true);
          setIsRecording(true);
        }

        clearTimer();

        timerRef.current =
          window.setInterval(
            () => {
              if (
                !recordingStartedAtRef.current
              ) {
                return;
              }

              const nextSeconds =
                Math.max(
                  0,
                  Math.floor(
                    (Date.now() -
                      recordingStartedAtRef.current) /
                      1000
                  )
                );

              elapsedSecondsRef.current =
                nextSeconds;

              if (mountedRef.current) {
                setElapsedSeconds(
                  nextSeconds
                );
              }
            },
            200
          );

        startingRecordingRef.current =
          false;

        showMessage(
          "success",
          isVietnamese
            ? "🎙️ Đang nghe... Cứ nói bình thường, mic sẽ tự tắt khi bạn dừng nói."
            : "🎙️ Listening... Speak normally, the mic will stop automatically when you're done."
        );

        /*
         * Auto-stop when the user goes quiet, just like a chatbot voice mic.
         * Falls back gracefully (no auto-stop, manual tap only) if the Web
         * Audio API isn't available on this browser.
         */
        destroySilenceDetector();

        silenceDetectorRef.current =
          createSilenceDetector({
            stream,
            silenceDurationMs:
              SILENCE_STOP_MS,
            minSpeechMs:
              MIN_SPEECH_MS,
            onSilenceTimeout: () => {
              endPress();
            },
          });

        clearMaxDurationTimer();

        maxDurationTimerRef.current =
          window.setTimeout(() => {
            endPress();
          }, MAX_RECORDING_MS);

        /*
         * User tapped "stop" again while the async start was still in
         * progress. Stop only now, after MediaRecorder is genuinely active.
         */
        if (
          releaseRequestedRef.current ||
          !pressActiveRef.current
        ) {
          stopRecording();
        }
      } catch (error) {
        console.error(
          "Start recording error:",
          error
        );

        startingRecordingRef.current =
          false;

        pressActiveRef.current =
          false;

        releaseRequestedRef.current =
          false;

        resetRecordingUi();

        if (mountedRef.current) {
          setIsHolding(false);
        }

        cleanupStream();
        releaseRecorder();

        showMessage(
          "error",
          getRecordingErrorMessage(
            error,
            language
          )
        );
      }
    };

  const beginPress = () => {
    if (
      isConfirmed ||
      permissionInFlightRef.current ||
      startingRecordingRef.current ||
      recorderRef.current ||
      pressActiveRef.current
    ) {
      return;
    }

    pressActiveRef.current =
      true;

    if (
      !microphoneReadyRef.current
    ) {
      void prepareMicrophonePermission();

      return;
    }

    /*
     * Immediate UI feedback. This does not wait for getUserMedia().
     */
    if (mountedRef.current) {
      setIsHolding(true);
    }

    void startRecording();
  };

  const endPress = () => {
    /*
     * Permission stage is intentionally not a recording session.
     */
    if (
      permissionInFlightRef.current
    ) {
      return;
    }

    if (
      !pressActiveRef.current &&
      !startingRecordingRef.current &&
      !recorderRef.current
    ) {
      return;
    }

    pressActiveRef.current =
      false;

    if (mountedRef.current) {
      setIsHolding(false);

      /*
       * The physical button has been released, so the visual recording state
       * should end immediately. MediaRecorder.onstop will still finalize the
       * Blob and call resetRecordingUi() once data is available.
       */
      if (
        recorderRef.current &&
        recorderRef.current.state !==
          "inactive"
      ) {
        setIsRecording(false);
      }
    }

    if (
      startingRecordingRef.current &&
      !recorderRef.current
    ) {
      releaseRequestedRef.current =
        true;

      return;
    }

    stopRecording();
  };

  /*
   * Tap-to-talk toggle (matches the chatbot mic UX): one tap/click/Enter
   * starts listening, a second tap can stop it manually, and otherwise it
   * stops on its own once the silence detector fires. No press-and-hold is
   * required.
   */
  const isSessionActive = () =>
    pressActiveRef.current ||
    startingRecordingRef.current ||
    Boolean(recorderRef.current);

  const handleActivate =
    (event) => {
      if (event?.button && event.button !== 0) {
        return;
      }

      event?.preventDefault?.();

      if (isConfirmed) {
        return;
      }

      if (isSessionActive()) {
        endPress();

        return;
      }

      beginPress();
    };

  const handleKeyDown =
    (event) => {
      if (
        event.key !== " " &&
        event.key !== "Enter"
      ) {
        return;
      }

      event.preventDefault();

      if (
        event.repeat ||
        keyboardPressRef.current
      ) {
        return;
      }

      keyboardPressRef.current =
        true;

      handleActivate(event);
    };

  const handleKeyUp =
    (event) => {
      if (
        event.key !== " " &&
        event.key !== "Enter"
      ) {
        return;
      }

      event.preventDefault();

      keyboardPressRef.current =
        false;
    };

  /*
   * Detect a permission already granted by Chrome/Edge.
   * If unsupported (Safari etc.), the first press simply performs the
   * permission-preparation step.
   */
  useEffect(() => {
    let permissionStatus;

    const detectExistingPermission =
      async () => {
        try {
          if (
            !navigator.permissions
              ?.query
          ) {
            return;
          }

          permissionStatus =
            await navigator.permissions.query(
              {
                name: "microphone",
              }
            );

          microphoneReadyRef.current =
            permissionStatus.state ===
            "granted";

          permissionStatus.onchange =
            () => {
              microphoneReadyRef.current =
                permissionStatus.state ===
                "granted";
            };
        } catch {
          // Browser does not expose microphone permission through Permissions API.
        }
      };

    void detectExistingPermission();

    return () => {
      if (permissionStatus) {
        permissionStatus.onchange =
          null;
      }
    };
  }, []);

  useEffect(() => {
    /*
     * IMPORTANT:
     * React StrictMode in development runs effect setup -> cleanup -> setup
     * once to detect unsafe side effects. The old implementation only set
     * mountedRef=false in cleanup, so it stayed false afterwards.
     *
     * That blocked:
     * - timer UI updates
     * - recording UI reset after stop
     *
     * Always restore the ref in every effect setup.
     */
    mountedRef.current =
      true;

    return () => {
      mountedRef.current =
        false;

      pressActiveRef.current =
        false;

      releaseRequestedRef.current =
        false;

      startingRecordingRef.current =
        false;

      keyboardPressRef.current =
        false;

      clearTimer();

      recordingStartedAtRef.current =
        null;

      const recorder =
        recorderRef.current;

      if (
        recorder &&
        recorder.state !==
          "inactive"
      ) {
        try {
          recorder.stop();
        } catch {
          // Ignore cleanup error.
        }
      }

      cleanupStream();
      revokeOwnedAudioUrl();
    };
  }, []);

  const buttonLabel =
    isConfirmed
      ? isVietnamese
        ? "Nhật ký đã được xác nhận"
        : "Log confirmed"
      : isPreparingPermission
        ? isVietnamese
          ? "Đang cấp quyền microphone..."
          : "Preparing microphone permission..."
        : isHolding || isRecording
          ? isVietnamese
            ? "Đang nghe · nhấn để dừng"
            : "Listening · tap to stop"
          : isVietnamese
            ? "Nhấn để nói"
            : "Tap to talk";

  return (
    <div className="record-section">
      <div className="record-control-wrap">
        <button
          type="button"
          className={`record-btn ${
            isHolding || isRecording
              ? "recording"
              : ""
          } ${
            isPreparingPermission
              ? "preparing"
              : ""
          }`}
          onClick={
            handleActivate
          }
          onKeyDown={
            handleKeyDown
          }
          onKeyUp={
            handleKeyUp
          }
          onContextMenu={(event) =>
            event.preventDefault()
          }
          disabled={
            isConfirmed
          }
          aria-pressed={
            isHolding || isRecording
          }
          aria-busy={
            isPreparingPermission
          }
          aria-label={
            buttonLabel
          }
          title={
            buttonLabel
          }
        >
          <span
            className="record-btn-icon"
            aria-hidden="true"
          >
            {isPreparingPermission
              ? "…"
              : "🎙️"}
          </span>
        </button>

        {(isHolding || isRecording) && (
          <span
            className="record-live-dot"
            aria-hidden="true"
          />
        )}
      </div>

      <div
        className={`record-status ${
          isHolding || isRecording
            ? "recording"
            : ""
        }`}
        aria-live="polite"
      >
        {isHolding || isRecording ? (
          <>
            <span className="record-status-main">
              {isVietnamese
                ? "Đang ghi âm"
                : "Recording"}
            </span>

            <strong>
              {formatDuration(
                elapsedSeconds
              )}
            </strong>

            <span className="record-status-hint">
              {isVietnamese
                ? "Dừng nói sẽ tự tắt · hoặc nhấn để dừng"
                : "Stops automatically when you go quiet · or tap to stop"}
            </span>
          </>
        ) : (
          <span className="record-status-main">
            {buttonLabel}
          </span>
        )}
      </div>

      {audioUrl && (
        <div className="audio-player audio-player-compact">
          <div className="audio-player-header audio-player-header-compact">
            <h3>
              {isVietnamese
                ? "Bản ghi vừa tạo"
                : "Latest recording"}
            </h3>

            <span className="audio-ready-badge">
              <span aria-hidden="true">✓</span>
              {isVietnamese
                ? "Sẵn sàng"
                : "Ready"}
            </span>
          </div>

          <audio
            controls
            playsInline
            preload="metadata"
            src={audioUrl}
          >
            {text?.audio
              ?.unsupported ||
              (isVietnamese
                ? "Trình duyệt không hỗ trợ phát âm thanh."
                : "Your browser does not support audio playback.")}
          </audio>
        </div>
      )}
    </div>
  );
}

export default RecordButton;