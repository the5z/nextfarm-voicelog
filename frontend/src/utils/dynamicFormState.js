import {
  getDynamicFormTemplate,
} from "../constants/dynamicFormTemplates";

export function createEmptyDynamicForm(
  operation
) {
  const template =
    getDynamicFormTemplate(operation);

  if (!template) {
    return null;
  }

  const fields = {};

  template.fields.forEach((field) => {
    if (field.type === "materials") {
      fields[field.name] = [];
      return;
    }

    fields[field.name] = null;
  });

  return {
    contract_version: "3.1",
    operation,
    template_id: template.templateId,
    fields,
    missing_fields: template.fields
      .filter((field) => field.required)
      .map((field) => field.name),
    warnings: [],
    field_confidence: {},
    requires_confirmation: false,
    next_question: null,
  };
}

export function updateDynamicFormFields(
  dynamicForm,
  nextFields
) {
  if (!dynamicForm) {
    return dynamicForm;
  }

  return {
    ...dynamicForm,
    fields: {
      ...dynamicForm.fields,
      ...nextFields,
    },
  };
}