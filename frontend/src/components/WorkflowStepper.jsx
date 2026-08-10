const STEPS = [
  {
    id: 1,
    label: "Ghi âm",
  },
  {
    id: 2,
    label: "AI xử lý",
  },
  {
    id: 3,
    label: "Kiểm tra",
  },
  {
    id: 4,
    label: "Xác nhận",
  },
];

function WorkflowStepper({ currentStep = 1 }) {
  return (
    <nav
      className="workflow-stepper"
      aria-label="Tiến trình tạo nhật ký"
    >
      {STEPS.map((step, index) => {
        const isCompleted = step.id < currentStep;
        const isActive = step.id === currentStep;

        return (
          <div
            className="workflow-step-wrapper"
            key={step.id}
          >
            <div
              className={[
                "workflow-step",
                isCompleted ? "completed" : "",
                isActive ? "active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <div className="workflow-step-number">
                {isCompleted ? "✓" : step.id}
              </div>

              <span className="workflow-step-label">
                {step.label}
              </span>
            </div>

            {index < STEPS.length - 1 && (
              <div
                className={`workflow-step-line ${
                  isCompleted ? "completed" : ""
                }`}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}

export default WorkflowStepper;