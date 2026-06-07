import type { ReactNode } from "react";
import { ErrorAlert } from "./ErrorAlert";

interface QueryStateProps {
  loading: boolean;
  isError: boolean;
  error: unknown;
  loadingFallback: ReactNode;
  errorFallbackMessage?: string;
  children: ReactNode;
}

export function QueryState({
  loading,
  isError,
  error,
  loadingFallback,
  errorFallbackMessage,
  children,
}: QueryStateProps) {
  if (loading) {
    return <>{loadingFallback}</>;
  }

  if (isError) {
    return <ErrorAlert error={error} fallbackMessage={errorFallbackMessage} />;
  }

  return <>{children}</>;
}
