function ActionButtons({
  onRetry,
  onUpload,
  onConfirm,
  onCreateNew,
  hasAudio,
  hasResult,
  isUploading = false,
  isConfirmed = false,
  text,
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
            {hasResult
              ? `🎤 ${text.actions.recordAgain}`
              : `🗑 ${text.actions.delete}`}
          </button>

          {!hasResult && (
            <button
              type="button"
              className="btn-primary"
              onClick={onUpload}
              disabled={!hasAudio || isUploading}
            >
              {isUploading ? (
                <span className="button-loading">
                  <span className="spinner" />
                  {text.actions.processing}
                </span>
              ) : (
                `⬆ ${text.actions.sendAI}`
              )}
            </button>
          )}

          {hasResult && (
            <button
              type="button"
              className="btn-primary"
              onClick={onConfirm}
              disabled={isUploading}
            >
              ✅ {text.actions.confirmLog}
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
            ✅ {text.actions.confirmed}
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={onCreateNew}
          >
            ➕ {text.actions.createNew}
          </button>
        </>
      )}
    </div>
  );
}

export default ActionButtons;