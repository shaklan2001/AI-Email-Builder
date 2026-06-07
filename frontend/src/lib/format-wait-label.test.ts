import { describe, expect, it } from "vitest";

import { formatWaitLabel, waitLabelForStep } from "./format-wait-label";
import type { WorkflowStep } from "../types/workflow-definition";

describe("formatWaitLabel", () => {
  it("formats minute delays", () => {
    expect(formatWaitLabel({ value: 2, unit: "minutes" })).toBe("Wait 2 Minutes");
    expect(formatWaitLabel({ value: 1, unit: "minutes" })).toBe("Wait 1 Minute");
  });
});

describe("waitLabelForStep", () => {
  it("uses step value and unit for minute waits instead of legacy days", () => {
    const step: WorkflowStep = {
      id: "step_2",
      type: "wait",
      value: 2,
      unit: "minutes",
      days: 1,
    };

    expect(waitLabelForStep(step)).toBe("Wait 2 Minutes");
  });
});
