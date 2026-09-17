export const DYNAMIC_FORM_TEMPLATES = {
  CREATE_CROP_TYPE: {
    templateId: "crop_type",
    fields: [
      {
        name: "crop_name",
        type: "text",
        required: true,
      },
      {
        name: "crop_group_text",
        type: "text",
        required: true,
      },
      {
        name: "crop_code_suggestion",
        type: "text",
        required: true,
      },
      {
        name: "days_to_harvest",
        type: "number",
        required: false,
      },
    ],
  },

  CREATE_SEASON: {
    templateId: "season",
    fields: [
      {
        name: "plot_text",
        type: "text",
        required: true,
      },
      {
        name: "crop_text",
        type: "text",
        required: true,
      },
      {
        name: "planting_date_text",
        type: "text",
        required: true,
      },
      {
        name: "season_name",
        type: "text",
        required: true,
      },
      {
        name: "expected_harvest_date_text",
        type: "text",
        required: false,
      },
      {
        name: "plant_count",
        type: "number",
        required: false,
      },
      {
        name: "expected_yield",
        type: "number",
        required: false,
      },
      {
        name: "expected_yield_unit_text",
        type: "text",
        required: false,
      },
      {
        name: "process_template_text",
        type: "text",
        required: false,
      },
    ],
  },

  CREATE_PLOT: {
    templateId: "plot",
    fields: [
      {
        name: "plot_name_or_code",
        type: "text",
        required: true,
      },
      {
        name: "region_text",
        type: "text",
        required: true,
      },
      {
        name: "boundary_required",
        type: "boolean",
        required: true,
      },
      {
        name: "owner_text",
        type: "text",
        required: false,
      },
      {
        name: "current_crop_text",
        type: "text",
        required: false,
      },
      {
        name: "location_hint_text",
        type: "text",
        required: false,
      },
    ],
  },

  CREATE_TASK: {
    templateId: "task",
    fields: [
      {
        name: "season_text",
        type: "text",
        required: true,
      },
      {
        name: "task_name",
        type: "text",
        required: true,
      },
      {
        name: "task_type_text",
        type: "text",
        required: true,
      },
      {
        name: "due_time_text",
        type: "text",
        required: true,
      },
      {
        name: "assignee_text",
        type: "text",
        required: false,
      },
      {
        name: "photo_required",
        type: "boolean",
        required: false,
      },
      {
        name: "note",
        type: "textarea",
        required: false,
      },
    ],
  },

  CREATE_WORK_LOG: {
    templateId: "work_log",
    fields: [
      {
        name: "plot_text",
        type: "text",
        required: false,
      },
      {
        name: "activity_text",
        type: "text",
        required: false,
      },
      {
        name: "performed_time_text",
        type: "text",
        required: false,
      },
      {
        name: "materials",
        type: "materials",
        required: false,
      },
      {
        name: "result_status",
        type: "select",
        required: true,
        options: [
          "completed",
          "partial",
          "failed",
        ],
      },
      {
        name: "photo_required",
        type: "boolean",
        required: false,
      },
      {
        name: "material_batch_text",
        type: "text",
        required: false,
      },
      {
        name: "note",
        type: "textarea",
        required: false,
      },
    ],
  },

  CREATE_ISSUE_REPORT: {
    templateId: "issue_report",
    fields: [
      {
        name: "plot_text",
        type: "text",
        required: true,
      },
      {
        name: "issue_type_text",
        type: "text",
        required: true,
      },
      {
        name: "severity_text",
        type: "text",
        required: true,
      },
      {
        name: "description",
        type: "textarea",
        required: true,
      },
      {
        name: "photo_required",
        type: "boolean",
        required: false,
      },
      {
        name: "note",
        type: "textarea",
        required: false,
      },
    ],
  },

  CREATE_HARVEST: {
    templateId: "harvest",
    fields: [
      {
        name: "plot_text",
        type: "text",
        required: true,
      },
      {
        name: "crop_text",
        type: "text",
        required: true,
      },
      {
        name: "quantity",
        type: "number",
        required: true,
      },
      {
        name: "unit_text",
        type: "text",
        required: true,
      },
      {
        name: "harvest_date_text",
        type: "text",
        required: true,
      },
      {
        name: "photo_required",
        type: "boolean",
        required: false,
      },
      {
        name: "note",
        type: "textarea",
        required: false,
      },
    ],
  },
};

export function getDynamicFormTemplate(
  operation
) {
  return (
    DYNAMIC_FORM_TEMPLATES[
      operation
    ] ?? null
  );
}
export const DYNAMIC_FORM_FIELD_TEXT = {
  crop_name: {
    vi: "Tên cây trồng",
    en: "Crop name",
  },
  crop_group_text: {
    vi: "Nhóm cây trồng",
    en: "Crop group",
  },
  crop_code_suggestion: {
    vi: "Mã cây trồng đề xuất",
    en: "Suggested crop code",
  },
  days_to_harvest: {
    vi: "Số ngày đến thu hoạch",
    en: "Days to harvest",
  },

  plot_text: {
    vi: "Lô canh tác",
    en: "Farm plot",
  },
  crop_text: {
    vi: "Cây trồng",
    en: "Crop",
  },
  planting_date_text: {
    vi: "Ngày trồng",
    en: "Planting date",
  },
  season_name: {
    vi: "Tên mùa vụ",
    en: "Season name",
  },
  expected_harvest_date_text: {
    vi: "Ngày thu hoạch dự kiến",
    en: "Expected harvest date",
  },
  plant_count: {
    vi: "Số lượng cây",
    en: "Plant count",
  },
  expected_yield: {
    vi: "Sản lượng dự kiến",
    en: "Expected yield",
  },
  expected_yield_unit_text: {
    vi: "Đơn vị sản lượng dự kiến",
    en: "Expected yield unit",
  },
  process_template_text: {
    vi: "Quy trình canh tác",
    en: "Process template",
  },

  plot_name_or_code: {
    vi: "Tên hoặc mã lô",
    en: "Plot name or code",
  },
  region_text: {
    vi: "Khu vực",
    en: "Region",
  },
  boundary_required: {
    vi: "Yêu cầu ranh giới",
    en: "Boundary required",
  },
  owner_text: {
    vi: "Chủ sở hữu",
    en: "Owner",
  },
  current_crop_text: {
    vi: "Cây trồng hiện tại",
    en: "Current crop",
  },
  location_hint_text: {
    vi: "Gợi ý vị trí",
    en: "Location hint",
  },

  season_text: {
    vi: "Mùa vụ",
    en: "Season",
  },
  task_name: {
    vi: "Tên công việc",
    en: "Task name",
  },
  task_type_text: {
    vi: "Loại công việc",
    en: "Task type",
  },
  due_time_text: {
    vi: "Thời hạn",
    en: "Due time",
  },
  assignee_text: {
    vi: "Người thực hiện",
    en: "Assignee",
  },

  activity_text: {
    vi: "Hoạt động",
    en: "Activity",
  },
  performed_time_text: {
    vi: "Thời gian thực hiện",
    en: "Performed time",
  },
  materials: {
    vi: "Vật tư sử dụng",
    en: "Materials",
  },
  material_text: {
    vi: "Vật tư",
    en: "Material",
  },
  quantity: {
    vi: "Số lượng",
    en: "Quantity",
  },
  unit_text: {
    vi: "Đơn vị",
    en: "Unit",
  },
  result_status: {
    vi: "Kết quả thực hiện",
    en: "Result status",
  },
  photo_required: {
    vi: "Yêu cầu ảnh",
    en: "Photo required",
  },
  material_batch_text: {
    vi: "Lô vật tư",
    en: "Material batch",
  },

  issue_type_text: {
    vi: "Loại sự cố",
    en: "Issue type",
  },
  severity_text: {
    vi: "Mức độ nghiêm trọng",
    en: "Severity",
  },
  description: {
    vi: "Mô tả",
    en: "Description",
  },

  harvest_date_text: {
    vi: "Ngày thu hoạch",
    en: "Harvest date",
  },

  note: {
    vi: "Ghi chú",
    en: "Note",
  },
};

export const DYNAMIC_FORM_OPTION_TEXT = {
  result_status: {
    completed: {
      vi: "Hoàn thành",
      en: "Completed",
    },
    partial: {
      vi: "Hoàn thành một phần",
      en: "Partially completed",
    },
    failed: {
      vi: "Không hoàn thành",
      en: "Failed",
    },
  },
};

export function getDynamicFormOptionText(
  fieldName,
  value,
  language = "vi"
) {
  const optionText =
    DYNAMIC_FORM_OPTION_TEXT[fieldName]?.[
      value
    ];

  if (!optionText) {
    return value;
  }

  return (
    optionText[language] ??
    optionText.vi ??
    value
  );
}
export function getDynamicFormFieldText(
  fieldName,
  language = "vi"
) {
  const fieldText =
    DYNAMIC_FORM_FIELD_TEXT[fieldName];

  if (!fieldText) {
    return fieldName;
  }

  return (
    fieldText[language] ??
    fieldText.vi ??
    fieldName
  );
}