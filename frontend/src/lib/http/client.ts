/**
 * Categorizes API error sources.
 */
export type ApiErrorKind = "http" | "network" | "parse";

/**
 * Normalized API error payload for callers.
 */
export type ApiError = {
  kind: ApiErrorKind;
  message: string;
  status?: number;
  retryable: boolean;
};

/**
 * Discriminated result for typed API requests.
 */
export type RequestResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };

/**
 * Optional retry configuration for requestJson.
 */
export type RequestJsonOptions = {
  retries?: number;
  retryDelayMs?: number;
  retryOn?: (error: ApiError, attempt: number) => boolean;
};

const defaultRetryableStatus = new Set([408, 429, 500, 502, 503, 504]);

const sleep = (ms: number) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

const classifyHttpError = (status: number, statusText: string): ApiError => ({
  kind: "http",
  status,
  message: statusText || `HTTP ${status}`,
  retryable: defaultRetryableStatus.has(status),
});

const classifyNetworkError = (error: unknown): ApiError => ({
  kind: "network",
  message: error instanceof Error ? error.message : "Network error",
  retryable: true,
});

const classifyParseError = (): ApiError => ({
  kind: "parse",
  message: "Invalid JSON response",
  retryable: false,
});

/**
 * Performs a JSON request with retry and error normalization.
 */
export async function requestJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
  options: RequestJsonOptions = {},
): Promise<RequestResult<T>> {
  const method = init?.method?.toUpperCase() ?? "GET";
  const retries = options.retries ?? (method === "GET" ? 2 : 0);
  const retryDelayMs = options.retryDelayMs ?? 250;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const response = await fetch(input, init);
      if (!response.ok) {
        const error = classifyHttpError(response.status, response.statusText);
        const shouldRetry =
          attempt < retries &&
          (options.retryOn ? options.retryOn(error, attempt) : error.retryable);
        if (shouldRetry) {
          await sleep(retryDelayMs * (attempt + 1));
          continue;
        }
        return { ok: false, error };
      }
      try {
        const data = (await response.json()) as T;
        return { ok: true, data };
      } catch {
        return { ok: false, error: classifyParseError() };
      }
    } catch (error) {
      const classified = classifyNetworkError(error);
      const shouldRetry =
        attempt < retries &&
        (options.retryOn ? options.retryOn(classified, attempt) : true);
      if (shouldRetry) {
        await sleep(retryDelayMs * (attempt + 1));
        continue;
      }
      return { ok: false, error: classified };
    }
  }

  return {
    ok: false,
    error: {
      kind: "network",
      message: "Request failed after retries",
      retryable: false,
    },
  };
}
