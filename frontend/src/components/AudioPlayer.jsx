function AudioPlayer({ audioUrl }) {
  if (!audioUrl) return null;

  return (
    <div className="audio-player">
      <h3>🎧 Bản ghi vừa tạo</h3>

      <audio
        controls
        src={audioUrl}
        style={{ width: "100%" }}
      >
        Trình duyệt của bạn không hỗ trợ phát âm thanh.
      </audio>
    </div>
  );
}

export default AudioPlayer;