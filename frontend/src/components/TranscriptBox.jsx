function TranscriptBox({
  transcript,
  onTranscriptChange,
  isConfirmed = false,
  text,
}) {
  const hasTranscript = Boolean(transcript?.trim());

  return (
    <div className="transcript-box">
      <div className="transcript-header">
        <h2>
          🎙 {text.transcript.title}
        </h2>

        {hasTranscript && !isConfirmed && (
          <span className="edit-badge">
            🤖 {text.transcript.aiProcessed}
          </span>
        )}

        {isConfirmed && (
          <span className="confirmed-badge">
            ✅ {text.transcript.confirmed}
          </span>
        )}
      </div>

      <textarea
        id="transcript"
        name="transcript"
        className="transcript-textarea"
        value={transcript ?? ""}
        onChange={(event) =>
          onTranscriptChange(event.target.value)
        }
        readOnly={isConfirmed}
        placeholder={text.transcript.placeholder}
        aria-label={text.transcript.ariaLabel}
        autoComplete="off"
      />

      {!hasTranscript && (
        <p className="transcript-hint">
          {text.transcript.empty}
        </p>
      )}

      {hasTranscript && !isConfirmed && (
        <div className="transcript-tip">
          💡 {text.transcript.reviewTip}
        </div>
      )}

      {isConfirmed && (
        <div className="transcript-success">
          ✅ {text.transcript.success}
        </div>
      )}
    </div>
  );
}

export default TranscriptBox;