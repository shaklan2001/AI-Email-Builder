import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import type { DraftSaveStatus } from "../../types/workflow-draft";

interface DraftStatusBarProps {
  saveStatus: DraftSaveStatus;
  onClearDraft: () => void;
}

function statusLabel(saveStatus: DraftSaveStatus): string {
  switch (saveStatus) {
    case "saving":
      return "Saving draft…";
    case "saved":
      return "Draft saved";
    default:
      return "";
  }
}

export function DraftStatusBar({ saveStatus, onClearDraft }: DraftStatusBarProps) {
  const label = statusLabel(saveStatus);

  return (
    <Stack
      direction="row"
      spacing={1}
      alignItems="center"
      sx={{
        px: 2,
        py: 0.75,
        flexShrink: 0,
        borderBottom: 1,
        borderColor: "divider",
        bgcolor: "background.default",
      }}
    >
      {label ? (
        <Chip
          size="small"
          label={label}
          color={saveStatus === "saved" ? "success" : "default"}
          variant="outlined"
        />
      ) : null}

      <Button
        size="small"
        color="inherit"
        startIcon={<DeleteOutlineIcon />}
        onClick={onClearDraft}
        sx={{ ml: "auto" }}
      >
        Clear Draft
      </Button>
    </Stack>
  );
}
