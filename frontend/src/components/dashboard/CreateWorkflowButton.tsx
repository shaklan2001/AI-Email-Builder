import AddIcon from "@mui/icons-material/Add";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";

interface CreateWorkflowButtonProps {
  size?: "medium" | "large";
}

export function CreateWorkflowButton({ size = "medium" }: CreateWorkflowButtonProps) {
  const navigate = useNavigate();

  return (
    <Button
      variant="contained"
      startIcon={<AddIcon />}
      size={size}
      onClick={() => navigate("/workflows/new")}
    >
      Create Workflow
    </Button>
  );
}
