import type { ReactNode } from "react"
import { FileQuestion, WifiOff, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

export type ErrorStateVariant = "not-found" | "network" | "generic"

interface ErrorStateProps {
  variant: ErrorStateVariant
  title?: string
  message?: string
  action?: ReactNode
  className?: string
}

const variantConfig: Record<ErrorStateVariant, { icon: ReactNode; title: string; message: string }> = {
  "not-found": {
    icon: <FileQuestion className="size-8" aria-hidden="true" />,
    title: "This page doesn't exist",
    message: "It may have been removed, or the link might be out of date.",
  },
  network: {
    icon: <WifiOff className="size-8" aria-hidden="true" />,
    title: "Can't reach the server",
    message: "Check that the backend is running and reachable, then try again.",
  },
  generic: {
    icon: <AlertTriangle className="size-8" aria-hidden="true" />,
    title: "Something went wrong",
    message: "Please try again. If this keeps happening, it's worth reporting.",
  },
}

/**
 * 404, network failure, and unexpected 500 are visually and
 * textually distinct (Architecture §15) so users don't conflate
 * "wrong URL" with "backend is down." Never used for
 * `summary`/`diagnostics: null` — that's PendingCard's job.
 */
export function ErrorState({ variant, title, message, action, className }: ErrorStateProps) {
  const config = variantConfig[variant]
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2 py-16 text-center text-muted-foreground",
        className,
      )}
    >
      {config.icon}
      <p className="mt-1 text-sm font-medium text-foreground">{title ?? config.title}</p>
      <p className="max-w-sm text-sm">{message ?? config.message}</p>
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
