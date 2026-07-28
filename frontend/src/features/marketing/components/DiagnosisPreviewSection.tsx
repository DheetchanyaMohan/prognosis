import { ArrowRight } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent, Badge, StatCard } from "@/components/ui"
import { GroundedBadge, ConfidenceBar, formatPercent } from "@/features/runs"

const FLOW_STEPS = ["Training Run", "AI Diagnosis", "Retrieved Evidence", "Hypotheses", "Grounded Recommendations"]

/**
 * Every value below is hand-written and illustrative — not fetched,
 * not derived from any run, not tied to any hook. Deliberately
 * separate from real content so there is zero risk of a real value
 * ever substituting in here by accident.
 */
const EXAMPLE = {
  runId: "run_014",
  knowledgeChunks: 8,
  similarRuns: 3,
  hypothesis: {
    title: "Severe overfitting due to insufficient regularization",
    confidence: 0.87,
  },
  recommendation: {
    title: "Add dropout and enable early stopping",
    confidence: 0.82,
    isGrounded: true,
  },
} as const

/**
 * A fully static example — no API call, no query/mutation hook, no
 * real run, and deliberately NOT built on `AiWorkflowPipeline` (which
 * carries real pending/active/complete execution semantics that
 * would be dishonest to fake here). Built from the same shared
 * primitives a genuine diagnosis renders with (`GroundedBadge`,
 * `ConfidenceBar`, `StatCard`, `Card`) specifically so a first-time
 * visitor recognizes this exact visual language once they run a real
 * one — but every label and border treatment says "example," and
 * nothing here is interactive (no button, mock or otherwise), so
 * there's no ambiguity about whether it's live.
 */
export function DiagnosisPreviewSection() {
  return (
    <div className="flex flex-col gap-4" aria-label="Diagnosis preview — illustrative example, not a live diagnosis">
      <div className="flex flex-col items-center gap-1 text-center">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-medium text-foreground">Diagnosis Preview</h2>
          <Badge tone="informational">Example</Badge>
        </div>
        <p className="max-w-md text-xs text-muted-foreground">
          A sample of what a completed diagnosis looks like — illustrative only, not a live result.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-1.5">
        {FLOW_STEPS.map((step, index) => (
          <div key={step} className="flex items-center gap-1.5">
            <span className="rounded-md border border-border bg-card px-2 py-1 text-xs font-medium text-muted-foreground">
              {step}
            </span>
            {index < FLOW_STEPS.length - 1 && (
              <ArrowRight className="size-3 shrink-0 text-muted-foreground" aria-hidden="true" />
            )}
          </div>
        ))}
      </div>

      <Card className="mx-auto w-full max-w-2xl border-dashed p-4">
        <CardHeader className="flex-row items-center justify-between p-0">
          <CardTitle className="font-mono text-foreground">{EXAMPLE.runId}</CardTitle>
          <Badge tone="informational">Example preview</Badge>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 p-0 pt-3">
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Knowledge Chunks" value={EXAMPLE.knowledgeChunks} />
            <StatCard label="Similar Runs" value={EXAMPLE.similarRuns} />
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground">Hypothesis</p>
            <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm text-foreground">{EXAMPLE.hypothesis.title}</p>
              <div className="flex items-center gap-2">
                <ConfidenceBar confidence={EXAMPLE.hypothesis.confidence} />
                <span className="font-mono text-xs tabular-nums text-muted-foreground">
                  {formatPercent(EXAMPLE.hypothesis.confidence)}%
                </span>
              </div>
            </div>
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground">Recommendation</p>
            <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm text-foreground">{EXAMPLE.recommendation.title}</p>
              <div className="flex flex-wrap items-center gap-2">
                <GroundedBadge isGrounded={EXAMPLE.recommendation.isGrounded} />
                <ConfidenceBar confidence={EXAMPLE.recommendation.confidence} />
                <span className="font-mono text-xs tabular-nums text-muted-foreground">
                  {formatPercent(EXAMPLE.recommendation.confidence)}%
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}