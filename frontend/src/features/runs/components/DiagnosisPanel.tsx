import { PendingCard } from "@/components/ui"
import { GapCard } from "./GapCard"
import { PlateauCard } from "./PlateauCard"
import { InstabilityCard } from "./InstabilityCard"
import { BestEpochCard } from "./BestEpochCard"
import type { RunDiagnostics } from "../types"

interface DiagnosisPanelProps {
  diagnostics: RunDiagnostics | null
  /** Drives the "checking again shortly" aria-live indicator while diagnostics is still null. */
  isPolling: boolean
}

/**
 * Architecture §7.2: three cards side by side on desktop, stacked on
 * mobile (GapCard, PlateauCard, InstabilityCard), plus a quieter
 * BestEpochCard. If `diagnostics` is `null`, render a single
 * "Analysis pending" PendingCard instead — never four empty/greyed
 * cards, that reads as broken rather than pending.
 */
export function DiagnosisPanel({ diagnostics, isPolling }: DiagnosisPanelProps) {
  if (!diagnostics) {
    return (
      <PendingCard
        title="Analysis pending"
        message="Diagnostics will appear once this run has enough training history."
        polling={isPolling}
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <GapCard gap={diagnostics.generalization_gap} totalEpochs={diagnostics.total_epochs} />
        <PlateauCard plateau={diagnostics.plateau} />
        <InstabilityCard instability={diagnostics.instability} />
      </div>
      <BestEpochCard bestEpoch={diagnostics.best_epoch} />
    </div>
  )
}
