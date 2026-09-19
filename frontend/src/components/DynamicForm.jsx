import {
  getDynamicFormFieldText,
  getDynamicFormOptionText,
  getDynamicFormTemplate,
} from "../constants/dynamicFormTemplates";

function DynamicForm({
  operation,
  dynamicForm,
  onFieldsChange,
  isConfirmed = false,
  showValidation = false,
  language = "vi",
}) {
  const template =
    getDynamicFormTemplate(operation);

  const fields =
    dynamicForm?.fields ?? {};

  const isVietnamese =
    language === "vi";

  const missingFields =
    dynamicForm?.missing_fields ?? [];

  const warnings =
    Array.isArray(dynamicForm?.warnings)
      ? dynamicForm.warnings
      : [];

  const globalWarnings = warnings.filter(
    (warning) => warning?.field === null
  );

  const fieldConfidence =
    dynamicForm?.field_confidence &&
    typeof dynamicForm.field_confidence === "object"
      ? dynamicForm.field_confidence
      : {};

  const getFieldValueByPath = (
    fieldPath
  ) => {
    const materialMatch =
      /^materials\[(\d+)\]\.(.+)$/.exec(
        fieldPath
      );

    if (materialMatch) {
      const materialIndex =
        Number(materialMatch[1]);

      const materialField =
        materialMatch[2];

      return Array.isArray(
        fields.materials
      )
        ? fields.materials[
            materialIndex
          ]?.[materialField]
        : undefined;
    }

    return fields[fieldPath];
  };

  const hasFieldValue = (
    value
  ) => {
    if (typeof value === "string") {
      return value.trim().length > 0;
    }

    return value !== null &&
      value !== undefined;
  };

  const isFieldMissing = (
    fieldPath
  ) =>
    missingFields.includes(fieldPath) &&
    !hasFieldValue(
      getFieldValueByPath(fieldPath)
    );

  const getFieldWarning = (
    fieldPath
  ) =>
    warnings.find(
      (warning) =>
        warning?.field === fieldPath
    ) ?? null;

  const getFieldConfidence = (
    fieldPath
  ) => {
    const confidence =
      fieldConfidence[fieldPath];

    return typeof confidence === "number" &&
      Number.isFinite(confidence)
      ? confidence
      : null;
  };

  const getFieldClassName = (
    fieldPath
  ) => {
    if (showValidation && isFieldMissing(fieldPath)) {
      return "ai-field validation-error";
    }

    if (getFieldWarning(fieldPath)) {
      return "ai-field validation-warning";
    }

    const confidence =
      getFieldConfidence(fieldPath);

    if (
      confidence !== null &&
      confidence < 0.85
    ) {
      return "ai-field validation-warning";
    }

    return "ai-field";
  };

  const renderMissingMessage = (
    fieldPath
  ) => {
    if (showValidation && isFieldMissing(fieldPath)) {
      return (
        <p className="field-validation-message error">
          {isVietnamese
            ? "Trường bắt buộc còn thiếu."
            : "Required field is missing."}
        </p>
      );
    }

    const warning =
      getFieldWarning(fieldPath);

    if (warning?.message) {
      return (
        <p className="field-validation-message warning">
          {warning.message}
        </p>
      );
    }

    const confidence =
      getFieldConfidence(fieldPath);

    if (
      confidence === null ||
      confidence >= 0.85
    ) {
      return null;
    }

    const confidencePercent =
      Math.round(confidence * 100);

    return (
      <p className="field-validation-message warning">
        {confidence < 0.6
          ? isVietnamese
            ? `Độ tin cậy thấp (${confidencePercent}%). Cần kiểm tra lại.`
            : `Low confidence (${confidencePercent}%). Please review.`
          : isVietnamese
            ? `Độ tin cậy ${confidencePercent}%. Nên kiểm tra lại.`
            : `Confidence ${confidencePercent}%. Please review.`}
      </p>
    );
  };

  if (!template) {
    return (
      <div className="ai-form">
        <p className="ai-hint">
          {isVietnamese
            ? "Không tìm thấy mẫu biểu cho nghiệp vụ này."
            : "No form template was found for this operation."}
        </p>
      </div>
    );
  }

  const updateField = (
    fieldName,
    value
  ) => {
    onFieldsChange?.({
      ...fields,
      [fieldName]: value,
    });
  };

  const getMaterials = () =>
    Array.isArray(fields.materials)
      ? fields.materials
      : [];

  const updateMaterial = (
    index,
    fieldName,
    value
  ) => {
    const nextMaterials = [
      ...getMaterials(),
    ];

    nextMaterials[index] = {
      ...nextMaterials[index],
      [fieldName]: value,
    };

    updateField(
      "materials",
      nextMaterials
    );
  };

  const addMaterial = () => {
    updateField("materials", [
      ...getMaterials(),
      {
        material_text: null,
        quantity: null,
        unit_text: null,
      },
    ]);
  };

  const removeMaterial = (
    index
  ) => {
    updateField(
      "materials",
      getMaterials().filter(
        (_, itemIndex) =>
          itemIndex !== index
      )
    );
  };

  const renderLabel = (
    field
  ) => (
    <label htmlFor={field.name}>
      {getDynamicFormFieldText(
        field.name,
        language
      )}
      {field.required && (
        <span
          className="required-mark"
          aria-hidden="true"
        >
          {" *"}
        </span>
      )}
    </label>
  );

  const renderStandardField = (
    field
  ) => {
    const value =
      fields[field.name];

    if (field.type === "textarea") {
      return (
        <div
          key={field.name}
          className={getFieldClassName(
            field.name
          )}
        >
          {renderLabel(field)}

          <textarea
            id={field.name}
            value={value ?? ""}
            onChange={(event) =>
              updateField(
                field.name,
                event.target.value
              )
            }
            readOnly={isConfirmed}
            rows={4}
          />

          {renderMissingMessage(field.name)}
        </div>
      );
    }

    if (field.type === "select") {
      return (
        <div
          key={field.name}
          className={getFieldClassName(
            field.name
          )}
        >
          {renderLabel(field)}

          <select
            id={field.name}
            value={value ?? ""}
            onChange={(event) =>
              updateField(
                field.name,
                event.target.value ||
                  null
              )
            }
            disabled={isConfirmed}
          >
            <option value="">
              {isVietnamese
                ? "-- Chọn --"
                : "-- Select --"}
            </option>

            {field.options?.map(
              (option) => (
                <option
                  key={option}
                  value={option}
                >
                  {getDynamicFormOptionText(
                    field.name,
                    option,
                    language
                  )}
                </option>
              )
            )}
          </select>

          {renderMissingMessage(field.name)}
        </div>
      );
    }

    if (field.type === "boolean") {
      return (
        <div
          key={field.name}
          className={getFieldClassName(
            field.name
          )}
        >
          {renderLabel(field)}

          <select
            id={field.name}
            value={
              value === true
                ? "true"
                : value === false
                  ? "false"
                  : ""
            }
            onChange={(event) => {
              const nextValue =
                event.target.value;

              updateField(
                field.name,
                nextValue === ""
                  ? null
                  : nextValue ===
                      "true"
              );
            }}
            disabled={isConfirmed}
          >
            <option value="">
              {isVietnamese
                ? "-- Chưa xác định --"
                : "-- Not specified --"}
            </option>

            <option value="true">
              {isVietnamese
                ? "Có"
                : "Yes"}
            </option>

            <option value="false">
              {isVietnamese
                ? "Không"
                : "No"}
            </option>
          </select>

          {renderMissingMessage(field.name)}
          {field.name === "photo_required" && (
            <div
              className={
                value === true
                  ? "confirm-helper warning"
                  : "ai-hint"
              }
            >
              <span aria-hidden="true">
                📷
              </span>

              <span>
                {value === true
                  ? isVietnamese
                    ? "Nghiệp vụ này yêu cầu ảnh. Contract V3.1 hiện chưa định nghĩa payload hoặc API tải ảnh, nên ảnh chưa được chọn hoặc gửi từ frontend."
                    : "This operation requires a photo. Contract V3.1 does not yet define a photo payload or upload API, so no image is selected or submitted from the frontend yet."
                  : value === false
                    ? isVietnamese
                      ? "Nghiệp vụ này hiện không yêu cầu ảnh."
                      : "This operation currently does not require a photo."
                    : isVietnamese
                      ? "Chưa xác định nghiệp vụ này có yêu cầu ảnh hay không."
                      : "It has not been specified whether this operation requires a photo."}
              </span>
            </div>
          )}
        </div>
      );
    }

    return (
      <div
        key={field.name}
        className={getFieldClassName(
          field.name
        )}
      >
        {renderLabel(field)}

        <input
          id={field.name}
          type={
            field.type === "number"
              ? "number"
              : "text"
          }
          value={value ?? ""}
          onChange={(event) => {
            const rawValue =
              event.target.value;

            if (
              field.type === "number"
            ) {
              updateField(
                field.name,
                rawValue === ""
                  ? null
                  : Number(rawValue)
              );

              return;
            }

            updateField(
              field.name,
              rawValue
            );
          }}
          readOnly={isConfirmed}
          min={
            field.type === "number"
              ? "0"
              : undefined
          }
          step={
            field.type === "number"
              ? "any"
              : undefined
          }
        />

        {renderMissingMessage(field.name)}
      </div>
    );
  };

  const renderMaterials = (
    field
  ) => {
    const materials =
      getMaterials();

    return (
      <div
        key={field.name}
        className="materials-section"
      >
        <div className="materials-header">
          <div>
            <span className="materials-title">
              {getDynamicFormFieldText(
                "materials",
                language
              )}
            </span>

            <p className="ai-hint">
              {isVietnamese
                ? "Nếu có sử dụng vật tư, hãy nhập đủ tên, số lượng và đơn vị."
                : "If materials were used, enter the name, quantity, and unit."}
            </p>
          </div>

          {!isConfirmed && (
            <button
              type="button"
              className="material-add-button"
              onClick={addMaterial}
            >
              +{" "}
              {isVietnamese
                ? "Thêm vật tư"
                : "Add material"}
            </button>
          )}
        </div>

        {materials.length === 0 && (
          <p className="ai-hint">
            {isVietnamese
              ? "Chưa có vật tư."
              : "No materials added."}
          </p>
        )}

        {materials.map(
          (
            material,
            index
          ) => (
            <div
              key={index}
              className="material-card"
            >
              <div className="material-card-header">
                <strong>
                  {isVietnamese
                    ? `Vật tư ${index + 1}`
                    : `Material ${index + 1}`}
                </strong>

                {!isConfirmed && (
                  <button
                    type="button"
                    className="material-remove-button"
                    onClick={() =>
                      removeMaterial(
                        index
                      )
                    }
                  >
                    {isVietnamese
                      ? "Xóa"
                      : "Remove"}
                  </button>
                )}
              </div>

              <div className="material-grid">
                <div
                  className={getFieldClassName(
                    `materials[${index}].material_text`
                  )}
                >
                  <label
                    htmlFor={`materials.${index}.material_text`}
                  >
                    {getDynamicFormFieldText(
                      "material_text",
                      language
                    )}
                  </label>

                  <input
                    id={`materials.${index}.material_text`}
                    type="text"
                    value={
                      material
                        ?.material_text ??
                      ""
                    }
                    onChange={(
                      event
                    ) =>
                      updateMaterial(
                        index,
                        "material_text",
                        event.target
                          .value
                      )
                    }
                    readOnly={
                      isConfirmed
                    }
                  />

                  {renderMissingMessage(
                    `materials[${index}].material_text`
                  )}
                </div>

                <div
                  className={getFieldClassName(
                    `materials[${index}].quantity`
                  )}
                >
                  <label
                    htmlFor={`materials.${index}.quantity`}
                  >
                    {getDynamicFormFieldText(
                      "quantity",
                      language
                    )}
                  </label>

                  <input
                    id={`materials.${index}.quantity`}
                    type="number"
                    min="0"
                    step="any"
                    value={
                      material
                        ?.quantity ??
                      ""
                    }
                    onChange={(
                      event
                    ) =>
                      updateMaterial(
                        index,
                        "quantity",
                        event.target
                          .value === ""
                          ? null
                          : Number(
                              event
                                .target
                                .value
                            )
                      )
                    }
                    readOnly={
                      isConfirmed
                    }
                  />

                  {renderMissingMessage(
                    `materials[${index}].quantity`
                  )}
                </div>

                <div
                  className={getFieldClassName(
                    `materials[${index}].unit_text`
                  )}
                >
                  <label
                    htmlFor={`materials.${index}.unit_text`}
                  >
                    {getDynamicFormFieldText(
                      "unit_text",
                      language
                    )}
                  </label>

                  <input
                    id={`materials.${index}.unit_text`}
                    type="text"
                    value={
                      material
                        ?.unit_text ??
                      ""
                    }
                    onChange={(
                      event
                    ) =>
                      updateMaterial(
                        index,
                        "unit_text",
                        event.target
                          .value
                      )
                    }
                    readOnly={
                      isConfirmed
                    }
                  />

                  {renderMissingMessage(
                    `materials[${index}].unit_text`
                  )}
                </div>
              </div>
            </div>
          )
        )}
      </div>
    );
  };

  return (
    <div className="ai-form dynamic-form">
      <div className="ai-form-header">
        <div>
          <h3>
            🤖{" "}
            {isVietnamese
              ? "Dữ liệu biểu mẫu"
              : "Form data"}
          </h3>

          <p className="ai-hint">
            {dynamicForm?.template_id ??
              template.templateId}
          </p>
        </div>

        <span className="ai-badge">
          {isConfirmed
            ? isVietnamese
              ? "Đã xác nhận"
              : "Confirmed"
            : isVietnamese
              ? "Có thể chỉnh sửa"
              : "Editable"}
        </span>
      </div>

      {dynamicForm?.next_question && (
        <div className="ai-hint dynamic-form-next-question">
          <strong>
            {isVietnamese
              ? "Câu hỏi tiếp theo:"
              : "Next question:"}
          </strong>{" "}
          {dynamicForm.next_question}
        </div>
      )}

      {globalWarnings.length > 0 && (
        <div className="confirm-helper warning">
          <span aria-hidden="true">⚠️</span>
          <div>
            {globalWarnings.map((warning, index) => (
              <div
                key={`${warning?.code ?? "global"}-${index}`}
              >
                {warning.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {dynamicForm?.requires_confirmation === true &&
        !isConfirmed && (
          <div className="confirm-helper warning">
            <span aria-hidden="true">⚠️</span>
            <span>
              {isVietnamese
                ? "AI yêu cầu bạn kiểm tra và xác nhận dữ liệu này trước khi lưu."
                : "AI requires you to review and confirm this data before saving."}
            </span>
          </div>
        )}

      <div className="dynamic-form-fields">
        {template.fields.map(
          (field) =>
            field.type ===
            "materials"
              ? renderMaterials(
                  field
                )
              : renderStandardField(
                  field
                )
        )}
      </div>

      {operation === "CREATE_PLOT" && (
        <div className="ai-field dynamic-form-map-shell">
          <div className="ai-field-label-row">
            <span className="ai-field-label">
              {isVietnamese
                ? "Bản đồ ranh giới thửa đất"
                : "Plot boundary map"}
            </span>
          </div>

          <div className="confirm-helper warning">
            <span aria-hidden="true">
              🗺️
            </span>

            <span>
              {isVietnamese
                ? "Ranh giới thửa đất phải được thực hiện trên bản đồ. Contract V3.1 hiện chưa định nghĩa dữ liệu tọa độ hoặc geometry để lưu, nên phần này chưa tạo hoặc gửi dữ liệu ranh giới."
                : "The plot boundary must be handled on a map. Contract V3.1 does not yet define coordinate or geometry data for saving, so this section does not create or submit boundary data yet."}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default DynamicForm;