function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Converts plain text paragraphs into simple HTML for email delivery. */
export function plainTextToHtml(plainText: string): string {
  const trimmed = plainText.trim();
  if (!trimmed) {
    return "";
  }

  const paragraphs = trimmed.split(/\n{2,}/);
  return paragraphs
    .map((paragraph) => {
      const lines = paragraph
        .split("\n")
        .map((line) => escapeHtml(line))
        .join("<br>");
      return `<p>${lines}</p>`;
    })
    .join("\n");
}
