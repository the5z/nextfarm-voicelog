function AIForm({
  aiData = {},
  onAiDataChange,
  isConfirmed = false,
  text,
  language = "vi",
  validation = {
    errors: {},
    warnings: {},
  },
  showValidation = false,
}) {
  const isVietnamese =
    language === "vi";

  const handleChange = (
    field,
    value
  ) => {
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

  const errors =
    validation?.errors || {};

  const warnings =
    validation?.warnings || {};

  const hasErrors =
    Object.keys(errors).length > 0;

  const hasWarnings =
    Object.keys(warnings).length > 0;

  const getFieldClassName = (
    field
  ) => {
    if (!showValidation) {
      return "";
    }

    if (errors[field]) {
      return "validation-error";
    }

    if (warnings[field]) {
      return "validation-warning";
    }

    return "";
  };

  return (
    <div className="ai-form">
      <div className="ai-form-header">
        <h3>
          🤖 {text.aiForm.title}
        </h3>

        {isConfirmed && (
          <span className="confirmed-badge">
            ✅ {text.aiForm.confirmed}
          </span>
        )}

        {!isConfirmed &&
          hasAiData &&
          !showValidation && (
            <span className="edit-badge">
              ✏️ {text.aiForm.editable}
            </span>
          )}

        {!isConfirmed &&
          hasAiData &&
          showValidation &&
          hasErrors && (
            <span className="validation-badge error">
              ❌{" "}
              {isVietnamese
                ? "Thiếu thông tin"
                : "Missing information"}
            </span>
          )}

        {!isConfirmed &&
          hasAiData &&
          showValidation &&
          !hasErrors &&
          hasWarnings && (
            <span className="validation-badge warning">
              ⚠️{" "}
              {isVietnamese
                ? "Cần kiểm tra"
                : "Needs review"}
            </span>
          )}

        {!isConfirmed &&
          hasAiData &&
          showValidation &&
          !hasErrors &&
          !hasWarnings && (
            <span className="confirmed-badge">
              ✅{" "}
              {isVietnamese
                ? "Sẵn sàng"
                : "Ready"}
            </span>
          )}
      </div>

      <div
        className={`ai-field ${getFieldClassName(
          "lot"
        )}`}
      >
        <label htmlFor="lot">
          🏷️ {text.aiForm.lot}
          <span className="required-mark">
            *
          </span>
        </label>

        <input
          id="lot"
          type="text"
          placeholder={
            text.aiForm
              .lotPlaceholder
          }
          value={aiData.lot || ""}
          onChange={(event) =>
            handleChange(
              "lot",
              event.target.value
            )
          }
          readOnly={isConfirmed}
          aria-invalid={
            showValidation &&
            Boolean(errors.lot)
          }
        />

        {showValidation &&
          errors.lot && (
            <span className="field-validation-message error">
              ❌ {errors.lot}
            </span>
          )}

        {showValidation &&
          warnings.lot &&
          !errors.lot && (
            <span className="field-validation-message warning">
              ⚠️ {warnings.lot}
            </span>
          )}
      </div>

      <div
        className={`ai-field ${getFieldClassName(
          "work"
        )}`}
      >
        <label htmlFor="work">
          🛠️ {text.aiForm.work}
          <span className="required-mark">
            *
          </span>
        </label>

        <input
          id="work"
          type="text"
          placeholder={
            text.aiForm
              .workPlaceholder
          }
          value={
            aiData.work || ""
          }
          onChange={(event) =>
            handleChange(
              "work",
              event.target.value
            )
          }
          readOnly={isConfirmed}
          aria-invalid={
            showValidation &&
            Boolean(errors.work)
          }
        />

        {showValidation &&
          errors.work && (
            <span className="field-validation-message error">
              ❌ {errors.work}
            </span>
          )}

        {showValidation &&
          warnings.work &&
          !errors.work && (
            <span className="field-validation-message warning">
              ⚠️ {warnings.work}
            </span>
          )}
      </div>

      <div
        className={`ai-field ${getFieldClassName(
          "material"
        )}`}
      >
        <label htmlFor="material">
          🌾 {text.aiForm.material}
        </label>

        <input
          id="material"
          type="text"
          placeholder={
            text.aiForm
              .materialPlaceholder
          }
          value={
            aiData.material || ""
          }
          onChange={(event) =>
            handleChange(
              "material",
              event.target.value
            )
          }
          readOnly={isConfirmed}
        />

        {showValidation &&
          warnings.material && (
            <span className="field-validation-message warning">
              ⚠️{" "}
              {warnings.material}
            </span>
          )}
      </div>

      <div className="ai-form-row">
        <div
          className={`ai-field ${getFieldClassName(
            "quantity"
          )}`}
        >
          <label htmlFor="quantity">
            📦{" "}
            {text.aiForm.quantity}
          </label>

          <input
            id="quantity"
            type="number"
            placeholder={
              text.aiForm
                .quantityPlaceholder
            }
            value={
              aiData.quantity || ""
            }
            onChange={(event) =>
              handleChange(
                "quantity",
                event.target.value
              )
            }
            readOnly={isConfirmed}
            min="0"
            step="any"
            aria-invalid={
              showValidation &&
              Boolean(
                errors.quantity
              )
            }
          />

          {showValidation &&
            errors.quantity && (
              <span className="field-validation-message error">
                ❌{" "}
                {errors.quantity}
              </span>
            )}

          {showValidation &&
            warnings.quantity &&
            !errors.quantity && (
              <span className="field-validation-message warning">
                ⚠️{" "}
                {
                  warnings.quantity
                }
              </span>
            )}
        </div>

        <div
          className={`ai-field ${getFieldClassName(
            "unit"
          )}`}
        >
          <label htmlFor="unit">
            ⚖️ {text.aiForm.unit}
          </label>

          <input
            id="unit"
            type="text"
            placeholder={
              text.aiForm
                .unitPlaceholder
            }
            value={
              aiData.unit || ""
            }
            onChange={(event) =>
              handleChange(
                "unit",
                event.target.value
              )
            }
            readOnly={isConfirmed}
            aria-invalid={
              showValidation &&
              Boolean(errors.unit)
            }
          />

          {showValidation &&
            errors.unit && (
              <span className="field-validation-message error">
                ❌ {errors.unit}
              </span>
            )}

          {showValidation &&
            warnings.unit &&
            !errors.unit && (
              <span className="field-validation-message warning">
                ⚠️ {warnings.unit}
              </span>
            )}
        </div>
      </div>

      <div
        className={`ai-field ${getFieldClassName(
          "time"
        )}`}
      >
        <label htmlFor="time">
          🕒 {text.aiForm.time}
        </label>

        <input
          id="time"
          type="time"
          value={
            aiData.time || ""
          }
          onChange={(event) =>
            handleChange(
              "time",
              event.target.value
            )
          }
          readOnly={isConfirmed}
        />

        {showValidation &&
          warnings.time && (
            <span className="field-validation-message warning">
              ⚠️ {warnings.time}
            </span>
          )}
      </div>

      {!hasAiData && (
        <p className="ai-hint">
          {text.aiForm.empty}
        </p>
      )}

      {hasAiData &&
        !isConfirmed &&
        !showValidation && (
          <p className="ai-hint">
            {text.aiForm.editHint}
          </p>
        )}

      {hasAiData &&
        !isConfirmed &&
        showValidation &&
        hasErrors && (
          <div className="validation-summary error">
            <strong>
              ❌{" "}
              {isVietnamese
                ? "Chưa thể xác nhận"
                : "Cannot confirm yet"}
            </strong>

            <span>
              {isVietnamese
                ? "Vui lòng bổ sung hoặc sửa các trường được đánh dấu đỏ."
                : "Please complete or correct the fields highlighted in red."}
            </span>
          </div>
        )}

      {hasAiData &&
        !isConfirmed &&
        showValidation &&
        !hasErrors &&
        hasWarnings && (
          <div className="validation-summary warning">
            <strong>
              ⚠️{" "}
              {isVietnamese
                ? "Dữ liệu cần kiểm tra"
                : "Please review the data"}
            </strong>

            <span>
              {isVietnamese
                ? "Một số trường chưa đầy đủ nhưng không bắt buộc. Bạn vẫn có thể xác nhận nếu thông tin phù hợp."
                : "Some optional fields are incomplete. You may still confirm if the information is appropriate."}
            </span>
          </div>
        )}

      {hasAiData &&
        !isConfirmed &&
        showValidation &&
        !hasErrors &&
        !hasWarnings && (
          <div className="validation-summary success">
            <strong>
              ✅{" "}
              {isVietnamese
                ? "Dữ liệu hợp lệ"
                : "Data is valid"}
            </strong>

            <span>
              {isVietnamese
                ? "Các trường chính đã đầy đủ và sẵn sàng xác nhận."
                : "The main fields are complete and ready to confirm."}
            </span>
          </div>
        )}
    </div>
  );
}

export default AIForm;