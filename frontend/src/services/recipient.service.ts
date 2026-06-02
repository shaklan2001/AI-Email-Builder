import { apiClient } from "../api/client";
import type { Recipient, RecipientCounts } from "../types/recipient";

interface SuccessResponse<T> {
  success: true;
  data: T;
}

interface RecipientItemRaw {
  email: string;
}

interface RecipientListRaw {
  recipients?: RecipientItemRaw[];
  validCount?: number;
  valid_count?: number;
  invalidCount?: number;
  invalid_count?: number;
}

interface RecipientUploadRaw extends RecipientListRaw {
  validEmails?: string[];
  valid_emails?: string[];
  invalidRows?: Array<{ row: string; email: string; reason: string }>;
  invalid_rows?: Array<{ row: string; email: string; reason: string }>;
}

function createRecipientId(email: string): string {
  return `rec-${email.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}

function mapRecipients(raw: RecipientItemRaw[]): Recipient[] {
  return raw.map((item) => ({
    id: createRecipientId(item.email),
    email: item.email,
  }));
}

function mapCounts(raw: RecipientListRaw): RecipientCounts {
  return {
    validCount: raw.validCount ?? raw.valid_count ?? 0,
    invalidCount: raw.invalidCount ?? raw.invalid_count ?? 0,
  };
}

export async function fetchWorkflowRecipients(workflowId: string): Promise<{
  recipients: Recipient[];
  counts: RecipientCounts;
}> {
  const response = await apiClient<SuccessResponse<RecipientListRaw>>(
    `/api/v1/workflows/${encodeURIComponent(workflowId)}/recipients`,
  );
  const data = response.data;
  const items = data.recipients ?? [];
  return {
    recipients: mapRecipients(items),
    counts: mapCounts(data),
  };
}

export async function saveWorkflowRecipients(
  workflowId: string,
  emails: string[],
): Promise<{
  recipients: Recipient[];
  counts: RecipientCounts;
  invalidCount: number;
}> {
  const response = await apiClient<SuccessResponse<RecipientUploadRaw>>(
    `/api/v1/workflows/${encodeURIComponent(workflowId)}/recipients`,
    {
      method: "POST",
      body: JSON.stringify({ emails }),
    },
  );
  const data = response.data;
  const items = data.recipients ?? [];
  const validEmails = data.validEmails ?? data.valid_emails ?? [];
  const recipients =
    items.length > 0
      ? mapRecipients(items)
      : validEmails.map((email) => ({
          id: createRecipientId(email),
          email,
        }));

  return {
    recipients,
    counts: mapCounts(data),
    invalidCount: data.invalidCount ?? data.invalid_count ?? 0,
  };
}
