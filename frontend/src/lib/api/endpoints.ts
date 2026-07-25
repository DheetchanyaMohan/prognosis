/**
 * Every backend endpoint the frontend is allowed to call, in one
 * place (Engineering Spec §5). Components must never hardcode a URL
 * — they go through a query/mutation function in a feature's
 * `api/queries.ts` or `api/mutations.ts`, which calls one of these.
 *
 * This is the complete API surface documented in FRONTEND_INTEGRATION.md
 * as of the backend freeze: six routes total. Do not add an endpoint
 * here that the backend doesn't actually expose.
 */

export const endpoints = {
  /** GET /health — unprefixed, unlike every resource endpoint. */
  health: () => "/health",

  /** GET /api/v1/experiments */
  experiments: () => "/api/v1/experiments",

  /** GET /api/v1/experiments/{experimentId} */
  experiment: (experimentId: string) =>
    `/api/v1/experiments/${encodeURIComponent(experimentId)}`,

  /** GET /api/v1/runs/{runId} */
  run: (runId: string) => `/api/v1/runs/${encodeURIComponent(runId)}`,

  /**
   * POST /api/v1/runs/{runId}/diagnose — the only non-idempotent,
   * non-GET route in the API. Invokes the LangGraph agent.
   */
  diagnoseRun: (runId: string) => `/api/v1/runs/${encodeURIComponent(runId)}/diagnose`,

  /**
   * GET /api/v1/runs/{runAId}/compare/{runBId} — deterministic,
   * fast, no LLM. Order doesn't imply which run is "better."
   */
  compareRuns: (runAId: string, runBId: string) =>
    `/api/v1/runs/${encodeURIComponent(runAId)}/compare/${encodeURIComponent(runBId)}`,
} as const