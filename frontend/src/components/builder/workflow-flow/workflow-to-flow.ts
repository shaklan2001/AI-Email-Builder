import type { Edge, Node } from "@xyflow/react";
import { MarkerType } from "@xyflow/react";
import { waitLabelForStep } from "../../../lib/format-wait-label";
import type {
  WorkflowDefinition,
  WorkflowStep,
} from "../../../types/workflow-definition";
import type {
  AiReplyAgentNodeData,
  ConditionNodeData,
  EmailNodeData,
  WaitNodeData,
  WorkflowFlowNodeType,
} from "./types";

const WIDE_NODE_WIDTH = 320;
const NARROW_NODE_WIDTH = 200;
const CANVAS_CENTER_X = 400;
const BRANCH_SPREAD = 220;
const VERTICAL_GAP = 56;

const NODE_HEIGHT = {
  email: 168,
  wait: 52,
  condition: 52,
  aiAgent: 300,
} as const;

function wideCenterX(): number {
  return CANVAS_CENTER_X - WIDE_NODE_WIDTH / 2;
}

function narrowCenterX(): number {
  return CANVAS_CENTER_X - NARROW_NODE_WIDTH / 2;
}

function leftBranchX(): number {
  return CANVAS_CENTER_X - BRANCH_SPREAD - WIDE_NODE_WIDTH / 2;
}

function rightBranchX(): number {
  return CANVAS_CENTER_X + BRANCH_SPREAD - WIDE_NODE_WIDTH / 2;
}

function stepHeight(step: WorkflowStep): number {
  if (step.type === "send_email") {
    return NODE_HEIGHT.email;
  }
  if (step.type === "wait") {
    return NODE_HEIGHT.wait;
  }
  if (
    step.type === "reply_condition" ||
    (step.type === "condition" && step.condition === "reply_received")
  ) {
    return NODE_HEIGHT.condition;
  }
  if (step.type === "interested_branch") {
    return NODE_HEIGHT.aiAgent;
  }
  return NODE_HEIGHT.wait;
}

function isReplyReceivedCondition(step: WorkflowStep | undefined): boolean {
  return (
    step?.type === "reply_condition" ||
    (step?.type === "condition" && step.condition === "reply_received")
  );
}

function formatConditionLabel(condition: string): string {
  if (condition === "reply_received") {
    return "Reply?";
  }
  const words = condition.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1) + "?";
}

function getStepLabel(
  step: WorkflowStep,
  followUpDelay?: WorkflowDefinition["followUpDelay"],
): string {
  if (step.type === "send_email") {
    return step.name ?? "Send Email";
  }
  if (step.type === "wait") {
    return waitLabelForStep(step, followUpDelay);
  }
  if (step.type === "reply_condition") {
    return "Reply?";
  }
  if (step.type === "interested_branch") {
    return step.name ?? "AI Reply Agent";
  }
  if (step.type === "no_reply_branch") {
    return "No Reply";
  }
  if (step.type === "condition" && step.condition) {
    return formatConditionLabel(step.condition);
  }
  if (step.type === "end") {
    return "End";
  }
  return step.name ?? step.type;
}

function findConditionIndex(steps: WorkflowStep[]): number {
  return steps.findIndex(
    (s) =>
      s.type === "reply_condition" ||
      (s.type === "condition" && s.condition === "reply_received"),
  );
}

function defaultEdge(
  source: string,
  target: string,
  options?: {
    sourceHandle?: string;
    label?: string;
    labelColor?: string;
  },
): Edge {
  return {
    id: `${source}-${target}${options?.sourceHandle ? `-${options.sourceHandle}` : ""}`,
    source,
    target,
    sourceHandle: options?.sourceHandle,
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
    style: { stroke: "#919EAB", strokeWidth: 1.5 },
    label: options?.label,
    labelStyle: options?.label
      ? {
          fill: options.labelColor ?? "#637381",
          fontWeight: 600,
          fontSize: 12,
        }
      : undefined,
    labelBgStyle: { fill: "transparent" },
    labelBgPadding: [4, 0] as [number, number],
    labelBgBorderRadius: 0,
  };
}

function isConditionalWorkflow(
  definition: WorkflowDefinition,
  steps: WorkflowStep[],
): boolean {
  return (
    definition.workflowType === "conditional" ||
    definition.workflowType === "multi_level_conditional" ||
    steps.some(
      (s) =>
        s.type === "condition" ||
        s.type === "reply_condition" ||
        s.type === "interested_branch",
    )
  );
}

function buildLinearFlow(
  steps: WorkflowStep[],
  followUpDelay?: WorkflowDefinition["followUpDelay"],
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  let y = 0;
  let previousId: string | null = null;

  for (const step of steps) {
    if (step.type === "end") {
      continue;
    }

    const node = stepToNode(step, { x: nodeCenterX(step), y }, followUpDelay);
    nodes.push(node);

    if (previousId) {
      edges.push(defaultEdge(previousId, step.id));
    }

    previousId = step.id;
    y += stepHeight(step) + VERTICAL_GAP;
  }

  return { nodes, edges };
}

function nodeCenterX(step: WorkflowStep): number {
  if (step.type === "send_email" || step.type === "interested_branch") {
    return wideCenterX();
  }
  return narrowCenterX();
}

function stepToNode(
  step: WorkflowStep,
  position: { x: number; y: number },
  followUpDelay?: WorkflowDefinition["followUpDelay"],
  variant: "default" | "branch" = "default",
): Node {
  if (step.type === "send_email" && step.email) {
    return {
      id: step.id,
      type: "emailNode" satisfies WorkflowFlowNodeType,
      position,
      data: {
        label: getStepLabel(step, followUpDelay),
        email: step.email,
        variant,
      } satisfies EmailNodeData,
      draggable: false,
      selectable: false,
    };
  }

  if (step.type === "wait") {
    return {
      id: step.id,
      type: "waitNode" satisfies WorkflowFlowNodeType,
      position,
      data: {
        label: getStepLabel(step, followUpDelay),
      } satisfies WaitNodeData,
      draggable: false,
      selectable: false,
    };
  }

  if (
    step.type === "reply_condition" ||
    (step.type === "condition" && step.condition)
  ) {
    return {
      id: step.id,
      type: "conditionNode" satisfies WorkflowFlowNodeType,
      position,
      data: {
        label: getStepLabel(step, followUpDelay),
      } satisfies ConditionNodeData,
      draggable: false,
      selectable: false,
    };
  }

  if (step.type === "interested_branch") {
    return {
      id: step.id,
      type: "aiReplyAgentNode" satisfies WorkflowFlowNodeType,
      position,
      data: {} satisfies AiReplyAgentNodeData,
      draggable: false,
      selectable: false,
    };
  }

  return {
    id: step.id,
    type: "waitNode" satisfies WorkflowFlowNodeType,
    position,
    data: {
      label: getStepLabel(step, followUpDelay),
    } satisfies WaitNodeData,
    draggable: false,
    selectable: false,
  };
}

function buildConditionalFlow(
  steps: WorkflowStep[],
  followUpDelay: WorkflowDefinition["followUpDelay"],
  campaignId?: string,
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const conditionIndex = findConditionIndex(steps);
  const beforeCondition =
    conditionIndex >= 0 ? steps.slice(0, conditionIndex) : steps;
  const conditionStep =
    conditionIndex >= 0 ? steps[conditionIndex] : undefined;
  const afterCondition =
    conditionIndex >= 0 ? steps.slice(conditionIndex + 1) : [];

  const usesGenerationBranches = afterCondition.some(
    (s) => s.type === "interested_branch" || s.type === "no_reply_branch",
  );

  const yesSteps = usesGenerationBranches
    ? afterCondition.filter((s) => s.type === "interested_branch")
    : afterCondition.filter((s) => s.branch === "yes");
  const noSteps = usesGenerationBranches
    ? afterCondition.filter((s) => s.type === "send_email")
    : afterCondition.filter((s) => s.branch === "no");
  const unbranched = usesGenerationBranches
    ? []
    : afterCondition.filter((s) => !s.branch);

  const replyBranch = isReplyReceivedCondition(conditionStep);

  const yesBranchSteps =
    yesSteps.length > 0
      ? yesSteps
      : unbranched.length > 0
        ? [unbranched[0]]
        : [];
  const noBranchSteps =
    noSteps.length > 0
      ? noSteps
      : unbranched.length > 1
        ? [unbranched[1]]
        : unbranched.length === 1
          ? []
          : unbranched;

  let y = 0;
  let previousId: string | null = null;

  for (const step of beforeCondition) {
    if (step.type === "end") {
      continue;
    }
    nodes.push(stepToNode(step, { x: nodeCenterX(step), y }, followUpDelay));
    if (previousId) {
      edges.push(defaultEdge(previousId, step.id));
    }
    previousId = step.id;
    y += stepHeight(step) + VERTICAL_GAP;
  }

  if (!conditionStep) {
    return { nodes, edges };
  }

  nodes.push(
    stepToNode(conditionStep, { x: nodeCenterX(conditionStep), y }, followUpDelay),
  );
  if (previousId) {
    edges.push(defaultEdge(previousId, conditionStep.id));
  }

  const branchY = y + stepHeight(conditionStep) + VERTICAL_GAP;
  const conditionId = conditionStep.id;

  if (replyBranch || yesBranchSteps.length > 0) {
    if (replyBranch) {
      const aiNodeId = `${conditionId}-ai-reply`;
      nodes.push({
        id: aiNodeId,
        type: "aiReplyAgentNode",
        position: { x: leftBranchX(), y: branchY },
        data: { campaignId } satisfies AiReplyAgentNodeData,
        draggable: false,
        selectable: false,
      });
      edges.push(
        defaultEdge(conditionId, aiNodeId, {
          sourceHandle: "yes",
          label: "Yes",
          labelColor: "#22C55E",
        }),
      );
    } else {
      let yesY = branchY;
      let yesPrev: string | null = null;
      for (const step of yesBranchSteps) {
        nodes.push(
          stepToNode(step, { x: leftBranchX(), y: yesY }, followUpDelay, "branch"),
        );
        if (yesPrev) {
          edges.push(defaultEdge(yesPrev, step.id));
        } else {
          edges.push(
            defaultEdge(conditionId, step.id, {
              sourceHandle: "yes",
              label: "Yes",
              labelColor: "#22C55E",
            }),
          );
        }
        yesPrev = step.id;
        yesY += stepHeight(step) + VERTICAL_GAP;
      }
    }
  }

  if (noBranchSteps.length > 0) {
    let noY = branchY;
    let noPrev: string | null = null;
    for (const step of noBranchSteps) {
      nodes.push(
        stepToNode(step, { x: rightBranchX(), y: noY }, followUpDelay, "branch"),
      );
      if (noPrev) {
        edges.push(defaultEdge(noPrev, step.id));
      } else {
        edges.push(
          defaultEdge(conditionId, step.id, {
            sourceHandle: "no",
            label: "No",
            labelColor: "#919EAB",
          }),
        );
      }
      noPrev = step.id;
      noY += stepHeight(step) + VERTICAL_GAP;
    }
  }

  return { nodes, edges };
}

export function workflowToFlow(
  definition: WorkflowDefinition | null,
  campaignId?: string,
): { nodes: Node[]; edges: Edge[] } {
  const steps = definition?.steps ?? [];
  if (!steps.length) {
    return { nodes: [], edges: [] };
  }

  const followUpDelay = definition?.followUpDelay;

  if (isConditionalWorkflow(definition ?? { steps }, steps)) {
    return buildConditionalFlow(steps, followUpDelay, campaignId);
  }

  return buildLinearFlow(steps, followUpDelay);
}
