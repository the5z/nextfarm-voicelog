import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  generateId,
} from "./utils/id";

import VoiceLog from "./pages/VoiceLog";
import MyLogs from "./pages/MyLogs";
import Settings from "./pages/Settings";

import AppSidebar from "./components/AppSidebar";
import AIAssistant from "./components/AIAssistant";

import {
  loadBackendLogs,
  loadLogs,
  persistLogs,
} from "./services/logService";

import {
  loadSettings,
  saveSettings,
} from "./services/settingsService";

import "./App.css";

const EMPTY_AI_DATA = {
  lot: "",
  work: "",
  material: "",
  quantity: "",
  unit: "",
  time: "",
};

function App() {
  const [
    activePage,
    setActivePage,
  ] = useState("create");

  /* ===========================
     Global settings
  =========================== */

  const [
    appSettings,
    setAppSettings,
  ] = useState(() =>
    loadSettings()
  );
  
  useEffect(() => {
    let cancelled =
      false;

    const loadLogsFromBackend =
      async () => {
        try {
          const backendLogs =
            await loadBackendLogs();

          if (cancelled) {
            return;
          }

          /*
            Backend thành công
            -> backend là source of truth.
          */

          setLogs(
            backendLogs
          );

          /*
            Local storage chỉ là cache.
          */

          if (
            appSettings
              .saveLocalLogs
          ) {
            persistLogs(
              backendLogs
            );
          }
        } catch (error) {
          /*
            Backend lỗi:
            không xóa state hiện tại.

            State lúc này vẫn là
            local fallback từ loadLogs().
          */

          console.error(
            "Load backend logs error:",
            error
          );
        }
      };

    loadLogsFromBackend();

    return () => {
      cancelled =
        true;
    };
  }, [
    appSettings
      .saveLocalLogs,
  ]);
  const language =
    appSettings.language;

  /* ===========================
     Current VoiceLog AI context
  =========================== */

  const [
    currentVoiceLogData,
    setCurrentVoiceLogData,
  ] = useState(
    EMPTY_AI_DATA
  );

  const [
    pendingAiChanges,
    setPendingAiChanges,
  ] = useState(null);

  const [
    highlightedField,
    setHighlightedField,
  ] = useState("");

  const [
    aiAuditEvents,
    setAiAuditEvents,
  ] = useState([]);

  const aiUndoStackRef =
    useRef([]);

  /* ===========================
     Logs
  =========================== */

  const [
    logToEdit,
    setLogToEdit,
  ] = useState(null);

  const [
    logs,
    setLogs,
  ] = useState(() =>
    loadLogs()
  );

  /* ===========================
     Settings persistence
  =========================== */

  useEffect(() => {
    saveSettings(
      appSettings
    );
  }, [appSettings]);

  /* ===========================
     Theme
  =========================== */

  useEffect(() => {
    const applyTheme = () => {
      if (
        appSettings.theme ===
        "dark"
      ) {
        document.body.classList.add(
          "dark-mode"
        );

        return;
      }

      if (
        appSettings.theme ===
        "light"
      ) {
        document.body.classList.remove(
          "dark-mode"
        );

        return;
      }

      const prefersDark =
        window.matchMedia?.(
          "(prefers-color-scheme: dark)"
        ).matches;

      document.body.classList.toggle(
        "dark-mode",
        Boolean(prefersDark)
      );
    };

    applyTheme();

    if (
      appSettings.theme !==
      "system"
    ) {
      return;
    }

    const mediaQuery =
      window.matchMedia?.(
        "(prefers-color-scheme: dark)"
      );

    if (!mediaQuery) {
      return;
    }

    const handleSystemTheme =
      () => {
        applyTheme();
      };

    mediaQuery.addEventListener?.(
      "change",
      handleSystemTheme
    );

    return () => {
      mediaQuery.removeEventListener?.(
        "change",
        handleSystemTheme
      );
    };
  }, [appSettings.theme]);

  /* ===========================
     Update setting
  =========================== */

  const updateSetting = (
    key,
    value
  ) => {
    setAppSettings(
      (previous) => ({
        ...previous,
        [key]: value,
      })
    );
  };

  /* ===========================
     Navigation
  =========================== */

  const handleNavigate = (
    page
  ) => {
    setActivePage(page);
  };

  /* ===========================
     Edit / Resume Log
  =========================== */

  const handleEditLog = (
    log
  ) => {
    setLogToEdit(log);

    setActivePage(
      "create"
    );
  };

  /* ===========================
     AI Assistant -> VoiceLog
  =========================== */

  const handleAiApplyChanges = (
    changes
  ) => {
    if (
      !changes ||
      Object.keys(
        changes
      ).length === 0
    ) {
      return;
    }

    const changedFields =
      Object.keys(
        changes
      );

    const previousValues = {};

    changedFields.forEach(
      (field) => {
        previousValues[field] =
          currentVoiceLogData[
            field
          ] ?? "";
      }
    );

    const undoEntry = {
      previousValues,
      appliedChanges: {
        ...changes,
      },
      createdAt:
        new Date().toISOString(),
    };

    aiUndoStackRef.current = [
      ...aiUndoStackRef.current,
      undoEntry,
    ].slice(-10);

    setAiAuditEvents(
      (previous) => [
        ...previous,
        {
          id: generateId(),
          type: "update",
          createdAt:
            undoEntry.createdAt,
          changes:
            changedFields.map(
              (field) => ({
                field,
                from:
                  previousValues[
                    field
                  ] ?? "",
                to:
                  changes[
                    field
                  ] ?? "",
              })
            ),
        },
      ].slice(-50)
    );

    setActivePage(
      "create"
    );

    setPendingAiChanges(
      changes
    );

    setHighlightedField(
      changedFields[0] ||
        ""
    );
  };

  const handleAiUndoChanges =
    () => {
      const stack =
        aiUndoStackRef.current;

      if (
        stack.length === 0
      ) {
        return {
          success: false,
        };
      }

      const lastEdit =
        stack[
          stack.length - 1
        ];

      aiUndoStackRef.current =
        stack.slice(
          0,
          -1
        );

      const fields =
        Object.keys(
          lastEdit.previousValues
        );

      setAiAuditEvents(
        (previous) => [
          ...previous,
          {
            id: generateId(),
            type: "undo",
            createdAt:
              new Date().toISOString(),
            changes:
              fields.map(
                (field) => ({
                  field,
                  from:
                    lastEdit
                      .appliedChanges[
                        field
                      ] ?? "",
                  to:
                    lastEdit
                      .previousValues[
                        field
                      ] ?? "",
                })
              ),
          },
        ].slice(-50)
      );

      setActivePage(
        "create"
      );

      setPendingAiChanges(
        lastEdit.previousValues
      );

      setHighlightedField(
        fields[0] || ""
      );

      return {
        success: true,
        previousValues:
          lastEdit.previousValues,
        appliedChanges:
          lastEdit.appliedChanges,
      };
    };

  const handleDeleteAiAuditEvents = (
    eventIds
  ) => {
    const ids =
      Array.isArray(
        eventIds
      )
        ? eventIds
        : [];

    if (ids.length === 0) {
      return;
    }

    const idSet =
      new Set(ids);

    setAiAuditEvents(
      (previous) =>
        previous.filter(
          (event) =>
            !idSet.has(
              event.id
            )
        )
    );
  };

  const handleClearAiAuditEvents =
    () => {
      setAiAuditEvents([]);
    };

  const handleAiChangesApplied =
    () => {
      setPendingAiChanges(
        null
      );
    };

  /* ===========================
     Save / Update Log
  =========================== */

  const handleSaveLog = (
    savedLog
  ) => {
    setLogs(
      (previousLogs) => {
        const exists =
          previousLogs.some(
            (log) =>
              log.id ===
              savedLog.id
          );

        let nextLogs;

        if (exists) {
          nextLogs =
            previousLogs.map(
              (log) =>
                log.id ===
                savedLog.id
                  ? {
                      ...log,
                      ...savedLog,

                      createdAt:
                        log.createdAt ||
                        savedLog.createdAt,
                    }
                  : log
            );
        } else {
          nextLogs = [
            savedLog,
            ...previousLogs,
          ];
        }

        if (
          appSettings
            .saveLocalLogs
        ) {
          persistLogs(
            nextLogs
          );
        }

        return nextLogs;
      }
    );
  };

  return (
    <div className="app-shell">
      <AppSidebar
        language={
          language
        }
        activePage={
          activePage
        }
        onNavigate={
          handleNavigate
        }
      />

      {activePage ===
        "create" && (
        <VoiceLog
          language={
            language
          }

          onLanguageChange={(
            value
          ) =>
            updateSetting(
              "language",
              value
            )
          }

          themeMode={
            appSettings.theme
          }

          onThemeChange={(
            value
          ) =>
            updateSetting(
              "theme",
              value
            )
          }

          logToEdit={
            logToEdit
          }

          onLogLoaded={() =>
            setLogToEdit(
              null
            )
          }

          onSaveLog={
            handleSaveLog
          }

          autoValidation={
            appSettings
              .autoValidation
          }

          onAiDataChange={
            setCurrentVoiceLogData
          }

          externalAiChanges={
            pendingAiChanges
          }

          onExternalAiChangesApplied={
            handleAiChangesApplied
          }

          highlightedField={
            highlightedField
          }

          onHighlightClear={() =>
            setHighlightedField(
              ""
            )
          }

          logs={
            logs
          }
        />
      )}

      {activePage ===
        "logs" && (
        <MyLogs
          language={
            language
          }

          logs={
            logs
          }

          onEditLog={
            handleEditLog
          }
        />
      )}

      {activePage ===
        "settings" && (
        <Settings
          settings={
            appSettings
          }

          onSettingChange={
            updateSetting
          }
        />
      )}

      {appSettings
        .aiAssistantEnabled && (
        <AIAssistant
          language={
            language
          }

          activePage={
            activePage
          }

          aiData={
            currentVoiceLogData
          }

          onApplyAiChanges={
            handleAiApplyChanges
          }

          onUndoAiChanges={
            handleAiUndoChanges
          }

          aiAuditEvents={
            aiAuditEvents
          }

          onDeleteAiAuditEvents={
            handleDeleteAiAuditEvents
          }

          onClearAiAuditEvents={
            handleClearAiAuditEvents
          }
        />
      )}
    </div>
  );
}

export default App;