import { config } from "@/lib/config"
import { ApiError, NetworkError, NotFoundError } from "./errors"

const DEFAULT_TIMEOUT_MS = 10_000

interface BackendErrorBody {
  detail?: string
}

interface RequestOptions {
  /** Overrides DEFAULT_TIMEOUT_MS — needed for POST /runs/{id}/diagnose, documented as taking up to ~30s (a real LLM call), which the 10s GET default would incorrectly abort. */
  timeoutMs?: number
}

async function request<T>(
  path: string,
  init: RequestInit,
  { timeoutMs = DEFAULT_TIMEOUT_MS }: RequestOptions = {},
): Promise<T> {
  const url = `${config.apiBaseUrl}${path}`

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  let response: Response
  try {
    response = await fetch(url, { ...init, signal: controller.signal })
  } catch (error) {
    throw new NetworkError(
      error instanceof Error && error.name === "AbortError"
        ? `Request to ${path} timed out`
        : `Could not reach the backend at ${url}`,
    )
  } finally {
    clearTimeout(timeout)
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = (await response.json()) as BackendErrorBody
      if (body.detail) detail = body.detail
    } catch {
      // Body wasn't JSON (or was empty) — fall back to statusText.
    }

    if (response.status === 404) {
      throw new NotFoundError(detail)
    }
    throw new ApiError(detail, response.status)
  }

  // A 200 with an empty body is not a documented shape for any current
  // endpoint, but guard it rather than let JSON.parse throw a confusing error.
  const text = await response.text()
  return (text ? JSON.parse(text) : undefined) as T
}

/**
 * Thin wrapper around `fetch` (Engineering Spec §5, §1 — native fetch
 * over Axios). Responsibilities: base URL, JSON parsing, HTTP status
 * checking, timeout, standardized errors. Nothing more — no caching,
 * no retries (React Query owns those), no response reshaping (that
 * belongs in selectors/utils, never here).
 */
export function apiGet<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>(path, { method: "GET", headers: { Accept: "application/json" } }, options)
}

/**
 * POST wrapper for the one non-idempotent endpoint in the API
 * (`/runs/{id}/diagnose`). Body is optional and JSON-encoded when
 * present — the backend accepts an empty body for the default query.
 */
export function apiPost<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return request<T>(
    path,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    },
    options,
  )
}