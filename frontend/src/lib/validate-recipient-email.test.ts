import { describe, expect, it } from "vitest";
import {
  parseRecipientCsv,
  validateRecipientEmail,
  validateRecipientEmails,
} from "./validate-recipient-email";

describe("validateRecipientEmail", () => {
  it("accepts valid emails", () => {
    expect(validateRecipientEmail("user@example.com")).toBeNull();
  });

  it("rejects empty values", () => {
    expect(validateRecipientEmail("  ")).toBe("missing_email");
  });

  it("rejects invalid format", () => {
    expect(validateRecipientEmail("not-an-email")).toBe("invalid_format");
  });
});

describe("validateRecipientEmails", () => {
  it("splits valid and invalid recipients", () => {
    const result = validateRecipientEmails(["good@example.com", "bad"]);

    expect(result.valid).toHaveLength(1);
    expect(result.valid[0]?.email).toBe("good@example.com");
    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0]?.reason).toBe("invalid_format");
  });
});

describe("parseRecipientCsv", () => {
  it("reads email column from header row", () => {
    const emails = parseRecipientCsv("email,name\none@example.com,One");

    expect(emails).toEqual(["one@example.com"]);
  });

  it("reads first column when no header", () => {
    const emails = parseRecipientCsv("two@example.com,Two");

    expect(emails).toEqual(["two@example.com"]);
  });
});
