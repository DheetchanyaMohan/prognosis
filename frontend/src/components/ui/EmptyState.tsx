import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  message?: string
  action?: ReactNode
  /** Full-page centering for a zero-experiments landing (§13) vs. an inline section (zero-runs). */
  variant?: "page" | "inline"
  className?: string
}

/**
 * A deliberately explained empty state, never a blank list. Zero
 * experiments and zero runs are both valid, normal conditions
 * (Architecture §13), not errors — this component's job is to say so.
 */
export function EmptyState({
  icon,
  title,
  message,
  action,
  variant = "inline",
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2 text-center",
        variant === "page" ? "py-24" : "py-12",
        className,
      )}
    >
      {icon && <div className="mb-1 text-muted-foreground">{icon}</div>}
      <p className="text-sm font-medium text-foreground">{title}</p>
      {message && <p className="max-w-sm text-sm text-muted-foreground">{message}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
