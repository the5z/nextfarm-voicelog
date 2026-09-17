export const DEFAULT_OPERATION = "CREATE_WORK_LOG";

export const DYNAMIC_FORM_OPERATIONS = [
  {
    operation: "CREATE_CROP_TYPE",
    templateId: "crop_type",
    labelVi: "Tạo loại cây trồng",
    labelEn: "Create crop type",
    descriptionVi:
      "Khai báo loại cây trồng mới.",
    descriptionEn:
      "Create a new crop type.",
  },
  {
    operation: "CREATE_SEASON",
    templateId: "season",
    labelVi: "Tạo mùa vụ",
    labelEn: "Create season",
    descriptionVi:
      "Khai báo mùa vụ cho lô canh tác.",
    descriptionEn:
      "Create a season for a farming plot.",
  },
  {
    operation: "CREATE_PLOT",
    templateId: "plot",
    labelVi: "Tạo lô canh tác",
    labelEn: "Create plot",
    descriptionVi:
      "Khai báo lô canh tác và thông tin khu vực.",
    descriptionEn:
      "Create a farming plot and region information.",
  },
  {
    operation: "CREATE_TASK",
    templateId: "task",
    labelVi: "Tạo công việc",
    labelEn: "Create task",
    descriptionVi:
      "Tạo công việc cần thực hiện trong mùa vụ.",
    descriptionEn:
      "Create a task for a farming season.",
  },
  {
    operation: "CREATE_WORK_LOG",
    templateId: "work_log",
    labelVi: "Ghi nhật ký công việc",
    labelEn: "Create work log",
    descriptionVi:
      "Ghi lại công việc canh tác đã thực hiện.",
    descriptionEn:
      "Record completed farming work.",
  },
  {
    operation: "CREATE_ISSUE_REPORT",
    templateId: "issue_report",
    labelVi: "Báo cáo sự cố",
    labelEn: "Report issue",
    descriptionVi:
      "Ghi nhận vấn đề hoặc sự cố trên lô canh tác.",
    descriptionEn:
      "Report an issue on a farming plot.",
  },
  {
    operation: "CREATE_HARVEST",
    templateId: "harvest",
    labelVi: "Ghi nhận thu hoạch",
    labelEn: "Record harvest",
    descriptionVi:
      "Ghi nhận sản lượng và thời điểm thu hoạch.",
    descriptionEn:
      "Record harvest quantity and date.",
  },
];

export function getDynamicFormOperation(
  operation
) {
  return (
    DYNAMIC_FORM_OPERATIONS.find(
      (item) =>
        item.operation === operation
    ) ?? null
  );
}
