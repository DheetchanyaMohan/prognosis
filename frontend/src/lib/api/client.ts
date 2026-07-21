import { config } from "@/lib/config"
import { ApiError, NetworkError, NotFoundError } from "./errors"

const DEFAULT_TIMEOUT_MS = 10_000

interface BackendErrorBody {
  detail?: string
}

/**
 * Thin wrapper around `fetch` (Engineering Spec §5, §1 — native fetch
 * over Axios). Responsibilities: base URL, JSON parsing, HTTP status
 * checking, timeout, standardized errors. Nothing more — no caching,
 * no retries (React Query owns those), no response reshaping (that
 * belongs in selectors/utils, never here).
 *
 * Every backend endpoint documented in the Frontend Integration Guide
 * is a parameter-less GET returning `application/json`, so this
 * client only needs to support that shape today.
 */
export async function apiGet<T>(path: string): Promise<T> {
  const url = `${config.apiBaseUrl}${path}`

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS)

  let response: Response
  try {
    response = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    })
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

  return (await response.json()) as T
}
