function AIForm({ aiData = {} }) {
  return (
    <div className="ai-form">
      <h3>🤖 Dữ liệu AI trích xuất</h3>

      <input
        type="text"
        placeholder="Lô"
        value={aiData.lot || ""}
        readOnly
      />

      <input
        type="text"
        placeholder="Công việc"
        value={aiData.work || ""}
        readOnly
      />

      <input
        type="text"
        placeholder="Vật tư"
        value={aiData.material || ""}
        readOnly
      />

      <input
        type="number"
        placeholder="Số lượng"
        value={aiData.quantity || ""}
        readOnly
      />

      <input
        type="text"
        placeholder="Đơn vị"
        value={aiData.unit || ""}
        readOnly
      />

      <input
        type="text"
        placeholder="Thời gian"
        value={aiData.time || ""}
        readOnly
      />

      {!aiData.lot &&
        !aiData.work &&
        !aiData.material && (
          <p className="ai-hint">
            Chưa có dữ liệu AI trích xuất.
          </p>
        )}
    </div>
  );
}

export default AIForm;