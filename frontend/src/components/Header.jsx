import {
  useEffect,
  useRef,
  useState,
} from "react";

function Header({
  language,
  onLanguageChange,
  text,

  onThemeChange,

  logs = [],
}) {
  const [
    showLanguageMenu,
    setShowLanguageMenu,
  ] = useState(false);

  const [
    showUserMenu,
    setShowUserMenu,
  ] = useState(false);

  const [
    accountPanel,
    setAccountPanel,
  ] = useState(null);

  const [
    showLogoutConfirm,
    setShowLogoutConfirm,
  ] = useState(false);

  const [
    logoutMessage,
    setLogoutMessage,
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

  const openAccountPanel = (
    panel
  ) => {
    setAccountPanel(panel);
    setShowUserMenu(false);
  };

  const closeAccountPanel =
    () => {
      setAccountPanel(null);
    };

  const completedLogs =
    logs.filter(
      (log) =>
        log.status ===
        "completed"
    ).length;

  const pendingLogs =
    logs.length -
    completedLogs;

  const recentLogs =
    [...logs]
      .sort(
        (a, b) =>
          new Date(
            b.updatedAt ||
              b.createdAt ||
              0
          ) -
          new Date(
            a.updatedAt ||
              a.createdAt ||
              0
          )
      )
      .slice(0, 3);

  const isVietnamese =
    language === "vi";

  const accountCopy =
    isVietnamese
      ? {
          profile:
            "Hồ sơ cá nhân",
          statistics:
            "Thống kê hoạt động",
          help:
            "Trợ giúp & hướng dẫn",
          logout:
            "Đăng xuất",
          role:
            "Nhân viên canh tác",
          language:
            "Tiếng Việt",
          account:
            "Tài khoản NextFarm",
          personalInfo:
            "Thông tin cá nhân",
          fullName:
            "Họ và tên",
          roleLabel:
            "Vai trò",
          languageLabel:
            "Ngôn ngữ",
          activity:
            "Hoạt động",
          totalLogs:
            "Nhật ký đã tạo",
          confirmed:
            "Đã xác nhận",
          pending:
            "Chờ kiểm tra",
          recent:
            "Hoạt động gần đây",
          noRecent:
            "Chưa có nhật ký gần đây.",
          recordGuide:
            "Cách ghi âm hiệu quả",
          recordGuideText:
            "Nói rõ hoạt động, lô, vật tư, số lượng và thời gian.",
          aiWrong:
            "AI nhận sai?",
          aiWrongText:
            "Bạn có thể sửa bản ghi và các trường AI trước khi xác nhận.",
          noisy:
            "Môi trường nhiều tiếng ồn",
          noisyText:
            "Đưa điện thoại gần người nói và tránh nguồn tiếng ồn lớn.",
          process:
            "Quy trình",
          processText:
            "Ghi âm → AI xử lý → Kiểm tra → Xác nhận.",
          logoutTitle:
            "Xác nhận đăng xuất",
          logoutText:
            "Bạn có chắc muốn đăng xuất khỏi NextFarm VoiceLog?",
          cancel:
            "Hủy",
          confirmLogout:
            "Đăng xuất",
          demoLogout:
            "Đã mô phỏng đăng xuất. Hệ thống hiện chưa kết nối xác thực tài khoản thật.",
          backToApp:
            "Quay lại ứng dụng",
        }
      : {
          profile:
            "Personal profile",
          statistics:
            "Activity statistics",
          help:
            "Help & guide",
          logout:
            "Log out",
          role:
            "Farm worker",
          language:
            "English",
          account:
            "NextFarm account",
          personalInfo:
            "Personal information",
          fullName:
            "Full name",
          roleLabel:
            "Role",
          languageLabel:
            "Language",
          activity:
            "Activity",
          totalLogs:
            "Logs created",
          confirmed:
            "Confirmed",
          pending:
            "Pending review",
          recent:
            "Recent activity",
          noRecent:
            "No recent logs.",
          recordGuide:
            "Record effectively",
          recordGuideText:
            "Clearly say the activity, plot, material, quantity and time.",
          aiWrong:
            "AI got it wrong?",
          aiWrongText:
            "You can edit the transcript and AI fields before confirmation.",
          noisy:
            "Noisy environment",
          noisyText:
            "Keep the phone close to the speaker and away from loud noise sources.",
          process:
            "Workflow",
          processText:
            "Record → AI processing → Review → Confirm.",
          logoutTitle:
            "Confirm logout",
          logoutText:
            "Are you sure you want to log out of NextFarm VoiceLog?",
          cancel:
            "Cancel",
          confirmLogout:
            "Log out",
          demoLogout:
            "Logout simulated. Real account authentication is not connected yet.",
          backToApp:
            "Back to app",
        };

  const handleLogout = () => {
    setShowLogoutConfirm(false);
    setShowUserMenu(false);
    setLogoutMessage(true);
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
                  onClick={() =>
                    openAccountPanel(
                      "profile"
                    )
                  }
                >
                  <span>👤</span>
                  <span>
                    {
                      accountCopy.profile
                    }
                  </span>
                  <span className="user-menu-chevron">
                    ›
                  </span>
                </button>

                <button
                  type="button"
                  className="user-menu-item"
                  onClick={() =>
                    openAccountPanel(
                      "statistics"
                    )
                  }
                >
                  <span>📊</span>
                  <span>
                    {
                      accountCopy.statistics
                    }
                  </span>
                  <span className="user-menu-chevron">
                    ›
                  </span>
                </button>

                <button
                  type="button"
                  className="user-menu-item"
                  onClick={() =>
                    openAccountPanel(
                      "help"
                    )
                  }
                >
                  <span>❓</span>
                  <span>
                    {
                      accountCopy.help
                    }
                  </span>
                  <span className="user-menu-chevron">
                    ›
                  </span>
                </button>

                <div className="user-menu-divider" />

                <button
                  type="button"
                  className="user-menu-item logout"
                  onClick={() => {
                    setShowUserMenu(
                      false
                    );
                    setShowLogoutConfirm(
                      true
                    );
                  }}
                >
                  <span>🚪</span>
                  <span>
                    {
                      accountCopy.logout
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

      {accountPanel && (
        <div
          className="account-modal-backdrop"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeAccountPanel();
            }
          }}
        >
          <section
            className="account-modal"
            role="dialog"
            aria-modal="true"
          >
            <div className="account-modal-top">
              <button
                type="button"
                className="account-back-btn"
                onClick={() => {
                  setAccountPanel(null);
                  setShowUserMenu(true);
                }}
                aria-label="Back"
              >
                ←
              </button>

              <h2>
                {accountPanel ===
                "profile"
                  ? accountCopy.profile
                  : accountPanel ===
                      "statistics"
                    ? accountCopy.statistics
                    : accountCopy.help}
              </h2>

              <button
                type="button"
                className="account-close-btn"
                onClick={
                  closeAccountPanel
                }
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            {accountPanel ===
              "profile" && (
              <div className="account-panel-content">
                <div className="profile-hero-card">
                  <div className="profile-large-avatar">
                    👤
                  </div>

                  <div>
                    <h3>
                      Khoa Nguyễn
                    </h3>
                    <p>
                      {
                        accountCopy.account
                      }
                    </p>
                  </div>
                </div>

                <h4>
                  {
                    accountCopy.personalInfo
                  }
                </h4>

                <div className="profile-info-list">
                  <div>
                    <span>
                      {
                        accountCopy.fullName
                      }
                    </span>
                    <strong>
                      Khoa Nguyễn
                    </strong>
                  </div>
                  <div>
                    <span>
                      {
                        accountCopy.roleLabel
                      }
                    </span>
                    <strong>
                      {
                        accountCopy.role
                      }
                    </strong>
                  </div>
                  <div>
                    <span>
                      {
                        accountCopy.languageLabel
                      }
                    </span>
                    <strong>
                      {
                        accountCopy.language
                      }
                    </strong>
                  </div>
                </div>

                <h4>
                  {
                    accountCopy.activity
                  }
                </h4>

                <div className="account-stat-grid">
                  <div>
                    <strong>
                      {logs.length}
                    </strong>
                    <span>
                      {
                        accountCopy.totalLogs
                      }
                    </span>
                  </div>
                  <div>
                    <strong>
                      {completedLogs}
                    </strong>
                    <span>
                      {
                        accountCopy.confirmed
                      }
                    </span>
                  </div>
                </div>
              </div>
            )}

            {accountPanel ===
              "statistics" && (
              <div className="account-panel-content">
                <div className="account-stat-grid three">
                  <div>
                    <strong>
                      {logs.length}
                    </strong>
                    <span>
                      {
                        accountCopy.totalLogs
                      }
                    </span>
                  </div>
                  <div>
                    <strong>
                      {completedLogs}
                    </strong>
                    <span>
                      {
                        accountCopy.confirmed
                      }
                    </span>
                  </div>
                  <div>
                    <strong>
                      {pendingLogs}
                    </strong>
                    <span>
                      {
                        accountCopy.pending
                      }
                    </span>
                  </div>
                </div>

                <h4>
                  {
                    accountCopy.recent
                  }
                </h4>

                <div className="recent-activity-list">
                  {recentLogs.length >
                  0 ? (
                    recentLogs.map(
                      (log) => (
                        <div
                          className="recent-activity-item"
                          key={
                            log.id
                          }
                        >
                          <span className="recent-activity-icon">
                            🌱
                          </span>

                          <div>
                            <strong>
                              {log.work ||
                                "—"}
                            </strong>
                            <span>
                              {log.lot
                                ? `${
                                    isVietnamese
                                      ? "Lô"
                                      : "Plot"
                                  } ${log.lot}`
                                : "—"}
                              {log.date
                                ? ` · ${log.date}`
                                : ""}
                            </span>
                          </div>

                          <span
                            className={`activity-status ${log.status || "draft"}`}
                          >
                            {log.status ===
                            "completed"
                              ? "✓"
                              : "•"}
                          </span>
                        </div>
                      )
                    )
                  ) : (
                    <p className="account-empty-text">
                      {
                        accountCopy.noRecent
                      }
                    </p>
                  )}
                </div>
              </div>
            )}

            {accountPanel ===
              "help" && (
              <div className="account-panel-content help-card-list">
                <div className="help-guide-card">
                  <span>🎙️</span>
                  <div>
                    <strong>
                      {
                        accountCopy.recordGuide
                      }
                    </strong>
                    <p>
                      {
                        accountCopy.recordGuideText
                      }
                    </p>
                  </div>
                </div>

                <div className="help-guide-card">
                  <span>🤖</span>
                  <div>
                    <strong>
                      {
                        accountCopy.aiWrong
                      }
                    </strong>
                    <p>
                      {
                        accountCopy.aiWrongText
                      }
                    </p>
                  </div>
                </div>

                <div className="help-guide-card">
                  <span>🔇</span>
                  <div>
                    <strong>
                      {
                        accountCopy.noisy
                      }
                    </strong>
                    <p>
                      {
                        accountCopy.noisyText
                      }
                    </p>
                  </div>
                </div>

                <div className="help-guide-card">
                  <span>🧭</span>
                  <div>
                    <strong>
                      {
                        accountCopy.process
                      }
                    </strong>
                    <p>
                      {
                        accountCopy.processText
                      }
                    </p>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      {showLogoutConfirm && (
        <div className="account-modal-backdrop">
          <section
            className="logout-confirm-card"
            role="alertdialog"
            aria-modal="true"
          >
            <div className="logout-confirm-icon">
              🚪
            </div>
            <h2>
              {
                accountCopy.logoutTitle
              }
            </h2>
            <p>
              {
                accountCopy.logoutText
              }
            </p>

            <div className="logout-confirm-actions">
              <button
                type="button"
                className="logout-cancel-btn"
                onClick={() =>
                  setShowLogoutConfirm(
                    false
                  )
                }
              >
                {
                  accountCopy.cancel
                }
              </button>
              <button
                type="button"
                className="logout-danger-btn"
                onClick={
                  handleLogout
                }
              >
                {
                  accountCopy.confirmLogout
                }
              </button>
            </div>
          </section>
        </div>
      )}

      {logoutMessage && (
        <div className="account-modal-backdrop">
          <section className="logout-confirm-card">
            <div className="logout-confirm-icon">
              ✅
            </div>
            <h2>
              {
                accountCopy.logout
              }
            </h2>
            <p>
              {
                accountCopy.demoLogout
              }
            </p>
            <button
              type="button"
              className="logout-cancel-btn full"
              onClick={() =>
                setLogoutMessage(
                  false
                )
              }
            >
              {
                accountCopy.backToApp
              }
            </button>
          </section>
        </div>
      )}
    </>
  );
}

export default Header;