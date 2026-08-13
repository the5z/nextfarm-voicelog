import {
  useEffect,
  useState,
} from "react";

import VoiceLog from "./pages/VoiceLog";
import MyLogs from "./pages/MyLogs";
import Settings from "./pages/Settings";

import AppSidebar from "./components/AppSidebar";
import AIAssistant from "./components/AIAssistant";

import {
  loadLogs,
  persistLogs,
} from "./services/logService";

import {
  loadSettings,
  saveSettings,
} from "./services/settingsService";

import "./App.css";

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

  const language =
    appSettings.language;

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
        />
      )}
    </div>
  );
}

export default App;