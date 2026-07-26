import { useParams } from "react-router-dom"
import { useRunComparison } from "@/features/runs/hooks/useRunComparison"
import { ComparisonDiagnosticsGrid } from "@/features/runs/components/ComparisonDiagnosticsGrid"
import { ConfigDiffTable } from "@/features/runs/components/ConfigDiffTable"
import { QueryErrorState, Skeleton } from "@/components/ui"

function RunComparisonSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-6 w-64" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
      <Skeleton className="h-40" />
    </div>
  )
}

/**
 * `/compare/:runAId/:runBId` — a real, bookmarkable route (unlike
 * Diagnose): the comparison result is fully deterministic, so a
 * shareable URL is honest here in a way it wouldn't be for a
 * non-idempotent agent call.
 */
export function RunComparisonPage() {
  const { runAId, runBId } = useParams<{ runAId: string; runBId: string }>()
  const { comparison, isPending, isError, error, refetch } = useRunComparison(runAId!, runBId!)

  if (isPending) {
    return <RunComparisonSkeleton />
  }

  if (isError) {
    return (
      <QueryErrorState
        error={error}
        onRetry={() => refetch()}
        notFoundTitle="One or both of these runs don't exist"
      />
    )
  }

  if (!comparison) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-foreground">
        <span className="font-mono">{comparison.run_a_id}</span>
        <span className="mx-2 text-muted-foreground">vs</span>
        <span className="font-mono">{comparison.run_b_id}</span>
      </h1>

      <section aria-labelledby="comparison-diagnostics-heading">
        <h2 id="comparison-diagnostics-heading" className="sr-only">
          Diagnostics comparison
        </h2>
        <ComparisonDiagnosticsGrid
          runAId={comparison.run_a_id}
          runBId={comparison.run_b_id}
          runADiagnostics={comparison.run_a_diagnostics}
          runBDiagnostics={comparison.run_b_diagnostics}
        />
      </section>

      <section aria-labelledby="config-diff-heading">
        <h2 id="config-diff-heading" className="mb-2 text-sm font-medium text-muted-foreground">
          Configuration differences
        </h2>
        <ConfigDiffTable differences={comparison.config_differences} />
      </section>
    </div>
  )
}