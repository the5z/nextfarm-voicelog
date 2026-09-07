import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  generateId,
} from "../utils/id";

import {
  createBotSession,
  getBotSession,
  sendBotMessage,
  updateBotSession,
} from "../services/botService";

import {
  ASSISTANT_INTENT,
  isQueryIntent,
  routeAssistantIntent,
} from "../services/intentRouter";

import {
  handleQueryIntent,
} from "../services/queryAssistantService";

const STORAGE_KEY =
  "nextfarm-ai-conversations";

const ACTIVE_CHAT_KEY =
  "nextfarm-ai-active-chat";

function createConversation(title = "") {
  return {
    id: generateId(),
    title,
    pinned: false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: [],
  };
}

function AIAssistant({
  language = "vi",
  aiData = {},
  onApplyAiChanges,
  onUndoAiChanges,
  aiAuditEvents = [],
  onDeleteAiAuditEvents,
  onClearAiAuditEvents,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showAudit, setShowAudit] = useState(false);
  const [inputValue, setInputValue] = useState("");

  const [
    pendingEdit,
    setPendingEdit,
  ] = useState(null);


  const [
    isSelectingAudit,
    setIsSelectingAudit,
  ] = useState(false);

  const [
    selectedAuditIds,
    setSelectedAuditIds,
  ] = useState([]);
  const [assistantStatus, setAssistantStatus] =
    useState("ready");
  const [isListening, setIsListening] =
    useState(false);
  const [voiceMessage, setVoiceMessage] =
    useState("");

  const [
    botSessionIds,
    setBotSessionIds,
  ] = useState({});

  const [conversations, setConversations] =
    useState(() => {
      try {
        const saved =
          localStorage.getItem(
            STORAGE_KEY
          );

        if (!saved) {
          const firstConversation =
            createConversation();

          return [firstConversation];
        }

        const parsed =
          JSON.parse(saved);

        if (
          !Array.isArray(parsed) ||
          parsed.length === 0
        ) {
          return [
            createConversation(),
          ];
        }

        return parsed;
      } catch (error) {
        console.error(
          "Load conversations error:",
          error
        );

        return [
          createConversation(),
        ];
      }
    });

  const [activeConversationId, setActiveConversationId] =
    useState(() => {
      try {
        return (
          localStorage.getItem(
            ACTIVE_CHAT_KEY
          ) || ""
        );
      } catch {
        return "";
      }
    });

  const assistantRef = useRef(null);
  const assistantButtonRef = useRef(null);
  const messagesEndRef = useRef(null);
  const responseTimeoutRef = useRef(null);
  const statusResetTimeoutRef = useRef(null);
  const recognitionRef = useRef(null);
  const voiceTranscriptRef = useRef("");
  const voiceResetTimeoutRef = useRef(null);

  const isVietnamese =
    language === "vi";

  const statusConfig = {
    ready: {
      icon: "●",
      label: isVietnamese
        ? "Sẵn sàng"
        : "Ready",
    },
    listening: {
      icon: "🎧",
      label: isVietnamese
        ? "Đang nghe"
        : "Listening",
    },
    thinking: {
      icon: "🧠",
      label: isVietnamese
        ? "Đang suy nghĩ"
        : "Thinking",
    },
    needsInput: {
      icon: "⚠️",
      label: isVietnamese
        ? "Cần bổ sung"
        : "Needs input",
    },
    complete: {
      icon: "✅",
      label: isVietnamese
        ? "Hoàn tất"
        : "Complete",
    },
  };

  const currentStatus =
    statusConfig[assistantStatus] ||
    statusConfig.ready;

  /* ===========================
     Resolve active conversation
  =========================== */

  useEffect(() => {
    const exists =
      conversations.some(
        (conversation) =>
          conversation.id ===
          activeConversationId
      );

    if (!exists) {
      setActiveConversationId(
        conversations[0]?.id || ""
      );
    }
  }, [
    conversations,
    activeConversationId,
  ]);

  const activeConversation =
    useMemo(() => {
      return (
        conversations.find(
          (conversation) =>
            conversation.id ===
            activeConversationId
        ) || conversations[0]
      );
    }, [
      conversations,
      activeConversationId,
    ]);

  const messages =
    activeConversation?.messages || [];

  /* ===========================
     Persist conversations
  =========================== */

  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(
          conversations
        )
      );
    } catch (error) {
      console.error(
        "Save conversations error:",
        error
      );
    }
  }, [conversations]);

  useEffect(() => {
    if (!activeConversationId) {
      return;
    }

    try {
      localStorage.setItem(
        ACTIVE_CHAT_KEY,
        activeConversationId
      );
    } catch (error) {
      console.error(
        "Save active conversation error:",
        error
      );
    }
  }, [activeConversationId]);

  /* ===========================
     Auto-scroll
  =========================== */

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, assistantStatus]);

  useEffect(() => {
    return () => {
      if (responseTimeoutRef.current) {
        clearTimeout(
          responseTimeoutRef.current
        );
      }

      if (statusResetTimeoutRef.current) {
        clearTimeout(
          statusResetTimeoutRef.current
        );
      }

      if (voiceResetTimeoutRef.current) {
        clearTimeout(
          voiceResetTimeoutRef.current
        );
      }

      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore cleanup errors.
        }

        recognitionRef.current = null;
      }

      voiceTranscriptRef.current = "";
    };
  }, []);

  /* ===========================
     Close assistant on outside click / Esc
  =========================== */

  useEffect(() => {
    const handleClickOutside = (
      event
    ) => {
      if (!isOpen) return;

      const clickedInside =
        assistantRef.current?.contains(
          event.target
        );

      const clickedFloatingButton =
        assistantButtonRef.current?.contains(
          event.target
        );

      if (
        !clickedInside &&
        !clickedFloatingButton
      ) {
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }

        setIsOpen(false);
        setShowHistory(false);
        setShowAudit(false);
        setShowAudit(false);
      }
    };

    const handleKeyDown = (
      event
    ) => {
      if (event.key === "Escape") {
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }

        setIsOpen(false);
        setShowHistory(false);
        setShowAudit(false);
        setShowAudit(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    document.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );

      document.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, [isOpen]);

  useEffect(() => {
    const validIds =
      new Set(
        aiAuditEvents.map(
          (event) =>
            event.id
        )
      );

    setSelectedAuditIds(
      (previous) =>
        previous.filter(
          (id) =>
            validIds.has(id)
        )
    );
  }, [aiAuditEvents]);

  /* ===========================
     Current VoiceLog context
  =========================== */

  const getCurrentLogContext = () => {
    return {
      lot:
        String(
          aiData?.lot || ""
        ).trim(),

      work:
        String(
          aiData?.work || ""
        ).trim(),

      material:
        String(
          aiData?.material || ""
        ).trim(),

      quantity:
        String(
          aiData?.quantity ?? ""
        ).trim(),

      unit:
        String(
          aiData?.unit || ""
        ).trim(),

      time:
        String(
          aiData?.time || ""
        ).trim(),
    };
  };

  const formatCurrentLogContext = (
    replyInVietnamese = isVietnamese
  ) => {
    const context =
      getCurrentLogContext();

    const hasData =
      Object.values(
        context
      ).some(
        (value) =>
          String(value).trim() !== ""
      );

    if (!hasData) {
      return replyInVietnamese
        ? "Nhật ký hiện tại chưa có dữ liệu để tôi đọc."
        : "The current log does not have any data yet.";
    }

    const valueOrMissing = (
      value
    ) => {
      if (
        value !== "" &&
        value !== null &&
        value !== undefined
      ) {
        return value;
      }

      return replyInVietnamese
        ? "chưa có"
        : "not provided";
    };

    if (replyInVietnamese) {
      return [
        "Dữ liệu nhật ký hiện tại:",
        `• Lô canh tác: ${valueOrMissing(
          context.lot
        )}`,
        `• Công việc: ${valueOrMissing(
          context.work
        )}`,
        `• Vật tư: ${valueOrMissing(
          context.material
        )}`,
        `• Số lượng: ${valueOrMissing(
          context.quantity
        )}`,
        `• Đơn vị: ${valueOrMissing(
          context.unit
        )}`,
        `• Thời gian: ${valueOrMissing(
          context.time
        )}`,
      ].join("\n");
    }

    return [
      "Current farming log:",
      `• Plot: ${valueOrMissing(
        context.lot
      )}`,
      `• Task: ${valueOrMissing(
        context.work
      )}`,
      `• Material: ${valueOrMissing(
        context.material
      )}`,
      `• Quantity: ${valueOrMissing(
        context.quantity
      )}`,
      `• Unit: ${valueOrMissing(
        context.unit
      )}`,
      `• Time: ${valueOrMissing(
        context.time
      )}`,
    ].join("\n");
  };

  /* ===========================
     Edit command understanding
     Upgrade 3B:
     - chỉ phân tích lệnh
     - CHƯA thay đổi form
  =========================== */

  const normalizeEditText = (
    value
  ) => {
    return String(
      value || ""
    )
      .trim()
      .replace(
        /\s+/g,
        " "
      );
  };

  const parseEditCommand = (
    message
  ) => {
    const original =
      normalizeEditText(
        message
      );

    const changes = {};

    const setChange = (
      field,
      value
    ) => {
      const cleanValue =
        normalizeEditText(
          value
        );

      if (!cleanValue) {
        return;
      }

      changes[field] =
        cleanValue;
    };

    const clauses =
      original
        .split(
          /\s*(?:,|;)\s*|\s+và\s+(?=(?:lô(?:\s+canh\s+tác)?|công\s+việc|hoạt\s+động|vật\s+tư|số\s+lượng|đơn\s+vị|thời\s+gian|giờ)(?:\s|$))/i
        )
        .map(
          (part) =>
            part.trim()
        )
        .filter(Boolean);

    const parseClause = (
      clause
    ) => {
      let match;

      match =
        clause.match(
          /(?:đổi|sửa|cập nhật)?\s*(?:lô(?:\s+canh\s+tác)?)(?:\s+[A-Za-z0-9_-]+)?\s+(?:thành|sang|là)\s+([A-Za-z0-9_-]+)/i
        );

      if (!match) {
        match =
          clause.match(
            /không\s+phải\s+lô(?:\s+canh\s+tác)?\s+[A-Za-z0-9_-]+\s*[,，]?\s*(?:mà\s+)?(?:là|thành)\s+([A-Za-z0-9_-]+)/i
          );
      }

      if (!match) {
        match =
          clause.match(
            /change\s+(?:the\s+)?plot(?:\s+[A-Za-z0-9_-]+)?\s+to\s+([A-Za-z0-9_-]+)/i
          );
      }

      if (match) {
        setChange(
          "lot",
          match[1]
        );

        return;
      }

      match =
        clause.match(
          /(?:đổi|sửa|cập nhật)?\s*(?:công\s+việc|hoạt\s+động)\s+(?:thành|sang|là)\s+(.+)$/i
        );

      if (!match) {
        match =
          clause.match(
            /change\s+(?:the\s+)?(?:task|activity)\s+to\s+(.+)$/i
          );
      }

      if (match) {
        setChange(
          "work",
          match[1]
        );

        return;
      }

      match =
        clause.match(
          /(?:đổi|sửa|cập nhật)?\s*vật\s+tư\s+(?:thành|sang|là)\s+(.+)$/i
        );

      if (!match) {
        match =
          clause.match(
            /change\s+(?:the\s+)?material\s+to\s+(.+)$/i
          );
      }

      if (match) {
        setChange(
          "material",
          match[1]
        );

        return;
      }

      match =
        clause.match(
          /(?:đổi|sửa|cập nhật)?\s*số\s+lượng\s+(?:thành|sang|là)\s+(-?\d+(?:[.,]\d+)?)\s*([^\s,;.]+)?/i
        );

      if (!match) {
        match =
          clause.match(
            /change\s+(?:the\s+)?quantity\s+to\s+(-?\d+(?:[.,]\d+)?)\s*([^\s,;.]+)?/i
          );
      }

      if (match) {
        setChange(
          "quantity",
          match[1].replace(
            ",",
            "."
          )
        );

        if (match[2]) {
          setChange(
            "unit",
            match[2]
          );
        }

        return;
      }

      match =
        clause.match(
          /(?:đổi|sửa|cập nhật)?\s*đơn\s+vị\s+(?:thành|sang|là)\s+([^\s,;.]+)/i
        );

      if (!match) {
        match =
          clause.match(
            /change\s+(?:the\s+)?unit\s+to\s+([^\s,;.]+)/i
          );
      }

      if (match) {
        setChange(
          "unit",
          match[1]
        );

        return;
      }

      match =
        clause.match(
          /(?:đổi|sửa|cập nhật)?\s*(?:thời\s+gian|giờ)\s+(?:thành|sang|là)\s+(\d{1,2})(?::|h| giờ )(\d{1,2})/i
        );

      if (!match) {
        match =
          clause.match(
            /change\s+(?:the\s+)?time\s+to\s+(\d{1,2}):(\d{1,2})/i
          );
      }

      if (match) {
        const hour =
          String(
            Number(match[1])
          ).padStart(
            2,
            "0"
          );

        const minute =
          String(
            Number(match[2])
          ).padStart(
            2,
            "0"
          );

        setChange(
          "time",
          `${hour}:${minute}`
        );

        return;
      }

      match =
        clause.match(
          /(?:đổi|sửa|cập nhật)?\s*(?:thời\s+gian|giờ)\s+(?:thành|sang|là)\s+(\d{1,2})\s*(?:giờ|h)\s*$/i
        );

      if (match) {
        const hour =
          String(
            Number(match[1])
          ).padStart(
            2,
            "0"
          );

        setChange(
          "time",
          `${hour}:00`
        );
      }
    };

    clauses.forEach(
      parseClause
    );

    return {
      isEditCommand:
        Object.keys(
          changes
        ).length > 0,

      changes,
    };
  };

  const formatAppliedChanges = (
    changes,
    replyInVietnamese = isVietnamese
  ) => {
    const current =
      getCurrentLogContext();

    const labels = {
      lot: replyInVietnamese
        ? "Lô canh tác"
        : "Plot",

      work: replyInVietnamese
        ? "Công việc"
        : "Task",

      material: replyInVietnamese
        ? "Vật tư"
        : "Material",

      quantity: replyInVietnamese
        ? "Số lượng"
        : "Quantity",

      unit: replyInVietnamese
        ? "Đơn vị"
        : "Unit",

      time: replyInVietnamese
        ? "Thời gian"
        : "Time",
    };

    const lines =
      Object.entries(
        changes
      ).map(
        ([
          field,
          nextValue,
        ]) => {
          const oldValue =
            current[field] ||
            (replyInVietnamese
              ? "chưa có"
              : "not provided");

          return `• ${labels[field]}: ${oldValue} → ${nextValue}`;
        }
      );

    if (replyInVietnamese) {
      return [
        "✅ Đã cập nhật dữ liệu nhật ký:",
        ...lines,
        "",
        "Bạn có thể kiểm tra lại trực tiếp trên form.",
      ].join("");
    }

    return [
      "✅ Farming log updated:",
      ...lines,
      "",
      "You can review the changes directly in the form.",
    ].join("");
  };

  const getMeaningfulChanges = (
    changes
  ) => {
    const current =
      getCurrentLogContext();

    return Object.fromEntries(
      Object.entries(
        changes || {}
      ).filter(
        ([
          field,
          nextValue,
        ]) => {
          const currentValue =
            String(
              current[field] ?? ""
            ).trim();

          const normalizedNext =
            String(
              nextValue ?? ""
            ).trim();

          return (
            currentValue !==
            normalizedNext
          );
        }
      )
    );
  };

  const formatMultiEditPreview = (
    changes,
    replyInVietnamese = isVietnamese
  ) => {
    const current =
      getCurrentLogContext();

    const labels = {
      lot: replyInVietnamese
        ? "Lô canh tác"
        : "Plot",

      work: replyInVietnamese
        ? "Công việc"
        : "Task",

      material: replyInVietnamese
        ? "Vật tư"
        : "Material",

      quantity: replyInVietnamese
        ? "Số lượng"
        : "Quantity",

      unit: replyInVietnamese
        ? "Đơn vị"
        : "Unit",

      time: replyInVietnamese
        ? "Thời gian"
        : "Time",
    };

    const entries =
      Object.entries(
        changes
      );

    const lines =
      entries.map(
        ([
          field,
          nextValue,
        ]) => {
          const oldValue =
            current[field] ||
            (replyInVietnamese
              ? "chưa có"
              : "not provided");

          return `• ${labels[field]}: ${oldValue} → ${nextValue}`;
        }
      );

    if (replyInVietnamese) {
      return [
        `⚠️ AI chuẩn bị cập nhật ${entries.length} trường:`,
        ...lines,
        "",
        "Hãy kiểm tra trước khi áp dụng.",
      ].join("\n");
    }

    return [
      `⚠️ AI is ready to update ${entries.length} fields:`,
      ...lines,
      "",
      "Review the changes before applying them.",
    ].join("\n");
  };

  const formatUndoResult = (
    result,
    replyInVietnamese = isVietnamese
  ) => {
    if (
      !result ||
      !result.success
    ) {
      return replyInVietnamese
        ? "Hiện chưa có thay đổi AI nào để hoàn tác."
        : "There is no AI edit to undo yet.";
    }

    const labels = {
      lot: replyInVietnamese
        ? "Lô canh tác"
        : "Plot",

      work: replyInVietnamese
        ? "Công việc"
        : "Task",

      material: replyInVietnamese
        ? "Vật tư"
        : "Material",

      quantity: replyInVietnamese
        ? "Số lượng"
        : "Quantity",

      unit: replyInVietnamese
        ? "Đơn vị"
        : "Unit",

      time: replyInVietnamese
        ? "Thời gian"
        : "Time",
    };

    const previousValues =
      result.previousValues || {};

    const appliedChanges =
      result.appliedChanges || {};

    const lines =
      Object.keys(
        previousValues
      ).map(
        (field) => {
          const fromValue =
            appliedChanges[field] ??
            (replyInVietnamese
              ? "chưa có"
              : "not provided");

          const toValue =
            previousValues[field] ||
            (replyInVietnamese
              ? "chưa có"
              : "not provided");

          return `• ${labels[field] || field}: ${fromValue} → ${toValue}`;
        }
      );

    if (replyInVietnamese) {
      return [
        "↩️ Đã hoàn tác thay đổi AI gần nhất:",
        ...lines,
        "",
        "Form đã được khôi phục về dữ liệu trước đó.",
      ].join("\n");
    }

    return [
      "↩️ Latest AI edit undone:",
      ...lines,
      "",
      "The form has been restored to its previous values.",
    ].join("\n");
  };

  /* ===========================
     Voice Bot API
  =========================== */

  const syncBotSession = async (
    nextAiData = aiData
  ) => {
    const conversationId =
      activeConversationId;

    if (!conversationId) {
      return null;
    }

    const currentSessionId =
      botSessionIds[
        conversationId
      ];

    const session =
      currentSessionId
        ? await updateBotSession(
            currentSessionId,
            nextAiData
          )
        : await createBotSession(
            nextAiData
          );

    if (
      session?.session_id &&
      session.session_id !==
        currentSessionId
    ) {
      setBotSessionIds(
        (previous) => ({
          ...previous,
          [conversationId]:
            session.session_id,
        })
      );
    }

    return session;
  };

  const appendBotSessionGuidance = (
    baseText,
    session,
    replyInVietnamese = isVietnamese
  ) => {
    const text =
      String(
        baseText ?? ""
      ).trim();

    if (!session) {
      return text;
    }

    const additions = [];

    if (
      Array.isArray(
        session.warnings
      ) &&
      session.warnings.length > 0
    ) {
      additions.push(
        replyInVietnamese
          ? `⚠️ ${session.warnings.join(
              "\n⚠️ "
            )}`
          : `⚠️ ${session.warnings.join(
              "\n⚠️ "
            )}`
      );
    }

    if (
      session.status ===
        "collecting" &&
      session.next_question
    ) {
      additions.push(
        `🤖 ${session.next_question}`
      );
    } else if (
      session.status ===
        "completed" &&
      !session.requires_confirmation
    ) {
      additions.push(
        replyInVietnamese
          ? "✅ Voice Bot đã đồng bộ và dữ liệu nhật ký hiện đã đầy đủ."
          : "✅ Voice Bot is synchronized and the farming log data is complete."
      );
    }

    return [
      text,
      ...additions,
    ]
      .filter(Boolean)
      .join("\n\n");
  };

  const syncBotSessionSafely = async (
    nextAiData,
    fallbackText,
    replyInVietnamese = isVietnamese
  ) => {
    try {
      const session =
        await syncBotSession(
          nextAiData
        );

      return {
        session,
        text:
          appendBotSessionGuidance(
            fallbackText,
            session,
            replyInVietnamese
          ),
      };
    } catch (error) {
      console.error(
        "Voice Bot API error:",
        error
      );

      return {
        session: null,
        text: [
          String(
            fallbackText ?? ""
          ).trim(),
          replyInVietnamese
            ? "⚠️ Không thể đồng bộ với Voice Bot API. Kiểm tra AI Service tại cổng 8000 rồi thử lại."
            : "⚠️ Unable to synchronize with the Voice Bot API. Check the AI Service on port 8000 and try again.",
        ]
          .filter(Boolean)
          .join("\n\n"),
      };
    }
  };

  const getAiDataFromBotSession = (
    session
  ) => {
    const collectedData =
      session?.collected_data || {};

    const firstMaterial =
      Array.isArray(
        collectedData.materials
      ) &&
      collectedData.materials.length > 0
        ? collectedData.materials[0]
        : {};

    return {
      lot:
        collectedData.lot_text ??
        "",

      work:
        collectedData.activity_text ??
        "",

      material:
        firstMaterial?.material_text ??
        "",

      quantity:
        firstMaterial?.quantity ??
        "",

      unit:
        firstMaterial?.unit_text ??
        "",

      time:
        collectedData.time_text ??
        "",
    };
  };


  const isLikelyBotContextReply = (
    message,
    expectedField
  ) => {
    const text =
      String(
        message ?? ""
      ).trim();

    if (!text || !expectedField) {
      return false;
    }

    /*
      Backend có thể trả:
      - material_text
      - materials.material_text

      Ta chỉ lấy tên field cuối cùng để
      frontend tương thích với cả hai.
    */
    const normalizedExpectedField =
      String(expectedField)
        .trim()
        .split(".")
        .pop();

    /*
      Query luôn được ưu tiên hơn
      câu trả lời bổ sung VoiceLog.
    */
    if (
      isQueryIntent(
        text
      )
    ) {
      return false;
    }

    /*
      ==========================
      Thời gian
      ==========================
    */
    if (
      normalizedExpectedField ===
      "time_text"
    ) {
      return /^(?:(?:lúc|thời\s+gian(?:\s+là)?|giờ(?:\s+là)?)\s+)?\d{1,2}(?:(?::|h)\d{1,2}|\s+giờ(?:\s+\d{1,2})?)?\s*$/i.test(
        text
      );
    }

    /*
      ==========================
      Lô canh tác
      ==========================
    */
    if (
      normalizedExpectedField ===
      "lot_text"
    ) {
      const normalizedText =
        text.trim();

      /*
        Chấp nhận:
        Lô A
        lô B
        A
        B
        LO_A

        Không nhận:
        1313
        298
      */
      return /^(?:(?:lô|lo)[\s_-]*)?[A-Za-z][A-Za-z0-9_-]{0,19}$/i.test(
        normalizedText
      );
    }

    /*
      ==========================
      Số lượng
      ==========================
    */
    if (
      normalizedExpectedField ===
      "quantity"
    ) {
      return /^(?:số\s+lượng\s+)?\d+(?:[.,]\d+)?(?:\s*[^\d\s,;.]+)?\s*$/i.test(
        text
      );
    }

    /*
      ==========================
      Đơn vị
      ==========================
    */
    if (
      normalizedExpectedField ===
      "unit_text"
    ) {
      const hasLetter =
        /[A-Za-zÀ-ỹ]/.test(
          text
        );

      const isOnlyNumber =
        /^\d+(?:[.,]\d+)?$/.test(
          text
        );

      return (
        text.length <= 30 &&
        hasLetter &&
        !isOnlyNumber &&
        !/[?]/.test(text)
      );
    }

    /*
      ==========================
      Vật tư
      ==========================
    */
    if (
      normalizedExpectedField ===
      "material_text"
    ) {
      const hasLetter =
        /[A-Za-zÀ-ỹ]/.test(
          text
        );

      const isOnlyNumber =
        /^\d+(?:[.,]\d+)?$/.test(
          text
        );

      return (
        text.length <= 80 &&
        hasLetter &&
        !isOnlyNumber &&
        !/[?]/.test(text)
      );
    }

    /*
      ==========================
      Hoạt động / công việc
      ==========================
    */
    if (
      normalizedExpectedField ===
      "activity_text"
    ) {
      const normalizedText =
        text
          .toLowerCase()
          .trim();

      const looksLikeQuery =
        /(?:nh\u1eadt k\u00fd|l\u1ecbch s\u1eed|cho t\u00f4i xem|tra c\u1ee9u|t\u00ecm|bao nhi\u00eau|m\u1ea5y l\u1ea7n|l\u00f4 n\u00e0o|ho\u1ea1t \u0111\u1ed9ng g\u00ec|c\u00f4ng vi\u1ec7c g\u00ec|h\u00f4m nay c\u00f3|h\u00f4m qua c\u00f3)/i.test(
          normalizedText
        );

      const isOnlyNumber =
        /^\d+(?:[.,]\d+)?$/.test(
          normalizedText
        );

      const looksLikeTime =
        /^\d{1,2}(?::\d{1,2}|h\d{0,2})?$/i.test(
          normalizedText
        );

      const hasLetter =
        /[A-Za-zÀ-ỹ]/.test(
          text
        );

      return (
        text.length <= 120 &&
        hasLetter &&
        !isOnlyNumber &&
        !looksLikeTime &&
        !/[?]/.test(text) &&
        !looksLikeQuery
      );
    }

    return false;
  };


  const getCurrentBotSession =
    async () => {
      const conversationId =
        activeConversationId;

      if (!conversationId) {
        return null;
      }

      const sessionId =
        botSessionIds[
          conversationId
        ];

      if (!sessionId) {
        return null;
      }

      try {
        return await getBotSession(
          sessionId
        );
      } catch (error) {
        console.error(
          "Get Voice Bot session error:",
          error
        );

        return null;
      }
    };


  /* ===========================
     Local demo response
  =========================== */

  const getBotResponse = (
    message
  ) => {
    const normalized =
      message.toLowerCase();

    const vietnameseQuestion =
      /[ăâđêôơưáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ]/i.test(
        message
      ) ||
      normalized.includes(
        "cho tôi"
      ) ||
      normalized.includes(
        "thông tin"
      );

    const replyInVietnamese =
      vietnameseQuestion ||
      isVietnamese;

    const asksUndo =
      normalized === "undo" ||
      normalized.includes(
        "hoàn tác"
      ) ||
      normalized.includes(
        "quay lại thay đổi trước"
      ) ||
      normalized.includes(
        "khôi phục thay đổi trước"
      ) ||
      normalized.includes(
        "undo last change"
      );

    if (asksUndo) {
      return {
        type: "undo",
      };
    }

    const editCommand =
      parseEditCommand(
        message
      );

    if (
      editCommand
        .isEditCommand
    ) {
      return {
        type: "edit",
        changes:
          editCommand.changes,
        text:
          formatAppliedChanges(
            editCommand.changes,
            replyInVietnamese
          ),
      };
    }

    const asksCurrentLog =
      normalized.includes(
        "dữ liệu hiện tại"
      ) ||
      normalized.includes(
        "nhật ký hiện tại"
      ) ||
      normalized.includes(
        "form hiện tại"
      ) ||
      normalized.includes(
        "đang có gì"
      ) ||
      normalized.includes(
        "đã có gì"
      ) ||
      normalized.includes(
        "đọc dữ liệu"
      ) ||
      normalized.includes(
        "đọc thông tin hiện tại"
      ) ||
      normalized.includes(
        "current log"
      ) ||
      normalized.includes(
        "current form"
      ) ||
      normalized.includes(
        "current data"
      );

    if (asksCurrentLog) {
      return formatCurrentLogContext(
        replyInVietnamese
      );
    }

    if (
      normalized.includes(
        "a01"
      ) ||
      normalized.includes(
        "lô a"
      )
    ) {
      return replyInVietnamese
        ? "Lô A01 hiện đang được hệ thống ghi nhận. Khi kết nối API NextFarm, tôi sẽ lấy thông tin cây trồng, diện tích, trạng thái và nhật ký gần nhất của lô này."
        : "Plot A01 is currently recognized by the system. Once the NextFarm API is connected, I will retrieve its crop, area, status and latest farming logs.";
    }

    if (
      normalized.includes("ớt") ||
      normalized.includes("chili")
    ) {
      return replyInVietnamese
        ? "Bạn đang hỏi về cây ớt. Khi tích hợp dữ liệu NextFarm, tôi có thể cung cấp thông tin lô đang trồng ớt, tình trạng canh tác, vật tư đã sử dụng và các nhật ký liên quan."
        : "You are asking about chili crops. After connecting to NextFarm data, I will be able to provide related plots, farming status, materials used and recent logs.";
    }

    if (
      normalized.includes(
        "nhật ký"
      ) ||
      normalized.includes("log")
    ) {
      return replyInVietnamese
        ? "Chức năng lấy nhật ký gần nhất sẽ được kết nối với API lưu trữ nhật ký. Hiện tại đây đang là phản hồi thử nghiệm trên frontend."
        : "The latest log feature will be connected to the farming log API. This is currently a frontend test response.";
    }

    return replyInVietnamese
      ? (
          "Tôi có thể hỗ trợ tra cứu nhật ký canh tác, "
          + "hoạt động theo lô, số lần thực hiện công việc, "
          + "vật tư đã sử dụng hoặc hỗ trợ hoàn thiện nhật ký đang tạo. "
          + "Ví dụ: “Hôm nay có hoạt động gì?” hoặc "
          + "“Lô A bón phân bao nhiêu lần?”"
        )
      : (
          "I can help query cultivation logs, activities by plot, "
          + "activity counts, material usage, or complete the current farming log."
        );
  };
  /* ===========================
     Conversation helpers
  =========================== */

  const updateActiveConversation = (
    updater
  ) => {
    setConversations(
      (previous) =>
        previous.map(
          (conversation) => {
            if (
              conversation.id !==
              activeConversationId
            ) {
              return conversation;
            }

            return updater(
              conversation
            );
          }
        )
    );
  };

  const returnToChat = () => {
    setShowHistory(false);
    setShowAudit(false);
    setIsSelectingAudit(false);
    setSelectedAuditIds([]);
  };

  const createNewChat = () => {
    const conversation =
      createConversation();

    setConversations(
      (previous) => [
        conversation,
        ...previous,
      ]
    );

    setActiveConversationId(
      conversation.id
    );

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    setInputValue("");
    setVoiceMessage("");
    returnToChat();
    setAssistantStatus("ready");
  };

  const selectConversation = (
    id
  ) => {
    setActiveConversationId(id);
    returnToChat();
  };

  const togglePinConversation = (
    id
  ) => {
    setConversations(
      (previous) =>
        previous.map(
          (conversation) =>
            conversation.id === id
              ? {
                  ...conversation,
                  pinned:
                    !conversation.pinned,
                }
              : conversation
        )
    );
  };

  const deleteConversation = (
    id
  ) => {
    setBotSessionIds(
      (previous) => {
        const next = {
          ...previous,
        };

        delete next[id];

        return next;
      }
    );

    setConversations(
      (previous) => {
        const filtered =
          previous.filter(
            (conversation) =>
              conversation.id !== id
          );

        if (
          filtered.length === 0
        ) {
          const replacement =
            createConversation();

          setActiveConversationId(
            replacement.id
          );

          return [replacement];
        }

        if (
          id ===
          activeConversationId
        ) {
          setActiveConversationId(
            filtered[0].id
          );
        }

        return filtered;
      }
    );
  };

  /* ===========================
     Voice input
  =========================== */

  const clearVoiceResetTimer = () => {
    if (voiceResetTimeoutRef.current) {
      clearTimeout(
        voiceResetTimeoutRef.current
      );

      voiceResetTimeoutRef.current =
        null;
    }
  };

  const resetVoiceStatusLater = () => {
    clearVoiceResetTimer();

    voiceResetTimeoutRef.current =
      setTimeout(() => {
        setVoiceMessage("");

        setAssistantStatus((current) =>
          current === "needsInput"
            ? "ready"
            : current
        );

        voiceResetTimeoutRef.current =
          null;
      }, 2200);
  };

  const stopVoiceInput = () => {
    if (!recognitionRef.current) {
      return;
    }

    try {
      recognitionRef.current.stop();
    } catch (error) {
      console.error(
        "Stop speech recognition error:",
        error
      );
    }
  };

  const startVoiceInput = () => {
    if (assistantStatus === "thinking") {
      return;
    }

    if (isListening) {
      stopVoiceInput();
      return;
    }

    clearVoiceResetTimer();
    setVoiceMessage("");

    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setAssistantStatus("needsInput");

      setVoiceMessage(
        isVietnamese
          ? "Trình duyệt này chưa hỗ trợ nhận dạng giọng nói trực tiếp. Bạn vẫn có thể nhập câu hỏi bằng bàn phím."
          : "This browser does not support direct speech recognition. You can still type your question."
      );

      resetVoiceStatusLater();
      return;
    }

    const recognition =
      new SpeechRecognition();

    recognition.lang =
      isVietnamese
        ? "vi-VN"
        : "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;

    voiceTranscriptRef.current = "";

    recognition.onstart = () => {
      setIsListening(true);
      setAssistantStatus("listening");

      setVoiceMessage(
        isVietnamese
          ? "Đang nghe... Hãy nói câu hỏi của bạn."
          : "Listening... Ask your question."
      );
    };

    recognition.onresult = (event) => {
      let finalTranscript =
        voiceTranscriptRef.current;
      let interimTranscript = "";

      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        const result =
          event.results[index];

        const transcript =
          result?.[0]?.transcript?.trim() || "";

        if (!transcript) {
          continue;
        }

        if (result.isFinal) {
          finalTranscript = `${finalTranscript} ${transcript}`.trim();
        } else {
          interimTranscript = `${interimTranscript} ${transcript}`.trim();
        }
      }

      voiceTranscriptRef.current =
        finalTranscript;

      const preview = [
        finalTranscript,
        interimTranscript,
      ]
        .filter(Boolean)
        .join(" ")
        .trim();

      if (preview) {
        setInputValue(preview);
      }
    };

    recognition.onerror = (event) => {
      console.error(
        "Speech recognition error:",
        event.error
      );

      setIsListening(false);

      if (event.error === "aborted") {
        return;
      }

      setAssistantStatus("needsInput");

      const errorMessages = {
        "not-allowed": isVietnamese
          ? "Chưa được cấp quyền microphone. Hãy cho phép trình duyệt sử dụng microphone."
          : "Microphone permission was denied. Allow microphone access and try again.",
        "no-speech": isVietnamese
          ? "Chưa nghe thấy giọng nói. Hãy thử nói gần microphone hơn."
          : "No speech was detected. Try speaking closer to the microphone.",
        "audio-capture": isVietnamese
          ? "Không tìm thấy microphone khả dụng."
          : "No available microphone was found.",
        network: isVietnamese
          ? "Dịch vụ nhận dạng giọng nói tạm thời không khả dụng."
          : "Speech recognition is temporarily unavailable.",
      };

      setVoiceMessage(
        errorMessages[event.error] ||
          (isVietnamese
            ? "Không thể nhận dạng giọng nói. Vui lòng thử lại."
            : "Speech recognition failed. Please try again.")
      );

      resetVoiceStatusLater();
    };

    recognition.onend = () => {
      recognitionRef.current = null;
      setIsListening(false);

      const transcript =
        voiceTranscriptRef.current.trim();

      voiceTranscriptRef.current = "";

      if (transcript) {
        setInputValue(transcript);

        window.setTimeout(() => {
          void sendMessage(transcript);
        }, 0);

        return;
      }

      setAssistantStatus((current) =>
        current === "listening"
          ? "ready"
          : current
      );

      setVoiceMessage((current) =>
        current.startsWith("Đang nghe") ||
        current.startsWith("Listening")
          ? ""
          : current
      );
    };

    recognitionRef.current =
      recognition;

    try {
      recognition.start();
    } catch (error) {
      console.error(
        "Start speech recognition error:",
        error
      );

      recognitionRef.current = null;
      voiceTranscriptRef.current = "";
      setIsListening(false);
      setAssistantStatus("needsInput");

      setVoiceMessage(
        isVietnamese
          ? "Không thể bắt đầu nhận dạng giọng nói. Vui lòng thử lại."
          : "Unable to start speech recognition. Please try again."
      );

      resetVoiceStatusLater();
    }
  };

  /* ===========================
     Send message
  =========================== */

  const sendMessage = async (
    message
  ) => {
    const cleanMessage =
      message.trim();

    if (
      !cleanMessage ||
      assistantStatus === "thinking" ||
      pendingEdit
    ) {
      return;
    }

    if (statusResetTimeoutRef.current) {
      clearTimeout(
        statusResetTimeoutRef.current
      );

      statusResetTimeoutRef.current =
        null;
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    setVoiceMessage("");
    setAssistantStatus("thinking");

    const now =
      new Date().toISOString();

    const userMessage = {
      id: generateId(),
      role: "user",
      text: cleanMessage,
      createdAt: now,
    };

    updateActiveConversation(
      (conversation) => ({
        ...conversation,
        title:
          conversation.title ||
          cleanMessage.slice(
            0,
            34
          ),
        updatedAt: now,
        messages: [
          ...conversation.messages,
          userMessage,
        ],
      })
    );

    setInputValue("");

    try {
      const replyInVietnamese =
        /[ăâđêôơưáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ]/i.test(
          cleanMessage
        ) ||
        cleanMessage
          .toLowerCase()
          .includes(
            "cho tôi"
          ) ||
        cleanMessage
          .toLowerCase()
          .includes(
            "thông tin"
          ) ||
        isVietnamese;

      const currentBotSession =
        await getCurrentBotSession();

      console.log(
        "VOICE BOT DEBUG",
        {
          status:
            currentBotSession?.status,

          expectedField:
            currentBotSession?.expected_field,

          collectedData:
            currentBotSession?.collected_data,
        }
      );

      const isContextReply =
        currentBotSession?.status ===
          "collecting" &&
        Boolean(
          currentBotSession
            ?.expected_field
        ) &&
        isLikelyBotContextReply(
          cleanMessage,
          currentBotSession
            .expected_field
        );

      const assistantIntent =
        routeAssistantIntent({
          message: cleanMessage,

          hasCollectingSession:
            currentBotSession?.status ===
            "collecting",

          expectedField:
            currentBotSession
              ?.expected_field ||
            null,

          isContextReply,
        });
        
      console.log(
        "VOICE BOT ROUTING",
        {
          message:
            cleanMessage,

          isContextReply,

          assistantIntent,
        }
      );
      const shouldUseContextMessage =
        assistantIntent ===
        ASSISTANT_INTENT
          .VOICELOG_CONTEXT;

      if (shouldUseContextMessage) {
        const updatedSession =
          await sendBotMessage(
            currentBotSession
              .session_id,
            cleanMessage
          );

        const nextAiData =
          getAiDataFromBotSession(
            updatedSession
          );

        const botChanges =
          getMeaningfulChanges(
            nextAiData
          );

        if (
          Object.keys(
            botChanges
          ).length > 0
        ) {
          onApplyAiChanges?.(
            botChanges
          );
        }

        const baseText =
          Object.keys(
            botChanges
          ).length > 0
            ? formatAppliedChanges(
                botChanges,
                replyInVietnamese
              )
            : (
                replyInVietnamese
                  ? "Tôi chưa nhận diện được câu trả lời cho thông tin đang thiếu."
                  : "I could not recognize the answer for the missing information."
              );

        const responseText =
          appendBotSessionGuidance(
            baseText,
            updatedSession,
            replyInVietnamese
          );

        const botMessage = {
          id: generateId(),
          role: "assistant",
          text: responseText,
          createdAt:
            new Date().toISOString(),
        };

        updateActiveConversation(
          (conversation) => ({
            ...conversation,
            updatedAt:
              new Date().toISOString(),
            messages: [
              ...conversation.messages,
              botMessage,
            ],
          })
        );

        setAssistantStatus(
          updatedSession?.status ===
            "completed"
            ? "complete"
            : "needsInput"
        );

        statusResetTimeoutRef.current =
          setTimeout(() => {
            setAssistantStatus(
              (current) =>
                current ===
                  "needsInput"
                  ? current
                  : "ready"
            );

            statusResetTimeoutRef.current =
              null;
          }, 1400);

        return;
      }

      if (
        assistantIntent ===
        ASSISTANT_INTENT.QUERY
      ) {
        const responseText =
          await handleQueryIntent({
            message: cleanMessage,
            isVietnamese:
              replyInVietnamese,
          });

        const botMessage = {
          id: generateId(),
          role: "assistant",
          text: responseText,
          createdAt:
            new Date().toISOString(),
        };

        updateActiveConversation(
          (conversation) => ({
            ...conversation,
            updatedAt:
              new Date().toISOString(),
            messages: [
              ...conversation.messages,
              botMessage,
            ],
          })
        );

        setAssistantStatus(
          "complete"
        );

        statusResetTimeoutRef.current =
          setTimeout(() => {
            setAssistantStatus(
              "ready"
            );

            statusResetTimeoutRef.current =
              null;
          }, 1400);

        return;
      }

      /*
        Tin nhắn GENERAL không thuộc quá trình
        bổ sung dữ liệu VoiceLog.

        Vì vậy không đồng bộ nó với Voice Bot session.
      */
      if (
        assistantIntent ===
        ASSISTANT_INTENT.GENERAL
      ) {
        const responseText =
          getBotResponse(
            cleanMessage
          );

        const botMessage = {
          id: generateId(),
          role: "assistant",
          text: responseText,
          createdAt:
            new Date().toISOString(),
        };

        updateActiveConversation(
          (conversation) => ({
            ...conversation,
            updatedAt:
              new Date().toISOString(),
            messages: [
              ...conversation.messages,
              botMessage,
            ],
          })
        );

        setAssistantStatus(
          "complete"
        );

        statusResetTimeoutRef.current =
          setTimeout(() => {
            setAssistantStatus(
              "ready"
            );

            statusResetTimeoutRef.current =
              null;
          }, 1400);

        return;
      }

      const botResponse =
        getBotResponse(
          cleanMessage
        );

      const isObjectResponse =
        typeof botResponse ===
          "object" &&
        botResponse !== null;

      const isEditResponse =
        isObjectResponse &&
        botResponse?.type ===
          "edit";

      const isUndoResponse =
        isObjectResponse &&
        botResponse?.type ===
          "undo";

      let responseText =
        botResponse;

      let dataForBot =
        aiData;

      let shouldSyncBot =
        true;

      if (isEditResponse) {
        const meaningfulChanges =
          getMeaningfulChanges(
            botResponse.changes
          );

        const changeCount =
          Object.keys(
            meaningfulChanges
          ).length;

        if (changeCount === 0) {
          responseText =
            isVietnamese
              ? "Các giá trị bạn yêu cầu đã giống dữ liệu hiện tại nên không cần thay đổi."
              : "The requested values already match the current data, so no changes are needed.";
        } else if (
          changeCount === 1
        ) {
          onApplyAiChanges?.(
            meaningfulChanges
          );

          dataForBot = {
            ...aiData,
            ...meaningfulChanges,
          };

          responseText =
            formatAppliedChanges(
              meaningfulChanges,
              replyInVietnamese
            );
        } else {
          setPendingEdit({
            changes:
              meaningfulChanges,
            replyInVietnamese,
          });

          responseText =
            formatMultiEditPreview(
              meaningfulChanges,
              replyInVietnamese
            );

          shouldSyncBot =
            false;
        }
      }

      if (isUndoResponse) {
        const undoResult =
          onUndoAiChanges?.();

        const undoReplyInVietnamese =
          /[ăâđêôơưáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ]/i.test(
            cleanMessage
          ) ||
          cleanMessage
            .toLowerCase()
            .includes(
              "hoàn tác"
            ) ||
          isVietnamese;

        responseText =
          formatUndoResult(
            undoResult,
            undoReplyInVietnamese
          );

        if (
          undoResult?.success
        ) {
          dataForBot = {
            ...aiData,
            ...(
              undoResult
                .previousValues ||
              {}
            ),
          };
        }
      }

      if (shouldSyncBot) {
        const botSync =
          await syncBotSessionSafely(
            dataForBot,
            responseText,
            replyInVietnamese
          );

        responseText =
          botSync.text;
      }

      const botMessage = {
        id: generateId(),
        role: "assistant",
        text: responseText,
        createdAt:
          new Date().toISOString(),
      };

      updateActiveConversation(
        (conversation) => ({
          ...conversation,
          updatedAt:
            new Date().toISOString(),
          messages: [
            ...conversation.messages,
            botMessage,
          ],
        })
      );

      setAssistantStatus(
        shouldSyncBot
          ? "complete"
          : "needsInput"
      );
    } catch (error) {
      console.error(
        "AI assistant error:",
        error
      );

      const botMessage = {
        id: generateId(),
        role: "assistant",
        text:
          isVietnamese
            ? "Không thể xử lý yêu cầu lúc này. Vui lòng thử lại."
            : "Unable to process the request right now. Please try again.",
        createdAt:
          new Date().toISOString(),
      };

      updateActiveConversation(
        (conversation) => ({
          ...conversation,
          updatedAt:
            new Date().toISOString(),
          messages: [
            ...conversation.messages,
            botMessage,
          ],
        })
      );

      setAssistantStatus(
        "needsInput"
      );
    }

    statusResetTimeoutRef.current =
      setTimeout(() => {
        setAssistantStatus(
          (current) =>
            current === "needsInput"
              ? current
              : "ready"
        );

        statusResetTimeoutRef.current =
          null;
      }, 1400);
  };

  const appendAssistantMessage = (
    text
  ) => {
    const now =
      new Date().toISOString();

    const message = {
      id: generateId(),
      role: "assistant",
      text,
      createdAt: now,
    };

    updateActiveConversation(
      (conversation) => ({
        ...conversation,
        updatedAt: now,
        messages: [
          ...conversation.messages,
          message,
        ],
      })
    );
  };

  const handleApplyPendingEdit =
    async () => {
      if (!pendingEdit) {
        return;
      }

      const {
        changes,
        replyInVietnamese,
      } = pendingEdit;

      onApplyAiChanges?.(
        changes
      );

      const nextAiData = {
        ...aiData,
        ...changes,
      };

      const appliedText =
        formatAppliedChanges(
          changes,
          replyInVietnamese
        );

      const botSync =
        await syncBotSessionSafely(
          nextAiData,
          appliedText,
          replyInVietnamese
        );

      appendAssistantMessage(
        botSync.text
      );

      setPendingEdit(null);
      setAssistantStatus(
        "complete"
      );

      if (
        statusResetTimeoutRef.current
      ) {
        clearTimeout(
          statusResetTimeoutRef.current
        );
      }

      statusResetTimeoutRef.current =
        setTimeout(() => {
          setAssistantStatus(
            "ready"
          );

          statusResetTimeoutRef.current =
            null;
        }, 1400);
    };

  const handleCancelPendingEdit = () => {
    if (!pendingEdit) {
      return;
    }

    appendAssistantMessage(
      pendingEdit.replyInVietnamese
        ? "Đã hủy thay đổi. Form hiện tại được giữ nguyên."
        : "Changes cancelled. The current form was left unchanged."
    );

    setPendingEdit(null);
    setAssistantStatus(
      "ready"
    );
  };

  const handleSubmit = (
    event
  ) => {
    event.preventDefault();

    sendMessage(inputValue);
  };

  const handleSuggestion = (
    type
  ) => {
    if (type === "plot") {
      sendMessage(
        isVietnamese
          ? "Cho tôi thông tin lô A01"
          : "Show me information about plot A01"
      );

      return;
    }

    if (type === "crop") {
      sendMessage(
        isVietnamese
          ? "Cho tôi thông tin cây ớt"
          : "Show me information about chili crops"
      );

      return;
    }

    if (type === "log") {
      sendMessage(
        isVietnamese
          ? "Cho tôi xem nhật ký gần nhất"
          : "Show me the latest farming log"
      );
    }
  };

  /* ===========================
     AI audit trail
  =========================== */

  const AUDIT_FIELD_LABELS = {
    lot: isVietnamese
      ? "Lô canh tác"
      : "Plot",

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

  const formatAuditTime = (
    value
  ) => {
    try {
      return new Date(
        value
      ).toLocaleTimeString(
        isVietnamese
          ? "vi-VN"
          : "en-US",
        {
          hour: "2-digit",
          minute: "2-digit",
        }
      );
    } catch {
      return "--:--";
    }
  };

  const toggleAuditSelection = (
    id
  ) => {
    setSelectedAuditIds(
      (previous) =>
        previous.includes(id)
          ? previous.filter(
              (itemId) =>
                itemId !== id
            )
          : [
              ...previous,
              id,
            ]
    );
  };

  const selectAllAuditEvents =
    () => {
      setSelectedAuditIds(
        aiAuditEvents.map(
          (event) =>
            event.id
        )
      );
    };

  const clearAuditSelection =
    () => {
      setSelectedAuditIds([]);
    };

  const exitAuditSelection =
    () => {
      setIsSelectingAudit(false);
      clearAuditSelection();
    };

  const deleteSelectedAuditEvents =
    () => {
      if (
        selectedAuditIds.length ===
        0
      ) {
        return;
      }

      const confirmed =
        window.confirm(
          isVietnamese
            ? `Xóa ${selectedAuditIds.length} mục lịch sử chỉnh sửa đã chọn?`
            : `Delete ${selectedAuditIds.length} selected edit history item(s)?`
        );

      if (!confirmed) {
        return;
      }

      onDeleteAiAuditEvents?.(
        selectedAuditIds
      );

      exitAuditSelection();
    };

  const clearAllAuditEvents =
    () => {
      if (
        aiAuditEvents.length ===
        0
      ) {
        return;
      }

      const confirmed =
        window.confirm(
          isVietnamese
            ? "Xóa toàn bộ lịch sử chỉnh sửa AI? Thao tác này không thay đổi dữ liệu trên form."
            : "Delete all AI edit history? This will not change the form data."
        );

      if (!confirmed) {
        return;
      }

      onClearAiAuditEvents?.();
      exitAuditSelection();
    };

  /* ===========================
     History groups
  =========================== */

  const pinnedConversations =
    conversations
      .filter(
        (conversation) =>
          conversation.pinned
      )
      .sort(
        (a, b) =>
          new Date(
            b.updatedAt
          ) -
          new Date(
            a.updatedAt
          )
      );

  const recentConversations =
    conversations
      .filter(
        (conversation) =>
          !conversation.pinned &&
          conversation.messages
            .length > 0
      )
      .sort(
        (a, b) =>
          new Date(
            b.updatedAt
          ) -
          new Date(
            a.updatedAt
          )
      );

  return (
    <>
      {isOpen && (
        <div
          className="ai-assistant-panel"
          ref={assistantRef}
        >
          {/* ===========================
              Header
          =========================== */}

          <div className="ai-assistant-header">
            <div className="ai-assistant-title">
              <div className="ai-assistant-avatar">
                🤖
              </div>

              <div>
                <strong>
                  NextFarm AI
                </strong>

                <span>
                  {isVietnamese
                    ? "Trợ lý canh tác thông minh"
                    : "Smart farming assistant"}
                </span>

                <span
                  className={`assistant-status assistant-status-${assistantStatus}`}
                  aria-live="polite"
                >
                  <span
                    className="assistant-status-icon"
                    aria-hidden="true"
                  >
                    {currentStatus.icon}
                  </span>

                  <span>
                    {currentStatus.label}
                  </span>
                </span>
              </div>
            </div>

            <div className="assistant-header-actions">
              <button
                type="button"
                className="assistant-history-btn"
                onClick={() => {
                  setShowHistory(
                    (prev) =>
                      !prev
                  );

                  setShowAudit(
                    false
                  );
                }}
                title={
                  isVietnamese
                    ? "Lịch sử trò chuyện"
                    : "Chat history"
                }
              >
                ☰
              </button>

              <button
                type="button"
                className={`assistant-audit-btn ${
                  showAudit
                    ? "active"
                    : ""
                }`}
                onClick={() => {
                  setShowAudit(
                    (prev) =>
                      !prev
                  );

                  setShowHistory(
                    false
                  );
                }}
                title={
                  isVietnamese
                    ? "Lịch sử chỉnh sửa AI"
                    : "AI edit history"
                }
              >
                🕘
              </button>

              <button
                type="button"
                className="ai-assistant-close"
                onClick={() => {
                  if (recognitionRef.current) {
                    recognitionRef.current.stop();
                  }

                  setIsOpen(false);
                  setShowHistory(
                    false
                  );
                  setShowAudit(
                    false
                  );
                }}
                aria-label={
                  isVietnamese
                    ? "Đóng trợ lý AI"
                    : "Close AI assistant"
                }
              >
                ✕
              </button>
            </div>
          </div>

          {/* ===========================
              Body layout
          =========================== */}

          <div className="assistant-main-layout">
            {showHistory && (
              <aside className="assistant-history-panel">
                <div className="assistant-secondary-panel-top">
                  <button
                    type="button"
                    className="assistant-back-to-chat"
                    onClick={
                      returnToChat
                    }
                  >
                    <span aria-hidden="true">
                      ←
                    </span>

                    <span>
                      {isVietnamese
                        ? "Quay lại đoạn chat"
                        : "Back to chat"}
                    </span>
                  </button>

                  <span className="assistant-secondary-panel-title">
                    {isVietnamese
                      ? "Lịch sử trò chuyện"
                      : "Chat history"}
                  </span>
                </div>

                <button
                  type="button"
                  className="assistant-new-chat"
                  onClick={
                    createNewChat
                  }
                >
                  ✏️{" "}
                  {isVietnamese
                    ? "Đoạn chat mới"
                    : "New chat"}
                </button>

                {pinnedConversations.length >
                  0 && (
                  <div className="assistant-history-group">
                    <span className="assistant-history-label">
                      {isVietnamese
                        ? "Đã ghim"
                        : "Pinned"}
                    </span>

                    {pinnedConversations.map(
                      (
                        conversation
                      ) => (
                        <ConversationItem
                          key={
                            conversation.id
                          }
                          conversation={
                            conversation
                          }
                          active={
                            conversation.id ===
                            activeConversationId
                          }
                          onSelect={
                            selectConversation
                          }
                          onPin={
                            togglePinConversation
                          }
                          onDelete={
                            deleteConversation
                          }
                        />
                      )
                    )}
                  </div>
                )}

                <div className="assistant-history-group">
                  <span className="assistant-history-label">
                    {isVietnamese
                      ? "Gần đây"
                      : "Recent"}
                  </span>

                  {recentConversations.length ===
                  0 ? (
                    <span className="assistant-history-empty">
                      {isVietnamese
                        ? "Chưa có cuộc trò chuyện."
                        : "No conversations yet."}
                    </span>
                  ) : (
                    recentConversations.map(
                      (
                        conversation
                      ) => (
                        <ConversationItem
                          key={
                            conversation.id
                          }
                          conversation={
                            conversation
                          }
                          active={
                            conversation.id ===
                            activeConversationId
                          }
                          onSelect={
                            selectConversation
                          }
                          onPin={
                            togglePinConversation
                          }
                          onDelete={
                            deleteConversation
                          }
                        />
                      )
                    )
                  )}
                </div>
              </aside>
            )}

            {showAudit && (
              <aside className="assistant-audit-panel">
                <div className="assistant-secondary-panel-top">
                  <button
                    type="button"
                    className="assistant-back-to-chat"
                    onClick={
                      returnToChat
                    }
                  >
                    <span aria-hidden="true">
                      ←
                    </span>

                    <span>
                      {isVietnamese
                        ? "Quay lại đoạn chat"
                        : "Back to chat"}
                    </span>
                  </button>

                  <span className="assistant-secondary-panel-title">
                    {isVietnamese
                      ? "Lịch sử chỉnh sửa"
                      : "Edit history"}
                  </span>
                </div>

                <div className="assistant-audit-header">
                  <div>
                    <strong>
                      🕘{" "}
                      {isVietnamese
                        ? "Lịch sử chỉnh sửa AI"
                        : "AI edit history"}
                    </strong>

                    <span>
                      {isVietnamese
                        ? "Theo dõi các thay đổi do trợ lý thực hiện trong phiên hiện tại."
                        : "Track changes made by the assistant in the current session."}
                    </span>
                  </div>

                  <span className="assistant-audit-count">
                    {
                      aiAuditEvents.length
                    }
                  </span>
                </div>

                {aiAuditEvents.length >
                  0 && (
                  <div className="assistant-audit-toolbar">
                    {!isSelectingAudit ? (
                      <>
                        <button
                          type="button"
                          className="assistant-audit-select-btn"
                          onClick={() =>
                            setIsSelectingAudit(
                              true
                            )
                          }
                        >
                          ☑{" "}
                          {isVietnamese
                            ? "Chọn"
                            : "Select"}
                        </button>

                        <button
                          type="button"
                          className="assistant-audit-clear-all-btn"
                          onClick={
                            clearAllAuditEvents
                          }
                        >
                          🗑{" "}
                          {isVietnamese
                            ? "Xóa tất cả"
                            : "Clear all"}
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="assistant-audit-select-all-btn"
                          onClick={
                            selectedAuditIds.length ===
                            aiAuditEvents.length
                              ? clearAuditSelection
                              : selectAllAuditEvents
                          }
                        >
                          {selectedAuditIds.length ===
                          aiAuditEvents.length
                            ? isVietnamese
                              ? "Bỏ chọn tất cả"
                              : "Deselect all"
                            : isVietnamese
                              ? "Chọn tất cả"
                              : "Select all"}
                        </button>

                        <button
                          type="button"
                          className="assistant-audit-delete-selected-btn"
                          onClick={
                            deleteSelectedAuditEvents
                          }
                          disabled={
                            selectedAuditIds.length ===
                            0
                          }
                        >
                          🗑{" "}
                          {isVietnamese
                            ? `Xóa (${selectedAuditIds.length})`
                            : `Delete (${selectedAuditIds.length})`}
                        </button>

                        <button
                          type="button"
                          className="assistant-audit-cancel-select-btn"
                          onClick={
                            exitAuditSelection
                          }
                        >
                          {isVietnamese
                            ? "Hủy chọn"
                            : "Cancel"}
                        </button>
                      </>
                    )}
                  </div>
                )}

                {aiAuditEvents.length ===
                0 ? (
                  <div className="assistant-audit-empty">
                    <span>🧾</span>

                    <strong>
                      {isVietnamese
                        ? "Chưa có chỉnh sửa"
                        : "No edits yet"}
                    </strong>

                    <span>
                      {isVietnamese
                        ? "Các thay đổi do AI thực hiện sẽ xuất hiện tại đây."
                        : "AI-made changes will appear here."}
                    </span>
                  </div>
                ) : (
                  <div className="assistant-audit-list">
                    {[
                      ...aiAuditEvents,
                    ]
                      .reverse()
                      .map(
                        (event) => (
                          <div
                            key={
                              event.id
                            }
                            className={`assistant-audit-event ${
                              event.type
                            } ${
                              selectedAuditIds.includes(
                                event.id
                              )
                                ? "selected"
                                : ""
                            }`}
                            onClick={() => {
                              if (
                                isSelectingAudit
                              ) {
                                toggleAuditSelection(
                                  event.id
                                );
                              }
                            }}
                          >
                            {isSelectingAudit && (
                              <label
                                className="assistant-audit-checkbox"
                                onClick={(
                                  eventObject
                                ) =>
                                  eventObject.stopPropagation()
                                }
                              >
                                <input
                                  type="checkbox"
                                  checked={
                                    selectedAuditIds.includes(
                                      event.id
                                    )
                                  }
                                  onChange={() =>
                                    toggleAuditSelection(
                                      event.id
                                    )
                                  }
                                />

                                <span>
                                  {isVietnamese
                                    ? "Chọn mục này"
                                    : "Select item"}
                                </span>
                              </label>
                            )}

                            <div className="assistant-audit-event-top">
                              <span className="assistant-audit-event-type">
                                {event.type ===
                                "undo"
                                  ? "↩️"
                                  : "🤖"}

                                {" "}

                                {event.type ===
                                "undo"
                                  ? isVietnamese
                                    ? "Đã hoàn tác"
                                    : "Undo"
                                  : isVietnamese
                                    ? "AI đã cập nhật"
                                    : "AI updated"}
                              </span>

                              <time>
                                {formatAuditTime(
                                  event.createdAt
                                )}
                              </time>
                            </div>

                            <div className="assistant-audit-changes">
                              {event.changes.map(
                                (
                                  change
                                ) => (
                                  <div
                                    key={`${event.id}-${change.field}`}
                                    className="assistant-audit-change"
                                  >
                                    <strong>
                                      {AUDIT_FIELD_LABELS[
                                        change.field
                                      ] ||
                                        change.field}
                                    </strong>

                                    <span className="assistant-audit-values">
                                      <span>
                                        {change.from ||
                                          (isVietnamese
                                            ? "chưa có"
                                            : "not provided")}
                                      </span>

                                      <b>
                                        →
                                      </b>

                                      <span>
                                        {change.to ||
                                          (isVietnamese
                                            ? "chưa có"
                                            : "not provided")}
                                      </span>
                                    </span>
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        )
                      )}
                  </div>
                )}
              </aside>
            )}

            <div className="assistant-chat-area">
              <div className="ai-assistant-body">
                <div className="assistant-message assistant">
                  <div className="assistant-message-avatar">
                    🤖
                  </div>

                  <div className="assistant-message-content">
                    <strong>
                      {isVietnamese
                        ? "Xin chào Khoa 👋"
                        : "Hello Khoa 👋"}
                    </strong>

                    <p>
                      {isVietnamese
                        ? "Tôi là trợ lý AI của NextFarm. Bạn có thể hỏi tôi về lô canh tác, cây trồng hoặc nhật ký gần đây."
                        : "I am the NextFarm AI assistant. You can ask me about farm plots, crops or recent farming logs."}
                    </p>
                  </div>
                </div>

                {messages.length ===
                  0 && (
                  <div className="assistant-suggestions">
                    <button
                      type="button"
                      onClick={() =>
                        sendMessage(
                          isVietnamese
                            ? "Đọc dữ liệu hiện tại"
                            : "Read current log"
                        )
                      }
                    >
                      🧾{" "}
                      {isVietnamese
                        ? "Dữ liệu hiện tại"
                        : "Current log"}
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleSuggestion(
                          "plot"
                        )
                      }
                    >
                      🌱{" "}
                      {isVietnamese
                        ? "Thông tin lô A01"
                        : "Plot A01 information"}
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleSuggestion(
                          "crop"
                        )
                      }
                    >
                      🌶{" "}
                      {isVietnamese
                        ? "Thông tin cây ớt"
                        : "Chili crop information"}
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleSuggestion(
                          "log"
                        )
                      }
                    >
                      📋{" "}
                      {isVietnamese
                        ? "Nhật ký gần nhất"
                        : "Latest farming log"}
                    </button>
                  </div>
                )}

                <div className="assistant-chat-messages">
                  {messages.map(
                    (message) => (
                      <div
                        key={
                          message.id
                        }
                        className={`assistant-chat-message ${
                          message.role
                        }`}
                      >
                        {message.role ===
                          "assistant" && (
                          <div className="assistant-message-avatar">
                            🤖
                          </div>
                        )}

                        <div className="assistant-chat-bubble">
                          {
                            message.text
                          }
                        </div>
                      </div>
                    )
                  )}

                  {pendingEdit && (
                    <div className="assistant-pending-edit-card">
                      <div className="assistant-pending-edit-header">
                        <span>
                          ⚠️
                        </span>

                        <div>
                          <strong>
                            {pendingEdit.replyInVietnamese
                              ? "Xác nhận thay đổi"
                              : "Confirm changes"}
                          </strong>

                          <span>
                            {pendingEdit.replyInVietnamese
                              ? `${Object.keys(
                                  pendingEdit.changes
                                ).length} trường sẽ được cập nhật.`
                              : `${Object.keys(
                                  pendingEdit.changes
                                ).length} fields will be updated.`}
                          </span>
                        </div>
                      </div>

                      <div className="assistant-pending-edit-actions">
                        <button
                          type="button"
                          className="assistant-pending-edit-cancel"
                          onClick={
                            handleCancelPendingEdit
                          }
                        >
                          {pendingEdit.replyInVietnamese
                            ? "Hủy"
                            : "Cancel"}
                        </button>

                        <button
                          type="button"
                          className="assistant-pending-edit-apply"
                          onClick={
                            handleApplyPendingEdit
                          }
                        >
                          ✓{" "}
                          {pendingEdit.replyInVietnamese
                            ? "Áp dụng"
                            : "Apply"}
                        </button>
                      </div>
                    </div>
                  )}

                  {assistantStatus ===
                    "thinking" && (
                    <div
                      className="assistant-chat-message assistant assistant-typing-message"
                      aria-live="polite"
                      aria-label={
                        isVietnamese
                          ? "NextFarm AI đang xử lý"
                          : "NextFarm AI is processing"
                      }
                    >
                      <div className="assistant-message-avatar">
                        🤖
                      </div>

                      <div className="assistant-typing-bubble">
                        <span />
                        <span />
                        <span />
                      </div>
                    </div>
                  )}

                  <div
                    ref={
                      messagesEndRef
                    }
                  />
                </div>
              </div>

              <div className="ai-assistant-input-area">
                <form
                  className="assistant-input-wrapper"
                  onSubmit={
                    handleSubmit
                  }
                >
                  <input
                    type="text"
                    value={
                      inputValue
                    }
                    onChange={(
                      event
                    ) =>
                      setInputValue(
                        event.target
                          .value
                      )
                    }
                    placeholder={
                      pendingEdit
                        ? isVietnamese
                          ? "Xác nhận hoặc hủy thay đổi trước..."
                          : "Apply or cancel the pending changes first..."
                        : assistantStatus ===
                      "thinking"
                        ? isVietnamese
                          ? "NextFarm AI đang xử lý..."
                          : "NextFarm AI is processing..."
                        : isListening
                          ? isVietnamese
                            ? "Đang nghe giọng nói..."
                            : "Listening..."
                          : isVietnamese
                            ? "Hỏi NextFarm AI..."
                            : "Ask NextFarm AI..."
                    }
                    disabled={
                      assistantStatus ===
                        "thinking" ||
                      isListening ||
                      Boolean(
                        pendingEdit
                      )
                    }
                  />

                  <button
                    type="button"
                    className={`assistant-mic-btn ${
                      isListening
                        ? "listening"
                        : ""
                    }`}
                    title={
                      isListening
                        ? isVietnamese
                          ? "Dừng nghe"
                          : "Stop listening"
                        : isVietnamese
                          ? "Hỏi bằng giọng nói"
                          : "Ask by voice"
                    }
                    onClick={
                      startVoiceInput
                    }
                    disabled={
                      assistantStatus ===
                        "thinking" ||
                      Boolean(
                        pendingEdit
                      )
                    }
                    aria-pressed={
                      isListening
                    }
                  >
                    {isListening
                      ? "⏹"
                      : "🎤"}
                  </button>

                  <button
                    type="submit"
                    className="assistant-send-btn"
                    disabled={
                      !inputValue.trim() ||
                      assistantStatus ===
                        "thinking" ||
                      isListening ||
                      Boolean(
                        pendingEdit
                      )
                    }
                  >
                    ➤
                  </button>
                </form>

                {voiceMessage && (
                  <div
                    className={`assistant-voice-feedback ${
                      assistantStatus ===
                      "needsInput"
                        ? "error"
                        : "listening"
                    }`}
                    role="status"
                  >
                    <span>
                      {assistantStatus ===
                      "needsInput"
                        ? "⚠️"
                        : "🎧"}
                    </span>

                    <span>
                      {voiceMessage}
                    </span>
                  </div>
                )}

                <span className="assistant-disclaimer">
                  {isVietnamese
                    ? "AI có thể trả lời chưa chính xác. Hãy kiểm tra dữ liệu quan trọng."
                    : "AI responses may be inaccurate. Verify important information."}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      <button
        ref={
          assistantButtonRef
        }
        type="button"
        className={`ai-assistant-floating ${
          isOpen
            ? "active"
            : ""
        }`}
        onClick={() =>
          setIsOpen(
            (previous) =>
              !previous
          )
        }
      >
        {isOpen ? "✕" : "🤖"}

        {!isOpen && (
          <span className="assistant-online-dot" />
        )}
      </button>
    </>
  );
}

/* ===========================
   Conversation Item
=========================== */

function ConversationItem({
  conversation,
  active,
  onSelect,
  onPin,
  onDelete,
}) {
  return (
    <div
      className={`assistant-history-item ${
        active ? "active" : ""
      }`}
    >
      <button
        type="button"
        className="assistant-history-select"
        onClick={() =>
          onSelect(
            conversation.id
          )
        }
      >
        <span>💬</span>

        <span>
          {conversation.title ||
            "Conversation"}
        </span>
      </button>

      <div className="assistant-history-item-actions">
        <button
          type="button"
          title={
            conversation.pinned
              ? "Unpin"
              : "Pin"
          }
          onClick={() =>
            onPin(
              conversation.id
            )
          }
        >
          {conversation.pinned
            ? "📌"
            : "☆"}
        </button>

        <button
          type="button"
          title="Delete"
          onClick={() =>
            onDelete(
              conversation.id
            )
          }
        >
          ×
        </button>
      </div>
    </div>
  );
}

export default AIAssistant; 