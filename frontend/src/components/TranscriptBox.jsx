function TranscriptBox({ transcript }) {
  return (
    <div className="transcript-box">
      <h2>🎙 Nội dung ghi âm</h2>

      <textarea
        className="transcript-textarea"
        value={transcript}
        readOnly
        placeholder="Sau khi ghi âm, nội dung AI chuyển đổi sẽ hiển thị tại đây..."
      />

      {!transcript && (
        <p className="transcript-hint">
          Chưa có nội dung ghi âm.
        </p>
      )}
    </div>
  );
}

export default TranscriptBox;