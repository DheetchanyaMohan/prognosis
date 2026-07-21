import { Circle } from "lucide-react"
import { useHealthQuery } from "../api/queries"
import { cn } from "@/lib/utils"

/**
 * Lives only in the nav bar (Architecture §5, §7 "Health"). Quiet by
 * default — a small dot, not a panel. `llm_provider: "not_configured"`
 * is a normal, expected state right now and must never read as an
 * error (Integration Guide §3, §8). Only `status: "degraded"`
 * (database or Chroma reporting "error") should visually stand out.
 */
export function HealthIndicator() {
  const { data, isPending } = useHealthQuery()

  if (isPending || !data) {
    return (
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Circle className="size-2 fill-muted-foreground text-muted-foreground" aria-hidden="true" />
        Checking status
      </span>
    )
  }

  const degraded = data.status === "degraded"

  return (
    <span
      className={cn(
        "flex items-center gap-1.5 text-xs",
        degraded ? "text-red-700 dark:text-red-400" : "text-muted-foreground",
      )}
      title={degraded ? "One or more backend components are reporting an error" : "Backend is healthy"}
    >
      <Circle
        className={cn("size-2", degraded ? "fill-red-600 text-red-600" : "fill-green-600 text-green-600")}
        aria-hidden="true"
      />
      {degraded ? "Degraded" : "Operational"}
    </span>
  )
}
