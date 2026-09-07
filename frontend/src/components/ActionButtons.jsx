function ActionButtons({
  hasAudio = false,
  hasResult = false,
  isUploading = false,
  isConfirmed = false,

  validation = {
    errors: {},
    warnings: {},
  },

  showValidation = false,

  warningAcknowledged = false,
  requiresConfirmation = false,
  onAcknowledgeWarnings,

  onRetry,
  onUpload,
  onConfirm,
  onCreateNew,

  text,
  language = "vi",
}) {
  const isVietnamese =
    language === "vi";

  const errors =
    validation?.errors || {};

  const warnings =
    validation?.warnings || {};

  const hasErrors =
    Object.keys(errors).length > 0;

  const hasWarnings =
    Object.keys(warnings).length > 0;

  /* ===========================
     Confirm state
  =========================== */

  const getConfirmState = () => {
    if (isConfirmed) {
      return {
        type: "confirmed",
        icon: "✓",
        label: isVietnamese
          ? "Đã xác nhận"
          : "Confirmed",
        disabled: true,
      };
    }

    /*
      Trước lần kiểm tra đầu tiên:
      vẫn cho phép bấm để kích hoạt validation.
    */
    if (!showValidation) {
      return {
        type: "review",
        icon: "🔎",
        label: isVietnamese
          ? "Kiểm tra & xác nhận"
          : "Review & confirm",
        disabled: !hasResult,
      };
    }

    /*
      Sau khi validation đã chạy:
      lỗi bắt buộc => khóa xác nhận.
    */
    if (hasErrors) {
      return {
        type: "blocked",
        icon: "⚠️",
        label: isVietnamese
          ? "Cần bổ sung thông tin"
          : "Complete required fields",
        disabled: true,
      };
    }

    /*
      Risk-aware warning:
      - warning nhẹ: chỉ hiển thị, KHÔNG chặn confirm
      - warning requiresConfirmation: cần acknowledgement
    */
    if (
      hasWarnings &&
      requiresConfirmation
    ) {
      if (!warningAcknowledged) {
        return {
          type: "warning",
          icon: "⚠️",
          label: isVietnamese
            ? "Kiểm tra cảnh báo trước"
            : "Review warnings first",
          disabled: true,
        };
      }

      return {
        type: "ready",
        icon: "✓",
        label: isVietnamese
          ? "Xác nhận nhật ký"
          : "Confirm log",
        disabled: !hasResult,
      };
    }

    if (hasWarnings) {
      return {
        type: "ready",
        icon: "✓",
        label: isVietnamese
          ? "Xác nhận nhật ký"
          : "Confirm log",
        disabled: !hasResult,
      };
    }

    return {
      type: "ready",
      icon: "✓",
      label: isVietnamese
        ? "Xác nhận nhật ký"
        : "Confirm log",
      disabled: !hasResult,
    };
  };

  const confirmState =
    getConfirmState();

  /* ===========================
     Confirmed state
  =========================== */

  if (isConfirmed) {
    return (
      <div className="action-buttons action-buttons-confirmed">
        <button
          type="button"
          className="btn-confirm confirmed"
          disabled
        >
          <span>
            {confirmState.icon}
          </span>

          <span>
            {confirmState.label}
          </span>
        </button>

        <button
          type="button"
          className="btn-create-new"
          onClick={onCreateNew}
        >
          <span>＋</span>

          <span>
            {isVietnamese
              ? "Tạo nhật ký mới"
              : "Create new log"}
          </span>
        </button>
      </div>
    );
  }

  /* ===========================
     Before AI result
  =========================== */

  if (!hasResult) {
    return (
      <div className="action-buttons">
        <button
          type="button"
          className="btn-retry"
          onClick={onRetry}
          disabled={
            isUploading ||
            (!hasAudio && !hasResult)
          }
        >
          <span>🗑</span>

          <span>
            {isVietnamese
              ? "Xóa bản ghi"
              : "Delete recording"}
          </span>
        </button>

        <button
          type="button"
          className="btn-upload"
          onClick={onUpload}
          disabled={
            !hasAudio ||
            isUploading
          }
        >
          <span>
            {isUploading
              ? "⏳"
              : "⬆"}
          </span>

          <span>
            {isUploading
              ? isVietnamese
                ? "AI đang xử lý..."
                : "AI is processing..."
              : isVietnamese
                ? "Gửi AI"
                : "Send to AI"}
          </span>
        </button>
      </div>
    );
  }

  /* ===========================
     Review / Confirm
  =========================== */

  return (
    <div className="action-buttons">
      <button
        type="button"
        className="btn-retry"
        onClick={onRetry}
        disabled={isUploading}
      >
        <span>🗑</span>

        <span>
          {isVietnamese
            ? "Xóa bản ghi"
            : "Delete recording"}
        </span>
      </button>

      <button
        type="button"
        className={`btn-confirm ${confirmState.type}`}
        onClick={onConfirm}
        disabled={
          confirmState.disabled ||
          isUploading
        }
        aria-disabled={
          confirmState.disabled ||
          isUploading
        }
      >
        <span>
          {confirmState.icon}
        </span>

        <span>
          {confirmState.label}
        </span>
      </button>

      {showValidation &&
        hasErrors && (
          <div className="confirm-helper error">
            <span>❌</span>

            <span>
              {isVietnamese
                ? "Hãy sửa các trường bắt buộc được đánh dấu đỏ trước khi xác nhận."
                : "Fix the required fields highlighted in red before confirming."}
            </span>
          </div>
        )}

      {showValidation &&
        !hasErrors &&
        hasWarnings &&
        !requiresConfirmation && (
          <div className="confirm-helper warning">
            <span>⚠️</span>

            <span>
              {isVietnamese
                ? "Có cảnh báo nhẹ để bạn tham khảo. Cảnh báo này không chặn việc xác nhận."
                : "There is a non-blocking warning for review. You can still confirm the log."}
            </span>
          </div>
        )}

      {showValidation &&
        !hasErrors &&
        hasWarnings &&
        requiresConfirmation && (
          <div className="confirm-warning-review">
            <div className="confirm-helper warning">
              <span>⚠️</span>

              <span>
                {warningAcknowledged
                  ? isVietnamese
                    ? "Bạn đã xác nhận đã kiểm tra cảnh báo bắt buộc."
                    : "You acknowledged the confirmation-required warning."
                  : isVietnamese
                    ? "Cảnh báo này cần xác nhận của người dùng trước khi lưu."
                    : "This warning requires user acknowledgement before saving."}
              </span>
            </div>

            <button
              type="button"
              className={`btn-warning-ack ${
                warningAcknowledged
                  ? "acknowledged"
                  : ""
              }`}
              onClick={
                onAcknowledgeWarnings
              }
              disabled={
                isUploading ||
                warningAcknowledged
              }
            >
              <span>
                {warningAcknowledged
                  ? "✓"
                  : "👁"}
              </span>

              <span>
                {warningAcknowledged
                  ? isVietnamese
                    ? "Đã kiểm tra cảnh báo"
                    : "Warnings reviewed"
                  : isVietnamese
                    ? "Tôi đã kiểm tra cảnh báo"
                    : "I reviewed the warnings"}
              </span>
            </button>
          </div>
        )}
    </div>
  );
}

export default ActionButtons;