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
          ðŸŽ™ {text.transcript.title}
        </h2>

        {hasTranscript && !isConfirmed && (
          <span className="edit-badge">
            ðŸ¤– {text.transcript.aiProcessed}
          </span>
        )}

        {isConfirmed && (
          <span className="confirmed-badge">
            âœ… {text.transcript.confirmed}
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
          ðŸ’¡ {text.transcript.reviewTip}
        </div>
      )}

      {isConfirmed && (
        <div className="transcript-success">
          âœ… {text.transcript.success}
        </div>
      )}
    </div>
  );
}

export default TranscriptBox;