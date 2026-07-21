import { Minus, Activity, Hourglass } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui"
import type { PlateauDiagnostic } from "../types"

interface PlateauCardProps {
  plateau: PlateauDiagnostic
}

/**
 * Flat-line icon (Architecture §12). Three distinct states, not two:
 * plateaued, not plateaued, and `insufficient_data` — "not enough
 * data yet," never treated as "no plateau" (Integration Guide §4).
 */
export function PlateauCard({ plateau }: PlateauCardProps) {
  let icon = <Activity className="size-3.5" aria-hidden="true" />
  let label = "Not plateaued"
  let tone: "healthy" | "caution" | "neutral" = "healthy"
  let detail = `Observed range: ${plateau.observed_range?.toFixed(3) ?? "—"}`

  if (plateau.insufficient_data) {
    icon = <Hourglass className="size-3.5" aria-hidden="true" />
    label = "Not enough data yet"
    tone = "neutral"
    detail = `Needs ${plateau.window} epochs of history`
  } else if (plateau.plateaued) {
    icon = <Minus className="size-3.5" aria-hidden="true" />
    label = "Plateaued"
    tone = "caution"
    detail = plateau.plateau_start_epoch != null ? `Since epoch ${plateau.plateau_start_epoch}` : detail
  }

  return (
    <Card className="p-4">
      <CardHeader className="p-0">
        <CardTitle>Plateau</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 p-0 pt-3">
        <Badge tone={tone} icon={icon}>
          {label}
        </Badge>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  )
}
