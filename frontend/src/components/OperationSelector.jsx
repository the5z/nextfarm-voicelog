import {
  DYNAMIC_FORM_OPERATIONS,
} from "../constants/dynamicFormOperations";

function OperationSelector({
  operation,
  onOperationChange,
  language = "vi",
  disabled = false,
}) {
  const isVietnamese =
    language === "vi";

  return (
    <section
      className="operation-selector"
      aria-labelledby="operation-selector-title"
    >
      <div className="operation-selector-header">
        <div>
          <span className="operation-selector-eyebrow">
            {isVietnamese
              ? "Sổ nghiệp vụ"
              : "Operation notebook"}
          </span>

          <h3 id="operation-selector-title">
            {isVietnamese
              ? "Bạn muốn ghi nhận nội dung gì?"
              : "What would you like to record?"}
          </h3>

          <p>
            {isVietnamese
              ? "Chọn nghiệp vụ trước khi nhập liệu hoặc ghi âm."
              : "Choose an operation before entering data or recording."}
          </p>
        </div>
      </div>

      <div
        className="operation-selector-grid"
        aria-label={
          isVietnamese
            ? "Chọn nghiệp vụ"
            : "Choose operation"
        }
      >
        {DYNAMIC_FORM_OPERATIONS.map(
          (item) => {
            const isSelected =
              item.operation === operation;

            return (
              <button
                key={item.operation}
                type="button"
                aria-pressed={isSelected}
                className={`operation-selector-item${
                  isSelected
                    ? " is-selected"
                    : ""
                }`}
                disabled={disabled}
                onClick={() =>
                  onOperationChange?.(
                    item.operation
                  )
                }
              >
                <span className="operation-selector-item-label">
                  {isVietnamese
                    ? item.labelVi
                    : item.labelEn}
                </span>

                <span className="operation-selector-item-description">
                  {isVietnamese
                    ? item.descriptionVi
                    : item.descriptionEn}
                </span>
              </button>
            );
          }
        )}
      </div>
    </section>
  );
}

export default OperationSelector;
