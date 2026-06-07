import type { UseQueryResult } from "@tanstack/react-query";

export type StandardQueryResult<T> = {
  data: T | undefined;
  error: Error | null;
  loading: boolean;
  isError: boolean;
  isLoading: boolean;
  refetch: UseQueryResult<T, Error>["refetch"];
};

export function mapQueryResult<T>(query: UseQueryResult<T, Error>): StandardQueryResult<T> {
  return {
    data: query.data,
    error: query.error,
    loading: query.isLoading,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
