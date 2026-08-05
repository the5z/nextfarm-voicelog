function ActionButtons({
  onRetry,
  onUpload,
  hasAudio,
  isUploading = false,
}) {
  return (
    <div className="action-buttons">
      <button
        type="button"
        className="btn-secondary"
        onClick={onRetry}
        disabled={!hasAudio || isUploading}
      >
        🗑 Xóa bản ghi
      </button>

      <button
        type="button"
        className="btn-primary"
        onClick={onUpload}
        disabled={!hasAudio || isUploading}
      >
        {isUploading ? "⏳ Đang xử lý..." : "⬆ Gửi AI"}
      </button>
    </div>
  );
}

export default ActionButtons;