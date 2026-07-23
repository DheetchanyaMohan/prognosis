import { ErrorState } from "./ErrorState"
import { Button } from "./Button"
import { NetworkError, NotFoundError } from "@/lib/api/errors"

interface QueryErrorStateProps {
  error: unknown
  /** Omit for a 404 — an expected, navigable condition with nothing to retry (Architecture §15). */
  onRetry?: () => void
  /** Overrides ErrorState's generic 404 copy with a resource-specific one, e.g. "This run doesn't exist". */
  notFoundTitle?: string
}

/**
 * Maps a React Query error to the right `ErrorState` variant —
 * 404 vs. network vs. generic, visually and textually distinct per
 * Architecture §15. This depends only on the generic `lib/api/errors`
 * taxonomy, not on any feature, so it stays consistent with
 * `components/ui` knowing nothing about experiments/runs (Eng. Spec
 * §8) while still being reusable by any page that fetches data.
 *
 * Extracted after the same `error instanceof NotFoundError ? ... :
 * error instanceof NetworkError ? "network" : "generic"` branching
 * was found duplicated identically across ExperimentListPage,
 * ExperimentDetailPage, and RunDetailPage.
 */
export function QueryErrorState({ error, onRetry, notFoundTitle }: QueryErrorStateProps) {
  if (error instanceof NotFoundError) {
    return <ErrorState variant="not-found" title={notFoundTitle} />
  }

  return (
    <ErrorState
      variant={error instanceof NetworkError ? "network" : "generic"}
      action={
        onRetry && (
          <Button variant="outline" onClick={onRetry}>
            Try again
          </Button>
        )
      }
    />
  )
}
