import { StatusBadge } from "./StatusBadge"
import type { RunStatusFlag } from "../utils/deriveRunStatus"

interface RunHeaderBandProps {
  runId: string
  statusFlags: RunStatusFlag[]
}

/**
 * Header band of the Run Detail "diagnosis report" (Architecture
 * §7.1): run ID as `h1`, then the single large multi-flag
 * StatusBadge — the one thing a recruiter's 90-second glance needs
 * to land on.
 */
export function RunHeaderBand({ runId, statusFlags }: RunHeaderBandProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <h1 className="font-mono text-xl font-semibold text-foreground">{runId}</h1>
      <StatusBadge flags={statusFlags} />
    </div>
  )
}
