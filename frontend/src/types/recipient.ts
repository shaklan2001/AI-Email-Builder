export type InvalidRecipientReason = "missing_email" | "invalid_format";

export interface Recipient {
  id: string;
  email: string;
}

export interface InvalidRecipient {
  email: string;
  reason: InvalidRecipientReason;
}

export interface RecipientValidationResult {
  valid: Recipient[];
  invalid: InvalidRecipient[];
}

export interface RecipientCounts {
  validCount: number;
  invalidCount: number;
}
