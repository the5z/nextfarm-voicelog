import {
  useEffect,
  useRef,
  useState,
} from "react";

function Header({
  language,
  onLanguageChange,
  text,
}) {
  /* ===========================
     Theme
  =========================== */

  const [darkMode, setDarkMode] = useState(() => {
    try {
      const savedTheme =
        localStorage.getItem(
          "nextfarm-theme"
        );

      if (savedTheme === "dark") {
        return true;
      }

      if (savedTheme === "light") {
        return false;
      }

      return false;
    } catch (error) {
      console.error(
        "Load theme error:",
        error
      );

      return false;
    }
  });

  const [showLanguageMenu, setShowLanguageMenu] =
    useState(false);

  const [showUserMenu, setShowUserMenu] =
    useState(false);

  const languageRef = useRef(null);
  const userRef = useRef(null);

  /* ===========================
     Apply saved theme
  =========================== */

  useEffect(() => {
    document.body.classList.toggle(
      "dark-mode",
      darkMode
    );

    try {
      localStorage.setItem(
        "nextfarm-theme",
        darkMode
          ? "dark"
          : "light"
      );
    } catch (error) {
      console.error(
        "Save theme error:",
        error
      );
    }
  }, [darkMode]);

  const toggleTheme = () => {
    setDarkMode(
      (previousMode) =>
        !previousMode
    );
  };

  /* ===========================
     Language
  =========================== */

  const handleLanguageChange = (lang) => {
    onLanguageChange(lang);

    setShowLanguageMenu(false);
    setShowUserMenu(false);
  };

  const toggleLanguageMenu = () => {
    setShowLanguageMenu((prev) => {
      const nextState = !prev;

      if (nextState) {
        setShowUserMenu(false);
      }

      return nextState;
    });
  };

  /* ===========================
     User menu
  =========================== */

  const toggleUserMenu = () => {
    setShowUserMenu((prev) => {
      const nextState = !prev;

      if (nextState) {
        setShowLanguageMenu(false);
      }

      return nextState;
    });
  };

  /* ===========================
     Close dropdown
     - Click outside
     - Press Escape
  =========================== */

  useEffect(() => {
    const handleClickOutside = (event) => {
      const clickedOutsideLanguage =
        languageRef.current &&
        !languageRef.current.contains(
          event.target
        );

      const clickedOutsideUser =
        userRef.current &&
        !userRef.current.contains(
          event.target
        );

      if (clickedOutsideLanguage) {
        setShowLanguageMenu(false);
      }

      if (clickedOutsideUser) {
        setShowUserMenu(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setShowLanguageMenu(false);
        setShowUserMenu(false);
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
          {/* ===========================
              Language
          =========================== */}

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
              <span aria-hidden="true">
                🌐
              </span>

              <span>
                {language === "vi"
                  ? "VI"
                  : "EN"}
              </span>

              <span
                className="language-arrow"
                aria-hidden="true"
              >
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
                    language === "vi"
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    handleLanguageChange(
                      "vi"
                    )
                  }
                  role="menuitem"
                >
                  <span className="language-check">
                    {language === "vi"
                      ? "✓"
                      : ""}
                  </span>

                  <span>🇻🇳</span>

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
                    language === "en"
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    handleLanguageChange(
                      "en"
                    )
                  }
                  role="menuitem"
                >
                  <span className="language-check">
                    {language === "en"
                      ? "✓"
                      : ""}
                  </span>

                  <span>🇬🇧</span>

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

          {/* ===========================
              Theme
          =========================== */}

          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={
              text.header.toggleTheme
            }
            aria-pressed={darkMode}
          >
            {darkMode
              ? "☀️"
              : "🌙"}
          </button>

          {/* ===========================
              User
          =========================== */}

          <div
            className="topbar-user-wrapper"
            ref={userRef}
          >
            <button
              type="button"
              className="topbar-user"
              onClick={toggleUserMenu}
              aria-expanded={
                showUserMenu
              }
              aria-haspopup="menu"
            >
              <span
                className="user-icon"
                aria-hidden="true"
              >
                👤
              </span>

              <span className="user-greeting">
                {
                  text.header.greeting
                }
                ,{" "}

                <strong>
                  Khoa Nguyễn
                </strong>
              </span>

              <span
                className="user-arrow"
                aria-hidden="true"
              >
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
                  role="menuitem"
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
                  role="menuitem"
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
                  role="menuitem"
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
                  role="menuitem"
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