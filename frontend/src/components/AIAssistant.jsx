import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

const STORAGE_KEY =
  "nextfarm-ai-conversations";

const ACTIVE_CHAT_KEY =
  "nextfarm-ai-active-chat";

function createConversation(title = "") {
  return {
    id: crypto.randomUUID(),
    title,
    pinned: false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: [],
  };
}

function AIAssistant({
  language = "vi",
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [inputValue, setInputValue] = useState("");

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

  const isVietnamese =
    language === "vi";

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
  }, [messages]);

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
        setIsOpen(false);
        setShowHistory(false);
      }
    };

    const handleKeyDown = (
      event
    ) => {
      if (event.key === "Escape") {
        setIsOpen(false);
        setShowHistory(false);
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
      ? "Tôi đã nhận được câu hỏi của bạn. Hiện trợ lý đang chạy ở chế độ thử nghiệm frontend. Sau khi kết nối API, tôi sẽ có thể truy vấn dữ liệu NextFarm và trả lời chính xác hơn."
      : "I received your question. The assistant is currently running in frontend test mode. After API integration, I will be able to query NextFarm data and provide more accurate answers.";
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

    setInputValue("");
    setShowHistory(false);
  };

  const selectConversation = (
    id
  ) => {
    setActiveConversationId(id);
    setShowHistory(false);
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
     Send message
  =========================== */

  const sendMessage = (
    message
  ) => {
    const cleanMessage =
      message.trim();

    if (!cleanMessage) return;

    const now =
      new Date().toISOString();

    const userMessage = {
      id: crypto.randomUUID(),
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

    setTimeout(() => {
      const botMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: getBotResponse(
          cleanMessage
        ),
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
    }, 500);
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
              </div>
            </div>

            <div className="assistant-header-actions">
              <button
                type="button"
                className="assistant-history-btn"
                onClick={() =>
                  setShowHistory(
                    (prev) =>
                      !prev
                  )
                }
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
                className="ai-assistant-close"
                onClick={() => {
                  setIsOpen(false);
                  setShowHistory(
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
                      isVietnamese
                        ? "Hỏi NextFarm AI..."
                        : "Ask NextFarm AI..."
                    }
                  />

                  <button
                    type="button"
                    className="assistant-mic-btn"
                    title={
                      isVietnamese
                        ? "Hỏi bằng giọng nói"
                        : "Ask by voice"
                    }
                  >
                    🎤
                  </button>

                  <button
                    type="submit"
                    className="assistant-send-btn"
                    disabled={
                      !inputValue.trim()
                    }
                  >
                    ➤
                  </button>
                </form>

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