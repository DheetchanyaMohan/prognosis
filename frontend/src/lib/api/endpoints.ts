/**
 * Every backend endpoint the frontend is allowed to call, in one
 * place (Engineering Spec §5). Components must never hardcode a URL
 * — they go through a query function in a feature's `api/queries.ts`,
 * which calls one of these.
 *
 * This is the complete API surface documented in the Frontend
 * Integration Guide: four read-only GET routes, no others. Do not add
 * an endpoint here that the backend doesn't actually expose yet
 * (compare, agent, metrics, etc. are all Future Enhancement).
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
} as const
