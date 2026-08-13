import {
  useEffect,
  useRef,
  useState,
} from "react";

function Header({
  language,
  onLanguageChange,
  text,

  themeMode = "light",
  onThemeChange,
}) {
  const [
    showLanguageMenu,
    setShowLanguageMenu,
  ] = useState(false);

  const [
    showUserMenu,
    setShowUserMenu,
  ] = useState(false);

  const languageRef =
    useRef(null);

  const userRef =
    useRef(null);

  /* ===========================
     Theme
  =========================== */

  const isDarkMode =
    document.body.classList.contains(
      "dark-mode"
    );

  const toggleTheme = () => {
    /*
      Header chỉ chuyển nhanh
      Light <-> Dark.

      System vẫn chọn trong Settings.
    */

    const nextTheme =
      isDarkMode
        ? "light"
        : "dark";

    onThemeChange?.(
      nextTheme
    );
  };

  /* ===========================
     Language
  =========================== */

  const handleLanguageChange = (
    lang
  ) => {
    onLanguageChange?.(
      lang
    );

    setShowLanguageMenu(
      false
    );

    setShowUserMenu(false);
  };

  const toggleLanguageMenu =
    () => {
      setShowLanguageMenu(
        (previous) => {
          const next =
            !previous;

          if (next) {
            setShowUserMenu(
              false
            );
          }

          return next;
        }
      );
    };

  /* ===========================
     User
  =========================== */

  const toggleUserMenu =
    () => {
      setShowUserMenu(
        (previous) => {
          const next =
            !previous;

          if (next) {
            setShowLanguageMenu(
              false
            );
          }

          return next;
        }
      );
    };

  /* ===========================
     Outside / Escape
  =========================== */

  useEffect(() => {
    const handleClickOutside = (
      event
    ) => {
      const outsideLanguage =
        languageRef.current &&
        !languageRef.current.contains(
          event.target
        );

      const outsideUser =
        userRef.current &&
        !userRef.current.contains(
          event.target
        );

      if (outsideLanguage) {
        setShowLanguageMenu(
          false
        );
      }

      if (outsideUser) {
        setShowUserMenu(
          false
        );
      }
    };

    const handleKeyDown = (
      event
    ) => {
      if (
        event.key ===
        "Escape"
      ) {
        setShowLanguageMenu(
          false
        );

        setShowUserMenu(
          false
        );
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
  }, []);

  return (
    <>
      <div className="topbar">
        <div className="topbar-spacer" />

        <div className="topbar-actions">
          {/* Language */}

          <div
            className="topbar-language-wrapper"
            ref={languageRef}
          >
            <button
              type="button"
              className="language-toggle"
              onClick={
                toggleLanguageMenu
              }
              aria-label={
                text.header
                  .chooseLanguage
              }
              aria-expanded={
                showLanguageMenu
              }
              aria-haspopup="menu"
            >
              <span>
                🌐
              </span>

              <span>
                {language === "vi"
                  ? "VI"
                  : "EN"}
              </span>

              <span className="language-arrow">
                {showLanguageMenu
                  ? "⌃"
                  : "⌄"}
              </span>
            </button>

            {showLanguageMenu && (
              <div
                className="language-menu"
                role="menu"
              >
                <button
                  type="button"
                  className={`language-option ${
                    language ===
                    "vi"
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    handleLanguageChange(
                      "vi"
                    )
                  }
                >
                  <span className="language-check">
                    {language ===
                    "vi"
                      ? "✓"
                      : ""}
                  </span>

                  <span>
                    🇻🇳
                  </span>

                  <span>
                    {
                      text.header
                        .vietnamese
                    }
                  </span>
                </button>

                <button
                  type="button"
                  className={`language-option ${
                    language ===
                    "en"
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    handleLanguageChange(
                      "en"
                    )
                  }
                >
                  <span className="language-check">
                    {language ===
                    "en"
                      ? "✓"
                      : ""}
                  </span>

                  <span>
                    🇬🇧
                  </span>

                  <span>
                    {
                      text.header
                        .english
                    }
                  </span>
                </button>
              </div>
            )}
          </div>

          {/* Theme */}

          <button
            type="button"
            className="theme-toggle"
            onClick={
              toggleTheme
            }
            aria-label={
              text.header
                .toggleTheme
            }
          >
            {isDarkMode
              ? "☀️"
              : "🌙"}
          </button>

          {/* User */}

          <div
            className="topbar-user-wrapper"
            ref={userRef}
          >
            <button
              type="button"
              className="topbar-user"
              onClick={
                toggleUserMenu
              }
              aria-expanded={
                showUserMenu
              }
              aria-haspopup="menu"
            >
              <span className="user-icon">
                👤
              </span>

              <span className="user-greeting">
                {
                  text.header
                    .greeting
                }
                ,{" "}

                <strong>
                  Khoa Nguyễn
                </strong>
              </span>

              <span className="user-arrow">
                {showUserMenu
                  ? "⌃"
                  : "⌄"}
              </span>
            </button>

            {showUserMenu && (
              <div
                className="user-menu"
                role="menu"
              >
                <div className="user-menu-header">
                  <div className="user-menu-avatar">
                    👤
                  </div>

                  <div>
                    <strong>
                      Khoa Nguyễn
                    </strong>

                    <span>
                      {
                        text.header
                          .account
                      }
                    </span>
                  </div>
                </div>

                <div className="user-menu-divider" />

                <button
                  type="button"
                  className="user-menu-item"
                >
                  <span>
                    👤
                  </span>

                  <span>
                    {
                      text.header
                        .profile
                    }
                  </span>
                </button>

                <button
                  type="button"
                  className="user-menu-item"
                >
                  <span>
                    📋
                  </span>

                  <span>
                    {
                      text.header
                        .myLogs
                    }
                  </span>
                </button>

                <button
                  type="button"
                  className="user-menu-item"
                >
                  <span>
                    ⚙️
                  </span>

                  <span>
                    {
                      text.header
                        .settings
                    }
                  </span>
                </button>

                <div className="user-menu-divider" />

                <button
                  type="button"
                  className="user-menu-item logout"
                >
                  <span>
                    🚪
                  </span>

                  <span>
                    {
                      text.header
                        .logout
                    }
                  </span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <header className="header">
        <h1>
          🌱 NextFarm VoiceLog
        </h1>

        <p>
          {text.header.subtitle}
        </p>
      </header>
    </>
  );
}

export default Header;