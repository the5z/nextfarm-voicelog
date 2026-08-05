function TranscriptBox({
  transcript,
  onTranscriptChange,
  isConfirmed = false,
}) {
  const hasTranscript = Boolean(transcript?.trim());

  return (
    <div className="transcript-box">
      <div className="transcript-header">
        <h2>🎙 Nội dung ghi âm</h2>

        {hasTranscript && !isConfirmed && (
          <span className="edit-badge">✏️ Có thể chỉnh sửa</span>
        )}

        {isConfirmed && (
          <span className="confirmed-badge">✅ Đã xác nhận</span>
        )}
      </div>

      <textarea
        className="transcript-textarea"
        value={transcript}
        onChange={(event) => onTranscriptChange(event.target.value)}
        readOnly={isConfirmed}
        placeholder="Sau khi AI xử lý, nội dung chuyển đổi sẽ hiển thị tại đây..."
        aria-label="Nội dung ghi âm chuyển thành văn bản"
      />

      {!hasTranscript && (
        <p className="transcript-hint">
          Chưa có nội dung ghi âm.
        </p>
      )}

      {hasTranscript && !isConfirmed && (
        <p className="transcript-hint">
          Bạn có thể sửa riêng từ hoặc đoạn bị nhận sai, không cần ghi âm lại toàn bộ.
        </p>
      )}
    </div>
  );
}

export default TranscriptBox;