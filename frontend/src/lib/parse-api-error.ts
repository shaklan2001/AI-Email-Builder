interface ApiErrorBody {
  success?: boolean;
  error?: {
    message?: string;
    code?: string;
  };
}

export async function parseApiError(response: Response): Promise<string> {
  const fallback = `${response.status} ${response.statusText}`;
  try {
    const body = (await response.json()) as ApiErrorBody;
    const message = body.error?.message?.trim();
    if (message) {
      return message;
    }
  } catch {
    // ignore JSON parse errors
  }
  return fallback;
}
