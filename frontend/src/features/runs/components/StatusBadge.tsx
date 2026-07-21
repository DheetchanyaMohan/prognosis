import { TrendingUp, PauseCircle, Zap, CheckCircle2, Clock } from "lucide-react"
import { Badge, type BadgeTone } from "@/components/ui"
import type { RunStatusFlag } from "../utils/deriveRunStatus"

const flagConfig: Record<RunStatusFlag, { tone: BadgeTone; icon: React.ReactNode; label: string }> = {
  overfitting: { tone: "concern", icon: <TrendingUp className="size-3.5" aria-hidden="true" />, label: "Overfitting" },
  stalled: { tone: "caution", icon: <PauseCircle className="size-3.5" aria-hidden="true" />, label: "Stalled" },
  unstable: { tone: "concern", icon: <Zap className="size-3.5" aria-hidden="true" />, label: "Unstable" },
  healthy: { tone: "healthy", icon: <CheckCircle2 className="size-3.5" aria-hidden="true" />, label: "Healthy" },
  pending: { tone: "informational", icon: <Clock className="size-3.5" aria-hidden="true" />, label: "Pending" },
}

interface StatusBadgeProps {
  flags: RunStatusFlag[]
}

/**
 * Reused on the Run Detail header band and (eventually) each row of
 * the Experiment Detail run table. Purely presentational — takes
 * already-derived flags rather than raw `diagnostics`, so it never
 * duplicates `deriveRunStatus`'s logic. Supports a compact multi-flag
 * state (Architecture §10) — e.g. unstable *and* overfitting render
 * as two badges side by side, never forced into one verdict.
 */
export function StatusBadge({ flags }: StatusBadgeProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {flags.map((flag) => {
        const config = flagConfig[flag]
        return (
          <Badge key={flag} tone={config.tone} icon={config.icon}>
            {config.label}
          </Badge>
        )
      })}
    </div>
  )
}
