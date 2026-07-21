/**
 * Mirrors `ExperimentRecord` exactly, as returned by both
 * GET /api/v1/experiments (array) and
 * GET /api/v1/experiments/{experimentId} (single object).
 */
export interface ExperimentRecord {
  experiment_name: string
  description: string | null
  /** ISO 8601, no timezone suffix — stored as naive UTC. */
  created_at: string
  run_ids: string[]
}
