import {
  useEffect,
  useRef,
  useState,
} from "react";

import "./TimePicker.css";

const HOURS = Array.from(
  { length: 24 },
  (_, index) =>
    String(index).padStart(
      2,
      "0"
    )
);

const MINUTES = Array.from(
  { length: 60 },
  (_, index) =>
    String(index).padStart(
      2,
      "0"
    )
);

function parseTime(value) {
  if (
    !value ||
    !/^\d{2}:\d{2}$/.test(
      value
    )
  ) {
    return {
      hour: "08",
      minute: "00",
    };
  }

  const [
    hour,
    minute,
  ] = value.split(":");

  return {
    hour,
    minute,
  };
}

function TimePicker({
  id = "time-picker",
  value = "",
  onChange,
  disabled = false,
  className = "",
  placeholder = "--:--",
  language = "vi",
  ariaLabelledBy,
}) {
  const isVietnamese =
    language === "vi";

  const [
    isOpen,
    setIsOpen,
  ] = useState(false);

  const [
    draftHour,
    setDraftHour,
  ] = useState("08");

  const [
    draftMinute,
    setDraftMinute,
  ] = useState("00");

  const pickerRef =
    useRef(null);

  const handleOpen = () => {
    if (disabled) {
      return;
    }

    const parsed =
      parseTime(value);

    setDraftHour(
      parsed.hour
    );

    setDraftMinute(
      parsed.minute
    );

    setIsOpen(true);
  };

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerDown = (
      event
    ) => {
      if (
        pickerRef.current &&
        !pickerRef.current.contains(
          event.target
        )
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handlePointerDown
    );

    document.addEventListener(
      "touchstart",
      handlePointerDown
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handlePointerDown
      );

      document.removeEventListener(
        "touchstart",
        handlePointerDown
      );
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (
      event
    ) => {
      if (
        event.key ===
        "Escape"
      ) {
        setIsOpen(false);
      }
    };

    window.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, [isOpen]);

  const handleApply = () => {
    const nextValue =
      `${draftHour}:${draftMinute}`;

    onChange?.(
      nextValue
    );

    setIsOpen(false);
  };

  const handleClear = () => {
    onChange?.("");

    setIsOpen(false);
  };

  return (
    <div
      ref={pickerRef}
      className={[
        "nextfarm-time-picker",
        isOpen
          ? "is-open"
          : "",
        disabled
          ? "is-disabled"
          : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <button
        id={id}
        type="button"
        className="nextfarm-time-trigger"
        onClick={
          handleOpen
        }
        disabled={
          disabled
        }
        aria-expanded={
          isOpen
        }
        aria-labelledby={
          ariaLabelledBy
        }
        aria-controls={`${id}-dialog`}
      >
        <span
          className={
            value
              ? "nextfarm-time-value"
              : "nextfarm-time-placeholder"
          }
        >
          {value ||
            placeholder}
        </span>

        <span
          className="nextfarm-time-icon"
          aria-hidden="true"
        >
          🕒
        </span>
      </button>

      {isOpen && (
        <div
          id={`${id}-dialog`}
          className="nextfarm-time-popover"
          role="dialog"
          aria-modal="false"
          aria-labelledby={`${id}-dialog-title`}
          aria-label={
            isVietnamese
              ? "Chọn thời gian"
              : "Choose time"
          }
        >
          <div className="nextfarm-time-popover-header">
            <div>
              <strong
                id={`${id}-dialog-title`}
              >
                🕒{" "}
                {isVietnamese
                  ? "Chọn thời gian"
                  : "Choose time"}
              </strong>

              <span>
                {isVietnamese
                  ? "Định dạng 24 giờ"
                  : "24-hour format"}
              </span>
            </div>

            <button
              type="button"
              className="nextfarm-time-close"
              onClick={() =>
                setIsOpen(false)
              }
              aria-label={
                isVietnamese
                  ? "Đóng"
                  : "Close"
              }
            >
              ×
            </button>
          </div>

          <div className="nextfarm-time-preview">
            <span>
              {draftHour}
            </span>

            <strong>
              :
            </strong>

            <span>
              {draftMinute}
            </span>
          </div>

          <div className="nextfarm-time-columns">
            <div className="nextfarm-time-column">
              <label
                htmlFor={`${id}-hour`}
              >
                {isVietnamese
                  ? "Giờ"
                  : "Hour"}
              </label>

              <select
                id={`${id}-hour`}
                name="time-hour"
                value={
                  draftHour
                }
                onChange={(
                  event
                ) =>
                  setDraftHour(
                    event.target
                      .value
                  )
                }
              >
                {HOURS.map(
                  (hour) => (
                    <option
                      key={
                        hour
                      }
                      value={
                        hour
                      }
                    >
                      {hour}
                    </option>
                  )
                )}
              </select>
            </div>

            <div className="nextfarm-time-separator">
              :
            </div>

            <div className="nextfarm-time-column">
              <label
                htmlFor={`${id}-minute`}
              >
                {isVietnamese
                  ? "Phút"
                  : "Minute"}
              </label>

              <select
                id={`${id}-minute`}
                name="time-minute"
                value={
                  draftMinute
                }
                onChange={(
                  event
                ) =>
                  setDraftMinute(
                    event.target
                      .value
                  )
                }
              >
                {MINUTES.map(
                  (minute) => (
                    <option
                      key={
                        minute
                      }
                      value={
                        minute
                      }
                    >
                      {minute}
                    </option>
                  )
                )}
              </select>
            </div>
          </div>

          <div className="nextfarm-time-actions">
            <button
              type="button"
              className="nextfarm-time-clear"
              onClick={
                handleClear
              }
            >
              {isVietnamese
                ? "Xóa"
                : "Clear"}
            </button>

            <button
              type="button"
              className="nextfarm-time-cancel"
              onClick={() =>
                setIsOpen(false)
              }
            >
              {isVietnamese
                ? "Hủy"
                : "Cancel"}
            </button>

            <button
              type="button"
              className="nextfarm-time-apply"
              onClick={
                handleApply
              }
            >
              ✓{" "}
              {isVietnamese
                ? "Áp dụng"
                : "Apply"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default TimePicker;