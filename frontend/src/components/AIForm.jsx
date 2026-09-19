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
  const getMaterials = () => {
    if (
      Array.isArray(
        aiData.materials
      ) &&
      aiData.materials.length > 0
    ) {
      return aiData.materials;
    }

    return [
      {
        material: "",
        quantity: "",
        unit: "",
      },
    ];
  };

  const handleMaterialChange = (
    index,
    field,
    value
  ) => {
    const materials =
      getMaterials().map(
        (item) => ({
          ...item,
        })
      );

    materials[index] = {
      ...materials[index],
      [field]: value,
    };

    onAiDataChange({
      ...aiData,
      materials,
    });
  };

  const handleAddMaterial =
    () => {
      onAiDataChange({
        ...aiData,

        materials: [
          ...getMaterials(),

          {
            material: "",
            quantity: "",
            unit: "",
          },
        ],
      });
    };

  const handleRemoveMaterial = (
    index
  ) => {
    const remaining =
      getMaterials().filter(
        (
          _,
          materialIndex
        ) =>
          materialIndex !== index
      );

    onAiDataChange({
      ...aiData,

      materials:
        remaining.length > 0
          ? remaining
          : [
              {
                material: "",
                quantity: "",
                unit: "",
              },
            ],
    });
  };
  /* ===========================
     Data state
  =========================== */

  const hasMaterialData =
    (
      aiData.materials ??
      []
    ).some(
      (item) =>
        Boolean(
          String(
            item?.material ??
            ""
          ).trim() ||
          String(
            item?.quantity ??
            ""
          ).trim() ||
          String(
            item?.unit ??
            ""
          ).trim()
        )
    );

  const hasAiData = Boolean(
    aiData.lot ||
      aiData.work ||
      hasMaterialData ||
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
  const getFieldLabel = (
    field
  ) => {
    const match =
      String(field).match(
        /^materials\.(\d+)\.(material|quantity|unit)$/
      );

    if (!match) {
      return (
        FIELD_LABELS[field] ||
        field
      );
    }

    const number =
      Number(match[1]) + 1;

    const child =
      match[2];

    const childLabel = {
      material:
        isVietnamese
          ? "Vật tư"
          : "Material",

      quantity:
        isVietnamese
          ? "Số lượng"
          : "Quantity",

      unit:
        isVietnamese
          ? "Đơn vị"
          : "Unit",
    }[child];

    return (
      `${childLabel} ${number}`
    );
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

    const legacyHighlightMap = {
      material:
        "materials.0.material",

      quantity:
        "materials.0.quantity",

      unit:
        "materials.0.unit",
    };

    if (
      highlightedField === field ||
      legacyHighlightMap[
        highlightedField
      ] === field
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
    const materialMatch =
      String(field).match(
        /^materials\.(\d+)\.(material|quantity|unit)$/
      );

    if (materialMatch) {
      const index =
        Number(
          materialMatch[1]
        );

      const childField =
        materialMatch[2];

      const value =
        aiData.materials?.[
          index
        ]?.[childField];

      return (
        value !== null &&
        value !== undefined &&
        String(value).trim() !==
          ""
      );
    }

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

  const renderFieldStatus = (
    field
  ) => {
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
                            {getFieldLabel(
                              field
                            )}
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
                              {getFieldLabel(
                                field
                              )}
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

          {renderFieldStatus("lot")}
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

          {renderFieldStatus("work")}
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
          Materials
      =========================== */}

      <div className="ai-materials-section">
        <div className="ai-materials-header">
          <strong>
            🌾{" "}
            {isVietnamese
              ? "Vật tư sử dụng"
              : "Materials used"}
          </strong>

          {!isConfirmed && (
            <button
              type="button"
              className="btn-add-material"
              onClick={
                handleAddMaterial
              }
            >
              ＋{" "}
              {isVietnamese
                ? "Thêm vật tư"
                : "Add material"}
            </button>
          )}
        </div>

        {getMaterials().map(
          (
            materialItem,
            index
          ) => {
            const materialField =
              `materials.${index}.material`;

            const quantityField =
              `materials.${index}.quantity`;

            const unitField =
              `materials.${index}.unit`;

            return (
              <div
                key={index}
                className="ai-material-card"
              >
                <div className="ai-material-card-header">
                  <strong>
                    {isVietnamese
                      ? `Vật tư ${index + 1}`
                      : `Material ${index + 1}`}
                  </strong>

                  {!isConfirmed &&
                    getMaterials()
                      .length > 1 && (
                      <button
                        type="button"
                        className="btn-remove-material"
                        onClick={() =>
                          handleRemoveMaterial(
                            index
                          )
                        }
                      >
                        ✕{" "}
                        {isVietnamese
                          ? "Xóa"
                          : "Remove"}
                      </button>
                    )}
                </div>

                <div
                  className={`ai-field ${getFieldClassName(
                    materialField
                  )}`}
                >
                  <div className="ai-field-label-row">
                    <label
                      htmlFor={
                        materialField
                      }
                    >
                      🌾{" "}
                      {text.aiForm.material}
                    </label>

                    {renderFieldStatus(
                      materialField
                    )}
                  </div>

                  <input
                    id={
                      materialField
                    }
                    type="text"
                    placeholder={
                      text.aiForm
                        .materialPlaceholder
                    }
                    value={
                      materialItem
                        .material || ""
                    }
                    onChange={(
                      event
                    ) =>
                      handleMaterialChange(
                        index,
                        "material",
                        event.target.value
                      )
                    }
                    readOnly={
                      isConfirmed
                    }
                    aria-invalid={
                      showValidation &&
                      Boolean(
                        errors[
                          materialField
                        ]
                      )
                    }
                  />

                  {showValidation &&
                    errors[
                      materialField
                    ] && (
                      <span className="field-validation-message error">
                        ❌{" "}
                        {
                          errors[
                            materialField
                          ]
                        }
                      </span>
                    )}

                  {showValidation &&
                    warnings[
                      materialField
                    ] &&
                    !errors[
                      materialField
                    ] && (
                      <span className="field-validation-message warning">
                        ⚠️{" "}
                        {
                          warnings[
                            materialField
                          ]
                        }
                      </span>
                    )}
                </div>

                <div className="ai-form-row">
                  <div
                    className={`ai-field ${getFieldClassName(
                      quantityField
                    )}`}
                  >
                    <div className="ai-field-label-row">
                      <label
                        htmlFor={
                          quantityField
                        }
                      >
                        📦{" "}
                        {
                          text.aiForm
                            .quantity
                        }
                      </label>

                      {renderFieldStatus(
                        quantityField
                      )}
                    </div>

                    <input
                      id={
                        quantityField
                      }
                      type="number"
                      placeholder={
                        text.aiForm
                          .quantityPlaceholder
                      }
                      value={
                        materialItem
                          .quantity ?? ""
                      }
                      onChange={(
                        event
                      ) =>
                        handleMaterialChange(
                          index,
                          "quantity",
                          event.target
                            .value
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
                          errors[
                            quantityField
                          ]
                        )
                      }
                    />

                    {showValidation &&
                      errors[
                        quantityField
                      ] && (
                        <span className="field-validation-message error">
                          ❌{" "}
                          {
                            errors[
                              quantityField
                            ]
                          }
                        </span>
                      )}

                    {showValidation &&
                      warnings[
                        quantityField
                      ] &&
                      !errors[
                        quantityField
                      ] && (
                        <span className="field-validation-message warning">
                          ⚠️{" "}
                          {
                            warnings[
                              quantityField
                            ]
                          }
                        </span>
                      )}
                  </div>

                  <div
                    className={`ai-field ${getFieldClassName(
                      unitField
                    )}`}
                  >
                    <div className="ai-field-label-row">
                      <label
                        htmlFor={
                          unitField
                        }
                      >
                        ⚖️{" "}
                        {text.aiForm.unit}
                      </label>

                      {renderFieldStatus(
                        unitField
                      )}
                    </div>

                    <input
                      id={
                        unitField
                      }
                      type="text"
                      placeholder={
                        text.aiForm
                          .unitPlaceholder
                      }
                      value={
                        materialItem
                          .unit || ""
                      }
                      onChange={(
                        event
                      ) =>
                        handleMaterialChange(
                          index,
                          "unit",
                          event.target
                            .value
                        )
                      }
                      readOnly={
                        isConfirmed
                      }
                      aria-invalid={
                        showValidation &&
                        Boolean(
                          errors[
                            unitField
                          ]
                        )
                      }
                    />

                    {showValidation &&
                      errors[
                        unitField
                      ] && (
                        <span className="field-validation-message error">
                          ❌{" "}
                          {
                            errors[
                              unitField
                            ]
                          }
                        </span>
                      )}

                    {showValidation &&
                      warnings[
                        unitField
                      ] &&
                      !errors[
                        unitField
                      ] && (
                        <span className="field-validation-message warning">
                          ⚠️{" "}
                          {
                            warnings[
                              unitField
                            ]
                          }
                        </span>
                      )}
                  </div>
                </div>
              </div>
            );
          }
        )}
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

          {renderFieldStatus("time")}
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
          errors.time && (
            <span className="field-validation-message error">
              ❌ {errors.time}
            </span>
          )}

        {showValidation &&
          warnings.time &&
          !errors.time && (
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