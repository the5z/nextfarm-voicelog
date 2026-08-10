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
          <span className="edit-badge">
            ✏️ Có thể chỉnh sửa
          </span>
        )}

        {isConfirmed && (
          <span className="confirmed-badge">
            ✅ Đã xác nhận
          </span>
        )}
      </div>

      <div className="ai-field">
        <label htmlFor="lot">
          🏷️ Lô canh tác
        </label>

        <input
          id="lot"
          type="text"
          placeholder="Ví dụ: A01"
          value={aiData.lot || ""}
          onChange={(event) =>
            handleChange("lot", event.target.value)
          }
          readOnly={isConfirmed}
        />
      </div>

      <div className="ai-field">
        <label htmlFor="work">
          🛠️ Công việc
        </label>

        <input
          id="work"
          type="text"
          placeholder="Ví dụ: Bón phân"
          value={aiData.work || ""}
          onChange={(event) =>
            handleChange("work", event.target.value)
          }
          readOnly={isConfirmed}
        />
      </div>

      <div className="ai-field">
        <label htmlFor="material">
          🌾 Vật tư
        </label>

        <input
          id="material"
          type="text"
          placeholder="Ví dụ: Phân NPK"
          value={aiData.material || ""}
          onChange={(event) =>
            handleChange("material", event.target.value)
          }
          readOnly={isConfirmed}
        />
      </div>

      <div className="ai-form-row">
        <div className="ai-field">
          <label htmlFor="quantity">
            📦 Số lượng
          </label>

          <input
            id="quantity"
            type="number"
            placeholder="Ví dụ: 20"
            value={aiData.quantity || ""}
            onChange={(event) =>
              handleChange("quantity", event.target.value)
            }
            readOnly={isConfirmed}
            min="0"
          />
        </div>

        <div className="ai-field">
          <label htmlFor="unit">
            ⚖️ Đơn vị
          </label>

          <input
            id="unit"
            type="text"
            placeholder="Ví dụ: kg"
            value={aiData.unit || ""}
            onChange={(event) =>
              handleChange("unit", event.target.value)
            }
            readOnly={isConfirmed}
          />
        </div>
      </div>

      <div className="ai-field">
        <label htmlFor="time">
          🕒 Thời gian
        </label>

        <input
          id="time"
          type="time"
          value={aiData.time || ""}
          onChange={(event) =>
            handleChange("time", event.target.value)
          }
          readOnly={isConfirmed}
        />
      </div>

      {!hasAiData && (
        <p className="ai-hint">
          Chưa có dữ liệu AI trích xuất.
        </p>
      )}

      {hasAiData && !isConfirmed && (
        <p className="ai-hint">
          Chỉnh sửa nếu AI nhận sai trước khi xác nhận.
        </p>
      )}
    </div>
  );
}

export default AIForm;