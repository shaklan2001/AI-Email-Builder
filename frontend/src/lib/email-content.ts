import type {
  EmailBodyVersion,
  GeneratedEmail,
  WorkflowDefinition,
} from "../types/workflow-definition";

export function getFinalEmailContent(email: GeneratedEmail): EmailBodyVersion {
  return email.finalUserVersion;
}

type RawGeneratedEmail = {
  subject?: string;
  htmlContent?: string;
  html_content?: string;
  plainTextContent?: string;
  plain_text_content?: string;
  aiGeneratedVersion?: EmailBodyVersion;
  ai_generated_version?: EmailBodyVersion & { html_content?: string; plain_text_content?: string };
  finalUserVersion?: EmailBodyVersion;
  final_user_version?: EmailBodyVersion & { html_content?: string; plain_text_content?: string };
  userEdited?: boolean;
  user_edited?: boolean;
};

export function normalizeGeneratedEmail(raw: GeneratedEmail | RawGeneratedEmail): GeneratedEmail {
  if ("aiGeneratedVersion" in raw && "finalUserVersion" in raw && !("subject" in raw)) {
    return raw as GeneratedEmail;
  }

  const legacy = raw as RawGeneratedEmail;
  const htmlContent = legacy.htmlContent ?? legacy.html_content ?? "";
  const plainTextContent = legacy.plainTextContent ?? legacy.plain_text_content ?? "";
  const aiRaw = legacy.aiGeneratedVersion ?? legacy.ai_generated_version;
  const finalRaw = legacy.finalUserVersion ?? legacy.final_user_version;

  const fallback: EmailBodyVersion = {
    subject: legacy.subject ?? "",
    htmlContent,
    plainTextContent,
  };

  const aiGeneratedVersion: EmailBodyVersion = aiRaw
    ? {
        subject: aiRaw.subject,
        htmlContent: aiRaw.htmlContent ?? (aiRaw as { html_content?: string }).html_content ?? "",
        plainTextContent:
          aiRaw.plainTextContent ??
          (aiRaw as { plain_text_content?: string }).plain_text_content ??
          "",
      }
    : fallback;

  const finalUserVersion: EmailBodyVersion = finalRaw
    ? {
        subject: finalRaw.subject,
        htmlContent:
          finalRaw.htmlContent ?? (finalRaw as { html_content?: string }).html_content ?? "",
        plainTextContent:
          finalRaw.plainTextContent ??
          (finalRaw as { plain_text_content?: string }).plain_text_content ??
          "",
      }
    : fallback;

  return {
    aiGeneratedVersion,
    finalUserVersion,
    userEdited: legacy.userEdited ?? legacy.user_edited ?? false,
  };
}

export function updateWorkflowStepEmail(
  workflow: WorkflowDefinition,
  stepId: string,
  finalContent: EmailBodyVersion,
): WorkflowDefinition {
  return {
    ...workflow,
    steps: workflow.steps.map((step) => {
      if (step.id !== stepId || step.type !== "send_email" || !step.email) {
        return step;
      }
      return {
        ...step,
        email: {
          ...step.email,
          finalUserVersion: finalContent,
          userEdited: true,
        },
      };
    }),
  };
}
