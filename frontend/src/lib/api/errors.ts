/**
 * Custom error classes for the API layer (Engineering Spec §5).
 * These let React Query and error boundaries distinguish failure
 * modes without switching on an HTTP status code or a `detail`
 * string, since the backend defines no error `code` field
 * (Frontend Integration Guide §8).
 */

/** Base class for every error the API client can throw. */
export class ApiError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

/**
 * The backend returned a 404 with `{ "detail": "..." }`. This is an
 * expected, navigable condition (stale link, typo'd ID) — never
 * route it through a generic error boundary.
 */
export class NotFoundError extends ApiError {
  constructor(message: string) {
    super(message, 404)
    this.name = "NotFoundError"
  }
}

/**
 * The request never reached the backend (connection refused, DNS
 * failure, offline, etc.) — distinct from a 404, so the UI doesn't
 * conflate "wrong URL" with "backend is down."
 */
export class NetworkError extends ApiError {
  constructor(message: string) {
    super(message)
    this.name = "NetworkError"
  }
}

/**
 * Reserved for a future endpoint that takes a request body or typed
 * query parameter. No endpoint documented today triggers FastAPI's
 * 422 validation-error shape (Frontend Integration Guide §2), so
 * nothing throws this yet — it exists so the error hierarchy doesn't
 * need to change shape when that happens.
 */
export class ValidationError extends ApiError {
  constructor(message: string) {
    super(message, 422)
    this.name = "ValidationError"
  }
}
