import { Card, CardHeader, CardTitle, CardContent, StatCard } from "@/components/ui"
import { formatLoss, formatPercent } from "../utils/format-run-stats"
import type { BestEpochDiagnostic } from "../types"

interface BestEpochCardProps {
  bestEpoch: BestEpochDiagnostic
}

/**
 * Quieter than the other three (Architecture §7.2) — a StatCard-style
 * typographic callout, not a flagged concern. Uses
 * `diagnostics.best_epoch` rather than `summary`'s duplicate fields,
 * per Integration Guide §4's "prefer diagnostics.best_epoch if you
 * only want one source."
 */
export function BestEpochCard({ bestEpoch }: BestEpochCardProps) {
  return (
    <Card className="p-4">
      <CardHeader className="p-0">
        <CardTitle>Best Epoch</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 p-0 pt-3">
        <StatCard label="Epoch" value={bestEpoch.epoch} />
        <StatCard label="Val loss" value={formatLoss(bestEpoch.val_loss)} />
        <StatCard label="Val acc" value={`${formatPercent(bestEpoch.val_acc)}%`} />
        <StatCard label="Train acc" value={`${formatPercent(bestEpoch.train_acc)}%`} />
      </CardContent>
    </Card>
  )
}
