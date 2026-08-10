import { useState } from "react";

function Header() {
  const [darkMode, setDarkMode] = useState(false);
  const [language, setLanguage] = useState("vi");
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);

  const toggleTheme = () => {
    setDarkMode((prev) => {
      const nextMode = !prev;

      document.body.classList.toggle("dark-mode", nextMode);

      return nextMode;
    });
  };

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    setShowLanguageMenu(false);
  };

  return (
    <>
      <div className="topbar">
        <div className="topbar-language-wrapper">
          <button
            type="button"
            className="language-toggle"
            onClick={() => setShowLanguageMenu((prev) => !prev)}
            aria-label="Chọn ngôn ngữ"
            aria-expanded={showLanguageMenu}
          >
            <span>🌐</span>
            <span>{language === "vi" ? "VI" : "EN"}</span>
            <span className="language-arrow">
              {showLanguageMenu ? "⌃" : "⌄"}
            </span>
          </button>

          {showLanguageMenu && (
            <div className="language-menu">
              <button
                type="button"
                className={`language-option ${
                  language === "vi" ? "active" : ""
                }`}
                onClick={() => handleLanguageChange("vi")}
              >
                <span className="language-check">
                  {language === "vi" ? "✓" : ""}
                </span>

                <span>🇻🇳</span>

                <span>Tiếng Việt</span>
              </button>

              <button
                type="button"
                className={`language-option ${
                  language === "en" ? "active" : ""
                }`}
                onClick={() => handleLanguageChange("en")}
              >
                <span className="language-check">
                  {language === "en" ? "✓" : ""}
                </span>

                <span>🇬🇧</span>

                <span>English</span>
              </button>
            </div>
          )}
        </div>

        <div className="topbar-actions">
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label="Đổi giao diện sáng tối"
          >
            {darkMode ? "☀️" : "🌙"}
          </button>

          <div className="topbar-user">
            <span className="user-icon">👤</span>

            <span>
              Xin chào, <strong>Khoa Nguyễn</strong>
            </span>

            <span className="user-arrow">⌄</span>
          </div>
        </div>
      </div>

      <header className="header">
        <h1>🌱 NextFarm VoiceLog</h1>
        <p>Nhập nhật ký canh tác bằng giọng nói</p>
      </header>
    </>
  );
}

export default Header;