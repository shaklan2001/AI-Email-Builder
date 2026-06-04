import type {
  InvalidRecipient,
  InvalidRecipientReason,
  Recipient,
  RecipientValidationResult,
} from "../types/recipient";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateRecipientEmail(raw: string): InvalidRecipientReason | null {
  const email = raw.trim();

  if (!email) {
    return "missing_email";
  }

  if (!EMAIL_REGEX.test(email)) {
    return "invalid_format";
  }

  return null;
}

function createRecipientId(): string {
  return `rec-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function validateRecipientEmails(rawEmails: string[]): RecipientValidationResult {
  const valid: Recipient[] = [];
  const invalid: InvalidRecipient[] = [];

  for (const raw of rawEmails) {
    const reason = validateRecipientEmail(raw);

    if (reason) {
      invalid.push({ email: raw.trim(), reason });
      continue;
    }

    valid.push({
      id: createRecipientId(),
      email: raw.trim(),
    });
  }

  return { valid, invalid };
}

function parseCsvLine(line: string): string[] {
  return line.split(",").map((cell) => cell.trim().replace(/^"|"$/g, ""));
}

export function parseRecipientCsv(content: string): string[] {
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return [];
  }

  const firstRow = parseCsvLine(lines[0]);
  const emailIndex = firstRow.findIndex((cell) => cell.toLowerCase() === "email");
  const hasHeader = emailIndex >= 0;
  const startIndex = hasHeader ? 1 : 0;
  const columnIndex = hasHeader ? emailIndex : 0;

  const emails: string[] = [];

  for (let i = startIndex; i < lines.length; i += 1) {
    const cells = parseCsvLine(lines[i]);
    emails.push(cells[columnIndex] ?? "");
  }

  return emails;
}
