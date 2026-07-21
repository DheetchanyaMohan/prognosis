import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

/**
 * The four semantic tones are reserved exclusively for run-health/
 * diagnosis communication (Product Architecture §20) — they must not
 * be reused elsewhere in the product (e.g. a delete button, a save
 * toast), or they stop working as a fast, trustworthy visual signal.
 * "neutral" is the only tone safe to use outside a diagnosis context.
 */
export type BadgeTone = "neutral" | "healthy" | "caution" | "concern" | "informational"

const toneClasses: Record<BadgeTone, string> = {
  neutral: "bg-secondary text-secondary-foreground border-border",
  healthy: "bg-green-50 text-green-800 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-900",
  caution: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-900",
  concern: "bg-red-50 text-red-800 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-900",
  informational: "bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-900",
}

interface BadgeProps {
  tone?: BadgeTone
  /** Icon element (e.g. from lucide-react) — required alongside color + label, never color alone. */
  icon?: ReactNode
  children: ReactNode
  className?: string
}

export function Badge({ tone = "neutral", icon, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        toneClasses[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  )
}
