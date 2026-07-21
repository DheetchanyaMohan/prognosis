import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  /** The value itself — rendered in monospace (Architecture §19: data, not prose). */
  value: ReactNode
  sublabel?: string
  flag?: ReactNode
  className?: string
}

/**
 * Typographic emphasis (size/weight), not chart-junk. Used for best
 * epoch, final losses/accuracies, wall-clock time — anywhere a single
 * honest number is the whole story (Architecture §12).
 */
export function StatCard({ label, value, sublabel, flag, className }: StatCardProps) {
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">{label}</span>
        {flag}
      </div>
      <span className="font-mono text-lg font-semibold text-foreground tabular-nums">
        {value}
      </span>
      {sublabel && <span className="text-xs text-muted-foreground">{sublabel}</span>}
    </div>
  )
}
