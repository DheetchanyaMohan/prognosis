import { StatusBadge } from "./StatusBadge"
import { GapCard } from "./GapCard"
import { PlateauCard } from "./PlateauCard"
import { InstabilityCard } from "./InstabilityCard"
import { BestEpochCard } from "./BestEpochCard"
import { deriveRunStatus } from "../utils/deriveRunStatus"
import type { RunDiagnostics } from "../types"

interface ComparisonDiagnosticsGridProps {
  runAId: string
  runBId: string
  runADiagnostics: RunDiagnostics
  runBDiagnostics: RunDiagnostics
}

function RunColumnHeader({ runId, diagnostics }: { runId: string; diagnostics: RunDiagnostics }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="font-mono text-sm font-medium text-foreground">{runId}</span>
      <StatusBadge flags={deriveRunStatus(diagnostics)} />
    </div>
  )
}

/**
 * A genuine side-by-side comparison, not two independent
 * `DiagnosisPanel`s stacked with no relationship to each other: every
 * metric (Generalization Gap, Plateau, Instability, Best Epoch) is its
 * own row with Run A's and Run B's cards directly adjacent, so a
 * left-right glance compares like-for-like without hunting across two
 * separate panels. The two `StatusBadge`s at the top give the
 * fastest possible signal before any per-metric detail.
 *
 * Reuses `GapCard`/`PlateauCard`/`InstabilityCard`/`BestEpochCard`
 * completely unmodified (each already carries its own metric title,
 * so it repeats once per column — an acceptable, common comparison-UI
 * pattern, and far preferable to touching four already-shipped,
 * tested components for a purely cosmetic dedupe).
 */
export function ComparisonDiagnosticsGrid({
  runAId,
  runBId,
  runADiagnostics,
  runBDiagnostics,
}: ComparisonDiagnosticsGridProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <RunColumnHeader runId={runAId} diagnostics={runADiagnostics} />
        <RunColumnHeader runId={runBId} diagnostics={runBDiagnostics} />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <GapCard gap={runADiagnostics.generalization_gap} totalEpochs={runADiagnostics.total_epochs} />
        <GapCard gap={runBDiagnostics.generalization_gap} totalEpochs={runBDiagnostics.total_epochs} />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <PlateauCard plateau={runADiagnostics.plateau} />
        <PlateauCard plateau={runBDiagnostics.plateau} />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <InstabilityCard instability={runADiagnostics.instability} />
        <InstabilityCard instability={runBDiagnostics.instability} />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <BestEpochCard bestEpoch={runADiagnostics.best_epoch} />
        <BestEpochCard bestEpoch={runBDiagnostics.best_epoch} />
      </div>
    </div>
  )
}