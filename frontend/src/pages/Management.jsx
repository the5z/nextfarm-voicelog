import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCropTypes,
  getHarvests,
  getIssueReports,
  getPlots,
  getSeasons,
  getTasks,
} from "../services/integrationService";

const RESOURCE_CONFIGS = [
  {
    key: "cropTypes",
    icon: "🌾",
    labelVi: "Loại cây trồng",
    labelEn: "Crop types",
    loader: getCropTypes,
    titleField: "crop_name",
    fields: [
      ["crop_group_text", "Nhóm cây", "Crop group"],
      ["crop_id", "Mã nội bộ", "Internal ID"],
      ["crop_code_suggestion", "Mã gợi ý", "Suggested code"],
      ["days_to_harvest", "Số ngày thu hoạch", "Days to harvest"],
    ],
  },
  {
    key: "plots",
    icon: "🗺️",
    labelVi: "Lô canh tác",
    labelEn: "Plots",
    loader: getPlots,
    titleField: "plot_name_or_code",
    fields: [
      ["plot_code", "Mã lô", "Plot code"],
      ["region_id", "Khu vực", "Region"],
      ["current_crop_id", "Cây hiện tại", "Current crop"],
      ["boundary_required", "Yêu cầu ranh giới", "Boundary required"],
      ["owner_text", "Chủ lô", "Owner"],
      ["location_hint_text", "Gợi ý vị trí", "Location hint"],
    ],
  },
  {
    key: "seasons",
    icon: "🌱",
    labelVi: "Mùa vụ",
    labelEn: "Seasons",
    loader: getSeasons,
    titleField: "season_name",
    fields: [
      ["season_id", "Mã mùa vụ", "Season ID"],
      ["plot_code", "Mã lô", "Plot code"],
      ["crop_id", "Cây trồng", "Crop"],
      ["planting_date_text", "Ngày trồng", "Planting date"],
      ["expected_harvest_date_text", "Ngày thu hoạch dự kiến", "Expected harvest"],
      ["plant_count", "Số cây", "Plant count"],
      ["expected_yield", "Sản lượng dự kiến", "Expected yield"],
      ["expected_yield_unit_code", "Đơn vị sản lượng", "Yield unit"],
      ["process_template_text", "Quy trình", "Process template"],
    ],
  },
  {
    key: "tasks",
    icon: "✅",
    labelVi: "Công việc",
    labelEn: "Tasks",
    loader: getTasks,
    titleField: "task_name",
    fields: [
      ["season_id", "Mùa vụ", "Season"],
      ["task_type_text", "Loại công việc", "Task type"],
      ["due_time_text", "Hạn thực hiện", "Due time"],
      ["assignee_text", "Người thực hiện", "Assignee"],
      ["photo_required", "Yêu cầu ảnh", "Photo required"],
      ["note", "Ghi chú", "Note"],
    ],
  },
  {
    key: "issues",
    icon: "⚠️",
    labelVi: "Sự cố",
    labelEn: "Issues",
    loader: getIssueReports,
    titleField: "description",
    fields: [
      ["plot_code", "Mã lô", "Plot code"],
      ["issue_type", "Loại sự cố", "Issue type"],
      ["severity", "Mức độ", "Severity"],
      ["photo", "Ảnh", "Photo"],
      ["note", "Ghi chú", "Note"],
    ],
  },
  {
    key: "harvests",
    icon: "🧺",
    labelVi: "Thu hoạch",
    labelEn: "Harvests",
    loader: getHarvests,
    titleField: "harvest_date_text",
    fields: [
      ["plot_code", "Mã lô", "Plot code"],
      ["crop_id", "Cây trồng", "Crop"],
      ["quantity", "Số lượng", "Quantity"],
      ["unit_code", "Đơn vị", "Unit"],
      ["harvest_date_text", "Ngày thu hoạch", "Harvest date"],
      ["photo", "Ảnh", "Photo"],
      ["note", "Ghi chú", "Note"],
    ],
  },
];

function formatValue(
  value,
  language
) {
  const isVietnamese =
    language === "vi";

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return isVietnamese
      ? "Chưa có"
      : "Not available";
  }

  if (typeof value === "boolean") {
    return value
      ? isVietnamese
        ? "Có"
        : "Yes"
      : isVietnamese
        ? "Không"
        : "No";
  }

  return String(value);
}

function formatCreatedAt(
  value,
  language
) {
  if (!value) {
    return "";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return String(value);
  }

  return date.toLocaleString(
    language === "vi"
      ? "vi-VN"
      : "en-US"
  );
}

function Management({
  language = "vi",
}) {
  const isVietnamese =
    language === "vi";

  const [
    activeResource,
    setActiveResource,
  ] = useState("cropTypes");

  const [
    recordsByResource,
    setRecordsByResource,
  ] = useState({});

  const [
    loadingResource,
    setLoadingResource,
  ] = useState(null);

  const [
    errorByResource,
    setErrorByResource,
  ] = useState({});

  const [
    searchTerm,
    setSearchTerm,
  ] = useState("");

  const activeConfig =
    RESOURCE_CONFIGS.find(
      (item) =>
        item.key === activeResource
    ) || RESOURCE_CONFIGS[0];

  const loadRecords =
    useCallback(
      async (
        resourceKey,
        force = false
      ) => {
        const config =
          RESOURCE_CONFIGS.find(
            (item) =>
              item.key ===
              resourceKey
          );

        if (!config) {
          return;
        }

        if (
          !force &&
          Object.prototype
            .hasOwnProperty.call(
              recordsByResource,
              resourceKey
            )
        ) {
          return;
        }

        setLoadingResource(
          resourceKey
        );

        setErrorByResource(
          (previous) => ({
            ...previous,
            [resourceKey]:
              null,
          })
        );

        try {
          const result =
            await config.loader();

          const records =
            Array.isArray(
              result?.data
            )
              ? result.data
              : [];

          setRecordsByResource(
            (previous) => ({
              ...previous,
              [resourceKey]:
                records,
            })
          );
        } catch (error) {
          console.error(
            "Load management data error:",
            {
              resourceKey,
              error,
            }
          );

          setErrorByResource(
            (previous) => ({
              ...previous,
              [resourceKey]:
                error?.message ||
                (
                  isVietnamese
                    ? "Không thể tải dữ liệu từ Integration Service."
                    : "Could not load data from the Integration Service."
                ),
            })
          );
        } finally {
          setLoadingResource(
            (current) =>
              current ===
                resourceKey
                ? null
                : current
          );
        }
      },
      [
        recordsByResource,
        isVietnamese,
      ]
    );

  useEffect(() => {
    loadRecords(
      activeResource
    );
  }, [
    activeResource,
    loadRecords,
  ]);

  const records =
    recordsByResource[
      activeResource
    ] || [];

  const filteredRecords =
    useMemo(() => {
      const keyword =
        searchTerm
          .trim()
          .toLowerCase();

      const sorted =
        [...records].sort(
          (left, right) => {
            const leftTime =
              new Date(
                left?.created_at ||
                  0
              ).getTime();

            const rightTime =
              new Date(
                right?.created_at ||
                  0
              ).getTime();

            if (
              Number.isFinite(
                leftTime
              ) &&
              Number.isFinite(
                rightTime
              ) &&
              leftTime !==
                rightTime
            ) {
              return (
                rightTime -
                leftTime
              );
            }

            return (
              Number(
                right?.id || 0
              ) -
              Number(
                left?.id || 0
              )
            );
          }
        );

      if (!keyword) {
        return sorted;
      }

      return sorted.filter(
        (record) =>
          Object.values(
            record || {}
          )
            .filter(
              (value) =>
                value !== null &&
                value !==
                  undefined
            )
            .join(" ")
            .toLowerCase()
            .includes(keyword)
      );
    }, [
      records,
      searchTerm,
    ]);

  const isLoading =
    loadingResource ===
    activeResource;

  const error =
    errorByResource[
      activeResource
    ];

  return (
    <main className="workspace">
      <div className="workspace-container">
        <section className="workspace-hero">
          <div>
            <span className="workspace-eyebrow">
              NextFarm Data
            </span>

            <h2>
              {isVietnamese
                ? "Quản lý dữ liệu"
                : "Data management"}
            </h2>

            <p>
              {isVietnamese
                ? "Theo dõi các loại cây, lô canh tác, mùa vụ, công việc, sự cố và thu hoạch đã lưu trong hệ thống."
                : "Review crop types, plots, seasons, tasks, issues, and harvests saved in the system."}
            </p>
          </div>

          <div className="workspace-status">
            <span className="workspace-status-dot" />

            <span>
              {isVietnamese
                ? "Đọc trực tiếp từ Integration"
                : "Live Integration data"}
            </span>
          </div>
        </section>

        <section className="management-toolbar">
          <div className="logs-filter-tabs management-tabs">
            {RESOURCE_CONFIGS.map(
              (item) => (
                <button
                  key={item.key}
                  type="button"
                  className={
                    activeResource ===
                    item.key
                      ? "active"
                      : ""
                  }
                  onClick={() => {
                    setActiveResource(
                      item.key
                    );
                    setSearchTerm(
                      ""
                    );
                  }}
                >
                  <span aria-hidden="true">
                    {item.icon}
                  </span>
                  {" "}
                  {isVietnamese
                    ? item.labelVi
                    : item.labelEn}
                </button>
              )
            )}
          </div>

          <div className="management-actions">
            <label className="logs-search-wrapper">
              <span aria-hidden="true">
                🔍
              </span>

              <input
                type="search"
                value={searchTerm}
                onChange={(event) =>
                  setSearchTerm(
                    event.target.value
                  )
                }
                placeholder={
                  isVietnamese
                    ? "Tìm trong dữ liệu..."
                    : "Search records..."
                }
              />
            </label>

            <button
              type="button"
              className="management-refresh-btn"
              onClick={() =>
                loadRecords(
                  activeResource,
                  true
                )
              }
              disabled={isLoading}
            >
              {isLoading
                ? "⏳"
                : "↻"}
              {" "}
              {isVietnamese
                ? "Làm mới"
                : "Refresh"}
            </button>
          </div>
        </section>

        <section className="management-summary">
          <div>
            <span>
              {activeConfig.icon}
            </span>

            <div>
              <strong>
                {filteredRecords.length}
              </strong>

              <span>
                {isVietnamese
                  ? activeConfig.labelVi
                  : activeConfig.labelEn}
              </span>
            </div>
          </div>

          <p>
            {searchTerm.trim()
              ? isVietnamese
                ? `Hiển thị ${filteredRecords.length} / ${records.length} bản ghi phù hợp.`
                : `Showing ${filteredRecords.length} of ${records.length} matching records.`
              : isVietnamese
                ? `Có ${records.length} bản ghi đã lưu.`
                : `${records.length} saved records.`}
          </p>
        </section>

        {error && (
          <section className="management-state-card error">
            <strong>
              {isVietnamese
                ? "Không thể tải dữ liệu"
                : "Unable to load data"}
            </strong>

            <span>
              {error}
            </span>
          </section>
        )}

        {!error &&
          isLoading &&
          records.length ===
            0 && (
          <section className="management-state-card">
            <span className="management-state-icon">
              ⏳
            </span>

            <strong>
              {isVietnamese
                ? "Đang tải dữ liệu..."
                : "Loading data..."}
            </strong>
          </section>
        )}

        {!error &&
          !isLoading &&
          filteredRecords.length ===
            0 && (
          <section className="management-state-card">
            <span className="management-state-icon">
              📭
            </span>

            <strong>
              {searchTerm.trim()
                ? isVietnamese
                  ? "Không tìm thấy bản ghi phù hợp."
                  : "No matching records were found."
                : isVietnamese
                  ? "Chưa có dữ liệu cho mục này."
                  : "There is no data for this section yet."}
            </strong>
          </section>
        )}

        {!error &&
          filteredRecords.length >
            0 && (
          <section className="management-grid">
            {filteredRecords.map(
              (record) => {
                const title =
                  formatValue(
                    record?.[
                      activeConfig
                        .titleField
                    ],
                    language
                  );

                return (
                  <article
                    key={
                      record
                        ?.client_record_id ||
                      record?.id
                    }
                    className="management-card"
                  >
                    <div className="management-card-header">
                      <div>
                        <span className="management-card-icon">
                          {activeConfig.icon}
                        </span>

                        <div>
                          <h3>
                            {title}
                          </h3>

                          <code>
                            {record
                              ?.client_record_id ||
                              record?.id}
                          </code>
                        </div>
                      </div>

                      <span className="management-status-badge">
                        {record?.status ||
                          (
                            isVietnamese
                              ? "Đã lưu"
                              : "Saved"
                          )}
                      </span>
                    </div>

                    <dl className="management-field-grid">
                      {activeConfig.fields.map(
                        ([
                          key,
                          labelVi,
                          labelEn,
                        ]) => (
                          <div key={key}>
                            <dt>
                              {isVietnamese
                                ? labelVi
                                : labelEn}
                            </dt>

                            <dd>
                              {formatValue(
                                record?.[
                                  key
                                ],
                                language
                              )}
                            </dd>
                          </div>
                        )
                      )}
                    </dl>

                    <div className="management-card-footer">
                      <span>
                        {record?.confirmed
                          ? isVietnamese
                            ? "✓ Đã xác nhận"
                            : "✓ Confirmed"
                          : isVietnamese
                            ? "Chưa xác nhận"
                            : "Unconfirmed"}
                      </span>

                      <time>
                        {formatCreatedAt(
                          record
                            ?.created_at,
                          language
                        )}
                      </time>
                    </div>
                  </article>
                );
              }
            )}
          </section>
        )}
      </div>
    </main>
  );
}

export default Management;
