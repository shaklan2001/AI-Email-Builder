import Box from "@mui/material/Box";
import {
  Background,
  BackgroundVariant,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useEffect, useMemo } from "react";
import type { WorkflowDefinition } from "../../../types/workflow-definition";
import { AiReplyAgentNode } from "./nodes/ai-reply-agent-node";
import { ConditionNode } from "./nodes/condition-node";
import { EmailNode } from "./nodes/email-node";
import { WaitNode } from "./nodes/wait-node";
import { workflowToFlow } from "./workflow-to-flow";
import "./workflow-flow.css";

const nodeTypes = {
  emailNode: EmailNode,
  waitNode: WaitNode,
  conditionNode: ConditionNode,
  aiReplyAgentNode: AiReplyAgentNode,
};

interface WorkflowFlowCanvasProps {
  workflowDefinition: WorkflowDefinition;
  campaignId?: string;
}

function FitViewOnChange({ nodes }: { nodes: Node[] }) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (!nodes.length) {
      return;
    }
    const frame = requestAnimationFrame(() => {
      void fitView({ padding: 0.2, maxZoom: 1, minZoom: 0.5 });
    });
    return () => cancelAnimationFrame(frame);
  }, [nodes, fitView]);

  return null;
}

function WorkflowFlowInner({
  workflowDefinition,
  campaignId,
}: WorkflowFlowCanvasProps) {
  const { nodes, edges } = useMemo(
    () => workflowToFlow(workflowDefinition, campaignId),
    [workflowDefinition, campaignId],
  );

  return (
    <Box
      className="workflow-flow-canvas"
      sx={{
        width: "100%",
        height: "100%",
        minHeight: 360,
        bgcolor: "background.neutral",
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges as Edge[]}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        nodesFocusable={false}
        edgesFocusable={false}
        panOnDrag
        panOnScroll
        zoomOnScroll
        zoomOnPinch
        preventScrolling={false}
        minZoom={0.4}
        maxZoom={1.25}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#DFE3E8"
        />
        <FitViewOnChange nodes={nodes} />
      </ReactFlow>
    </Box>
  );
}

export function WorkflowFlowCanvas(props: WorkflowFlowCanvasProps) {
  return (
    <ReactFlowProvider>
      <WorkflowFlowInner {...props} />
    </ReactFlowProvider>
  );
}
