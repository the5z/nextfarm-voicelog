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
import AIForm from "../components/AIForm";
import ActionButtons from "../components/ActionButtons";

import { uploadAudio } from "../services/audioService";
import {
  resolveMasterData,
  validateCultivationLog,
  saveCultivationLog,
} from "../services/integrationService";
import { TEXT } from "../constants/translations";

const EMPTY_AI_DATA = {
  lot: "",
  work: "",
  material: "",
  quantity: "",
  unit: "",
  time: "",
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

const DEV_VALID_DATA = {
  transcript:
    "HÃ´m nay tÃ´i bÃ³n 20 kg phÃ¢n NPK cho lÃ´ A01 lÃºc 8 giá» 30.",

  structuredData: {
    lot: "A01",
    work: "BÃ³n phÃ¢n",
    material: "PhÃ¢n NPK",
    quantity: "20",
    unit: "kg",
    time: "08:30",
  },
};

const DEV_ERROR_DATA = {
  transcript:
    "HÃ´m nay tÃ´i thá»±c hiá»‡n cÃ´ng viá»‡c nhÆ°ng thÃ´ng tin nháº­n dáº¡ng chÆ°a Ä‘áº§y Ä‘á»§.",

  structuredData: {
    lot: "",
    work: "",
    material: "PhÃ¢n NPK",
    quantity: "0",
    unit: "",
    time: "",
  },
};

const DEV_WARNING_DATA = {
  transcript:
    "HÃ´m nay tÃ´i kiá»ƒm tra lÃ´ A01.",

  structuredData: {
    lot: "A01",
    work: "Kiá»ƒm tra lÃ´",
    material: "",
    quantity: "",
    unit: "",
    time: "",
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
}) {
  const t =
    TEXT[language];

  const isVietnamese =
    language === "vi";

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
    EMPTY_AI_DATA
  );


  /* ===========================
     Sync AI data to App
  =========================== */

  useEffect(() => {
    onAiDataChange?.(
      aiData
    );
  }, [
    aiData,
    onAiDataChange,
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

    setAiData(
      (previous) => ({
        ...previous,
        ...externalAiChanges,
      })
    );

    setIsConfirmed(false);
    setCurrentStep(3);

    if (autoValidation) {
      setHasAttemptedSubmit(true);
    }

    showMessage(
      "success",
      isVietnamese
        ? "ðŸ¤– NextFarm AI Ä‘Ã£ cáº­p nháº­t dá»¯ liá»‡u nháº­t kÃ½."
        : "ðŸ¤– NextFarm AI updated the farming log data."
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

  const [
    message,
    setMessage,
  ] = useState(null);

  const [
    currentStep,
    setCurrentStep,
  ] = useState(1);

  /* ===========================
     Current Log
  =========================== */

  const [
    currentLogId,
    setCurrentLogId,
  ] = useState(null);

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

  const showMessage = (
    type,
    text
  ) => {
    setMessage({
      type,
      text,
    });
  };

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

    const keywords = [
      "KhÃ´ng thá»ƒ",
      "Vui lÃ²ng",
      "lá»—i",
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

    const material =
      String(
        data?.material || ""
      ).trim();

    const quantityRaw =
      String(
        data?.quantity ?? ""
      ).trim();

    const unit =
      String(
        data?.unit || ""
      ).trim();

    const time =
      String(
        data?.time || ""
      ).trim();

    if (!lot) {
      errors.lot =
        isVietnamese
          ? "ChÆ°a cÃ³ thÃ´ng tin lÃ´ canh tÃ¡c."
          : "Farm plot is required.";
    }

    if (!work) {
      errors.work =
        isVietnamese
          ? "ChÆ°a cÃ³ thÃ´ng tin cÃ´ng viá»‡c."
          : "Farming task is required.";
    }

    if (quantityRaw) {
      const quantity =
        Number(
          quantityRaw
        );

      if (
        Number.isNaN(
          quantity
        )
      ) {
        errors.quantity =
          isVietnamese
            ? "Sá»‘ lÆ°á»£ng pháº£i lÃ  má»™t sá»‘ há»£p lá»‡."
            : "Quantity must be a valid number.";
      } else if (
        quantity <= 0
      ) {
        errors.quantity =
          isVietnamese
            ? "Sá»‘ lÆ°á»£ng pháº£i lá»›n hÆ¡n 0."
            : "Quantity must be greater than 0.";
      }

      if (!unit) {
        errors.unit =
          isVietnamese
            ? "CÃ³ sá»‘ lÆ°á»£ng nhÆ°ng chÆ°a cÃ³ Ä‘Æ¡n vá»‹."
            : "Unit is required when quantity is provided.";
      }
    }

    if (
      unit &&
      !quantityRaw
    ) {
      errors.quantity =
        isVietnamese
          ? "CÃ³ Ä‘Æ¡n vá»‹ nhÆ°ng chÆ°a cÃ³ sá»‘ lÆ°á»£ng."
          : "Quantity is required when a unit is provided.";
    }


    if (!time) {
      warnings.time =
        isVietnamese
          ? "ChÆ°a cÃ³ thá»i gian thá»±c hiá»‡n."
          : "No execution time was detected.";
    }

    return {
      errors,
      warnings,

      isValid:
        Object.keys(
          errors
        ).length === 0 &&
        Object.keys(
          warnings
        ).length === 0,
    };
  };

  const validation =
    validateAiData(
      aiData
    );

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

    setAudioUrl(null);
    setAudioBlob(null);

    setTranscript(
      logToEdit.transcript ||
        ""
    );

    setAiData({
      ...EMPTY_AI_DATA,

      lot:
        logToEdit.lot ||
        "",

      work:
        logToEdit.work ||
        "",

      material:
        logToEdit.material ||
        "",

      quantity:
        logToEdit.quantity ||
        "",

      unit:
        logToEdit.unit ||
        "",

      time:
        logToEdit.time ||
        "",
    });

    setCurrentLogId(
      logToEdit.id
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

    /*
      Náº¿u báº£n ghi Ä‘Ã£ thuá»™c
      Cáº§n kiá»ƒm tra:
      hiá»‡n validation ngay.

      Draft:
      chÆ°a cáº§n hiá»‡n lá»—i ngay.
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
          ? `âš ï¸ Nháº­t kÃ½ lÃ´ ${
              logToEdit.lot ||
              "---"
            } cáº§n Ä‘Æ°á»£c kiá»ƒm tra. HÃ£y sá»­a cÃ¡c trÆ°á»ng Ä‘Æ°á»£c Ä‘Ã¡nh dáº¥u trÆ°á»›c khi xÃ¡c nháº­n.`
          : `âš ï¸ The log for plot ${
              logToEdit.lot ||
              "---"
            } needs review. Correct the highlighted fields before confirming.`,
      });
    } else {
      setMessage({
        type: "success",

        text: isVietnamese
          ? `ðŸ“ ÄÃ£ má»Ÿ láº¡i nháº­t kÃ½ Ä‘ang dá»Ÿ cá»§a lÃ´ ${
              logToEdit.lot ||
              "---"
            }.`
          : `ðŸ“ Draft log for plot ${
              logToEdit.lot ||
              "---"
            } has been restored.`,
      });
    }

    onLogLoaded?.();
  }, [logToEdit]);

  /* ===========================
     Reset
  =========================== */

  const resetVoiceLog =
    () => {
      if (audioUrl) {
        URL.revokeObjectURL(
          audioUrl
        );
      }

      setAudioUrl(null);

      setAudioBlob(null);

      setTranscript("");

      setAiData(
        EMPTY_AI_DATA
      );

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

      setMessage(null);

      setCurrentStep(1);
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
      ...EMPTY_AI_DATA,

      ...testData.structuredData,
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

    setCurrentStep(3);

    showMessage(
      "success",

      isVietnamese
        ? `ðŸ§ª ÄÃ£ náº¡p dá»¯ liá»‡u DEV: ${name}.`
        : `ðŸ§ª DEV test data loaded: ${name}.`
    );
  };

  const handleLoadValidTest =
    () => {
      loadDevTestData(
        DEV_VALID_DATA,

        isVietnamese
          ? "Dá»¯ liá»‡u há»£p lá»‡"
          : "Valid data"
      );
    };

  const handleLoadWarningTest =
    () => {
      loadDevTestData(
        DEV_WARNING_DATA,

        isVietnamese
          ? "Dá»¯ liá»‡u cáº£nh bÃ¡o"
          : "Warning data"
      );
    };

  const handleLoadErrorTest =
    () => {
      loadDevTestData(
        DEV_ERROR_DATA,

        isVietnamese
          ? "Dá»¯ liá»‡u lá»—i"
          : "Error data"
      );
    };

  const handleResetDevTest =
    () => {
      resetVoiceLog();

      showMessage(
        "success",

        isVietnamese
          ? "ðŸ§ª ÄÃ£ reset dá»¯ liá»‡u DEV."
          : "ðŸ§ª DEV test data reset."
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

      showMessage(
        "success",
        t.messages.sending
      );

      try {
        const data =
          await uploadAudio(
            audioBlob
          );

        setTranscript(
          data?.transcript ||
            ""
        );

        const structuredData =
          data?.structured_data || {};

        const firstMaterial =
          structuredData.materials?.[0] || {};

        setAiData({
          lot:
            structuredData.lot_text ||
            "",

          work:
            structuredData.activity_text ||
            "",

          material:
            firstMaterial.material_text ||
            "",

          quantity:
            firstMaterial.quantity ??
            "",

          unit:
            firstMaterial.unit_text ||
            "",

          time:
            structuredData.time_text ||
            "",
        });

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
        !transcript.trim()
      ) {
        showMessage(
          "error",

          t.messages
            .reviewBeforeConfirm
        );

        return;
      }

      const currentValidation =
        validateAiData(
          aiData
        );

      if (
        !currentValidation.isValid
      ) {
        showMessage(
          "error",

          isVietnamese
            ? "ChÆ°a thá»ƒ xÃ¡c nháº­n nháº­t kÃ½. Vui lÃ²ng xá»­ lÃ½ táº¥t cáº£ lá»—i vÃ  cáº£nh bÃ¡o Ä‘Æ°á»£c Ä‘Ã¡nh dáº¥u trÆ°á»›c khi xÃ¡c nháº­n."
            : "The log cannot be confirmed yet. Please resolve all highlighted errors and warnings before confirmation."
        );

        setCurrentStep(3);

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

      const materialText =
        String(
          aiData.material || ""
        ).trim();

      const quantityText =
        String(
          aiData.quantity ?? ""
        ).trim();

      const unitText =
        String(
          aiData.unit || ""
        ).trim();

      const timeText =
        String(
          aiData.time || ""
        ).trim();

      if (!timeText) {
        showMessage(
          "error",

          isVietnamese
            ? "ChÆ°a cÃ³ thá»i gian thá»±c hiá»‡n. Vui lÃ²ng bá»• sung thá»i gian trÆ°á»›c khi xÃ¡c nháº­n."
            : "Execution time is missing. Please add it before confirming."
        );

        setCurrentStep(3);

        return;
      }

      if (
        !materialText &&
        (quantityText || unitText)
      ) {
        showMessage(
          "error",

          isVietnamese
            ? "CÃ³ sá»‘ lÆ°á»£ng hoáº·c Ä‘Æ¡n vá»‹ nhÆ°ng chÆ°a cÃ³ váº­t tÆ°. Vui lÃ²ng kiá»ƒm tra láº¡i."
            : "Quantity or unit is present but the material is missing. Please review the data."
        );

        setCurrentStep(3);

        return;
      }

      if (
        materialText &&
        (!quantityText || !unitText)
      ) {
        showMessage(
          "error",

          isVietnamese
            ? "Váº­t tÆ° chÆ°a Ä‘á»§ sá»‘ lÆ°á»£ng hoáº·c Ä‘Æ¡n vá»‹. Vui lÃ²ng bá»• sung trÆ°á»›c khi xÃ¡c nháº­n."
            : "The material is missing a quantity or unit. Please complete it before confirming."
        );

        setCurrentStep(3);

        return;
      }

      const performedAt =
        buildPerformedAt(
          timeText,
          currentLogDate
        );

      if (!performedAt) {
        showMessage(
          "error",

          isVietnamese
            ? "Thá»i gian khÃ´ng Ä‘Ãºng Ä‘á»‹nh dáº¡ng HH:mm. VÃ­ dá»¥: 07:30."
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
          ? "Äang Ä‘á»‘i chiáº¿u dá»¯ liá»‡u vá»›i Integration Service..."
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

        if (
          !lotResult?.matched ||
          !lotResult?.code ||
          lotResult?.requires_confirmation
        ) {
          showMessage(
            "error",

            isVietnamese
              ? `KhÃ´ng thá»ƒ xÃ¡c Ä‘á»‹nh lÃ´ "${lotText}" trong dá»¯ liá»‡u chuáº©n. Vui lÃ²ng kiá»ƒm tra láº¡i.`
              : `The plot "${lotText}" could not be resolved against master data. Please review it.`
          );

          setCurrentStep(3);

          return;
        }

        if (
          !activityResult?.matched ||
          !activityResult?.code ||
          activityResult?.requires_confirmation
        ) {
          showMessage(
            "error",

            isVietnamese
              ? `KhÃ´ng thá»ƒ xÃ¡c Ä‘á»‹nh cÃ´ng viá»‡c "${activityText}" trong dá»¯ liá»‡u chuáº©n. Vui lÃ²ng kiá»ƒm tra láº¡i.`
              : `The activity "${activityText}" could not be resolved against master data. Please review it.`
          );

          setCurrentStep(3);

          return;
        }

        const materials = [];

        if (materialText) {
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

          if (
            !materialResult?.matched ||
            !materialResult?.code ||
            materialResult?.requires_confirmation
          ) {
            showMessage(
              "error",

              isVietnamese
                ? `KhÃ´ng thá»ƒ xÃ¡c Ä‘á»‹nh váº­t tÆ° "${materialText}" trong dá»¯ liá»‡u chuáº©n. Vui lÃ²ng kiá»ƒm tra láº¡i.`
                : `The material "${materialText}" could not be resolved against master data. Please review it.`
            );

            setCurrentStep(3);

            return;
          }

          if (
            !unitResult?.matched ||
            !unitResult?.code ||
            unitResult?.requires_confirmation
          ) {
            showMessage(
              "error",

              isVietnamese
                ? `KhÃ´ng thá»ƒ xÃ¡c Ä‘á»‹nh Ä‘Æ¡n vá»‹ "${unitText}" trong dá»¯ liá»‡u chuáº©n. Vui lÃ²ng kiá»ƒm tra láº¡i.`
                : `The unit "${unitText}" could not be resolved against master data. Please review it.`
            );

            setCurrentStep(3);

            return;
          }

          const quantity =
            Number(
              quantityText
            );

          if (
            Number.isNaN(quantity) ||
            quantity <= 0
          ) {
            showMessage(
              "error",

              isVietnamese
                ? "Sá»‘ lÆ°á»£ng váº­t tÆ° pháº£i lÃ  sá»‘ lá»›n hÆ¡n 0."
                : "Material quantity must be a number greater than 0."
            );

            setCurrentStep(3);

            return;
          }

          materials.push({
            material_code:
              materialResult.code,

            quantity,

            unit_code:
              unitResult.code,
          });
        }

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

        const integrationIsValid =
          integrationValidation?.is_valid ??
          integrationValidation?.valid ??
          integrationErrors.length === 0;

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
              ? "Integration Service tá»« chá»‘i dá»¯ liá»‡u. Vui lÃ²ng kiá»ƒm tra láº¡i cÃ¡c trÆ°á»ng trÆ°á»›c khi lÆ°u."
              : "The Integration Service rejected the data. Please review the fields before saving."
          );

          setCurrentStep(3);

          return;
        }

        const savedIntegrationLog =
          await saveCultivationLog(
            finalContract
          );

        const savedLog = {
          id: logId,

          lot:
            lotText,

          work:
            activityText,

          material:
            materialText,

          quantity:
            quantityText,

          unit:
            unitText,

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

        setCurrentStep(4);

        showMessage(
          "success",

          isVietnamese
            ? "âœ… Nháº­t kÃ½ Ä‘Ã£ Ä‘Æ°á»£c xÃ¡c nháº­n, lÆ°u qua Integration Service vÃ  cáº­p nháº­t vÃ o Nháº­t kÃ½ cá»§a tÃ´i."
            : "âœ… The log was confirmed, saved through the Integration Service, and added to My Logs."
        );
      } catch (error) {
        console.error(
          "Confirm cultivation log error:",
          error
        );

        showMessage(
          "error",

          isVietnamese
            ? "KhÃ´ng thá»ƒ lÆ°u nháº­t kÃ½ qua Integration Service. HÃ£y kiá»ƒm tra Integration Service vÃ  thá»­ láº¡i."
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
                  ? "Kiá»ƒm tra vÃ  hoÃ n thiá»‡n nháº­t kÃ½"
                  : "Review and complete log"
                : isVietnamese
                  ? "Táº¡o nháº­t kÃ½ canh tÃ¡c báº±ng giá»ng nÃ³i"
                  : "Create farming logs with your voice"}
            </h2>

            <p>
              {editingStatus ===
              "review"
                ? isVietnamese
                  ? "Kiá»ƒm tra cÃ¡c trÆ°á»ng Ä‘Æ°á»£c cáº£nh bÃ¡o, bá»• sung thÃ´ng tin cÃ²n thiáº¿u vÃ  xÃ¡c nháº­n láº¡i nháº­t kÃ½."
                  : "Review highlighted fields, complete missing data and confirm the log."
                : isVietnamese
                  ? "Ghi Ã¢m, Ä‘á»ƒ AI xá»­ lÃ½ vÃ  kiá»ƒm tra dá»¯ liá»‡u trÆ°á»›c khi xÃ¡c nháº­n."
                  : "Record your voice, let AI process it, then review the extracted data before confirming."}
            </p>
          </div>

          <div className="workspace-status">
            <span className="workspace-status-dot" />

            <span>
              {editingStatus ===
              "review"
                ? isVietnamese
                  ? "Äang kiá»ƒm tra"
                  : "Reviewing"
                : isVietnamese
                  ? "Há»‡ thá»‘ng sáºµn sÃ ng"
                  : "System ready"}
            </span>
          </div>
        </section>

        {/* DEV */}

        {isDevMode && (
          <section className="dev-test-panel">
            <div className="dev-test-info">
              <span className="dev-test-icon">
                ðŸ§ª
              </span>

              <div>
                <strong>
                  DEV Test Mode
                </strong>

                <span>
                  {isVietnamese
                    ? "Kiá»ƒm thá»­ frontend khÃ´ng cáº§n AI Service."
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
                âœ…{" "}
                {isVietnamese
                  ? "Há»£p lá»‡"
                  : "Valid"}
              </button>

              <button
                type="button"
                className="dev-test-btn warning"
                onClick={
                  handleLoadWarningTest
                }
              >
                âš ï¸{" "}
                {isVietnamese
                  ? "Cáº£nh bÃ¡o"
                  : "Warning"}
              </button>

              <button
                type="button"
                className="dev-test-btn error"
                onClick={
                  handleLoadErrorTest
                }
              >
                âŒ{" "}
                {isVietnamese
                  ? "Dá»¯ liá»‡u lá»—i"
                  : "Error"}
              </button>

              <button
                type="button"
                className="dev-test-btn reset"
                onClick={
                  handleResetDevTest
                }
              >
                â†º Reset
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
              <AIForm
                aiData={
                  aiData
                }

                onAiDataChange={
                  setAiData
                }

                isConfirmed={
                  isConfirmed
                }

                text={t}

                language={
                  language
                }

                validation={
                  validation
                }

                showValidation={
                  hasAttemptedSubmit
                }

                highlightedField={
                  highlightedField
                }
              />

              <ActionButtons
                hasAudio={
                  Boolean(
                    audioBlob
                  )
                }

                hasResult={
                  Boolean(
                    transcript.trim()
                  )
                }

                isUploading={
                  isUploading
                }

                isConfirmed={
                  isConfirmed
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
                ? "âš ï¸"
                : "âœ…"}
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
