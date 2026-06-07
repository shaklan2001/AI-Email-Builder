import { describe, expect, it } from "vitest";
import { parseApiError } from "./parse-api-error";

describe("parseApiError", () => {
  it("returns API error message when present", async () => {
    const response = new Response(
      JSON.stringify({ error: { message: "Workflow not found" } }),
      { status: 404, statusText: "Not Found" },
    );

    await expect(parseApiError(response)).resolves.toBe("Workflow not found");
  });

  it("falls back to status text when body is not JSON", async () => {
    const response = new Response("not json", {
      status: 500,
      statusText: "Internal Server Error",
    });

    await expect(parseApiError(response)).resolves.toBe("500 Internal Server Error");
  });
});
