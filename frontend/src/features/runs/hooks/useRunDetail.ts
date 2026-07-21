import { useRunQuery } from "../api/queries"
import { deriveRunStatus, type RunStatusFlag } from "../utils/deriveRunStatus"
import type { RunDetailResponse } from "../types"

export interface RunDetailViewModel {
  runId: string
  /** `undefined` while loading or on error. */
  run: RunDetailResponse | undefined
  isPending: boolean
  isError: boolean
  error: unknown
  refetch: () => void
  /** Derived via deriveRunStatus(run.diagnostics) — see Architecture §10. */
  statusFlags: RunStatusFlag[]
  /**
   * Straight from `summary.diverged` (Integration Guide §4) — the
   * backend already computes this; the frontend doesn't re-derive it
   * from `total_epochs_completed < config.training.epochs` itself,
   * to avoid two sources of truth for the same fact (Eng. Spec
   * Principle 1). `false` while summary is null/pending.
   */
  isDiverged: boolean
  /** True while this section is still being background-polled. */
  isSummaryPending: boolean
  isDiagnosticsPending: boolean
}

/**
 * View model for the Run Detail page (Architecture §7 — the
 * "diagnosis report" centerpiece). Wraps `useRunQuery` and folds in
 * the one piece of client-side derivation the page needs
 * (`deriveRunStatus`), so `RunDetailPage` itself stays a thin
 * composer with no business logic of its own (Eng. Spec §8).
 *
 * Named `useRunDetail` rather than `useRunDiagnosis` since it may
 * eventually carry more than diagnosis-derived state (e.g. mutations,
 * once the API is no longer read-only) — this hook is "everything
 * the Run Detail page needs," not narrowly "the diagnosis part."
 */
export function useRunDetail(runId: string): RunDetailViewModel {
  const query = useRunQuery(runId)
  const run = query.data

  return {
    runId,
    run,
    isPending: query.isPending,
    isError: query.isError,
    error: query.error,
    refetch: () => void query.refetch(),
    statusFlags: deriveRunStatus(run?.diagnostics ?? null),
    isDiverged: run?.summary?.diverged ?? false,
    isSummaryPending: run ? run.summary === null : false,
    isDiagnosticsPending: run ? run.diagnostics === null : false,
  }
}
