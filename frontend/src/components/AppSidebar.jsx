function AppSidebar({
  language = "vi",
  activePage = "create",
  onNavigate,
}) {
  const isVietnamese =
    language === "vi";

  const handleNavigate = (page) => {
    if (onNavigate) {
      onNavigate(page);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          🌱
        </div>

        <div className="sidebar-brand-text">
          <strong>
            NextFarm
          </strong>

          <span>
            VoiceLog
          </span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button
          type="button"
          className={`sidebar-item ${
            activePage === "create"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigate("create")
          }
        >
          <span className="sidebar-item-icon">
            🎙
          </span>

          <span>
            {isVietnamese
              ? "Tạo nhật ký"
              : "Create log"}
          </span>
        </button>

        <button
          type="button"
          className={`sidebar-item ${
            activePage === "logs"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigate("logs")
          }
        >
          <span className="sidebar-item-icon">
            📋
          </span>

          <span>
            {isVietnamese
              ? "Nhật ký của tôi"
              : "My logs"}
          </span>
        </button>

        <div className="sidebar-divider" />

        <button
          type="button"
          className={`sidebar-item ${
            activePage === "settings"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigate("settings")
          }
        >
          <span className="sidebar-item-icon">
            ⚙️
          </span>

          <span>
            {isVietnamese
              ? "Cài đặt"
              : "Settings"}
          </span>
        </button>
      </nav>
    </aside>
  );
}

export default AppSidebar;