interface ConfidenceBarProps {
  /** 0.0–1.0, matching the raw `confidence` field. */
  confidence: number
}

/**
 * A plain linear 0–100% width bar (Milestone 6 §6) — no non-linear
 * scaling, no baseline offset that would visually exaggerate small
 * differences. Always paired with the existing numeric percentage
 * text in `HypothesesPanel`/`RecommendationsPanel`, never a
 * replacement for it.
 */
export function ConfidenceBar({ confidence }: ConfidenceBarProps) {
  const percent = Math.max(0, Math.min(100, confidence * 100))

  return (
    <div className="h-1.5 w-20 shrink-0 overflow-hidden rounded-full bg-secondary" role="presentation">
      <div className="h-full rounded-full bg-foreground/50" style={{ width: `${percent}%` }} />
    </div>
  )
}