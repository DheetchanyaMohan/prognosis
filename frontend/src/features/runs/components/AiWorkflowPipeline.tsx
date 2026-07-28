import type { ReactNode } from "react"
import { CheckCircle2, Circle, Loader2, ArrowDown } from "lucide-react"
import { toUtcDate } from "@/lib/format-date"
import { cn } from "@/lib/utils"
import type { PipelineStage, PipelineStageStatus } from "../utils/agent-workflow"

interface AiWorkflowPipelineProps {
  stages: PipelineStage[]
}

const statusIcon: Record<PipelineStageStatus, ReactNode> = {
  pending: <Circle className="size-4 text-muted-foreground" aria-hidden="true" />,
  active: <Loader2 className="size-4 animate-spin text-foreground" aria-hidden="true" />,
  complete: <CheckCircle2 className="size-4 text-green-600 dark:text-green-400" aria-hidden="true" />,
}

const statusLabel: Record<PipelineStageStatus, string> = {
  pending: "waiting",
  active: "running",
  complete: "completed",
}

/**
 * Visualizes the agent's LangGraph pipeline (Milestone 5 §1, §6).
 * Renders one of two fundamentally different inputs, decided entirely
 * by `agent-workflow.ts`, not by this component:
 *  - conceptual stages (idle/pending) — the pipeline's documented
 *    shape, at most one stage "active"; nothing here is ever
 *    "complete," since there's no real per-stage confirmation until
 *    the request actually returns (no streaming exists).
 *  - trace-derived stages (success) — every stage is "complete"
 *    because it corresponds to a real, returned `TraceEntry`, with
 *    that entry's own timestamp and evidence summary.
 * This keeps the honesty rule enforced in one place (the stage
 * builders) rather than scattered across rendering logic.
 */
export function AiWorkflowPipeline({ stages }: AiWorkflowPipelineProps) {
  return (
    <ol aria-label="Agent workflow steps" className="flex flex-col">
      {stages.map((stage, index) => (
        <li key={stage.key} aria-current={stage.status === "active" ? "step" : undefined}>
          <div className="flex items-start gap-3">
            <div className="flex flex-col items-center pt-0.5">{statusIcon[stage.status]}</div>
            <div className="flex-1 pb-1">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
                <span
                  className={cn(
                    "text-sm",
                    stage.status === "pending" ? "text-muted-foreground" : "font-medium text-foreground",
                  )}
                >
                  {stage.label}
                </span>
                {stage.timestamp && (
                  <span className="font-mono text-xs tabular-nums text-muted-foreground">
                    {toUtcDate(stage.timestamp).toLocaleTimeString()}
                    {stage.deltaLabel ? ` (+${stage.deltaLabel})` : ""}
                  </span>
                )}
              </div>
              {stage.detail && <p className="mt-0.5 text-xs text-muted-foreground">{stage.detail}</p>}
              <span className="sr-only">{statusLabel[stage.status]}</span>
            </div>
          </div>
          {index < stages.length - 1 && (
            <div className="ml-2 flex h-4 items-center">
              <ArrowDown className="size-3 text-border" aria-hidden="true" />
            </div>
          )}
        </li>
      ))}
    </ol>
  )
}