import AddIcon from "@mui/icons-material/Add";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";
import { NEW_CAMPAIGN_PATH } from "../../lib/campaign-routes";

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
      onClick={() => navigate(NEW_CAMPAIGN_PATH)}
    >
      Create Campaign
    </Button>
  );
}
