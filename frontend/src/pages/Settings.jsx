import {
  useEffect,
  useRef,
  useState,
} from "react";

function Settings({
  settings,
  onSettingChange,
}) {
  const language =
    settings.language;

  const isVietnamese =
    language === "vi";

  /* =========================================================
     MICROPHONE TEST STATE
  ========================================================= */

  const [
    micTesting,
    setMicTesting,
  ] = useState(false);

  const [
    micStatus,
    setMicStatus,
  ] = useState("idle");

  const [
    micDeviceName,
    setMicDeviceName,
  ] = useState("");

  const [
    micLevel,
    setMicLevel,
  ] = useState(0);

  const [
    micPeak,
    setMicPeak,
  ] = useState(0);

  const [
    micTestTime,
    setMicTestTime,
  ] = useState(0);

  const [
    micMessage,
    setMicMessage,
  ] = useState("");

  const streamRef =
    useRef(null);

  const audioContextRef =
    useRef(null);

  const analyserRef =
    useRef(null);

  const animationFrameRef =
    useRef(null);

  const timerRef =
    useRef(null);

  /* =========================================================
     STORAGE
  ========================================================= */

  const getLocalStorageSize =
    () => {
      try {
        let total = 0;

        for (
          let index = 0;
          index <
          localStorage.length;
          index += 1
        ) {
          const key =
            localStorage.key(
              index
            );

          const value =
            localStorage.getItem(
              key
            );

          total +=
            String(
              key || ""
            ).length +
            String(
              value || ""
            ).length;
        }

        return `${(
          total / 1024
        ).toFixed(2)} KB`;
      } catch {
        return "—";
      }
    };

  const clearChatHistory =
    () => {
      const confirmed =
        window.confirm(
          isVietnamese
            ? "Bạn có chắc muốn xóa toàn bộ lịch sử trò chuyện AI trên thiết bị này?"
            : "Are you sure you want to delete all AI chat history on this device?"
        );

      if (!confirmed) {
        return;
      }

      localStorage.removeItem(
        "nextfarm-ai-conversations"
      );

      localStorage.removeItem(
        "nextfarm-ai-active-chat"
      );

      localStorage.removeItem(
        "nextfarm-ai-chat"
      );

      window.alert(
        isVietnamese
          ? "Đã xóa lịch sử AI."
          : "AI history deleted."
      );
    };

  const clearLocalLogs =
    () => {
      const confirmed =
        window.confirm(
          isVietnamese
            ? "Bạn có chắc muốn xóa nhật ký đang lưu trên trình duyệt?"
            : "Are you sure you want to delete locally stored logs?"
        );

      if (!confirmed) {
        return;
      }

      localStorage.removeItem(
        "nextfarm-farming-logs"
      );

      window.alert(
        isVietnamese
          ? "Đã xóa dữ liệu nhật ký cục bộ. Tải lại trang để cập nhật."
          : "Local logs deleted. Reload the page to update."
      );
    };

  /* =========================================================
     MICROPHONE HELPERS
  ========================================================= */

  const stopMicTest = () => {
    if (
      animationFrameRef.current
    ) {
      cancelAnimationFrame(
        animationFrameRef.current
      );

      animationFrameRef.current =
        null;
    }

    if (timerRef.current) {
      clearInterval(
        timerRef.current
      );

      timerRef.current =
        null;
    }

    if (
      streamRef.current
    ) {
      streamRef.current
        .getTracks()
        .forEach(
          (track) =>
            track.stop()
        );

      streamRef.current =
        null;
    }

    if (
      audioContextRef.current
    ) {
      audioContextRef.current
        .close()
        .catch(() => {});

      audioContextRef.current =
        null;
    }

    analyserRef.current =
      null;

    setMicTesting(false);
  };

  const calculateMicResult =
    () => {
      if (micPeak >= 45) {
        setMicStatus("good");

        setMicMessage(
          isVietnamese
            ? "Microphone hoạt động tốt, mức tín hiệu rõ."
            : "Microphone is working well with a clear signal."
        );

        return;
      }

      if (micPeak >= 15) {
        setMicStatus("low");

        setMicMessage(
          isVietnamese
            ? "Microphone có nhận âm thanh nhưng mức tín hiệu hơi thấp."
            : "Microphone detects sound, but the input level is a little low."
        );

        return;
      }

      setMicStatus("silent");

      setMicMessage(
        isVietnamese
          ? "Hầu như không phát hiện âm thanh. Hãy kiểm tra microphone hoặc nói gần hơn."
          : "Almost no sound was detected. Check the microphone or speak closer to it."
      );
    };

  const handleStopMicTest =
    () => {
      calculateMicResult();

      stopMicTest();
    };

  const updateMicLevel =
    () => {
      const analyser =
        analyserRef.current;

      if (!analyser) {
        return;
      }

      const dataArray =
        new Uint8Array(
          analyser.fftSize
        );

      analyser.getByteTimeDomainData(
        dataArray
      );

      let sumSquares = 0;

      for (
        let index = 0;
        index <
        dataArray.length;
        index += 1
      ) {
        const normalized =
          (
            dataArray[
              index
            ] -
            128
          ) /
          128;

        sumSquares +=
          normalized *
          normalized;
      }

      const rms =
        Math.sqrt(
          sumSquares /
            dataArray.length
        );

      /*
        RMS thường khá nhỏ.
        Nhân để đưa về thang UI 0 - 100.
      */

      const level =
        Math.min(
          100,
          Math.round(
            rms * 320
          )
        );

      setMicLevel(level);

      setMicPeak(
        (previousPeak) =>
          Math.max(
            previousPeak,
            level
          )
      );

      animationFrameRef.current =
        requestAnimationFrame(
          updateMicLevel
        );
    };

  const startMicTest =
    async () => {
      if (micTesting) {
        return;
      }

      setMicStatus(
        "requesting"
      );

      setMicMessage(
        isVietnamese
          ? "Đang yêu cầu quyền truy cập microphone..."
          : "Requesting microphone permission..."
      );

      setMicLevel(0);
      setMicPeak(0);
      setMicTestTime(0);
      setMicDeviceName("");

      try {
        if (
          !navigator
            .mediaDevices
            ?.getUserMedia
        ) {
          throw new Error(
            "getUserMedia is not supported"
          );
        }

        const stream =
          await navigator.mediaDevices
            .getUserMedia({
              audio: {
                echoCancellation:
                  true,

                noiseSuppression:
                  true,

                autoGainControl:
                  true,

                channelCount: 1,
              },
            });

        streamRef.current =
          stream;

        const audioTrack =
          stream.getAudioTracks()[
            0
          ];

        const settings =
          audioTrack
            ?.getSettings?.() ||
          {};

        const label =
          audioTrack?.label ||
          settings.deviceId ||
          (isVietnamese
            ? "Microphone mặc định"
            : "Default microphone");

        setMicDeviceName(
          label
        );

        const AudioContextClass =
          window.AudioContext ||
          window.webkitAudioContext;

        if (
          !AudioContextClass
        ) {
          throw new Error(
            "Web Audio API is not supported"
          );
        }

        const audioContext =
          new AudioContextClass();

        audioContextRef.current =
          audioContext;

        const source =
          audioContext
            .createMediaStreamSource(
              stream
            );

        const analyser =
          audioContext
            .createAnalyser();

        analyser.fftSize =
          1024;

        analyser.smoothingTimeConstant =
          0.8;

        source.connect(
          analyser
        );

        analyserRef.current =
          analyser;

        setMicTesting(true);

        setMicStatus(
          "listening"
        );

        setMicMessage(
          isVietnamese
            ? "Đang nghe. Hãy nói một câu bình thường để kiểm tra."
            : "Listening. Speak normally to test your microphone."
        );

        timerRef.current =
          setInterval(
            () => {
              setMicTestTime(
                (
                  previous
                ) =>
                  previous + 1
              );
            },
            1000
          );

        updateMicLevel();
      } catch (error) {
        console.error(
          "Microphone test error:",
          error
        );

        stopMicTest();

        if (
          error.name ===
          "NotAllowedError"
        ) {
          setMicStatus(
            "denied"
          );

          setMicMessage(
            isVietnamese
              ? "Trình duyệt chưa được cấp quyền sử dụng microphone."
              : "Microphone permission was denied."
          );

          return;
        }

        if (
          error.name ===
          "NotFoundError"
        ) {
          setMicStatus(
            "missing"
          );

          setMicMessage(
            isVietnamese
              ? "Không tìm thấy thiết bị microphone."
              : "No microphone device was found."
          );

          return;
        }

        setMicStatus(
          "error"
        );

        setMicMessage(
          isVietnamese
            ? "Không thể kiểm tra microphone. Vui lòng thử lại."
            : "Unable to test the microphone. Please try again."
        );
      }
    };

  /* =========================================================
     CLEANUP
  ========================================================= */

  useEffect(() => {
    return () => {
      stopMicTest();
    };
  }, []);

  /* =========================================================
     MIC STATUS HELPERS
  ========================================================= */

  const getMicStatusText =
    () => {
      if (
        micStatus ===
        "listening"
      ) {
        return isVietnamese
          ? "Đang kiểm tra"
          : "Testing";
      }

      if (
        micStatus ===
        "good"
      ) {
        return isVietnamese
          ? "Hoạt động tốt"
          : "Good";
      }

      if (
        micStatus ===
        "low"
      ) {
        return isVietnamese
          ? "Tín hiệu thấp"
          : "Low signal";
      }

      if (
        micStatus ===
        "silent"
      ) {
        return isVietnamese
          ? "Không có tín hiệu"
          : "No signal";
      }

      if (
        micStatus ===
          "denied" ||
        micStatus ===
          "missing" ||
        micStatus ===
          "error"
      ) {
        return isVietnamese
          ? "Có lỗi"
          : "Error";
      }

      return isVietnamese
        ? "Chưa kiểm tra"
        : "Not tested";
    };

  const getMicStatusClass =
    () => {
      if (
        micStatus ===
        "good"
      ) {
        return "good";
      }

      if (
        micStatus ===
        "low"
      ) {
        return "warning";
      }

      if (
        [
          "silent",
          "denied",
          "missing",
          "error",
        ].includes(
          micStatus
        )
      ) {
        return "error";
      }

      if (
        micStatus ===
        "listening"
      ) {
        return "testing";
      }

      return "idle";
    };

  /* =========================================================
     UI
  ========================================================= */

  return (
    <main className="workspace">
      <div className="workspace-container">
        {/* ===========================
            Hero
        =========================== */}

        <section className="workspace-hero">
          <div>
            <span className="workspace-eyebrow">
              NextFarm VoiceLog
            </span>

            <h2>
              ⚙️{" "}
              {isVietnamese
                ? "Cài đặt"
                : "Settings"}
            </h2>

            <p>
              {isVietnamese
                ? "Tùy chỉnh giao diện, giọng nói, AI và dữ liệu của hệ thống."
                : "Customize interface, voice, AI and application data."}
            </p>
          </div>
        </section>

        <div className="settings-layout">
          {/* ===========================
              Appearance
          =========================== */}

          <section className="settings-card">
            <div className="settings-card-header">
              <div className="settings-card-icon">
                🎨
              </div>

              <div>
                <h3>
                  {isVietnamese
                    ? "Giao diện"
                    : "Appearance"}
                </h3>

                <p>
                  {isVietnamese
                    ? "Ngôn ngữ và chế độ hiển thị của ứng dụng."
                    : "Application language and display mode."}
                </p>
              </div>
            </div>

            <div className="settings-field">
              <div className="settings-field-label">
                <strong>
                  🌐{" "}
                  {isVietnamese
                    ? "Ngôn ngữ"
                    : "Language"}
                </strong>

                <span>
                  {isVietnamese
                    ? "Áp dụng cho toàn bộ giao diện."
                    : "Applied across the entire interface."}
                </span>
              </div>

              <select
                value={
                  settings.language
                }
                onChange={(
                  event
                ) =>
                  onSettingChange(
                    "language",
                    event.target
                      .value
                  )
                }
              >
                <option value="vi">
                  🇻🇳 Tiếng Việt
                </option>

                <option value="en">
                  🇬🇧 English
                </option>
              </select>
            </div>

            <div className="settings-field settings-field-column">
              <div className="settings-field-label">
                <strong>
                  🌓{" "}
                  {isVietnamese
                    ? "Chủ đề"
                    : "Theme"}
                </strong>

                <span>
                  {isVietnamese
                    ? "Cài đặt này được giữ nguyên sau khi tải lại trang."
                    : "This preference persists after reloading."}
                </span>
              </div>

              <div className="settings-segmented">
                <button
                  type="button"
                  className={
                    settings.theme ===
                    "light"
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    onSettingChange(
                      "theme",
                      "light"
                    )
                  }
                >
                  ☀️{" "}
                  {isVietnamese
                    ? "Sáng"
                    : "Light"}
                </button>

                <button
                  type="button"
                  className={
                    settings.theme ===
                    "dark"
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    onSettingChange(
                      "theme",
                      "dark"
                    )
                  }
                >
                  🌙{" "}
                  {isVietnamese
                    ? "Tối"
                    : "Dark"}
                </button>

                <button
                  type="button"
                  className={
                    settings.theme ===
                    "system"
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    onSettingChange(
                      "theme",
                      "system"
                    )
                  }
                >
                  💻{" "}
                  {isVietnamese
                    ? "Thiết bị"
                    : "System"}
                </button>
              </div>
            </div>
          </section>

          {/* ===========================
              Voice
          =========================== */}

          <section className="settings-card">
            <div className="settings-card-header">
              <div className="settings-card-icon">
                🎙️
              </div>

              <div>
                <h3>
                  {isVietnamese
                    ? "Giọng nói"
                    : "Voice"}
                </h3>

                <p>
                  {isVietnamese
                    ? "Cấu hình và kiểm tra thiết bị thu âm."
                    : "Configure and test the audio input device."}
                </p>
              </div>
            </div>

            <div className="settings-field">
              <div className="settings-field-label">
                <strong>
                  🗣️{" "}
                  {isVietnamese
                    ? "Ngôn ngữ nhận dạng"
                    : "Recognition language"}
                </strong>

                <span>
                  {isVietnamese
                    ? "Dùng cho AI Service khi backend hỗ trợ."
                    : "Used by the AI Service once supported."}
                </span>
              </div>

              <select
                value={
                  settings
                    .recognitionLanguage
                }
                onChange={(
                  event
                ) =>
                  onSettingChange(
                    "recognitionLanguage",
                    event.target
                      .value
                  )
                }
              >
                <option value="vi-VN">
                  🇻🇳 Tiếng Việt
                </option>

                <option value="en-US">
                  🇺🇸 English
                </option>
              </select>
            </div>

            <div className="settings-field">
              <div className="settings-field-label">
                <strong>
                  📍{" "}
                  {isVietnamese
                    ? "Vùng / giọng nói"
                    : "Dialect / region"}
                </strong>

                <span>
                  {isVietnamese
                    ? "Phục vụ thử nghiệm giọng vùng miền."
                    : "Prepared for regional speech testing."}
                </span>
              </div>

              <select
                value={
                  settings.dialect
                }
                onChange={(
                  event
                ) =>
                  onSettingChange(
                    "dialect",
                    event.target
                      .value
                  )
                }
              >
                <option value="auto">
                  🤖{" "}
                  {isVietnamese
                    ? "Tự động"
                    : "Automatic"}
                </option>

                <option value="north">
                  {isVietnamese
                    ? "Miền Bắc"
                    : "Northern"}
                </option>

                <option value="central">
                  {isVietnamese
                    ? "Miền Trung"
                    : "Central"}
                </option>

                <option value="south">
                  {isVietnamese
                    ? "Miền Nam"
                    : "Southern"}
                </option>
              </select>
            </div>

            {/* ===========================
                Microphone Test
            =========================== */}

            <div className="mic-test-panel">
              <div className="mic-test-header">
                <div>
                  <strong>
                    🎙️{" "}
                    {isVietnamese
                      ? "Kiểm tra microphone"
                      : "Microphone test"}
                  </strong>

                  <span>
                    {isVietnamese
                      ? "Kiểm tra quyền truy cập, thiết bị và mức tín hiệu đầu vào."
                      : "Check permission, device and input signal level."}
                  </span>
                </div>

                <span
                  className={`mic-status-badge ${getMicStatusClass()}`}
                >
                  {micTesting
                    ? "●"
                    : "○"}{" "}
                  {getMicStatusText()}
                </span>
              </div>

              {micDeviceName && (
                <div className="mic-device-info">
                  <span>
                    🎤
                  </span>

                  <div>
                    <strong>
                      {isVietnamese
                        ? "Thiết bị"
                        : "Device"}
                    </strong>

                    <span>
                      {
                        micDeviceName
                      }
                    </span>
                  </div>
                </div>
              )}

              <div className="mic-level-section">
                <div className="mic-level-label">
                  <span>
                    {isVietnamese
                      ? "Mức tín hiệu"
                      : "Input level"}
                  </span>

                  <strong>
                    {micLevel}%
                  </strong>
                </div>

                <div className="mic-level-track">
                  <div
                    className="mic-level-fill"
                    style={{
                      width: `${micLevel}%`,
                    }}
                  />
                </div>

                <div className="mic-level-meta">
                  <span>
                    Peak: {micPeak}%
                  </span>

                  <span>
                    {isVietnamese
                      ? "Thời gian"
                      : "Duration"}
                    :{" "}
                    {micTestTime}s
                  </span>
                </div>
              </div>

              {micMessage && (
                <div
                  className={`mic-test-message ${getMicStatusClass()}`}
                >
                  {micStatus ===
                  "good"
                    ? "✅"
                    : micStatus ===
                        "low"
                      ? "⚠️"
                      : micStatus ===
                          "listening"
                        ? "🎧"
                        : micStatus ===
                            "idle"
                          ? "ℹ️"
                          : "❌"}{" "}
                  {micMessage}
                </div>
              )}

              <div className="mic-test-actions">
                {!micTesting ? (
                  <button
                    type="button"
                    className="mic-test-start"
                    onClick={
                      startMicTest
                    }
                  >
                    🎙️{" "}
                    {isVietnamese
                      ? "Bắt đầu kiểm tra"
                      : "Start test"}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="mic-test-stop"
                    onClick={
                      handleStopMicTest
                    }
                  >
                    ⏹{" "}
                    {isVietnamese
                      ? "Dừng kiểm tra"
                      : "Stop test"}
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* ===========================
              AI
          =========================== */}

          <section className="settings-card">
            <div className="settings-card-header">
              <div className="settings-card-icon">
                🤖
              </div>

              <div>
                <h3>
                  AI
                </h3>

                <p>
                  {isVietnamese
                    ? "Quản lý các chức năng AI trong hệ thống."
                    : "Manage AI functions across the system."}
                </p>
              </div>
            </div>

            <SettingToggle
              icon="💬"
              title={
                isVietnamese
                  ? "Trợ lý NextFarm AI"
                  : "NextFarm AI Assistant"
              }
              description={
                isVietnamese
                  ? "Tắt chức năng này sẽ ẩn nút trợ lý AI trên toàn hệ thống."
                  : "Turning this off hides the AI assistant across the application."
              }
              checked={
                settings
                  .aiAssistantEnabled
              }
              onChange={(
                value
              ) =>
                onSettingChange(
                  "aiAssistantEnabled",
                  value
                )
              }
            />

            <SettingToggle
              icon="✅"
              title={
                isVietnamese
                  ? "Kiểm tra dữ liệu AI"
                  : "AI data validation"
              }
              description={
                isVietnamese
                  ? "Lưu tùy chọn kiểm tra dữ liệu trích xuất."
                  : "Store the extracted-data validation preference."
              }
              checked={
                settings
                  .autoValidation
              }
              onChange={(
                value
              ) =>
                onSettingChange(
                  "autoValidation",
                  value
                )
              }
            />

            <div className="settings-api-note">
              <span className="settings-api-dot" />

              <div>
                <strong>
                  Frontend / Mock
                </strong>

                <span>
                  Speech:{" "}
                  {
                    settings
                      .recognitionLanguage
                  }{" "}
                  • Dialect:{" "}
                  {
                    settings.dialect
                  }
                </span>
              </div>
            </div>
          </section>

          {/* ===========================
              Data
          =========================== */}

          <section className="settings-card">
            <div className="settings-card-header">
              <div className="settings-card-icon">
                💾
              </div>

              <div>
                <h3>
                  {isVietnamese
                    ? "Dữ liệu & quyền riêng tư"
                    : "Data & privacy"}
                </h3>

                <p>
                  {isVietnamese
                    ? "Quản lý dữ liệu lưu cục bộ trên thiết bị."
                    : "Manage data stored locally on this device."}
                </p>
              </div>
            </div>

            <SettingToggle
              icon="🕘"
              title={
                isVietnamese
                  ? "Lưu lịch sử AI"
                  : "Save AI history"
              }
              description={
                isVietnamese
                  ? "Lưu lựa chọn để chuẩn bị điều khiển lịch sử chatbot."
                  : "Store the preference for AI conversation history."
              }
              checked={
                settings
                  .saveChatHistory
              }
              onChange={(
                value
              ) =>
                onSettingChange(
                  "saveChatHistory",
                  value
                )
              }
            />

            <SettingToggle
              icon="📋"
              title={
                isVietnamese
                  ? "Lưu nhật ký cục bộ"
                  : "Save local logs"
              }
              description={
                isVietnamese
                  ? "Khi tắt, nhật ký mới chỉ tồn tại trong phiên hiện tại."
                  : "When disabled, new logs only remain for the current session."
              }
              checked={
                settings
                  .saveLocalLogs
              }
              onChange={(
                value
              ) =>
                onSettingChange(
                  "saveLocalLogs",
                  value
                )
              }
            />

            <div className="settings-storage-info">
              <span>
                💽
              </span>

              <div>
                <strong>
                  {isVietnamese
                    ? "Dung lượng localStorage"
                    : "Local storage usage"}
                </strong>

                <span>
                  {getLocalStorageSize()}
                </span>
              </div>
            </div>

            <div className="settings-danger-actions">
              <button
                type="button"
                onClick={
                  clearChatHistory
                }
              >
                🗑️{" "}
                {isVietnamese
                  ? "Xóa lịch sử AI"
                  : "Delete AI history"}
              </button>

              <button
                type="button"
                onClick={
                  clearLocalLogs
                }
              >
                🗑️{" "}
                {isVietnamese
                  ? "Xóa nhật ký cục bộ"
                  : "Delete local logs"}
              </button>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

function SettingToggle({
  icon,
  title,
  description,
  checked,
  onChange,
}) {
  return (
    <div className="settings-toggle-row">
      <div className="settings-toggle-info">
        <span className="settings-toggle-icon">
          {icon}
        </span>

        <div>
          <strong>
            {title}
          </strong>

          <span>
            {description}
          </span>
        </div>
      </div>

      <button
        type="button"
        className={`settings-switch ${
          checked
            ? "active"
            : ""
        }`}
        onClick={() =>
          onChange(!checked)
        }
        role="switch"
        aria-checked={checked}
      >
        <span />
      </button>
    </div>
  );
}

export default Settings;