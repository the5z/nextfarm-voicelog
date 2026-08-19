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
      Warning không chặn xác nhận.
    */
    if (hasWarnings) {
      return {
        type: "warning",
        icon: "⚠️",
        label: isVietnamese
          ? "Kiểm tra & xác nhận"
          : "Review & confirm",
        disabled: false,
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
        hasWarnings && (
          <div className="confirm-helper warning">
            <span>⚠️</span>

            <span>
              {isVietnamese
                ? "Có thông tin nên kiểm tra lại. Bạn vẫn có thể xác nhận nếu dữ liệu phù hợp."
                : "Some information should be reviewed. You can still confirm if it is correct."}
            </span>
          </div>
        )}
    </div>
  );
}

export default ActionButtons;