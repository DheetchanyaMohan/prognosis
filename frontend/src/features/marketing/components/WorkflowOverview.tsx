import { ArrowRight } from "lucide-react"

/**
 * The exact 7-stage flow requested for the landing page — a
 * conceptual, product-level overview ("without exposing implementation
 * details yet"), distinct from `AiWorkflowPipeline` (Run Detail's
 * real, trace-derived LangGraph execution view). This component is
 * static marketing content with no request state at all: no
 * pending/active/complete distinction, since it never represents a
 * specific execution — just the shape of what the product does.
 */
const STAGES = [
  "Experiment",
  "Run",
  "Agentic Analysis",
  "Knowledge Retrieval",
  "Reasoning",
  "Grounded Recommendations",
  "Decision Support",
]

export function WorkflowOverview() {
  return (
    <div className="flex flex-col items-center gap-3">
      <h2 className="text-sm font-medium text-foreground">How Prognosis Works</h2>
      <div className="flex flex-wrap items-center justify-center gap-2">
        {STAGES.map((stage, index) => (
          <div key={stage} className="flex items-center gap-2">
            <span className="rounded-md border border-border bg-card px-3 py-2 text-sm font-medium text-foreground">
              {stage}
            </span>
            {index < STAGES.length - 1 && (
              <ArrowRight className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}