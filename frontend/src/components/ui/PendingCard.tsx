import { Loader2 } from "lucide-react"
import { Card } from "./Card"
import { cn } from "@/lib/utils"

interface PendingCardProps {
  title: string
  message?: string
  /**
   * Set while this section is being background-polled (Architecture
   * §14 "checking again shortly"). Renders an aria-live="polite"
   * region so a screen-reader user is told when the data arrives —
   * never a spinner implying the whole page is loading.
   */
  polling?: boolean
  className?: string
}

/**
 * Reused everywhere `summary`/`diagnostics` might be `null`
 * (Architecture §8, §13). This is a normal, expected state — framed
 * with calm, reassurance copy, never as an error or missing-data
 * warning.
 */
export function PendingCard({ title, message, polling, className }: PendingCardProps) {
  return (
    <Card className={cn("p-6 text-center", className)}>
      <p className="text-sm font-medium text-foreground">{title}</p>
      {message && <p className="mt-1 text-sm text-muted-foreground">{message}</p>}
      {polling && (
        <div
          aria-live="polite"
          className="mt-3 flex items-center justify-center gap-2 text-xs text-muted-foreground"
        >
          <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
          <span>Checking again shortly</span>
        </div>
      )}
    </Card>
  )
}
