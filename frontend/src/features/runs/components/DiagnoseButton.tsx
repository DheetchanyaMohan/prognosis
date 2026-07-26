import { Loader2, Sparkles } from "lucide-react"
import { Button } from "@/components/ui"

interface DiagnoseButtonProps {
  onClick: () => void
  isPending: boolean
  hasResult: boolean
}

/**
 * Triggers `POST /runs/{id}/diagnose`. Disables itself while pending
 * — this is a real, non-idempotent LLM call (`retry: false` on the
 * mutation itself, per `api/mutations.ts`), so a second click mid-
 * flight would kick off a second, wasted invocation rather than doing
 * anything useful.
 */
export function DiagnoseButton({ onClick, isPending, hasResult }: DiagnoseButtonProps) {
  return (
    <Button onClick={onClick} disabled={isPending}>
      {isPending ? (
        <>
          <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
          Diagnosing…
        </>
      ) : (
        <>
          <Sparkles className="mr-2 size-4" aria-hidden="true" />
          {hasResult ? "Diagnose again" : "Diagnose with AI"}
        </>
      )}
    </Button>
  )
}