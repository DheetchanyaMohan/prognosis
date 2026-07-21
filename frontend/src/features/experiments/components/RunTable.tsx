interface RunTableProps {
  experimentId: string
  runIds: string[]
}

/**
 * Architecture §7/§8: one row per `run_id` from `experiment.run_ids`.
 * Each `RunRow` self-fetches via `useRunQuery(runId)` and upgrades in
 * place (subtle shimmer on just the status/number cells, not the
 * whole row — the run ID itself is already known). This is the N+1
 * fetch pattern documented in Integration Guide §7/§9: real,
 * currently-unavoidable, not a bug to "optimize away."
 *
 * Zero runs is valid, not broken — "No runs yet for this experiment."
 *
 * TODO: implement RunRow and this table.
 */
export function RunTable({ experimentId: _experimentId, runIds: _runIds }: RunTableProps) {
  return null
}
