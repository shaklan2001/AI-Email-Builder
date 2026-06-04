import type { ChatMessage } from "../components/chat/types";
import {
  defaultWorkflowState,
  type WorkflowState,
} from "../types/workflow-state";

const FOLLOW_UP_STEP = "Follow Up Email";
const DISCOUNT_STEP = "Discount Email";

function parseWaitDays(text: string): number | null {
  const match = text.match(/wait\s+(\d+)\s+days?/i);
  if (!match) {
    return null;
  }
  const days = Number.parseInt(match[1], 10);
  return Number.isNaN(days) ? null : days;
}

function applyUserMessage(state: WorkflowState, content: string): WorkflowState {
  const text = content.toLowerCase();
  let next = state;

  const waitDays = parseWaitDays(content);
  if (waitDays !== null) {
    const dayWord = waitDays === 1 ? "Day" : "Days";
    next = {
      ...next,
      waitLabel: `Wait ${waitDays} ${dayWord}`,
    };
  }

  if (text.includes("follow up") && !next.extraSteps.includes(FOLLOW_UP_STEP)) {
    next = {
      ...next,
      extraSteps: [...next.extraSteps, FOLLOW_UP_STEP],
    };
  }

  if (text.includes("discount") && !next.extraSteps.includes(DISCOUNT_STEP)) {
    next = {
      ...next,
      extraSteps: [...next.extraSteps, DISCOUNT_STEP],
    };
  }

  return next;
}

export function deriveWorkflowFromChat(messages: ChatMessage[]): WorkflowState {
  const userMessages = messages.filter(
    (m) => m.role === "user" && m.content.trim().length > 0,
  );

  return userMessages.reduce(
    (state, message) => applyUserMessage(state, message.content),
    defaultWorkflowState,
  );
}
