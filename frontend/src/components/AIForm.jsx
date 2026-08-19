import TimePicker from "./TimePicker";

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
  highlightedField = "",
}) {
  const isVietnamese =
    language === "vi";

  /* ===========================
     Change data
  =========================== */

  const handleChange = (
    field,
    value
  ) => {
    onAiDataChange({
      ...aiData,
      [field]: value,
    });
  };

  /* ===========================
     Data state
  =========================== */

  const hasAiData = Boolean(
    aiData.lot ||
      aiData.work ||
      aiData.material ||
      aiData.quantity ||
      aiData.unit ||
      aiData.time
  );

  /* ===========================
     Validation
  =========================== */

  const errors =
    validation?.errors || {};

  const warnings =
    validation?.warnings || {};

  const errorEntries =
    Object.entries(errors).filter(
      ([, message]) =>
        Boolean(message)
    );

  const warningEntries =
    Object.entries(
      warnings
    ).filter(
      ([, message]) =>
        Boolean(message)
    );

  const hasErrors =
    errorEntries.length > 0;

  const hasWarnings =
    warningEntries.length > 0;

  /* ===========================
     Field labels
  =========================== */

  const FIELD_LABELS = {
    lot: isVietnamese
      ? "Lô canh tác"
      : "Farm plot",

    work: isVietnamese
      ? "Công việc"
      : "Task",

    material: isVietnamese
      ? "Vật tư"
      : "Material",

    quantity: isVietnamese
      ? "Số lượng"
      : "Quantity",

    unit: isVietnamese
      ? "Đơn vị"
      : "Unit",

    time: isVietnamese
      ? "Thời gian"
      : "Time",
  };

  /* ===========================
     Field helpers
  =========================== */

  const getFieldClassName = (
    field
  ) => {
    const classes = [];

    if (showValidation) {
      if (errors[field]) {
        classes.push(
          "validation-error"
        );
      } else if (
        warnings[field]
      ) {
        classes.push(
          "validation-warning"
        );
      }
    }

    if (
      highlightedField ===
      field
    ) {
      classes.push(
        "ai-field-updated"
      );
    }

    return classes.join(" ");
  };

  const hasFieldValue = (
    field
  ) => {
    const value =
      aiData[field];

    if (
      value === null ||
      value === undefined
    ) {
      return false;
    }

    return (
      String(value).trim() !== ""
    );
  };

  const getFieldStatus = (
    field
  ) => {
    /*
      Không hiện trạng thái ngay khi mới mở trang.

      Thứ tự ưu tiên:
      1. Error
      2. Warning
      3. Confirmed / identified
      4. Neutral

      Quan trọng:
      Warning phải được xử lý trước khi xác nhận.
      Nếu có warning, field vẫn hiển thị trạng thái
      "Cần kiểm tra".
    */

    if (
      !hasAiData ||
      (
        !showValidation &&
        !isConfirmed
      )
    ) {
      return null;
    }

    if (errors[field]) {
      return {
        type: "error",
        icon: "✕",
        label: isVietnamese
          ? "Chưa xác định"
          : "Not identified",
      };
    }

    if (warnings[field]) {
      return {
        type: "warning",
        icon: "!",
        label: isVietnamese
          ? "Cần kiểm tra"
          : "Needs review",
      };
    }

    if (isConfirmed) {
      if (hasFieldValue(field)) {
        return {
          type: "success",
          icon: "✓",
          label: isVietnamese
            ? "Đã xác nhận"
            : "Confirmed",
        };
      }

      return null;
    }

    if (hasFieldValue(field)) {
      return {
        type: "success",
        icon: "✓",
        label: isVietnamese
          ? "Đã xác định"
          : "Identified",
      };
    }

    return {
      type: "neutral",
      icon: "–",
      label: isVietnamese
        ? "Chưa có dữ liệu"
        : "No data",
    };
  };

  const FieldStatus = ({
    field,
  }) => {
    const status =
      getFieldStatus(field);

    if (!status) {
      return null;
    }

    return (
      <span
        className={`ai-field-status ${status.type}`}
        title={
          status.label
        }
        aria-label={
          status.label
        }
      >
        <span
          className="ai-field-status-icon"
          aria-hidden="true"
        >
          {status.icon}
        </span>

        <span className="ai-field-status-text">
          {status.label}
        </span>
      </span>
    );
  };

  /* ===========================
     UI
  =========================== */

  return (
    <div className="ai-form">
      {/* ===========================
          Header
      =========================== */}

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

      {/* ===========================
          AI COMPLETENESS
      =========================== */}

      {hasAiData &&
        !isConfirmed &&
        showValidation && (
          <>
            {hasErrors && (
              <div className="ai-completeness-box error">
                <div className="ai-completeness-header">
                  <span className="ai-completeness-icon">
                    ❌
                  </span>

                  <div>
                    <strong>
                      {isVietnamese
                        ? "Cần bổ sung hoặc chỉnh sửa"
                        : "Information needs attention"}
                    </strong>

                    <span>
                      {isVietnamese
                        ? `${errorEntries.length} vấn đề cần xử lý trước khi xác nhận.`
                        : `${errorEntries.length} issue(s) must be fixed before confirmation.`}
                    </span>
                  </div>
                </div>

                <div className="ai-completeness-list">
                  {errorEntries.map(
                    ([
                      field,
                      message,
                    ]) => (
                      <div
                        key={field}
                        className="ai-completeness-item"
                      >
                        <span className="ai-completeness-bullet">
                          •
                        </span>

                        <div>
                          <strong>
                            {FIELD_LABELS[field] ||
                              field}
                          </strong>

                          <span>
                            {message}
                          </span>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {!hasErrors &&
              hasWarnings && (
                <div className="ai-completeness-box warning">
                  <div className="ai-completeness-header">
                    <span className="ai-completeness-icon">
                      ⚠️
                    </span>

                    <div>
                      <strong>
                        {isVietnamese
                          ? "AI đề xuất kiểm tra thêm"
                          : "AI suggests a quick review"}
                      </strong>

                      <span>
                        {isVietnamese
                          ? "Các thông tin dưới đây cần được kiểm tra và xử lý trước khi xác nhận nhật ký."
                          : "The following information must be reviewed and resolved before confirming the log."}
                      </span>
                    </div>
                  </div>

                  <div className="ai-completeness-list">
                    {warningEntries.map(
                      ([
                        field,
                        message,
                      ]) => (
                        <div
                          key={field}
                          className="ai-completeness-item"
                        >
                          <span className="ai-completeness-bullet">
                            •
                          </span>

                          <div>
                            <strong>
                              {FIELD_LABELS[field] ||
                                field}
                            </strong>

                            <span>
                              {message}
                            </span>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}

            {!hasErrors &&
              !hasWarnings && (
                <div className="ai-completeness-box success">
                  <div className="ai-completeness-header">
                    <span className="ai-completeness-icon">
                      ✅
                    </span>

                    <div>
                      <strong>
                        {isVietnamese
                          ? "Đã đủ thông tin để xác nhận"
                          : "Ready for confirmation"}
                      </strong>

                      <span>
                        {isVietnamese
                          ? "Các trường chính đã hợp lệ. Bạn có thể kiểm tra lại và xác nhận nhật ký."
                          : "The main fields are valid. You can review and confirm the log."}
                      </span>
                    </div>
                  </div>
                </div>
              )}
          </>
        )}

      {/* ===========================
          Lot
      =========================== */}

      <div
        className={`ai-field ${getFieldClassName(
          "lot"
        )}`}
      >
        <div className="ai-field-label-row">
          <label htmlFor="lot">
            🏷️ {text.aiForm.lot}

            <span className="required-mark">
              *
            </span>
          </label>

          <FieldStatus field="lot" />
        </div>

        <input
          id="lot"
          type="text"
          placeholder={
            text.aiForm
              .lotPlaceholder
          }
          value={
            aiData.lot || ""
          }
          onChange={(event) =>
            handleChange(
              "lot",
              event.target.value
            )
          }
          readOnly={
            isConfirmed
          }
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

      {/* ===========================
          Work
      =========================== */}

      <div
        className={`ai-field ${getFieldClassName(
          "work"
        )}`}
      >
        <div className="ai-field-label-row">
          <label htmlFor="work">
            🛠️ {text.aiForm.work}

            <span className="required-mark">
              *
            </span>
          </label>

          <FieldStatus field="work" />
        </div>

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
          readOnly={
            isConfirmed
          }
          aria-invalid={
            showValidation &&
            Boolean(
              errors.work
            )
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

      {/* ===========================
          Material
      =========================== */}

      <div
        className={`ai-field ${getFieldClassName(
          "material"
        )}`}
      >
        <div className="ai-field-label-row">
          <label htmlFor="material">
            🌾 {text.aiForm.material}
          </label>

          <FieldStatus field="material" />
        </div>

        <input
          id="material"
          type="text"
          placeholder={
            text.aiForm
              .materialPlaceholder
          }
          value={
            aiData.material ||
            ""
          }
          onChange={(event) =>
            handleChange(
              "material",
              event.target.value
            )
          }
          readOnly={
            isConfirmed
          }
        />

        {showValidation &&
          warnings.material && (
            <span className="field-validation-message warning">
              ⚠️{" "}
              {
                warnings.material
              }
            </span>
          )}
      </div>

      {/* ===========================
          Quantity + Unit
      =========================== */}

      <div className="ai-form-row">
        <div
          className={`ai-field ${getFieldClassName(
            "quantity"
          )}`}
        >
          <div className="ai-field-label-row">
            <label htmlFor="quantity">
              📦{" "}
              {text.aiForm.quantity}
            </label>

            <FieldStatus field="quantity" />
          </div>

          <input
            id="quantity"
            type="number"
            placeholder={
              text.aiForm
                .quantityPlaceholder
            }
            value={
              aiData.quantity ||
              ""
            }
            onChange={(event) =>
              handleChange(
                "quantity",
                event.target.value
              )
            }
            readOnly={
              isConfirmed
            }
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
                {
                  errors.quantity
                }
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
          <div className="ai-field-label-row">
            <label htmlFor="unit">
              ⚖️ {text.aiForm.unit}
            </label>

            <FieldStatus field="unit" />
          </div>

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
            readOnly={
              isConfirmed
            }
            aria-invalid={
              showValidation &&
              Boolean(
                errors.unit
              )
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
                ⚠️{" "}
                {warnings.unit}
              </span>
            )}
        </div>
      </div>

      {/* ===========================
          Time
      =========================== */}

      <div
        className={`ai-field ${getFieldClassName(
          "time"
        )}`}
      >
        <div className="ai-field-label-row">
          <span
            id="time-label"
            className="ai-time-field-label"
          >
            🕒 {text.aiForm.time}
          </span>

          <FieldStatus field="time" />
        </div>

        <TimePicker
          id="time"
          ariaLabelledBy="time-label"
          value={
            aiData.time || ""
          }
          onChange={(value) =>
            handleChange(
              "time",
              value
            )
          }
          disabled={
            isConfirmed
          }
          placeholder="--:--"
          language={
            language
          }
        />

        {showValidation &&
          warnings.time && (
            <span className="field-validation-message warning">
              ⚠️ {warnings.time}
            </span>
          )}
      </div>

      {/* ===========================
          Empty / Editing
      =========================== */}

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
    </div>
  );
}

export default AIForm;