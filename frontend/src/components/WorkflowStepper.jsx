function WorkflowStepper({
  currentStep = 1,
  text,
}) {
  const steps = [
    {
      id: 1,
      label: text.workflow.record,
    },
    {
      id: 2,
      label: text.workflow.processing,
    },
    {
      id: 3,
      label: text.workflow.review,
    },
    {
      id: 4,
      label: text.workflow.confirm,
    },
  ];

  return (
    <nav
      className="workflow-stepper"
      aria-label="Voice log workflow"
    >
      {steps.map((step, index) => {
        const isCompleted =
          step.id < currentStep;

        const isActive =
          step.id === currentStep;

        return (
          <div
            className="workflow-step-wrapper"
            key={step.id}
          >
            <div
              className={[
                "workflow-step",
                isCompleted
                  ? "completed"
                  : "",
                isActive
                  ? "active"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <div className="workflow-step-number">
                {isCompleted
                  ? "✓"
                  : step.id}
              </div>

              <span className="workflow-step-label">
                {step.label}
              </span>
            </div>

            {index < steps.length - 1 && (
              <div
                className={`workflow-step-line ${
                  isCompleted
                    ? "completed"
                    : ""
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