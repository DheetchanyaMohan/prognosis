import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui"
import { GroundedBadge } from "./GroundedBadge"
import { ConfidenceBar } from "./ConfidenceBar"
import { RecommendationLineage } from "./RecommendationLineage"
import { formatPercent } from "../utils/format-run-stats"
import type { Recommendation } from "../types"

interface RecommendationsPanelProps {
  recommendations: Recommendation[]
}

/**
 * `estimated_effort` gets a plain `neutral`-tone Badge, matching the
 * treatment `ConfigPanel` already gives `optimizer`/`lr_scheduler` —
 * the four semantic tones are reserved exclusively for diagnosis-
 * state communication (Architecture §20); effort level isn't one, so
 * it deliberately does not get a green/amber/red treatment.
 *
 * Confidence, provenance, and grounded status are always rendered
 * directly on the card — never behind a "details" toggle, per
 * FRONTEND_INTEGRATION.md §1's "always render these" instruction for
 * provenance, extended here to the other two trust-relevant fields.
 * `supporting_evidence` is now rendered too (Milestone 6 §5) — a real
 * field that was previously only shown for Hypotheses, not
 * Recommendations.
 *
 * `RecommendationLineage` appears once per card as a general
 * pipeline-order indicator (Retrieved Evidence → Diagnostics →
 * Hypotheses → Recommendation) — see that component's own doc
 * comment for why it deliberately does NOT claim a specific per-item
 * link the response data doesn't provide. The one clarifying caption
 * below the section title states this once, rather than repeating it
 * on every card.
 */
export function RecommendationsPanel({ recommendations }: RecommendationsPanelProps) {
  if (recommendations.length === 0) {
    return (
      <Card className="p-4">
        <CardHeader className="p-0">
          <CardTitle>Recommendations</CardTitle>
        </CardHeader>
        <CardContent className="p-0 pt-3">
          <p className="text-sm text-muted-foreground">
            No recommendations were generated for this query.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs text-muted-foreground">
        Every recommendation follows the same evidence → diagnostics → hypotheses → recommendation
        pipeline; see Provenance/Supporting Evidence on each card for what specifically grounds it.
      </p>
      <ul className="flex flex-col gap-3">
        {recommendations.map((rec, index) => (
          <li key={index}>
            <Card className="p-4">
              <CardHeader className="p-0">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle className="text-sm font-medium text-foreground">{rec.title}</CardTitle>
                  <div className="flex flex-wrap items-center gap-2">
                    <GroundedBadge isGrounded={rec.is_grounded} />
                    <ConfidenceBar confidence={rec.confidence} />
                    <span className="font-mono text-xs tabular-nums text-muted-foreground">
                      {formatPercent(rec.confidence)}% confidence
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-2 p-0 pt-2">
                <RecommendationLineage />
                <p className="text-sm text-foreground">{rec.rationale}</p>
                <p className="text-sm text-muted-foreground">Expected benefit: {rec.expected_benefit}</p>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Effort:</span>
                  <Badge tone="neutral">{rec.estimated_effort}</Badge>
                </div>
                {rec.supporting_evidence.length > 0 && (
                  <div className="mt-1 border-t border-border pt-2">
                    <p className="text-xs font-medium text-muted-foreground">Supporting Evidence</p>
                    <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
                      {rec.supporting_evidence.map((evidence, i) => (
                        <li key={i}>{evidence}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {rec.provenance.length > 0 && (
                  <div className="mt-1 border-t border-border pt-2">
                    <p className="text-xs font-medium text-muted-foreground">Provenance</p>
                    <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
                      {rec.provenance.map((source, i) => (
                        <li key={i}>{source}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </li>
        ))}
      </ul>
    </div>
  )
}