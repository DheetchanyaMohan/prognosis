import type { HTMLAttributes } from "react"
import { cn } from "@/lib/utils"

/**
 * Generic shimmer block (Architecture §14: skeletons over spinners).
 * Feature skeletons (e.g. ExperimentCardSkeleton) compose this into
 * their own final-layout dimensions rather than each hand-rolling
 * `animate-pulse` classes.
 */
export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded bg-muted", className)} {...props} />
}
