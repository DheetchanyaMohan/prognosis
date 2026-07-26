import { useParams } from "react-router-dom"
import { useExperimentQuery } from "@/features/experiments"
import { RunTable } from "@/features/experiments/components/RunTable"
import { QueryErrorState, Skeleton } from "@/components/ui"
import { formatBackendDate } from "@/lib/format-date"
import { cn, pageHeadingClass } from "@/lib/utils"

function ExperimentDetailSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-6 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>
      <div className="flex flex-col gap-2">
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
      </div>
    </div>
  )
}

/**
 * `/experiments/:experimentId` — Architecture §7 "Experiment Detail".
 * `experimentId` in the URL is the human-readable `experiment_name`
 * (Integration Guide §3), used directly as the path param.
 */
export function ExperimentDetailPage() {
  const { experimentId } = useParams<{ experimentId: string }>()
  const { data: experiment, isPending, isError, error, refetch } = useExperimentQuery(experimentId!)

  if (isPending) {
    return <ExperimentDetailSkeleton />
  }

  if (isError) {
    return (
      <QueryErrorState
        error={error}
        onRetry={() => refetch()}
        notFoundTitle="This experiment doesn't exist"
      />
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className={cn("font-mono", pageHeadingClass)}>{experiment.experiment_name}</h1>
        <p className="text-sm text-muted-foreground">
          {experiment.description ?? "No description"}
        </p>
        <p className="text-xs text-muted-foreground">
          Created {formatBackendDate(experiment.created_at)}
        </p>
      </div>

      <section aria-labelledby="runs-heading">
        <h2 id="runs-heading" className="mb-2 text-sm font-medium text-muted-foreground">
          Runs
        </h2>
        <RunTable experimentId={experiment.experiment_name} runIds={experiment.run_ids} />
      </section>
    </div>
  )
}