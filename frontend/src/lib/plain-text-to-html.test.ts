import { describe, expect, it } from "vitest";
import { plainTextToHtml } from "./plain-text-to-html";

describe("plainTextToHtml", () => {
  it("wraps paragraphs in p tags", () => {
    expect(plainTextToHtml("Hello\n\nWorld")).toBe("<p>Hello</p>\n<p>World</p>");
  });

  it("converts single line breaks to br", () => {
    expect(plainTextToHtml("Line one\nLine two")).toBe("<p>Line one<br>Line two</p>");
  });

  it("escapes HTML characters", () => {
    expect(plainTextToHtml("<script>")).toBe("<p>&lt;script&gt;</p>");
  });

  it("returns empty string for blank input", () => {
    expect(plainTextToHtml("   ")).toBe("");
  });
});
