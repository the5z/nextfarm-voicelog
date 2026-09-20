import {
  useEffect,
  useState,
} from "react";

import {
  generateId,
} from "../utils/id";

import Header from "../components/Header";
import WorkflowStepper from "../components/WorkflowStepper";
import RecordButton from "../components/RecordButton";
import TranscriptBox from "../components/TranscriptBox";
import ActionButtons from "../components/ActionButtons";
import OperationSelector from "../components/OperationSelector";
import DynamicForm from "../components/DynamicForm";

import { uploadAudio } from "../services/audioService";
import {
  resolveMasterData,
  validateCultivationLog,
  saveCultivationLog,
  updateCultivationLog,
  saveDynamicOperation,
} from "../services/integrationService";
import { TEXT } from "../constants/translations";
import {
  DEFAULT_OPERATION,
} from "../constants/dynamicFormOperations";
import {
  createEmptyDynamicForm,
} from "../utils/dynamicFormState";
import {
  getDynamicFormTemplate,
} from "../constants/dynamicFormTemplates";

const createEmptyMaterial = () => ({
  material: "",
  quantity: "",
  unit: "",
});

const createEmptyAiData = () => ({
  lot: "",
  work: "",

  materials: [
    createEmptyMaterial(),
  ],

  time: "",
});

const normalizeMaterials = (
  materials
) => {
  if (
    !Array.isArray(materials) ||
    materials.length === 0
  ) {
    return [
      createEmptyMaterial(),
    ];
  }

  return materials.map(
    (item) => ({
      material:
        String(
          item?.material ??
          item?.material_text ??
          ""
        ),

      quantity:
        item?.quantity ??
        "",

      unit:
        String(
          item?.unit ??
          item?.unit_text ??
          ""
        ),
    })
  );
};

function buildPerformedAt(
  timeText,
  dateText = null
) {
  const normalizedTime =
    String(timeText || "").trim();

  const timeMatch =
    normalizedTime.match(
      /^([01]?\d|2[0-3]):([0-5]\d)$/
    );

  if (!timeMatch) {
    return null;
  }

  const performedAt =
    new Date();

  const normalizedDate =
    String(dateText || "").trim();

  const dateMatch =
    normalizedDate.match(
      /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/
    );

  if (dateMatch) {
    performedAt.setFullYear(
      Number(dateMatch[3]),
      Number(dateMatch[2]) - 1,
      Number(dateMatch[1])
    );
  }

  performedAt.setHours(
    Number(timeMatch[1]),
    Number(timeMatch[2]),
    0,
    0
  );

  return performedAt.toISOString();
}

function validateDynamicOperationFields(
  operation,
  fields,
  isVietnamese
) {
  const template =
    getDynamicFormTemplate(
      operation
    );

  const errors = {};

  if (!template) {
    errors._general =
      isVietnamese
        ? "Không tìm thấy mẫu biểu cho nghiệp vụ này."
        : "No form template was found for this operation.";

    return errors;
  }

  template.fields.forEach(
    (field) => {
      const value =
        fields?.[field.name];

      const hasValue =
        typeof value === "string"
          ? value.trim() !== ""
          : value !== null &&
            value !== undefined;

      if (
        field.required &&
        !hasValue
      ) {
        errors[field.name] =
          isVietnamese
            ? "Trường bắt buộc còn thiếu."
            : "Required field is missing.";

        return;
      }

      if (
        field.type === "number" &&
        hasValue &&
        (
          !Number.isFinite(
            Number(value)
          ) ||
          Number(value) <= 0
        )
      ) {
        errors[field.name] =
          isVietnamese
            ? "Giá trị phải là số lớn hơn 0."
            : "Value must be a number greater than 0.";
      }
    }
  );

  return errors;
}

const DEV_VALID_DATA = {
  transcript:
    "Hôm nay tôi bón 20 kg phân NPK cho lô A01 lúc 8 giờ 30.",

  structuredData: {
    lot: "A01",

    work: "Bón phân",

    materials: [
      {
        material: "Phân NPK",
        quantity: "20",
        unit: "kg",
      },
    ],

    time: "08:30",
  },
};

const DEV_ERROR_DATA = {
  transcript:
    "Hôm nay tôi thực hiện công việc nhưng thông tin nhận dạng chưa đầy đủ.",

  structuredData: {
    lot: "",
    work: "",

    materials: [
      {
        material: "Phân NPK",
        quantity: "0",
        unit: "",
      },
    ],

    time: "",
  },
};

const DEV_WARNING_DATA = {
  transcript:
    "Hôm nay tôi bón 20 kg phân NPK cho lô A01 lúc 8 giờ 30.",

  structuredData: {
    lot: "A01",

    work: "Bón phân",

    materials: [
      {
        material: "Phân NPK",
        quantity: "20",
        unit: "kg",
      },
    ],

    time: "08:30",
  },

  /*
   * Chỉ dùng trong DEV Test Mode để kiểm tra WARNING nhẹ.
   * Không yêu cầu acknowledgement và KHÔNG phải ngưỡng nghiệp vụ.
   */
  dynamicFormWarnings: [
    {
      field: null,
      code: "DEV_GLOBAL_WARNING",
      message:
        "🧪 Cảnh báo Dynamic Form DEV: warning toàn form.",
    },
  ],

  simulateWarning: {
    field:
      "materials.0.quantity",

    message:
      "🧪 Cảnh báo mô phỏng DEV: đây là warning nhẹ, không chặn xác nhận.",

    requiresConfirmation:
      false,
  },
};

function VoiceLog({
  language = "vi",
  onLanguageChange,

  themeMode = "light",
  onThemeChange,

  logToEdit = null,
  onLogLoaded,

  onSaveLog,

  autoValidation = true,

  onAiDataChange,
  externalAiChanges = null,
  onExternalAiChangesApplied,
  highlightedField = "",
  onHighlightClear,
  logs = [],
}) {
  const t =
    TEXT[language];

  const isVietnamese =
    language === "vi";

  /* ===========================
     Dynamic Form Operation
  =========================== */

  const [
    operation,
    setOperation,
  ] = useState(
    DEFAULT_OPERATION
  );

  const [
    dynamicForm,
    setDynamicForm,
  ] = useState(() =>
    createEmptyDynamicForm(
      DEFAULT_OPERATION
    )
  );

  /* ===========================
     Audio
  =========================== */

  const [
    audioUrl,
    setAudioUrl,
  ] = useState(null);

  const [
    audioBlob,
    setAudioBlob,
  ] = useState(null);

  /* ===========================
     AI Data
  =========================== */

  const [
    transcript,
    setTranscript,
  ] = useState("");

  const [
    aiData,
    setAiData,
  ] = useState(
    createEmptyAiData
  );

  /* ===========================
     Workflow
  =========================== */

  const [
    isUploading,
    setIsUploading,
  ] = useState(false);

  const [
    isConfirmed,
    setIsConfirmed,
  ] = useState(false);

  const [
    hasAttemptedSubmit,
    setHasAttemptedSubmit,
  ] = useState(false);

  /*
   * Warning phải được người dùng xác nhận đã kiểm tra trước khi lưu.
   * Giá trị này luôn reset khi dữ liệu form thay đổi.
   */
  const [
    warningAcknowledged,
    setWarningAcknowledged,
  ] = useState(false);

  /*
   * Chỉ dùng cho nút "Dữ liệu cảnh báo" trong DEV Test Mode.
   * Không phải business threshold production.
   */
  const [
    devWarning,
    setDevWarning,
  ] = useState(null);

  /*
   * Validation trả về từ Integration Service.
   * Frontend chỉ phản ánh canonical business rules từ backend.
   */
  const [
    serverValidation,
    setServerValidation,
  ] = useState({
    errors: {},
    warnings: {},
    requiresConfirmation: false,
    ruleVersion: null,
  });

  const [
    message,
    setMessage,
  ] = useState(null);

  const [
    currentStep,
    setCurrentStep,
  ] = useState(1);


  const showMessage = (
    type,
    text
  ) => {
    setMessage({
      type,
      text,
    });
  };

  const clearServerValidation =
    () => {
      setServerValidation({
        errors: {},
        warnings: {},
        requiresConfirmation: false,
        ruleVersion: null,
      });
    };

  /* ===========================
     Sync AI data to App
  =========================== */

  useEffect(() => {
    const firstMaterial =
      aiData.materials?.[0] ??
      createEmptyMaterial();

    /*
      material / quantity / unit
      chỉ là compatibility fields
      cho chatbot cũ.

      materials[] mới là nguồn
      dữ liệu chính.
    */
    onAiDataChange?.({
      ...aiData,

      material:
        firstMaterial.material ??
        "",

      quantity:
        firstMaterial.quantity ??
        "",

      unit:
        firstMaterial.unit ??
        "",
    });
  }, [
    aiData,
    onAiDataChange,
  ]);

  useEffect(() => {
    // Intentional reset when legacy AI form data changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setWarningAcknowledged(false);
    clearServerValidation();
  }, [
    aiData.lot,
    aiData.work,
    aiData.materials,
    aiData.time,
  ]);

  /* ===========================
     Apply external AI edits
  =========================== */

  useEffect(() => {
    if (
      !externalAiChanges ||
      Object.keys(
        externalAiChanges
      ).length === 0
    ) {
      return;
    }

    // Intentional prop-to-local-state synchronization for legacy AI edits.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAiData(
      (previous) => {
        const next = {
          ...previous,
          ...externalAiChanges,
        };

        const hasMaterialChange =
          Object.prototype
            .hasOwnProperty.call(
              externalAiChanges,
              "material"
            );

        const hasQuantityChange =
          Object.prototype
            .hasOwnProperty.call(
              externalAiChanges,
              "quantity"
            );

        const hasUnitChange =
          Object.prototype
            .hasOwnProperty.call(
              externalAiChanges,
              "unit"
            );

        if (
          hasMaterialChange ||
          hasQuantityChange ||
          hasUnitChange
        ) {
          const materials =
            normalizeMaterials(
              previous.materials
            );

          const firstMaterial = {
            ...materials[0],
          };

          if (hasMaterialChange) {
            firstMaterial.material =
              externalAiChanges
                .material ?? "";
          }

          if (hasQuantityChange) {
            firstMaterial.quantity =
              externalAiChanges
                .quantity ?? "";
          }

          if (hasUnitChange) {
            firstMaterial.unit =
              externalAiChanges
                .unit ?? "";
          }

          next.materials = [
            firstMaterial,
            ...materials.slice(1),
          ];
        }

        /*
          Không lưu legacy fields
          trong state chính.
        */
        delete next.material;
        delete next.quantity;
        delete next.unit;

        next.materials =
          normalizeMaterials(
            next.materials
          );

        return next;
      }
    );

    setIsConfirmed(false);
    setWarningAcknowledged(false);
    setDevWarning(null);
    setCurrentStep(3);

    if (autoValidation) {
      setHasAttemptedSubmit(true);
    }

    showMessage(
      "success",
      isVietnamese
        ? "🤖 NextFarm AI đã cập nhật dữ liệu nhật ký."
        : "🤖 NextFarm AI updated the farming log data."
    );

    onExternalAiChangesApplied?.();
  }, [
    externalAiChanges,
    autoValidation,
    isVietnamese,
    onExternalAiChangesApplied,
  ]);

  useEffect(() => {
    if (!highlightedField) {
      return;
    }

    const timer =
      window.setTimeout(() => {
        onHighlightClear?.();
      }, 1800);

    return () => {
      window.clearTimeout(
        timer
      );
    };
  }, [
    highlightedField,
    onHighlightClear,
  ]);

  /* ===========================
     Current Log
  =========================== */

  const [
    currentLogId,
    setCurrentLogId,
  ] = useState(null);

  const [
    isEditingExistingLog,
    setIsEditingExistingLog,
  ] = useState(false);

  const [
    currentLogDate,
    setCurrentLogDate,
  ] = useState(null);

  const [
    editingStatus,
    setEditingStatus,
  ] = useState(null);

  const isDevMode =
    import.meta.env.DEV;

  /* ===========================
     Message
  =========================== */


  const getMessageText = () => {
    if (!message) {
      return "";
    }

    if (
      typeof message ===
      "string"
    ) {
      return message;
    }

    return (
      message.text || ""
    );
  };

  const getMessageType = () => {
    if (!message) {
      return "success";
    }

    if (
      typeof message ===
      "object"
    ) {
      return (
        message.type ||
        "success"
      );
    }

    const warningKeywords = [
      "cảnh báo",
      "Cảnh báo",
      "warning",
      "Warning",
    ];

    if (
      warningKeywords.some(
        (keyword) =>
          message.includes(
            keyword
          )
      )
    ) {
      return "warning";
    }

    const keywords = [
      "Không thể",
      "Vui lòng",
      "lỗi",
      "Unable",
      "Please",
      "error",
    ];

    return keywords.some(
      (keyword) =>
        message.includes(
          keyword
        )
    )
      ? "error"
      : "success";
  };


  const mapIntegrationFieldToUi = (
    field
  ) => {
    const normalized =
      String(
        field || ""
      );

    if (
      normalized === "lot_code" ||
      normalized === "lot"
    ) {
      return "lot";
    }

    if (
      normalized ===
        "activity_code" ||
      normalized === "activity"
    ) {
      return "work";
    }

    if (
      normalized ===
        "performed_at" ||
      normalized === "time"
    ) {
      return "time";
    }

    /*
      ==========================
      Multi-material fields
      ==========================

      Hỗ trợ các dạng backend có thể trả:

      materials.0.material_code
      materials.0.quantity
      materials.0.unit_code

      hoặc:

      materials[0].material_code
      materials[0].quantity
      materials[0].unit_code
    */
    const materialMatch =
      normalized.match(
        /^materials(?:\[(\d+)\]|\.(\d+))\.(.+)$/
      );

    if (materialMatch) {
      const index =
        materialMatch[1] ??
        materialMatch[2];

      const childField =
        materialMatch[3];

      if (
        childField.includes(
          "material"
        )
      ) {
        return (
          `materials.${index}.material`
        );
      }

      if (
        childField.includes(
          "quantity"
        )
      ) {
        return (
          `materials.${index}.quantity`
        );
      }

      if (
        childField.includes(
          "unit"
        )
      ) {
        return (
          `materials.${index}.unit`
        );
      }
    }

    /*
      Backend báo chung cả materials[]
    */
    if (
      normalized === "materials"
    ) {
      return "materials";
    }

    /*
      Fallback cho response cũ
      chưa có index.

      Tạm map về vật tư đầu tiên.
    */
    if (
      normalized.includes(
        "material_code"
      ) ||
      normalized === "material"
    ) {
      return (
        "materials.0.material"
      );
    }

    if (
      normalized.includes(
        "quantity"
      )
    ) {
      return (
        "materials.0.quantity"
      );
    }

    if (
      normalized.includes(
        "unit_code"
      ) ||
      normalized === "unit"
    ) {
      return (
        "materials.0.unit"
      );
    }

    return "_general";
  };

  const normalizeIntegrationIssues = (
    issues
  ) => {
    const mapped = {};

    for (const issue of (
      Array.isArray(issues)
        ? issues
        : []
    )) {
      const message =
        typeof issue === "string"
          ? issue
          : (
              issue?.message ||
              issue?.detail ||
              issue?.code ||
              ""
            );

      if (!message) {
        continue;
      }

      const field =
        mapIntegrationFieldToUi(
          typeof issue === "string"
            ? ""
            : issue?.field
        );

      mapped[field] =
        mapped[field]
          ? `${mapped[field]} ${message}`
          : message;
    }

    return mapped;
  };

  /* ===========================
     Validation
  =========================== */

  const validateAiData = (
    data
  ) => {
    const errors = {};
    const warnings = {};

    const lot =
      String(
        data?.lot || ""
      ).trim();

    const work =
      String(
        data?.work || ""
      ).trim();

    /* ---------- Materials ---------- */

    const materials =
      normalizeMaterials(
        data?.materials
      );

    materials.forEach(
      (
        materialItem,
        index
      ) => {
        const material =
          String(
            materialItem
              ?.material || ""
          ).trim();

        const quantityRaw =
          String(
            materialItem
              ?.quantity ?? ""
          ).trim();

        const unit =
          String(
            materialItem
              ?.unit || ""
          ).trim();

        const hasAnyValue =
          Boolean(
            material ||
            quantityRaw ||
            unit
          );

        /*
          Một row hoàn toàn trống
          không phải lỗi local.

          Activity nào bắt buộc
          phải có material sẽ do
          Integration Service enforce.
        */
        if (!hasAnyValue) {
          return;
        }

        const materialKey =
          `materials.${index}.material`;

        const quantityKey =
          `materials.${index}.quantity`;

        const unitKey =
          `materials.${index}.unit`;

        if (!material) {
          errors[materialKey] =
            isVietnamese
              ? "Có số lượng hoặc đơn vị nhưng chưa có vật tư."
              : "Material is required when quantity or unit is provided.";
        }

        if (!quantityRaw) {
          errors[quantityKey] =
            isVietnamese
              ? "Đã có vật tư nhưng chưa có số lượng."
              : "Quantity is required for this material.";
        } else {
          const quantity =
            Number(
              quantityRaw.replace(
                ",",
                "."
              )
            );

          if (
            Number.isNaN(
              quantity
            )
          ) {
            errors[quantityKey] =
              isVietnamese
                ? "Số lượng phải là một số hợp lệ."
                : "Quantity must be a valid number.";
          } else if (
            quantity <= 0
          ) {
            errors[quantityKey] =
              isVietnamese
                ? "Số lượng phải lớn hơn 0."
                : "Quantity must be greater than 0.";
          }
        }

        if (!unit) {
          errors[unitKey] =
            isVietnamese
              ? "Đã có vật tư nhưng chưa có đơn vị."
              : "Unit is required for this material.";
        }
      }
    );
    const time =
      String(
        data?.time || ""
      ).trim();

    /* ---------- Required ---------- */

    if (!lot) {
      errors.lot =
        isVietnamese
          ? "Chưa có thông tin lô canh tác."
          : "Farm plot is required.";
    }

    if (!work) {
      errors.work =
        isVietnamese
          ? "Chưa có thông tin công việc."
          : "Farming task is required.";
    }

    /*
     * Time được yêu cầu trước khi lưu Integration Service,
     * vì performed_at không thể tạo nếu thiếu HH:mm.
     * Do đó time phải là ERROR, không phải WARNING.
     */
    if (!time) {
      errors.time =
        isVietnamese
          ? "Chưa có thời gian thực hiện."
          : "Execution time is required.";
    } else if (
      !/^([01]?\d|2[0-3]):([0-5]\d)$/.test(
        time
      )
    ) {
      errors.time =
        isVietnamese
          ? "Thời gian phải đúng định dạng HH:mm. Ví dụ: 07:30."
          : "Time must use HH:mm format, for example 07:30.";
    }


    /*
     * Không hardcode quantity threshold.
     * DEV warning chỉ kiểm tra UI và mặc định KHÔNG yêu cầu acknowledgement.
     */
    if (
      import.meta.env.DEV &&
      devWarning &&
      Object.keys(errors).length === 0
    ) {
      warnings[
        devWarning.field ||
          "_general"
      ] =
        isVietnamese
          ? devWarning.message
          : "🧪 DEV warning simulation: non-blocking review notice.";
    }

    const hasErrors =
      Object.keys(
        errors
      ).length > 0;

    const hasWarnings =
      Object.keys(
        warnings
      ).length > 0;

    return {
      errors,
      warnings,
      hasErrors,
      hasWarnings,

      /*
       * isValid chỉ phản ánh lỗi blocking.
       * Warning được xử lý riêng bằng warningAcknowledged.
       */
      requiresConfirmation:
        Boolean(
          devWarning
            ?.requiresConfirmation
        ) &&
        hasWarnings,

      isValid:
        !hasErrors,
    };
  };

  const localValidation =
    validateAiData(
      aiData
    );

  const validation = {
    errors: {
      ...localValidation.errors,
      ...serverValidation.errors,
    },

    warnings: {
      ...localValidation.warnings,
      ...serverValidation.warnings,
    },

    hasErrors:
      Object.keys({
        ...localValidation.errors,
        ...serverValidation.errors,
      }).length > 0,

    hasWarnings:
      Object.keys({
        ...localValidation.warnings,
        ...serverValidation.warnings,
      }).length > 0,

    requiresConfirmation:
      Boolean(
        localValidation
          .requiresConfirmation ||
        serverValidation
          .requiresConfirmation
      ),

    ruleVersion:
      serverValidation.ruleVersion,

    isValid:
      Object.keys({
        ...localValidation.errors,
        ...serverValidation.errors,
      }).length === 0,
  };

  const focusFirstValidationIssue = (
    currentValidation
  ) => {
    const firstField =
      Object.keys(
        currentValidation?.errors ||
          {}
      )[0] ||
      Object.keys(
        currentValidation?.warnings ||
          {}
      )[0];

    if (!firstField) {
      return;
    }

    window.setTimeout(
      () => {
        const target =
          document.getElementById(
            firstField
          );

        target?.scrollIntoView?.({
          behavior: "smooth",
          block: "center",
        });

        target?.focus?.();
      },
      80
    );
  };

  const handleAcknowledgeWarnings =
    () => {
      if (
        validation.hasErrors ||
        !validation.hasWarnings ||
        !validation
          .requiresConfirmation
      ) {
        setWarningAcknowledged(
          false
        );

        if (
          validation.hasErrors
        ) {
          focusFirstValidationIssue(
            validation
          );
        }

        return;
      }

      setWarningAcknowledged(
        true
      );

      showMessage(
        "success",
        isVietnamese
          ? "✅ Đã ghi nhận bạn đã kiểm tra cảnh báo cần xác nhận."
          : "✅ Confirmation-required warnings were acknowledged."
      );
    };

  /* ===========================
     Load Log For Editing
  =========================== */

  useEffect(() => {
    if (!logToEdit) {
      return;
    }

    if (audioUrl) {
      URL.revokeObjectURL(
        audioUrl
      );
    }

    // Intentional one-shot restoration of the selected log into local state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAudioUrl(null);
    setAudioBlob(null);

    setTranscript(
      logToEdit.transcript ||
        ""
    );

    const restoredMaterials =
      Array.isArray(
        logToEdit.materials
      ) &&
      logToEdit.materials.length > 0
        ? normalizeMaterials(
            logToEdit.materials
          )
        : [
            {
              material:
                logToEdit.material ||
                "",

              quantity:
                logToEdit.quantity ??
                "",

              unit:
                logToEdit.unit ||
                "",
            },
          ];

    setAiData({
      ...createEmptyAiData(),

      lot:
        logToEdit.lot ||
        "",

      work:
        logToEdit.work ||
        "",

      materials:
        restoredMaterials,

      time:
        logToEdit.time ||
        "",
    });

    setCurrentLogId(
      logToEdit.id
    );

    setIsEditingExistingLog(
      true
    );

    setCurrentLogDate(
      logToEdit.date ||
        null
    );

    setEditingStatus(
      logToEdit.status ||
        null
    );

    setIsUploading(
      false
    );

    setIsConfirmed(
      false
    );

    setWarningAcknowledged(
      false
    );

    setDevWarning(
      null
    );

    /*
      Nếu bản ghi đã thuộc
      Cần kiểm tra:
      hiện validation ngay.

      Draft:
      chưa cần hiện lỗi ngay.
    */

    setHasAttemptedSubmit(
      logToEdit.status ===
        "review"
    );

    setCurrentStep(3);

    if (
      logToEdit.status ===
      "review"
    ) {
      setMessage({
        type: "error",

        text: isVietnamese
          ? `⚠️ Nhật ký lô ${
              logToEdit.lot ||
              "---"
            } cần được kiểm tra. Hãy sửa các trường được đánh dấu trước khi xác nhận.`
          : `⚠️ The log for plot ${
              logToEdit.lot ||
              "---"
            } needs review. Correct the highlighted fields before confirming.`,
      });
    } else {
      setMessage({
        type: "success",

        text: isVietnamese
          ? `📝 Đã mở lại nhật ký đang dở của lô ${
              logToEdit.lot ||
              "---"
            }.`
          : `📝 Draft log for plot ${
              logToEdit.lot ||
              "---"
            } has been restored.`,
      });
    }

    onLogLoaded?.();

    // logToEdit identity intentionally controls this one-shot restore.
    // Adding local state/callback dependencies can replay the restore.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [logToEdit]);

  /* ===========================
     Reset
  =========================== */

  const resetVoiceLog =
    (
      targetOperation = operation
    ) => {
      if (audioUrl) {
        URL.revokeObjectURL(
          audioUrl
        );
      }

      setAudioUrl(null);

      setAudioBlob(null);

      setTranscript("");

      setAiData(
        createEmptyAiData()
      );

      setDynamicForm(
        createEmptyDynamicForm(
          targetOperation
        )
      );

      setCurrentLogId(
        null
      );

      setIsEditingExistingLog(
        false
      );

      setCurrentLogDate(
        null
      );
      setEditingStatus(
        null
      );

      setIsUploading(
        false
      );

      setIsConfirmed(
        false
      );

      setHasAttemptedSubmit(
        false
      );

      setMessage(null);

      setCurrentStep(1);
    };

  const handleOperationChange = (
    nextOperation
  ) => {
    if (
      !nextOperation ||
      nextOperation === operation ||
      isUploading ||
      isConfirmed
    ) {
      return;
    }

    resetVoiceLog(
      nextOperation
    );
    setOperation(nextOperation);
  };

  const handleDelete =
    () => {
      resetVoiceLog();
    };

  const handleCreateNew =
    () => {
      resetVoiceLog();
    };

  /* ===========================
     DEV Test
  =========================== */

  const loadDevTestData = (
    testData,
    name
  ) => {
    if (audioUrl) {
      URL.revokeObjectURL(
        audioUrl
      );
    }

    setAudioUrl(null);

    setAudioBlob(null);

    setTranscript(
      testData.transcript
    );

    setAiData({
      ...createEmptyAiData(),

      ...testData.structuredData,

      materials:
        normalizeMaterials(
          testData
            .structuredData
            ?.materials
        ),
    });

    setCurrentLogId(
      null
    );

    setCurrentLogDate(
      null
    );

    setEditingStatus(
      null
    );

    setIsUploading(
      false
    );

    setIsConfirmed(
      false
    );

    setHasAttemptedSubmit(
      false
    );

    setWarningAcknowledged(
      false
    );

    setDevWarning(
      testData.simulateWarning ||
        null
    );

    if (
      Array.isArray(
        testData.dynamicFormWarnings
      )
    ) {
      setDynamicForm(
        (previous) => ({
          ...previous,
          warnings:
            testData.dynamicFormWarnings,
        })
      );
    }

    clearServerValidation();

    setCurrentStep(3);

    showMessage(
      "success",

      isVietnamese
        ? `🧪 Đã nạp dữ liệu DEV: ${name}.`
        : `🧪 DEV test data loaded: ${name}.`
    );
  };

  const handleLoadValidTest =
    () => {
      loadDevTestData(
        DEV_VALID_DATA,

        isVietnamese
          ? "Dữ liệu hợp lệ"
          : "Valid data"
      );
    };

  const handleLoadWarningTest =
    () => {
      loadDevTestData(
        DEV_WARNING_DATA,

        isVietnamese
          ? "Dữ liệu cảnh báo"
          : "Warning data"
      );
    };

  const handleLoadErrorTest =
    () => {
      loadDevTestData(
        DEV_ERROR_DATA,

        isVietnamese
          ? "Dữ liệu lỗi"
          : "Error data"
      );
    };

  const handleResetDevTest =
    () => {
      resetVoiceLog();

      showMessage(
        "success",

        isVietnamese
          ? "🧪 Đã reset dữ liệu DEV."
          : "🧪 DEV test data reset."
      );
    };

  /* ===========================
     Upload AI
  =========================== */

  const handleUpload =
    async () => {
      if (
        !audioBlob ||
        isUploading ||
        isConfirmed
      ) {
        return;
      }

      setCurrentStep(2);

      setIsUploading(
        true
      );

      setHasAttemptedSubmit(
        false
      );

      setWarningAcknowledged(
        false
      );

      setDevWarning(null);
      clearServerValidation();

      showMessage(
        "success",
        t.messages.sending
      );

      try {
        const data =
          await uploadAudio(
            audioBlob,
            {
              operation,
              currentFields:
                dynamicForm.fields,
            }
          );

        setTranscript(
          data?.transcript ||
            ""
        );

        const nextDynamicForm =
          data?.dynamic_form;

        if (!nextDynamicForm) {
          throw new Error(
            "AI response is missing dynamic_form."
          );
        }

        setDynamicForm(
          nextDynamicForm
        );

        if (
          operation ===
          "CREATE_WORK_LOG"
        ) {
          const fields =
            nextDynamicForm.fields || {};

          const materials =
            normalizeMaterials(
              fields.materials
            );

          setAiData({
            lot:
              fields.plot_text ||
              "",

            work:
              fields.activity_text ||
              "",

            materials,

            time:
              fields.performed_time_text ||
              "",
          });
        }

        setAudioBlob(null);

        showMessage(
          "success",
          t.messages.processed
        );

        setCurrentStep(3);
      } catch (error) {
        console.error(
          "Upload audio error:",
          error
        );

        showMessage(
          "error",
          t.messages.backendError
        );

        setCurrentStep(1);
      } finally {
        setIsUploading(
          false
        );
      }
    };

  /* ===========================
     Confirm + Save
  =========================== */

  const handleConfirm =
    async () => {
      if (
        isUploading ||
        isConfirmed
      ) {
        return;
      }

      setHasAttemptedSubmit(
        true
      );

      if (
        operation !==
        "CREATE_WORK_LOG"
      ) {
        const fields =
          dynamicForm?.fields || {};

        const dynamicErrors =
          validateDynamicOperationFields(
            operation,
            fields,
            isVietnamese
          );

        if (
          Object.keys(
            dynamicErrors
          ).length > 0
        ) {
          setServerValidation({
            errors:
              dynamicErrors,
            warnings: {},
            requiresConfirmation:
              false,
            ruleVersion:
              null,
          });

          setWarningAcknowledged(
            false
          );

          showMessage(
            "error",
            isVietnamese
              ? "Chưa thể xác nhận. Hãy bổ sung hoặc sửa các trường được đánh dấu."
              : "The operation cannot be confirmed yet. Complete or fix the highlighted fields."
          );

          setCurrentStep(3);

          focusFirstValidationIssue({
            errors:
              dynamicErrors,
            warnings: {},
          });

          return;
        }

        if (
          (
            operation ===
              "CREATE_ISSUE_REPORT" ||
            operation ===
              "CREATE_HARVEST"
          ) &&
          fields.photo_required ===
            true
        ) {
          const photoError = {
            photo_required:
              isVietnamese
                ? "Nghiệp vụ yêu cầu ảnh nhưng frontend hiện chưa có chức năng chọn/tải ảnh theo Contract V3.1."
                : "This operation requires a photo, but the frontend does not yet support selecting/uploading one under Contract V3.1.",
          };

          setServerValidation({
            errors:
              photoError,
            warnings: {},
            requiresConfirmation:
              false,
            ruleVersion:
              null,
          });

          showMessage(
            "error",
            photoError.photo_required
          );

          setCurrentStep(3);

          focusFirstValidationIssue({
            errors:
              photoError,
            warnings: {},
          });

          return;
        }

        const recordId =
          currentLogId ||
          generateId();

        setIsUploading(
          true
        );

        clearServerValidation();

        showMessage(
          "success",
          isVietnamese
            ? "Đang lưu dữ liệu qua Integration Service..."
            : "Saving data through the Integration Service..."
        );

        try {
          const savedOperation =
            await saveDynamicOperation(
              operation,
              recordId,
              fields
            );

          setCurrentLogId(
            recordId
          );

          setIsConfirmed(
            true
          );

          setWarningAcknowledged(
            false
          );

          setCurrentStep(4);

          showMessage(
            "success",
            isVietnamese
              ? "✅ Dữ liệu đã được xác nhận và lưu qua Integration Service."
              : "✅ The data was confirmed and saved through the Integration Service."
          );

          console.info(
            "Dynamic operation saved:",
            {
              operation,
              response:
                savedOperation,
            }
          );
        } catch (error) {
          console.error(
            "Save dynamic operation error:",
            error
          );

          const detail =
            error?.data?.detail;

          const backendField =
            typeof detail ===
              "object" &&
            detail !== null
              ? detail.field
              : null;

          const backendMessage =
            typeof detail ===
              "string"
              ? detail
              : detail?.message ||
                error?.message ||
                (
                  isVietnamese
                    ? "Không thể lưu dữ liệu qua Integration Service."
                    : "The data could not be saved through the Integration Service."
                );

          if (backendField) {
            setServerValidation({
              errors: {
                [backendField]:
                  backendMessage,
              },
              warnings: {},
              requiresConfirmation:
                false,
              ruleVersion:
                null,
            });

            focusFirstValidationIssue({
              errors: {
                [backendField]:
                  backendMessage,
              },
              warnings: {},
            });
          }

          showMessage(
            "error",
            backendMessage
          );

          setCurrentStep(3);
        } finally {
          setIsUploading(
            false
          );
        }

        return;
      }

      const currentValidation =
        validateAiData(
          aiData
        );

      if (
        currentValidation.hasErrors
      ) {
        showMessage(
          "error",

          isVietnamese
            ? "Chưa thể xác nhận nhật ký. Hãy sửa các trường lỗi được đánh dấu đỏ."
            : "The log cannot be confirmed yet. Fix the fields highlighted in red."
        );

        setWarningAcknowledged(
          false
        );

        setCurrentStep(3);

        focusFirstValidationIssue(
          currentValidation
        );

        return;
      }

      if (
        currentValidation.hasWarnings &&
        currentValidation
          .requiresConfirmation &&
        !warningAcknowledged
      ) {
        showMessage(
          "warning",

          isVietnamese
            ? "Có cảnh báo cần kiểm tra. Hãy chọn “Tôi đã kiểm tra cảnh báo” trước khi xác nhận."
            : "There are warnings to review. Select “I reviewed the warnings” before confirming."
        );

        setCurrentStep(3);

        focusFirstValidationIssue(
          currentValidation
        );

        return;
      }

      const lotText =
        String(
          aiData.lot || ""
        ).trim();

      const activityText =
        String(
          aiData.work || ""
        ).trim();

      const logId =
        currentLogId ||
        generateId();

      const materialItems =
        normalizeMaterials(
          aiData.materials
        ).filter(
          (item) =>
            Boolean(
              String(
                item.material || ""
              ).trim() ||
              String(
                item.quantity ?? ""
              ).trim() ||
              String(
                item.unit || ""
              ).trim()
            )
        );

      const timeText =
        String(
          aiData.time || ""
        ).trim();

      const performedAt =
        buildPerformedAt(
          timeText,
          currentLogDate
        );

      if (!performedAt) {
        showMessage(
          "error",

          isVietnamese
            ? "Thời gian không đúng định dạng HH:mm. Ví dụ: 07:30."
            : "Time must use HH:mm format, for example 07:30."
        );

        setCurrentStep(3);

        return;
      }

      setIsUploading(
        true
      );

      showMessage(
        "success",

        isVietnamese
          ? "Đang đối chiếu dữ liệu với Integration Service..."
          : "Validating data with the Integration Service..."
      );

      try {
        const [
          lotResult,
          activityResult,
        ] = await Promise.all([
          resolveMasterData(
            "lot",
            lotText
          ),

          resolveMasterData(
            "activity",
            activityText
          ),
        ]);


        // =========================================================
        // HARD FAILURE: LOT
        // =========================================================
        if (
          !lotResult?.matched ||
          !lotResult?.code
        ) {
          showMessage(
            "error",

            isVietnamese
              ? `Không thể xác định lô "${lotText}" trong dữ liệu chuẩn. Vui lòng kiểm tra lại.`
              : `The plot "${lotText}" could not be resolved against master data. Please review it.`
          );

          setServerValidation(
            (previous) => ({
              ...(previous || {}),

              errors: {
                ...(previous?.errors || {}),

                lot:
                  isVietnamese
                    ? `Không thể xác định lô "${lotText}" trong dữ liệu chuẩn.`
                    : `The plot "${lotText}" could not be resolved against master data.`,
              },
            })
          );

          setCurrentStep(3);

          return;
        }


        // =========================================================
        // HARD FAILURE: ACTIVITY
        // =========================================================
        if (
          !activityResult?.matched ||
          !activityResult?.code
        ) {
          showMessage(
            "error",

            isVietnamese
              ? `Không thể xác định công việc "${activityText}" trong dữ liệu chuẩn. Vui lòng kiểm tra lại.`
              : `The activity "${activityText}" could not be resolved against master data. Please review it.`
          );

          setServerValidation(
            (previous) => ({
              ...(previous || {}),

              errors: {
                ...(previous?.errors || {}),

                work:
                  isVietnamese
                    ? `Không thể xác định công việc "${activityText}" trong dữ liệu chuẩn.`
                    : `The activity "${activityText}" could not be resolved against master data.`,
              },
            })
          );

          setCurrentStep(3);

          return;
        }


        // =========================================================
        // RESOLVE ALL MATERIALS
        // =========================================================
        const resolvedMaterialItems =
          await Promise.all(
            materialItems.map(
              async (
                materialItem,
                index
              ) => {
                const materialText =
                  String(
                    materialItem.material || ""
                  ).trim();

                const unitText =
                  String(
                    materialItem.unit || ""
                  ).trim();

                const quantityText =
                  String(
                    materialItem.quantity ?? ""
                  ).trim();

                const [
                  materialResult,
                  unitResult,
                ] = await Promise.all([
                  resolveMasterData(
                    "material",
                    materialText
                  ),

                  resolveMasterData(
                    "unit",
                    unitText
                  ),
                ]);


                // ---------------------------------------------
                // Material không tìm thấy
                // ---------------------------------------------
                if (
                  !materialResult?.matched ||
                  !materialResult?.code
                ) {
                  throw new Error(
                    `MATERIAL_RESOLVE:${index}:${materialText}`
                  );
                }


                // ---------------------------------------------
                // Unit không tìm thấy
                // ---------------------------------------------
                if (
                  !unitResult?.matched ||
                  !unitResult?.code
                ) {
                  throw new Error(
                    `UNIT_RESOLVE:${index}:${unitText}`
                  );
                }


                // ---------------------------------------------
                // Quantity
                // ---------------------------------------------
                const quantity =
                  Number(
                    quantityText.replace(
                      ",",
                      "."
                    )
                  );

                if (
                  Number.isNaN(
                    quantity
                  ) ||
                  quantity <= 0
                ) {
                  throw new Error(
                    `QUANTITY_INVALID:${index}`
                  );
                }


                return {
                  index,

                  materialText,

                  unitText,

                  quantity,

                  materialResult,

                  unitResult,
                };
              }
            )
          );


        // =========================================================
        // COLLECT RESOLVER WARNINGS
        // =========================================================
        const resolverWarnings = {};

        if (
          lotResult?.requires_confirmation
        ) {
          resolverWarnings.lot =
            isVietnamese
              ? `Lô "${lotText}" chỉ được khớp gần đúng với "${lotResult.name}". Hãy kiểm tra trước khi xác nhận.`
              : `The plot "${lotText}" was only approximately matched to "${lotResult.name}". Please review it.`;
        }

        if (
          activityResult?.requires_confirmation
        ) {
          resolverWarnings.work =
            isVietnamese
              ? `Công việc "${activityText}" chỉ được khớp gần đúng với "${activityResult.name}". Hãy kiểm tra trước khi xác nhận.`
              : `The activity "${activityText}" was only approximately matched to "${activityResult.name}". Please review it.`;
        }


        resolvedMaterialItems.forEach(
          (item) => {
            if (
              item.materialResult
                ?.requires_confirmation
            ) {
              resolverWarnings[
                `materials.${item.index}.material`
              ] =
                isVietnamese
                  ? `Vật tư "${item.materialText}" chỉ được khớp gần đúng với "${item.materialResult.name}". Hãy kiểm tra trước khi xác nhận.`
                  : `The material "${item.materialText}" was approximately matched to "${item.materialResult.name}". Please review it.`;
            }

            if (
              item.unitResult
                ?.requires_confirmation
            ) {
              resolverWarnings[
                `materials.${item.index}.unit`
              ] =
                isVietnamese
                  ? `Đơn vị "${item.unitText}" chỉ được khớp gần đúng với "${item.unitResult.name}". Hãy kiểm tra trước khi xác nhận.`
                  : `The unit "${item.unitText}" was approximately matched to "${item.unitResult.name}". Please review it.`;
            }
          }
        );


        // =========================================================
        // REQUIRE USER CONFIRMATION FOR FUZZY MATCH
        // =========================================================
        const hasResolverWarnings =
          Object.keys(
            resolverWarnings
          ).length > 0;

        if (
          hasResolverWarnings &&
          !warningAcknowledged
        ) {
          setServerValidation(
            (previous) => ({
              ...(previous || {}),

              errors: {
                ...(previous?.errors || {}),
              },

              warnings: {
                ...(previous?.warnings || {}),
                ...resolverWarnings,
              },

              requiresConfirmation:
                true,
            })
          );

          setWarningAcknowledged(
            false
          );

          showMessage(
            "warning",

            isVietnamese
              ? "Một số dữ liệu chỉ được khớp gần đúng với dữ liệu chuẩn. Hãy kiểm tra các cảnh báo và chọn “Tôi đã kiểm tra cảnh báo” trước khi xác nhận."
              : "Some values were only approximately matched to master data. Review the warnings and acknowledge them before confirming."
          );

          setCurrentStep(3);

          window.setTimeout(
            () =>
              focusFirstValidationIssue({
                errors: {},
                warnings:
                  resolverWarnings,
              }),
            80
          );

          return;
        }


        // =========================================================
        // BUILD CANONICAL MATERIAL CONTRACT
        // =========================================================
        const materials =
          resolvedMaterialItems.map(
            (item) => ({
              material_code:
                item.materialResult.code,

              quantity:
                item.quantity,

              unit_code:
                item.unitResult.code,
            })
          );
        const now =
          new Date();

        const finalContract = {
          schema_version:
            "1.0",

          client_record_id:
            logId,

          transcript:
            transcript.trim(),

          lot_code:
            lotResult.code,

          activity_code:
            activityResult.code,

          materials,

          performed_at:
            performedAt,

          performer_code:
            null,

          notes:
            null,

          source:
            "voice",

          confirmed:
            true,
        };

        const integrationValidation =
          await validateCultivationLog(
            finalContract
          );

        const integrationErrors =
          Array.isArray(
            integrationValidation?.errors
          )
            ? integrationValidation.errors
            : [];

        const integrationWarnings =
          Array.isArray(
            integrationValidation?.warnings
          )
            ? integrationValidation.warnings
            : [];

        const integrationIsValid =
          integrationValidation?.is_valid ??
          integrationValidation?.valid ??
          integrationErrors.length === 0;

        const backendRequiresConfirmation =
          Boolean(
            integrationValidation
              ?.requires_confirmation
          ) ||
          integrationWarnings.some(
            (issue) =>
              Boolean(
                issue?.requires_confirmation
              )
          );

        const mappedServerValidation = {
          errors:
            normalizeIntegrationIssues(
              integrationErrors
            ),

          warnings:
            normalizeIntegrationIssues(
              integrationWarnings
            ),

          requiresConfirmation:
            backendRequiresConfirmation,

          ruleVersion:
            integrationValidation
              ?.rule_version ||
            null,
        };

        setServerValidation(
          mappedServerValidation
        );

        if (
          !integrationIsValid ||
          integrationErrors.length > 0
        ) {
          console.error(
            "Integration validation failed:",
            integrationValidation
          );

          showMessage(
            "error",

            isVietnamese
              ? "Integration Service từ chối dữ liệu theo business rule. Hãy sửa các trường được đánh dấu."
              : "Integration Service rejected the data according to business rules. Fix the highlighted fields."
          );

          setWarningAcknowledged(
            false
          );

          setCurrentStep(3);

          window.setTimeout(
            () =>
              focusFirstValidationIssue({
                errors:
                  mappedServerValidation.errors,
                warnings:
                  mappedServerValidation.warnings,
              }),
            80
          );

          return;
        }

        if (
          backendRequiresConfirmation &&
          !warningAcknowledged
        ) {
          showMessage(
            "warning",

            isVietnamese
              ? "Integration Service yêu cầu bạn kiểm tra và xác nhận cảnh báo trước khi lưu."
              : "Integration Service requires you to review and acknowledge the warning before saving."
          );

          setCurrentStep(3);

          return;
        }

        const savedIntegrationLog = isEditingExistingLog
          ? await updateCultivationLog(logId, finalContract)
          : await saveCultivationLog(finalContract);

        const savedLog = {
          id: logId,

          lot:
            lotText,

          work:
            activityText,

          materials:
            materialItems,

          /*
            Compatibility tạm cho
            My Logs hiện tại.
            Sau khi sửa My Logs,
            3 field này sẽ bỏ.
          */
          material:
            materialItems[0]
              ?.material || "",

          quantity:
            materialItems[0]
              ?.quantity ?? "",

          unit:
            materialItems[0]
              ?.unit || "",

          time:
            timeText,

          transcript:
            transcript.trim(),

          status:
            "completed",

          warning:
            "",

          date:
            currentLogDate ||
            now.toLocaleDateString(
              "vi-VN"
            ),

          updatedAt:
            now.toISOString(),

          createdAt:
            now.toISOString(),

          integration:
            savedIntegrationLog,
        };

        onSaveLog?.(
          savedLog
        );

        setCurrentLogId(
          logId
        );

        setEditingStatus(
          "completed"
        );

        setIsConfirmed(
          true
        );

        setDevWarning(null);
        clearServerValidation();

        setCurrentStep(4);

        showMessage(
          "success",

          isVietnamese
            ? "✅ Nhật ký đã được xác nhận, lưu qua Integration Service và cập nhật vào Nhật ký của tôi."
            : "✅ The log was confirmed, saved through the Integration Service, and added to My Logs."
        );
      } catch (error) {
        console.error(
          "Confirm cultivation log error:",
          error
        );

        const errorMessage =
          String(
            error?.message || ""
          );


        // =========================================================
        // MATERIAL RESOLVE ERROR
        // =========================================================
        const materialResolveMatch =
          errorMessage.match(
            /^MATERIAL_RESOLVE:(\d+):(.*)$/
          );

        if (materialResolveMatch) {
          const materialIndex =
            Number(
              materialResolveMatch[1]
            );

          const materialText =
            materialResolveMatch[2];

          const field =
            `materials.${materialIndex}.material`;

          setServerValidation(
            (previous) => ({
              ...(previous || {}),

              errors: {
                ...(previous?.errors || {}),

                [field]:
                  isVietnamese
                    ? `Không thể xác định vật tư "${materialText}" trong dữ liệu chuẩn.`
                    : `The material "${materialText}" could not be resolved against master data.`,
              },
            })
          );

          showMessage(
            "error",

            isVietnamese
              ? `Không thể xác định vật tư ${materialIndex + 1}: "${materialText}". Vui lòng kiểm tra lại.`
              : `Material ${materialIndex + 1}, "${materialText}", could not be resolved. Please review it.`
          );

          setCurrentStep(3);

          window.setTimeout(
            () => {
              document
                .getElementById(
                  field
                )
                ?.scrollIntoView?.({
                  behavior: "smooth",
                  block: "center",
                });

              document
                .getElementById(
                  field
                )
                ?.focus?.();
            },
            80
          );

          return;
        }


        // =========================================================
        // UNIT RESOLVE ERROR
        // =========================================================
        const unitResolveMatch =
          errorMessage.match(
            /^UNIT_RESOLVE:(\d+):(.*)$/
          );

        if (unitResolveMatch) {
          const materialIndex =
            Number(
              unitResolveMatch[1]
            );

          const unitText =
            unitResolveMatch[2];

          const field =
            `materials.${materialIndex}.unit`;

          setServerValidation(
            (previous) => ({
              ...(previous || {}),

              errors: {
                ...(previous?.errors || {}),

                [field]:
                  isVietnamese
                    ? `Không thể xác định đơn vị "${unitText}" trong dữ liệu chuẩn.`
                    : `The unit "${unitText}" could not be resolved against master data.`,
              },
            })
          );

          showMessage(
            "error",

            isVietnamese
              ? `Không thể xác định đơn vị của vật tư ${materialIndex + 1}: "${unitText}".`
              : `The unit for material ${materialIndex + 1}, "${unitText}", could not be resolved.`
          );

          setCurrentStep(3);

          window.setTimeout(
            () => {
              document
                .getElementById(
                  field
                )
                ?.scrollIntoView?.({
                  behavior: "smooth",
                  block: "center",
                });

              document
                .getElementById(
                  field
                )
                ?.focus?.();
            },
            80
          );

          return;
        }


        // =========================================================
        // QUANTITY INVALID ERROR
        // =========================================================
        const quantityInvalidMatch =
          errorMessage.match(
            /^QUANTITY_INVALID:(\d+)$/
          );

        if (quantityInvalidMatch) {
          const materialIndex =
            Number(
              quantityInvalidMatch[1]
            );

          const field =
            `materials.${materialIndex}.quantity`;

          setServerValidation(
            (previous) => ({
              ...(previous || {}),

              errors: {
                ...(previous?.errors || {}),

                [field]:
                  isVietnamese
                    ? "Số lượng phải là một số lớn hơn 0."
                    : "Quantity must be a number greater than 0.",
              },
            })
          );

          showMessage(
            "error",

            isVietnamese
              ? `Số lượng của vật tư ${materialIndex + 1} không hợp lệ.`
              : `The quantity for material ${materialIndex + 1} is invalid.`
          );

          setCurrentStep(3);

          window.setTimeout(
            () => {
              document
                .getElementById(
                  field
                )
                ?.scrollIntoView?.({
                  behavior: "smooth",
                  block: "center",
                });

              document
                .getElementById(
                  field
                )
                ?.focus?.();
            },
            80
          );

          return;
        }


        // =========================================================
        // GENERIC ERROR
        // =========================================================
        showMessage(
          "error",

          isVietnamese
            ? "Không thể lưu nhật ký qua Integration Service. Hãy kiểm tra Integration Service và thử lại."
            : "The log could not be saved through the Integration Service. Check the service and try again."
        );

        setCurrentStep(3);
      } finally {
        setIsUploading(
          false
        );
      }
    };
  const messageText =
    getMessageText();

  const messageType =
    getMessageType();

  const hasManualFormData =
    Boolean(
      String(
        aiData?.lot ?? ""
      ).trim() ||
      String(
        aiData?.work ?? ""
      ).trim() ||
      (
        aiData?.materials ??
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
      ) ||
      String(
        aiData?.time ?? ""
      ).trim()
    );

  const hasDynamicFormData =
    Object.values(
      dynamicForm?.fields ?? {}
    ).some((value) => {
      if (Array.isArray(value)) {
        return value.some(
          (item) =>
            item &&
            typeof item === "object" &&
            Object.values(item).some(
              (nestedValue) =>
                nestedValue !== null &&
                nestedValue !== undefined &&
                String(
                  nestedValue
                ).trim() !== ""
            )
        );
      }

      return (
        value !== null &&
        value !== undefined &&
        String(value).trim() !== ""
      );
    });

  const hasUsableResult =
    Boolean(
      transcript.trim()
    ) ||
    hasDynamicFormData ||
    hasManualFormData;
  return (
    <main className="workspace">
      <div className="workspace-container">
        <Header
          language={
            language
          }

          onLanguageChange={
            onLanguageChange
          }

          text={t}

          themeMode={
            themeMode
          }

          onThemeChange={
            onThemeChange
          }

          logs={
            logs
          }
        />

        {/* Hero */}

        <section className="workspace-hero">
          <div>
            <span className="workspace-eyebrow">
              NextFarm AI Workspace
            </span>

            <h2>
              {editingStatus ===
              "review"
                ? isVietnamese
                  ? "Kiểm tra và hoàn thiện nhật ký"
                  : "Review and complete log"
                : isVietnamese
                  ? "Tạo nhật ký canh tác bằng giọng nói"
                  : "Create farming logs with your voice"}
            </h2>

            <p>
              {editingStatus ===
              "review"
                ? isVietnamese
                  ? "Kiểm tra các trường được cảnh báo, bổ sung thông tin còn thiếu và xác nhận lại nhật ký."
                  : "Review highlighted fields, complete missing data and confirm the log."
                : isVietnamese
                  ? "Ghi âm, để AI xử lý và kiểm tra dữ liệu trước khi xác nhận."
                  : "Record your voice, let AI process it, then review the extracted data before confirming."}
            </p>
          </div>

          <div className="workspace-status">
            <span className="workspace-status-dot" />

            <span>
              {editingStatus ===
              "review"
                ? isVietnamese
                  ? "Đang kiểm tra"
                  : "Reviewing"
                : isVietnamese
                  ? "Hệ thống sẵn sàng"
                  : "System ready"}
            </span>
          </div>
        </section>

        {/* Operation Selector */}

        <OperationSelector
          operation={
            operation
          }

          onOperationChange={
            handleOperationChange
          }

          language={
            language
          }

          disabled={
            isUploading ||
            isConfirmed
          }
        />

        {/* DEV */}

        {isDevMode && (
          <section className="dev-test-panel">
            <div className="dev-test-info">
              <span className="dev-test-icon">
                🧪
              </span>

              <div>
                <strong>
                  DEV Test Mode
                </strong>

                <span>
                  {isVietnamese
                    ? "Kiểm thử frontend không cần AI Service."
                    : "Test the frontend without the AI Service."}
                </span>
              </div>
            </div>

            <div className="dev-test-actions">
              <button
                type="button"
                className="dev-test-btn valid"
                onClick={
                  handleLoadValidTest
                }
              >
                ✅{" "}
                {isVietnamese
                  ? "Hợp lệ"
                  : "Valid"}
              </button>

              <button
                type="button"
                className="dev-test-btn warning"
                onClick={
                  handleLoadWarningTest
                }
              >
                ⚠️{" "}
                {isVietnamese
                  ? "Cảnh báo"
                  : "Warning"}
              </button>

              <button
                type="button"
                className="dev-test-btn error"
                onClick={
                  handleLoadErrorTest
                }
              >
                ❌{" "}
                {isVietnamese
                  ? "Dữ liệu lỗi"
                  : "Error"}
              </button>

              <button
                type="button"
                className="dev-test-btn reset"
                onClick={
                  handleResetDevTest
                }
              >
                ↺ Reset
              </button>
            </div>
          </section>
        )}

        {/* Workflow */}

        <section className="workflow-card">
          <WorkflowStepper
            currentStep={
              currentStep
            }
            text={t}
          />
        </section>

        {/* Workspace */}

        <section className="voice-workspace-grid">
          <div className="voice-primary-column">
            <div className="workspace-card record-card">
              <RecordButton
                audioUrl={
                  audioUrl
                }

                setAudioUrl={
                  setAudioUrl
                }

                setAudioBlob={
                  setAudioBlob
                }

                setTranscript={
                  setTranscript
                }

                setAiData={
                  setAiData
                }

                setMessage={
                  setMessage
                }

                isConfirmed={
                  isConfirmed
                }

                text={t}

                language={
                  language
                }
              />
            </div>

            <div className="workspace-card">
              <TranscriptBox
                transcript={
                  transcript
                }

                onTranscriptChange={
                  setTranscript
                }

                isConfirmed={
                  isConfirmed
                }

                text={t}
              />
            </div>
          </div>

          <div className="voice-secondary-column">
            <div className="workspace-card ai-data-card">
              <DynamicForm
                operation={
                  operation
                }

                dynamicForm={
                  dynamicForm
                }

                onFieldsChange={
                  (nextFields) => {
                    setDynamicForm(
                      (previous) => ({
                        ...previous,
                        fields:
                          nextFields,
                      })
                    );
                  }
                }

                isConfirmed={
                  isConfirmed
                }


                showValidation={
                  hasAttemptedSubmit
                }

                language={
                  language
                }
              />

              <ActionButtons
                hasAudio={
                  Boolean(
                    audioBlob
                  )
                }

                hasResult={
                  hasUsableResult
                }

                isUploading={
                  isUploading
                }

                isConfirmed={
                  isConfirmed
                }

                validation={
                  validation
                }

                showValidation={
                  hasAttemptedSubmit
                }

                warningAcknowledged={
                  warningAcknowledged
                }

                requiresConfirmation={
                  validation
                    .requiresConfirmation
                }

                onAcknowledgeWarnings={
                  handleAcknowledgeWarnings
                }

                onRetry={
                  handleDelete
                }

                onUpload={
                  handleUpload
                }

                onConfirm={
                  handleConfirm
                }

                onCreateNew={
                  handleCreateNew
                }

                text={t}

                language={
                  language
                }
              />
            </div>
          </div>
        </section>

        {/* Toast */}

        {messageText && (
          <div
            className={`app-toast ${messageType}`}
            role="status"
          >
            <span className="app-toast-icon">
              {messageType ===
              "error"
                ? "❌"
                : messageType ===
                    "warning"
                  ? "⚠️"
                  : "✅"}
            </span>

            <span>
              {messageText}
            </span>
          </div>
        )}
      </div>
    </main>
  );
}

export default VoiceLog;
