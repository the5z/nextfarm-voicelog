const SETTINGS_KEY =
  "nextfarm-app-settings";

export const DEFAULT_SETTINGS = {
  language: "vi",

  theme: "light",

  recognitionLanguage:
    "vi-VN",

  dialect: "auto",

  aiAssistantEnabled: true,

  autoValidation: true,

  saveChatHistory: true,

  saveLocalLogs: true,
};

export function loadSettings() {
  try {
    const saved =
      localStorage.getItem(
        SETTINGS_KEY
      );

    if (!saved) {
      return {
        ...DEFAULT_SETTINGS,
      };
    }

    const parsed =
      JSON.parse(saved);

    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
    };
  } catch (error) {
    console.error(
      "Load settings error:",
      error
    );

    return {
      ...DEFAULT_SETTINGS,
    };
  }
}

export function saveSettings(
  settings
) {
  try {
    localStorage.setItem(
      SETTINGS_KEY,
      JSON.stringify(settings)
    );
  } catch (error) {
    console.error(
      "Save settings error:",
      error
    );
  }
}