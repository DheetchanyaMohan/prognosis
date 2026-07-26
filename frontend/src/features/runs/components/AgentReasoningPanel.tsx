import { useState } from "react"
import { ChevronRight } from "lucide-react"
import { Card } from "@/components/ui"
import { cn } from "@/lib/utils"
import { toUtcDate } from "@/lib/format-date"
import type { TraceEntry } from "../types"

interface AgentReasoningPanelProps {
  trace: TraceEntry[]
}

/**
 * Renamed from "Trace" to "Agent Reasoning" for a general audience —
 * still displays the same underlying `TraceEntry` data, just under
 * friendlier framing. Collapsed by default: this is secondary,
 * technical-audience material (mirrors Product Architecture §11's
 * "based on: ..." provenance-trail philosophy) that must never
 * compete visually with hypotheses/recommendations, the primary
 * findings.
 */
export function AgentReasoningPanel({ trace }: AgentReasoningPanelProps) {
  const [expanded, setExpanded] = useState(false)

  if (trace.length === 0) {
    return null
  }

  return (
    <Card className="p-4">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center justify-between gap-2 text-left"
        aria-expanded={expanded}
      >
        <span className="text-sm font-medium text-foreground">Agent Reasoning</span>
        <ChevronRight
          className={cn("size-4 text-muted-foreground transition-transform", expanded && "rotate-90")}
          aria-hidden="true"
        />
      </button>

      {expanded && (
        <ol className="mt-3 flex flex-col gap-3 border-t border-border pt-3">
          {trace.map((entry, index) => (
            <li key={index} className="text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-medium text-foreground">{entry.node}</span>
                <span className="text-xs text-muted-foreground">
                  {toUtcDate(entry.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{entry.reasoning}</p>
              {entry.tools_called.length > 0 && (
                <p className="mt-1 font-mono text-xs text-muted-foreground">
                  Tools: {entry.tools_called.join(", ")}
                </p>
              )}
              <p className="mt-1 text-xs text-muted-foreground">{entry.evidence_summary}</p>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}