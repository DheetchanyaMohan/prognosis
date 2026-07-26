import { useEffect, useState } from "react"
import { AlertTriangle } from "lucide-react"
import { Card, Button } from "@/components/ui"
import { ApiError } from "@/lib/api/errors"
import { useDiagnoseRunMutation } from "../api/mutations"
import { DiagnoseButton } from "./DiagnoseButton"
import { HypothesesPanel } from "./HypothesesPanel"
import { RecommendationsPanel } from "./RecommendationsPanel"
import { EvidenceList } from "./EvidenceList"
import { AgentReasoningPanel } from "./AgentReasoningPanel"
import { ComparisonDiagnosticsGrid } from "./ComparisonDiagnosticsGrid"
import { ConfigDiffTable } from "./ConfigDiffTable"

interface DiagnosisResultPanelProps {
  runId: string
}

/**
 * The three real backend stages this call moves through
 * (FRONTEND_INTEGRATION.md's documented agent graph: router →
 * retrieve_context → analyze_metrics/generate_hypotheses → ...).
 * Cycling through this copy is loading-state *text*, not fabricated
 * progress — there is no percentage, no fake progress bar, and no
 * claim about exactly how far along the real call is; it just names
 * the stages honestly and settles on the last one for however much
 * longer the call actually takes.
 */
const STAGE_MESSAGES = ["Retrieving evidence…", "Analyzing diagnostics…", "Generating hypotheses…"]
const STAGE_INTERVAL_MS = 6_000

function useStagedLoadingMessage(isPending: boolean): string {
  const [stageIndex, setStageIndex] = useState(0)

  useEffect(() => {
    if (!isPending) {
      setStageIndex(0)
      return
    }
    const interval = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, STAGE_MESSAGES.length - 1))
    }, STAGE_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [isPending])

  return STAGE_MESSAGES[stageIndex]
}

function formatGeneratedAt(timestamp: string): string {
  const iso = timestamp.endsWith("Z") ? timestamp : `${timestamp}Z`
  return new Date(iso).toLocaleString()
}

/**
 * The flagship feature (Milestone 3). Renders inline on Run Detail —
 * deliberately never its own route, since the response is
 * non-idempotent and non-cacheable (two clicks can yield different
 * hypotheses), so a bookmarkable URL would imply a stability that
 * doesn't exist.
 *
 * Does NOT re-render `diagnostics` or `run_summary` from the response
 * — both describe the exact same run already shown in full above on
 * this same page (via the existing `DiagnosisPanel`/`ConfigPanel`),
 * so repeating them here would be pure redundancy, not new
 * information. `comparison` is rendered defensively (see below) since
 * nothing else on this page could show it.
 */
export function DiagnosisResultPanel({ runId }: DiagnosisResultPanelProps) {
  const mutation = useDiagnoseRunMutation()
  const stageMessage = useStagedLoadingMessage(mutation.isPending)

  function handleDiagnose() {
    mutation.mutate({ runId })
  }

  const isDiagnosisFailure = mutation.error instanceof ApiError && mutation.error.status === 502

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium text-foreground">AI Diagnosis</h2>
          <p className="text-xs text-muted-foreground">
            Ask the agent to generate hypotheses and recommendations for this run.
          </p>
        </div>
        <DiagnoseButton
          onClick={handleDiagnose}
          isPending={mutation.isPending}
          hasResult={mutation.isSuccess}
        />
      </div>

      {mutation.isPending && (
        <Card
          className="flex items-center justify-center p-8 text-sm text-muted-foreground"
          aria-live="polite"
        >
          {stageMessage}
        </Card>
      )}

      {mutation.isError && (
        <Card className="flex flex-col items-center gap-2 p-6 text-center">
          <AlertTriangle className="size-6 text-muted-foreground" aria-hidden="true" />
          <p className="text-sm font-medium text-foreground">
            {isDiagnosisFailure
              ? "The agent couldn't complete a diagnosis"
              : "Something went wrong generating a diagnosis"}
          </p>
          <p className="text-sm text-muted-foreground">
            {isDiagnosisFailure
              ? "This can happen if the language model is temporarily unavailable. Try again."
              : "Please try again."}
          </p>
          <Button variant="outline" onClick={handleDiagnose}>
            Try again
          </Button>
        </Card>
      )}

      {mutation.isSuccess && mutation.data && (
        <div className="flex flex-col gap-4">
          <p className="text-xs text-muted-foreground">
            Generated {formatGeneratedAt(mutation.data.generated_at)}
          </p>

          <HypothesesPanel hypotheses={mutation.data.hypotheses} />
          <RecommendationsPanel recommendations={mutation.data.recommendations} />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <EvidenceList title="Retrieved Knowledge" chunks={mutation.data.retrieved_knowledge} />
            <EvidenceList title="Similar Runs" chunks={mutation.data.similar_runs} />
          </div>

          {/*
            Defensive only: `comparison` is populated when
            request_type === "compare_runs", which this single-run
            button never explicitly requests — but the type permits
            it, and nothing else on this page could show a comparison,
            so render it rather than silently dropping real data if
            the backend ever returns it.
          */}
          {mutation.data.comparison && (
            <div className="flex flex-col gap-3">
              <ComparisonDiagnosticsGrid
                runAId={mutation.data.comparison.run_a_id}
                runBId={mutation.data.comparison.run_b_id}
                runADiagnostics={mutation.data.comparison.run_a_diagnostics}
                runBDiagnostics={mutation.data.comparison.run_b_diagnostics}
              />
              <ConfigDiffTable differences={mutation.data.comparison.config_differences} />
            </div>
          )}

          <AgentReasoningPanel trace={mutation.data.trace} />
        </div>
      )}
    </div>
  )
}