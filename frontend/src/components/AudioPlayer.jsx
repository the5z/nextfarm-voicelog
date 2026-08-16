function AudioPlayer({
  audioUrl,
  text,
}) {
  if (!audioUrl) return null;

  return (
    <div className="audio-player">
      <h3>
        🎧 {text.audioPlayer.title}
      </h3>

      <audio
        controls
        src={audioUrl}
        style={{ width: "100%" }}
      >
        {text.audioPlayer.unsupported}
      </audio>
    </div>
  );
}

export default AudioPlayer;