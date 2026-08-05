function ActionButtons({
  onRetry,
  onUpload,
  onConfirm,
  onCreateNew,
  hasAudio,
  hasResult,
  isUploading = false,
  isConfirmed = false,
}) {
  return (
    <div className="action-buttons">
      {!isConfirmed && (
        <>
          <button
            type="button"
            className="btn-secondary"
            onClick={onRetry}
            disabled={!hasAudio || isUploading}
          >
            {hasResult ? "🎤 Ghi lại" : "🗑 Xóa bản ghi"}
          </button>

          {!hasResult && (
            <button
              type="button"
              className="btn-primary"
              onClick={onUpload}
              disabled={!hasAudio || isUploading}
            >
              {isUploading
                ? "⏳ Đang xử lý..."
                : "⬆ Gửi AI"}
            </button>
          )}

          {hasResult && (
            <button
              type="button"
              className="btn-primary"
              onClick={onConfirm}
              disabled={isUploading}
            >
              ✅ Xác nhận nhật ký
            </button>
          )}
        </>
      )}

      {isConfirmed && (
        <>
          <button
            type="button"
            className="btn-primary"
            disabled
          >
            ✅ Đã xác nhận
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={onCreateNew}
          >
            ➕ Tạo nhật ký mới
          </button>
        </>
      )}
    </div>
  );
}

export default ActionButtons;