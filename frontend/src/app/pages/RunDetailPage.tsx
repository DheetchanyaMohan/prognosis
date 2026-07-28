import { useParams } from "react-router-dom"
import { useRunDetail } from "@/features/runs/hooks/useRunDetail"
import { useDiagnosis } from "@/features/runs/hooks/useDiagnosis"
import { RunHeaderBand } from "@/features/runs/components/RunHeaderBand"
import { RunOverviewSummary } from "@/features/runs/components/RunOverviewSummary"
import { AiDiagnosisSection } from "@/features/runs/components/AiDiagnosisSection"
import { DiagnosisPanel } from "@/features/runs/components/DiagnosisPanel"
import { SummaryPanel } from "@/features/runs/components/SummaryPanel"
import { ConfigPanel } from "@/features/runs/components/ConfigPanel"
import { DetailedAnalysisSection } from "@/features/runs/components/DetailedAnalysisSection"
import { QueryErrorState, Skeleton } from "@/components/ui"

function RunDetailSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-7 w-40" />
      <Skeleton className="h-16" />
      <Skeleton className="h-40" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
    </div>
  )
}

/**
 * `/experiments/:experimentId/runs/:runId` — restructured around 5
 * named, visibly-headed sections meant to read as a guided journey
 * rather than an internal report (the brief: "the AI should feel
 * like the star of the product"):
 *
 *   1. Overview          — compact: status badge + one-line summary
 *   2. AI Diagnosis       — the invitation + button + workflow pipeline
 *   3. Metrics            — deterministic diagnostics + final stats
 *   4. Configuration      — hyperparameters (unchanged)
 *   5. Detailed Analysis  — evidence, reasoning, hypotheses, recommendations
 *
 * Two deliberate departures from the previous structure, both
 * requested directly:
 *  - AI Diagnosis moved from last to second, right after a
 *    deliberately compact Overview, so the Diagnose button needs no
 *    scrolling to reach.
 *  - The diagnosis mutation is now split across two components
 *    (`AiDiagnosisSection` early, `DetailedAnalysisSection` late)
 *    that share one `useDiagnosis` instance — calling the mutation
 *    hook twice would create two independent, out-of-sync states.
 *
 * All 5 section headings are now visible (previously Diagnosis/
 * Summary were `sr-only`, since their content self-labeled via card
 * titles) — a deliberate change: this page is now meant to visibly
 * guide a first-time reader step by step, not just structure content
 * for a reader who's already oriented.
 */
export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>()
  const { run, isPending, isError, error, refetch, statusFlags, isSummaryPending, isDiagnosticsPending } =
    useRunDetail(runId!)
  // Always called (Rules of Hooks) — runId is known from the route
  // even before `run` itself has loaded.
  const diagnosis = useDiagnosis(runId!)

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
    <div className="flex flex-col gap-8">
      <RunHeaderBand runId={run.run_id} statusFlags={statusFlags} />

      <section aria-labelledby="overview-heading">
        <h2 id="overview-heading" className="mb-2 text-sm font-medium text-muted-foreground">
          Overview
        </h2>
        <RunOverviewSummary summary={run.summary} isPolling={isSummaryPending} />
      </section>

      <section aria-labelledby="ai-diagnosis-heading" className="border-t border-border pt-8">
        <h2 id="ai-diagnosis-heading" className="mb-2 text-sm font-medium text-muted-foreground">
          AI Diagnosis
        </h2>
        <AiDiagnosisSection diagnosis={diagnosis} />
      </section>

      <section aria-labelledby="metrics-heading" className="border-t border-border pt-8">
        <h2 id="metrics-heading" className="mb-2 text-sm font-medium text-muted-foreground">
          Metrics
        </h2>
        <div className="flex flex-col gap-4">
          <DiagnosisPanel diagnostics={run.diagnostics} isPolling={isDiagnosticsPending} />
          <SummaryPanel summary={run.summary} />
        </div>
      </section>

      <section aria-labelledby="config-heading" className="border-t border-border pt-8">
        <h2 id="config-heading" className="mb-2 text-sm font-medium text-muted-foreground">
          Configuration
        </h2>
        <ConfigPanel config={run.config} />
      </section>

      {diagnosis.isSuccess && (
        <section aria-labelledby="detailed-analysis-heading" className="border-t border-border pt-8">
          <h2 id="detailed-analysis-heading" className="mb-2 text-sm font-medium text-muted-foreground">
            Detailed Analysis
          </h2>
          <DetailedAnalysisSection diagnosis={diagnosis} />
        </section>
      )}
    </div>
  )
}