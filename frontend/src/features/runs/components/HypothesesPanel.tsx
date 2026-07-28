import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui"
import { ConfidenceBar } from "./ConfidenceBar"
import { formatPercent } from "../utils/format-run-stats"
import type { Hypothesis } from "../types"

interface HypothesesPanelProps {
  hypotheses: Hypothesis[]
}

/**
 * Hypotheses come before recommendations in reading order (Milestone
 * 3 layout): diagnose, then prescribe — mirroring how a lab report
 * reads. `CardTitle`'s default muted styling (used elsewhere for
 * metric *labels* like "Generalization Gap") is overridden here since
 * a hypothesis title is actual findings content, not a category
 * label, and deserves the visual weight.
 */
export function HypothesesPanel({ hypotheses }: HypothesesPanelProps) {
  if (hypotheses.length === 0) {
    return (
      <Card className="p-4">
        <CardHeader className="p-0">
          <CardTitle>Hypotheses</CardTitle>
        </CardHeader>
        <CardContent className="p-0 pt-3">
          <p className="text-sm text-muted-foreground">No hypotheses were generated for this query.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <ul className="flex flex-col gap-3">
      {hypotheses.map((hypothesis, index) => (
        <li key={index}>
          <Card className="p-4">
            <CardHeader className="p-0">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CardTitle className="text-sm font-medium text-foreground">{hypothesis.title}</CardTitle>
                <div className="flex items-center gap-2">
                  <ConfidenceBar confidence={hypothesis.confidence} />
                  <span className="font-mono text-xs tabular-nums text-muted-foreground">
                    {formatPercent(hypothesis.confidence)}% confidence
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0 pt-2">
              <p className="text-sm text-foreground">{hypothesis.explanation}</p>
              {hypothesis.supporting_evidence.length > 0 && (
                <ul className="mt-2 list-inside list-disc text-xs text-muted-foreground">
                  {hypothesis.supporting_evidence.map((evidence, i) => (
                    <li key={i}>{evidence}</li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </li>
      ))}
    </ul>
  )
}