function AIForm({
  aiData = {},
  onAiDataChange,
  isConfirmed = false,
}) {
  const handleChange = (field, value) => {
    onAiDataChange({
      ...aiData,
      [field]: value,
    });
  };

  const hasAiData = Boolean(
    aiData.lot ||
      aiData.work ||
      aiData.material ||
      aiData.quantity ||
      aiData.unit ||
      aiData.time
  );

  return (
    <div className="ai-form">
      <div className="ai-form-header">
        <h3>🤖 Dữ liệu AI trích xuất</h3>

        {hasAiData && !isConfirmed && (
          <span className="edit-badge">✏️ Có thể chỉnh sửa</span>
        )}

        {isConfirmed && (
          <span className="confirmed-badge">✅ Đã xác nhận</span>
        )}
      </div>

      <input
        type="text"
        placeholder="Lô"
        value={aiData.lot || ""}
        onChange={(event) =>
          handleChange("lot", event.target.value)
        }
        readOnly={isConfirmed}
      />

      <input
        type="text"
        placeholder="Công việc"
        value={aiData.work || ""}
        onChange={(event) =>
          handleChange("work", event.target.value)
        }
        readOnly={isConfirmed}
      />

      <input
        type="text"
        placeholder="Vật tư"
        value={aiData.material || ""}
        onChange={(event) =>
          handleChange("material", event.target.value)
        }
        readOnly={isConfirmed}
      />

      <input
        type="number"
        placeholder="Số lượng"
        value={aiData.quantity || ""}
        onChange={(event) =>
          handleChange("quantity", event.target.value)
        }
        readOnly={isConfirmed}
        min="0"
      />

      <input
        type="text"
        placeholder="Đơn vị"
        value={aiData.unit || ""}
        onChange={(event) =>
          handleChange("unit", event.target.value)
        }
        readOnly={isConfirmed}
      />

      <input
        type="time"
        value={aiData.time || ""}
        onChange={(event) =>
          handleChange("time", event.target.value)
        }
        readOnly={isConfirmed}
        aria-label="Thời gian"
      />

      {!hasAiData && (
        <p className="ai-hint">
          Chưa có dữ liệu AI trích xuất.
        </p>
      )}

      {hasAiData && !isConfirmed && (
        <p className="ai-hint">
          Bạn có thể sửa riêng trường bị AI nhận sai trước khi xác nhận.
        </p>
      )}
    </div>
  );
}

export default AIForm;