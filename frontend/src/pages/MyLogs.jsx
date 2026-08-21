import {
  useMemo,
  useState,
} from "react";

function MyLogs({
  language = "vi",
  logs = [],
  onEditLog,
}) {
  const isVietnamese =
    language === "vi";

  const [
    activeFilter,
    setActiveFilter,
  ] = useState("all");

  const [
    searchTerm,
    setSearchTerm,
  ] = useState("");

  const [
    selectedLog,
    setSelectedLog,
  ] = useState(null);

  /* ===========================
     Counters
  =========================== */

  const completedCount =
    logs.filter(
      (log) =>
        log.status ===
        "completed"
    ).length;

  const draftCount =
    logs.filter(
      (log) =>
        log.status ===
        "draft"
    ).length;

  const reviewCount =
    logs.filter(
      (log) =>
        log.status ===
        "review"
    ).length;

  /* ===========================
     Filter
  =========================== */

  const filteredLogs =
    useMemo(() => {
      let result =
        [...logs].sort(
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
        );

      if (
        activeFilter ===
        "completed"
      ) {
        result =
          result.filter(
            (log) =>
              log.status ===
              "completed"
          );
      }

      if (
        activeFilter ===
        "draft"
      ) {
        result =
          result.filter(
            (log) =>
              log.status ===
              "draft"
          );
      }

      if (
        activeFilter ===
        "review"
      ) {
        result =
          result.filter(
            (log) =>
              log.status ===
              "review"
          );
      }

      if (
        activeFilter ===
        "recent"
      ) {
        result =
          result.slice(
            0,
            3
          );
      }

      if (
        searchTerm.trim()
      ) {
        const keyword =
          searchTerm
            .trim()
            .toLowerCase();

        result =
          result.filter(
            (log) => {
              const combined =
                [
                  log.lot,
                  log.work,
                  log.material,
                  log.quantity,
                  log.unit,
                  log.date,
                  log.transcript,
                ]
                  .join(" ")
                  .toLowerCase();

              return combined.includes(
                keyword
              );
            }
          );
      }

      return result;
    }, [
      logs,
      activeFilter,
      searchTerm,
    ]);

  /* ===========================
     Status
  =========================== */

  const getStatusInfo = (
    status
  ) => {
    if (
      status ===
      "completed"
    ) {
      return {
        label:
          isVietnamese
            ? "Đã hoàn thành"
            : "Completed",

        icon: "✅",

        className:
          "completed",
      };
    }

    if (
      status ===
      "draft"
    ) {
      return {
        label:
          isVietnamese
            ? "Đang dở"
            : "Draft",

        icon: "📝",

        className:
          "draft",
      };
    }

    return {
      label:
        isVietnamese
          ? "Cần kiểm tra"
          : "Needs review",

      icon: "⚠️",

      className:
        "review",
    };
  };

  /* ===========================
     Card Action
  =========================== */

  const handleLogAction = (
    log
  ) => {
    /*
      Draft:
      tiếp tục ngay.
    */

    if (
      log.status ===
      "draft"
    ) {
      onEditLog?.(log);

      return;
    }

    /*
      Completed / Review:
      mở modal chi tiết trước.
    */

    setSelectedLog(log);
  };

  /* ===========================
     Edit from modal
  =========================== */

  const handleReviewAndEdit =
    () => {
      if (!selectedLog) {
        return;
      }

      const logToEdit =
        selectedLog;

      setSelectedLog(null);

      onEditLog?.(
        logToEdit
      );
    };

  return (
    <main className="workspace">
      <div className="workspace-container">
        {/* ===========================
            Hero
        =========================== */}

        <section className="workspace-hero">
          <div>
            <span className="workspace-eyebrow">
              NextFarm VoiceLog
            </span>

            <h2>
              📋{" "}
              {isVietnamese
                ? "Nhật ký của tôi"
                : "My logs"}
            </h2>

            <p>
              {isVietnamese
                ? "Quản lý, tìm kiếm và theo dõi trạng thái các nhật ký canh tác."
                : "Manage, search and track the status of your farming logs."}
            </p>
          </div>
        </section>

        {/* ===========================
            Summary
        =========================== */}

        <section className="logs-summary-grid">
          <div className="logs-summary-card">
            <span className="logs-summary-icon">
              📋
            </span>

            <div>
              <strong>
                {logs.length}
              </strong>

              <span>
                {isVietnamese
                  ? "Tổng nhật ký"
                  : "Total logs"}
              </span>
            </div>
          </div>

          <div className="logs-summary-card completed">
            <span className="logs-summary-icon">
              ✅
            </span>

            <div>
              <strong>
                {
                  completedCount
                }
              </strong>

              <span>
                {isVietnamese
                  ? "Đã hoàn thành"
                  : "Completed"}
              </span>
            </div>
          </div>

          <div className="logs-summary-card draft">
            <span className="logs-summary-icon">
              📝
            </span>

            <div>
              <strong>
                {draftCount}
              </strong>

              <span>
                {isVietnamese
                  ? "Đang dở"
                  : "Draft"}
              </span>
            </div>
          </div>

          <div className="logs-summary-card review">
            <span className="logs-summary-icon">
              ⚠️
            </span>

            <div>
              <strong>
                {reviewCount}
              </strong>

              <span>
                {isVietnamese
                  ? "Cần kiểm tra"
                  : "Needs review"}
              </span>
            </div>
          </div>
        </section>

        {/* ===========================
            Toolbar
        =========================== */}

        <section className="logs-toolbar">
          <div className="logs-filter-tabs">
            {[
              [
                "all",
                "Tất cả",
                "All",
              ],
              [
                "completed",
                "Hoàn thành",
                "Completed",
              ],
              [
                "draft",
                "Đang dở",
                "Draft",
              ],
              [
                "review",
                "Cần kiểm tra",
                "Needs review",
              ],
              [
                "recent",
                "Gần đây",
                "Recent",
              ],
            ].map(
              ([
                id,
                vi,
                en,
              ]) => (
                <button
                  key={id}
                  type="button"
                  className={
                    activeFilter ===
                    id
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    setActiveFilter(
                      id
                    )
                  }
                >
                  {isVietnamese
                    ? vi
                    : en}
                </button>
              )
            )}
          </div>

          <div className="logs-search-wrapper">
            <span>
              🔍
            </span>

            <input
              type="text"
              value={
                searchTerm
              }
              onChange={(
                event
              ) =>
                setSearchTerm(
                  event.target
                    .value
                )
              }
              placeholder={
                isVietnamese
                  ? "Tìm theo lô, công việc, vật tư..."
                  : "Search by plot, task, material..."
              }
            />
          </div>
        </section>

        {/* ===========================
            List
        =========================== */}

        <section className="logs-list">
          {filteredLogs.length ===
          0 ? (
            <div className="logs-empty-state">
              <span>
                📭
              </span>

              <h3>
                {isVietnamese
                  ? "Không tìm thấy nhật ký"
                  : "No logs found"}
              </h3>

              <p>
                {isVietnamese
                  ? "Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm."
                  : "Try another filter or search term."}
              </p>
            </div>
          ) : (
            filteredLogs.map(
              (log) => {
                const status =
                  getStatusInfo(
                    log.status
                  );

                return (
                  <article
                    key={
                      log.id
                    }
                    className="log-card"
                  >
                    <div className="log-card-header">
                      <div>
                        <span className="log-lot">
                          🏷️{" "}
                          {log.lot ||
                            "---"}
                        </span>

                        <h3>
                          {log.work ||
                            (isVietnamese
                              ? "Chưa có công việc"
                              : "No task")}
                        </h3>
                      </div>

                      <span
                        className={`log-status ${status.className}`}
                      >
                        {
                          status.icon
                        }{" "}
                        {
                          status.label
                        }
                      </span>
                    </div>

                    <div className="log-card-info">
                      <span>
                        🌾{" "}
                        {log.material ||
                          (isVietnamese
                            ? "Không có vật tư"
                            : "No material")}
                      </span>

                      <span>
                        📦{" "}
                        {log.quantity
                          ? `${log.quantity} ${
                              log.unit ||
                              ""
                            }`
                          : isVietnamese
                            ? "Chưa có số lượng"
                            : "No quantity"}
                      </span>

                      <span>
                        🕒{" "}
                        {log.time ||
                          (isVietnamese
                            ? "Chưa có thời gian"
                            : "No time")}
                      </span>
                    </div>

                    {log.status ===
                      "review" && (
                      <div className="log-review-warning">
                        ⚠️{" "}
                        {log.warning ||
                          (isVietnamese
                            ? "Nhật ký có dữ liệu cần kiểm tra."
                            : "This log needs review.")}
                      </div>
                    )}

                    <div className="log-card-footer">
                      <span>
                        📅{" "}
                        {log.date}
                      </span>

                      <button
                        type="button"
                        className="log-action-btn"
                        onClick={() =>
                          handleLogAction(
                            log
                          )
                        }
                      >
                        {log.status ===
                        "draft"
                          ? isVietnamese
                            ? "Tiếp tục →"
                            : "Continue →"
                          : log.status ===
                              "review"
                            ? isVietnamese
                              ? "Kiểm tra →"
                              : "Review →"
                            : isVietnamese
                              ? "Xem chi tiết →"
                              : "View details →"}
                      </button>
                    </div>
                  </article>
                );
              }
            )
          )}
        </section>

        <div className="logs-dev-note">
          💾{" "}
          {isVietnamese
            ? "Nhật ký hiện được lưu cục bộ trên trình duyệt để phục vụ phát triển frontend. Khi API production sẵn sàng, tầng lưu trữ này sẽ được thay bằng backend."
            : "Logs are currently stored locally for frontend development. This storage layer will later be replaced by the production API."}
        </div>
      </div>

      {/* ===========================
          Detail Modal
      =========================== */}

      {selectedLog && (
        <div
          className="log-detail-overlay"
          onMouseDown={(
            event
          ) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              setSelectedLog(
                null
              );
            }
          }}
        >
          <div className="log-detail-modal">
            <div className="log-detail-header">
              <div>
                <span className="workspace-eyebrow">
                  {
                    selectedLog.id
                  }
                </span>

                <h2>
                  🏷️{" "}
                  {
                    selectedLog.lot
                  }
                </h2>
              </div>

              <button
                type="button"
                className="log-detail-close"
                onClick={() =>
                  setSelectedLog(
                    null
                  )
                }
                aria-label={
                  isVietnamese
                    ? "Đóng"
                    : "Close"
                }
              >
                ✕
              </button>
            </div>

            <div className="log-detail-status-row">
              {(() => {
                const status =
                  getStatusInfo(
                    selectedLog.status
                  );

                return (
                  <span
                    className={`log-status ${status.className}`}
                  >
                    {
                      status.icon
                    }{" "}
                    {
                      status.label
                    }
                  </span>
                );
              })()}

              <span>
                📅{" "}
                {
                  selectedLog.date
                }
              </span>
            </div>

            {/* Transcript */}

            <div className="log-detail-section">
              <h3>
                🎙{" "}
                {isVietnamese
                  ? "Nội dung ghi âm"
                  : "Transcript"}
              </h3>

              <div className="log-detail-transcript">
                {
                  selectedLog.transcript ||
                  "-"
                }
              </div>
            </div>

            {/* Data */}

            <div className="log-detail-section">
              <h3>
                🤖{" "}
                {isVietnamese
                  ? "Dữ liệu nhật ký"
                  : "Log data"}
              </h3>

              <div className="log-detail-grid">
                <DetailItem
                  icon="🏷️"
                  label={
                    isVietnamese
                      ? "Lô canh tác"
                      : "Farm plot"
                  }
                  value={
                    selectedLog.lot ||
                    "-"
                  }
                />

                <DetailItem
                  icon="🛠️"
                  label={
                    isVietnamese
                      ? "Công việc"
                      : "Task"
                  }
                  value={
                    selectedLog.work ||
                    "-"
                  }
                />

                <DetailItem
                  icon="🌾"
                  label={
                    isVietnamese
                      ? "Vật tư"
                      : "Material"
                  }
                  value={
                    selectedLog.material ||
                    "-"
                  }
                />

                <DetailItem
                  icon="📦"
                  label={
                    isVietnamese
                      ? "Số lượng"
                      : "Quantity"
                  }
                  value={
                    selectedLog.quantity ||
                    "-"
                  }
                />

                <DetailItem
                  icon="⚖️"
                  label={
                    isVietnamese
                      ? "Đơn vị"
                      : "Unit"
                  }
                  value={
                    selectedLog.unit ||
                    "-"
                  }
                />

                <DetailItem
                  icon="🕒"
                  label={
                    isVietnamese
                      ? "Thời gian"
                      : "Time"
                  }
                  value={
                    selectedLog.time ||
                    "-"
                  }
                />

                <DetailItem
                  icon="📅"
                  label={
                    isVietnamese
                      ? "Ngày"
                      : "Date"
                  }
                  value={
                    selectedLog.date ||
                    "-"
                  }
                />
              </div>
            </div>

            {/* Review warning */}

            {selectedLog.status ===
              "review" && (
              <div className="log-detail-warning">
                <strong>
                  ⚠️{" "}
                  {isVietnamese
                    ? "Cần kiểm tra"
                    : "Needs review"}
                </strong>

                <span>
                  {selectedLog.warning ||
                    (isVietnamese
                      ? "Nhật ký có thông tin cần được kiểm tra trước khi hoàn tất."
                      : "This log contains information that must be reviewed before completion.")}
                </span>
              </div>
            )}

            {/* Footer */}

            <div className="log-detail-footer log-detail-footer-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() =>
                  setSelectedLog(null)
                }
              >
                {isVietnamese
                  ? "Đóng"
                  : "Close"}
              </button>

              <button
                type="button"
                className="btn-primary"
                onClick={
                  handleReviewAndEdit
                }
              >
                ✏️{" "}
                {selectedLog.status === "review"
                  ? isVietnamese
                    ? "Kiểm tra & sửa"
                    : "Review & edit"
                  : isVietnamese
                    ? "Chỉnh sửa"
                    : "Edit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function DetailItem({
  icon,
  label,
  value,
}) {
  return (
    <div className="log-detail-item">
      <span>
        {icon} {label}
      </span>

      <strong>
        {value}
      </strong>
    </div>
  );
}

export default MyLogs;