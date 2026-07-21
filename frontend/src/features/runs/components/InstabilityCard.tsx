import { Zap, ShieldCheck } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui"
import type { InstabilityDiagnostic } from "../types"

interface InstabilityCardProps {
  instability: InstabilityDiagnostic
}

/**
 * Jagged-line icon (Architecture §12). An empty `spike_epochs` array
 * is a *good* result (no instability found) — rendered as reassuring,
 * not blank (Architecture §13).
 */
export function InstabilityCard({ instability }: InstabilityCardProps) {
  const hasSpikes = instability.spike_epochs.length > 0

  return (
    <Card className="p-4">
      <CardHeader className="p-0">
        <CardTitle>Instability</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 p-0 pt-3">
        <Badge
          tone={instability.is_unstable ? "concern" : "healthy"}
          icon={
            instability.is_unstable ? (
              <Zap className="size-3.5" aria-hidden="true" />
            ) : (
              <ShieldCheck className="size-3.5" aria-hidden="true" />
            )
          }
        >
          {instability.is_unstable ? "Unstable" : "No instability found"}
        </Badge>
        <p className="text-xs text-muted-foreground">
          {hasSpikes
            ? `Spikes at epoch${instability.spike_epochs.length > 1 ? "s" : ""}: ${instability.spike_epochs.join(", ")}`
            : `Coefficient of variation: ${instability.coefficient_of_variation.toFixed(3)}`}
        </p>
      </CardContent>
    </Card>
  )
}
