import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { ConditionNodeData } from "../types";

export function ConditionNode({ data }: NodeProps) {
  const { label } = data as ConditionNodeData;

  return (
    <>
      <Handle
        type="target"
        position={Position.Top}
        isConnectable={false}
        style={{ opacity: 0, width: 8, height: 8 }}
      />
      <Paper
        variant="outlined"
        sx={{
          width: 200,
          px: 2,
          py: 1.25,
          borderColor: "primary.main",
          borderWidth: 1,
          borderRadius: 1.5,
          bgcolor: "background.paper",
          boxShadow: "none",
          textAlign: "center",
        }}
      >
        <Typography variant="body2" fontWeight={500}>
          {label}
        </Typography>
      </Paper>
      <Handle
        type="source"
        position={Position.Bottom}
        id="yes"
        isConnectable={false}
        style={{ left: "30%", opacity: 0, width: 8, height: 8 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="no"
        isConnectable={false}
        style={{ left: "70%", opacity: 0, width: 8, height: 8 }}
      />
    </>
  );
}
