import { Sparkles, AlertTriangle } from "lucide-react"
import { Link } from "react-router-dom"
import { Card, Button } from "@/components/ui"
import { cn } from "@/lib/utils"
import { DiagnoseButton } from "./DiagnoseButton"
import { AiWorkflowPipeline } from "./AiWorkflowPipeline"
import { AgentCards } from "./AgentCards"
import type { DiagnosisViewModel } from "../hooks/useDiagnosis"

interface AiDiagnosisSectionProps {
  diagnosis: DiagnosisViewModel
}

/**
 * The star of the page (per the "AI as the star of the product"
 * brief): the invitation to run a diagnosis, the button itself, and
 * the workflow pipeline — positioned as page section 2 (right after
 * the compact Overview) specifically so the button needs no
 * scrolling to reach. The detailed findings this produces (evidence,
 * reasoning, hypotheses, recommendations) live much further down the
 * page in `DetailedAnalysisSection` — deliberately not here, so
 * recommendations read as the *final* output of the process rather
 * than competing with the invitation to start it.
 *
 * The pipeline card gets visibly heavier treatment (more padding, a
 * firmer border) once `isSuccess` — "the workflow visualization
 * should become the centerpiece of the page" after analysis
 * completes. No animation is used to achieve this, just a static
 * size/emphasis difference between the idle/pending and complete
 * states.
 */
export function AiDiagnosisSection({ diagnosis }: AiDiagnosisSectionProps) {
  const workflowStateCaption = diagnosis.isSuccess ? "Complete" : diagnosis.isPending ? "Running…" : "Not yet run"

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="max-w-xl">
          <p className="flex items-center gap-2 text-base font-semibold text-foreground">
            <Sparkles className="size-4 text-foreground" aria-hidden="true" />
            Get an AI diagnosis
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            The agent retrieves relevant evidence, reasons over this run's metrics, and produces
            grounded, explainable recommendations — showing its work at every step.
          </p>
        </div>
        <DiagnoseButton onClick={diagnosis.run} isPending={diagnosis.isPending} hasResult={diagnosis.isSuccess} />
      </div>

      <Card
        className={cn(
          "transition-[padding]",
          diagnosis.isSuccess ? "border-foreground/20 p-6" : "p-4",
        )}
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className={cn("font-medium text-foreground", diagnosis.isSuccess ? "text-base" : "text-sm")}>
            AI Workflow
          </h3>
          <div className="flex items-center gap-3">
            <Link to="/architecture" className="text-xs text-muted-foreground hover:text-foreground">
              See the full system architecture →
            </Link>
            <span className="text-xs text-muted-foreground">{workflowStateCaption}</span>
          </div>
        </div>
        <AiWorkflowPipeline stages={diagnosis.pipelineStages} />
      </Card>

      {diagnosis.isIdle && <AgentCards />}

      {diagnosis.isError && (
        <Card className="flex flex-col items-center gap-2 p-6 text-center">
          <AlertTriangle className="size-6 text-muted-foreground" aria-hidden="true" />
          <p className="text-sm font-medium text-foreground">
            {diagnosis.isDiagnosisFailure
              ? "The agent couldn't complete a diagnosis"
              : "Something went wrong generating a diagnosis"}
          </p>
          <p className="text-sm text-muted-foreground">
            {diagnosis.isDiagnosisFailure
              ? "This can happen if the language model is temporarily unavailable. Try again."
              : "Please try again."}
          </p>
          <Button variant="outline" onClick={diagnosis.run}>
            Try again
          </Button>
        </Card>
      )}
    </div>
  )
}