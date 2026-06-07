import Alert from "@mui/material/Alert";

interface ErrorAlertProps {
  error: unknown;
  fallbackMessage?: string;
}

export function ErrorAlert({
  error,
  fallbackMessage = "Something went wrong.",
}: ErrorAlertProps) {
  const message = error instanceof Error ? error.message : fallbackMessage;

  return (
    <Alert severity="error" role="alert">
      {message}
    </Alert>
  );
}
