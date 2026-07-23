import { EmptyState } from "@/components/ui"
import { RunRow } from "./RunRow"

interface RunTableProps {
  experimentId: string
  runIds: string[]
}

/**
 * Architecture §7/§8: one row per `run_id` from `experiment.run_ids`.
 * Each `RunRow` self-fetches via `useRunQuery(runId)` and upgrades in
 * place (subtle shimmer on just the status/number cells, not the
 * whole row). This is the N+1 fetch pattern documented in Integration
 * Guide §7/§9: real, currently-unavoidable, not a bug to "optimize
 * away."
 *
 * Zero runs is valid, not broken (Architecture §13) — an inline
 * "No runs yet" state, not a blank list.
 */
export function RunTable({ experimentId, runIds }: RunTableProps) {
  if (runIds.length === 0) {
    return (
      <EmptyState
        title="No runs yet for this experiment"
        message="Runs will appear here once training has started."
      />
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {runIds.map((runId) => (
        <RunRow key={runId} experimentId={experimentId} runId={runId} />
      ))}
    </div>
  )
}
