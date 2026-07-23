import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui"
import { formatLoss, formatPercent } from "../utils/format-run-stats"
import type { GeneralizationGap } from "../types"

interface GapCardProps {
  gap: GeneralizationGap
  /** Needed to caveat a "stable" trend when there's too little history to call one (Integration Guide §4). */
  totalEpochs: number
}

const trendConfig = {
  widening: { icon: TrendingUp, label: "Widening", tone: "concern" as const },
  narrowing: { icon: TrendingDown, label: "Narrowing", tone: "healthy" as const },
  stable: { icon: Minus, label: "Stable", tone: "neutral" as const },
}

/** loss_gap_pct can be very large (e.g. 2140%) when train_loss is near zero — cap the *displayed* value, not the underlying number (Integration Guide §4). */
function formatLossGapPct(pct: number): string {
  return pct > 999 ? "999%+" : `${pct.toFixed(0)}%`
}

/**
 * Trend arrow + gap value (Architecture §12 — iconography, not a
 * fabricated chart).
 */
export function GapCard({ gap, totalEpochs }: GapCardProps) {
  const { icon: Icon, label, tone } = trendConfig[gap.trend]
  const insufficientHistory = gap.trend === "stable" && totalEpochs < 4

  return (
    <Card className="p-4">
      <CardHeader className="p-0">
        <CardTitle>Generalization Gap</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 p-0 pt-3">
        <Badge tone={tone} icon={<Icon className="size-3.5" aria-hidden="true" />}>
          {label}
        </Badge>
        {insufficientHistory && (
          <p className="text-xs text-muted-foreground">Not enough epochs yet to call a trend.</p>
        )}
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
          <dt className="text-muted-foreground">Loss gap</dt>
          <dd className="text-right font-mono tabular-nums text-foreground">
            {formatLoss(gap.loss_gap)} ({formatLossGapPct(gap.loss_gap_pct)})
          </dd>
          <dt className="text-muted-foreground">Accuracy gap</dt>
          <dd className="text-right font-mono tabular-nums text-foreground">
            {formatPercent(gap.accuracy_gap)} pts
          </dd>
        </dl>
      </CardContent>
    </Card>
  )
}
