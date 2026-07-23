import { FolderOpen } from "lucide-react"
import { useExperimentsQuery } from "@/features/experiments"
import { ExperimentCard } from "@/features/experiments/components/ExperimentCard"
import { ExperimentCardSkeleton } from "@/features/experiments/components/ExperimentCardSkeleton"
import { EmptyState, QueryErrorState } from "@/components/ui"

/**
 * `/experiments` — Architecture §7. Zero experiments gets a full-page
 * explanatory empty state, never an empty table with no context.
 */
export function ExperimentListPage() {
  const { data, isPending, isError, error, refetch } = useExperimentsQuery()

  if (isPending) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <ExperimentCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (isError) {
    return <QueryErrorState error={error} onRetry={() => refetch()} />
  }

  if (data.length === 0) {
    return (
      <EmptyState
        variant="page"
        icon={<FolderOpen className="size-8" aria-hidden="true" />}
        title="No experiments yet"
        message="Experiments appear here once training runs have been logged."
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <h1 className="sr-only">Experiments</h1>
      {data.map((experiment) => (
        <ExperimentCard key={experiment.experiment_name} experiment={experiment} />
      ))}
    </div>
  )
}
