import { ChevronRight } from "lucide-react"

const TIERS = ["Retrieved Evidence", "Diagnostics", "Hypotheses", "Recommendation"]

/**
 * Represents the general pipeline order every recommendation is
 * produced through (Milestone 6 §5). This is NOT a claim that a
 * specific recommendation traces to one specific hypothesis or
 * diagnostic record — the response schema has no `hypothesis_id` or
 * `chunk_id` field on `Recommendation` linking them that precisely,
 * only free-text `provenance`/`supporting_evidence`. Showing a
 * fabricated one-to-one graph would overstate what's actually known,
 * so this stays a genuine, honest statement about the pipeline's
 * shape — the concrete, recommendation-specific data (provenance,
 * supporting evidence) is rendered separately, right below it.
 */
export function RecommendationLineage() {
  return (
    <div className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
      {TIERS.map((tier, index) => (
        <span key={tier} className="flex items-center gap-1">
          <span className={index === TIERS.length - 1 ? "font-medium text-foreground" : undefined}>{tier}</span>
          {index < TIERS.length - 1 && <ChevronRight className="size-3" aria-hidden="true" />}
        </span>
      ))}
    </div>
  )
}