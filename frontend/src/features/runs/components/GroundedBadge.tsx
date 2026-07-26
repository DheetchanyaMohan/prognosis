import { ShieldCheck, ShieldAlert } from "lucide-react"
import { Badge } from "@/components/ui"

interface GroundedBadgeProps {
  isGrounded: boolean
}

/**
 * Set by `self_check`, never by the LLM itself — the one field that
 * proves the system checked its own work rather than just asserting
 * an answer (FRONTEND_INTEGRATION.md §1, §2). This is called out
 * explicitly as one of the project's key trust features, so it's
 * rendered larger and bolder than a standard `Badge` usage elsewhere
 * in the app (e.g. `ConfigPanel`'s optimizer/scheduler badges) —
 * deliberately, not an oversight — while still going through the same
 * shared primitive and semantic tone system (Architecture §20), never
 * color alone (Accessibility §17: icon + tone + text label together).
 */
export function GroundedBadge({ isGrounded }: GroundedBadgeProps) {
  return isGrounded ? (
    <Badge
      tone="healthy"
      icon={<ShieldCheck className="size-4" aria-hidden="true" />}
      className="px-3 py-1 text-sm font-semibold"
    >
      Grounded
    </Badge>
  ) : (
    <Badge
      tone="caution"
      icon={<ShieldAlert className="size-4" aria-hidden="true" />}
      className="px-3 py-1 text-sm font-semibold"
    >
      Needs review
    </Badge>
  )
}