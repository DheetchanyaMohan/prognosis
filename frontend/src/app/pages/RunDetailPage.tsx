import { useParams } from "react-router-dom"
import { useRunDetail } from "@/features/runs/hooks/useRunDetail"
import { RunHeaderBand } from "@/features/runs/components/RunHeaderBand"
import { DiagnosisPanel } from "@/features/runs/components/DiagnosisPanel"
import { SummaryPanel } from "@/features/runs/components/SummaryPanel"
import { ConfigPanel } from "@/features/runs/components/ConfigPanel"
import { DiagnosisResultPanel } from "@/features/runs/components/DiagnosisResultPanel"
import { QueryErrorState, Skeleton } from "@/components/ui"

function RunDetailSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-7 w-40" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
      <Skeleton className="h-24" />
      <Skeleton className="h-40" />
    </div>
  )
}

/**
 * `/experiments/:experimentId/runs/:runId` — the centerpiece
 * "diagnosis report" (Architecture §7). Visual hierarchy is
 * deliberate and matches §10 exactly: status badge (in
 * RunHeaderBand) → diagnosis cards → summary prose → configuration
 * table, never the other way around. The AI Diagnosis section
 * (Milestone 3) comes last and is opt-in — it's an additional,
 * on-demand interpretive layer on top of the always-present
 * deterministic report above it, not a replacement for any of it.
 */
export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>()
  const { run, isPending, isError, error, refetch, statusFlags, isSummaryPending, isDiagnosticsPending } =
    useRunDetail(runId!)

  if (isPending) {
    return <RunDetailSkeleton />
  }

  if (isError) {
    return <QueryErrorState error={error} onRetry={refetch} notFoundTitle="This run doesn't exist" />
  }

  if (!run) {
    // Shouldn't happen (isPending/isError cover every other state), but
    // narrows the type for TS and fails safe rather than crashing.
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <RunHeaderBand runId={run.run_id} statusFlags={statusFlags} />
      <section aria-labelledby="diagnosis-heading">
        <h2 id="diagnosis-heading" className="sr-only">
          Diagnosis
        </h2>
        <DiagnosisPanel diagnostics={run.diagnostics} isPolling={isDiagnosticsPending} />
      </section>
      <section aria-labelledby="summary-heading">
        <h2 id="summary-heading" className="sr-only">
          Summary
        </h2>
        <SummaryPanel summary={run.summary} isPolling={isSummaryPending} />
      </section>
      <section aria-labelledby="config-heading">
        <h2 id="config-heading" className="mb-2 text-sm font-medium text-muted-foreground">
          Configuration
        </h2>
        <ConfigPanel config={run.config} />
      </section>
      <section aria-labelledby="ai-diagnosis-heading" className="border-t border-border pt-6">
        <h2 id="ai-diagnosis-heading" className="sr-only">
          AI Diagnosis
        </h2>
        <DiagnosisResultPanel runId={run.run_id} />
      </section>
    </div>
  )
}