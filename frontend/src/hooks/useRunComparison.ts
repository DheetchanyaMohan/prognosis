import { useRunComparisonQuery } from "../api/queries"

/**
 * View model for the Compare page (mirrors `useRunDetail`'s role for
 * Run Detail — Eng. Spec §8: pages stay thin composers, this is where
 * any composition logic lives instead). Currently a thin pass-through
 * since the comparison response needs no client-side derivation the
 * way `deriveRunStatus` derives a run's status flags — kept as its
 * own hook rather than calling `useRunComparisonQuery` directly from
 * the page, so the page's dependency is "the Compare view model," not
 * "a specific React Query hook," matching the same boundary
 * `useRunDetail` established.
 */
export function useRunComparison(runAId: string, runBId: string) {
  const query = useRunComparisonQuery(runAId, runBId)

  return {
    runAId,
    runBId,
    comparison: query.data,
    isPending: query.isPending,
    isError: query.isError,
    error: query.error,
    refetch: () => void query.refetch(),
  }
}