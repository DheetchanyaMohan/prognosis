import { MousePointerClick, Sparkles, GitCompare } from "lucide-react"
import { Card } from "@/components/ui"

const ACTIONS = [
  { icon: MousePointerClick, text: "Click a run to inspect its training details and diagnostics." },
  { icon: Sparkles, text: "Click \"Diagnose with AI\" inside a run for grounded, evidence-backed recommendations." },
  { icon: GitCompare, text: "Select two runs with the checkboxes to compare them side by side." },
]

/**
 * Static, always-visible orientation for a first-time visitor to an
 * experiment (Milestone 6 §7). Doesn't depend on any request state —
 * purely descriptive, same spirit as `AgentCards` on the Run Detail
 * page.
 */
export function QuickActionsPanel() {
  return (
    <Card className="p-4">
      <h3 className="mb-2 text-sm font-medium text-foreground">Quick Actions</h3>
      <ul className="flex flex-col gap-2">
        {ACTIONS.map(({ icon: Icon, text }) => (
          <li key={text} className="flex items-start gap-2 text-sm text-muted-foreground">
            <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            <span>{text}</span>
          </li>
        ))}
      </ul>
    </Card>
  )
}