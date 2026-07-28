import { useNavigate } from "react-router-dom"
import { EmptyState } from "@/components/ui"
import { RunRow } from "./RunRow"
import { CompareBar } from "./CompareBar"
import { useRunSelection } from "../hooks/useRunSelection"

interface RunTableProps {
  experimentId: string
  runIds: string[]
}

/**
 * Architecture §7/§8: one row per `run_id` from `experiment.run_ids`.
 * Each `RunRow` self-fetches via `useRunQuery(runId)` and upgrades in
 * place. This is the N+1 fetch pattern documented in Integration
 * Guide §7/§9: real, currently-unavoidable, not a bug to "optimize
 * away."
 *
 * Compare selection: every row always shows a checkbox (no separate
 * "Compare Mode" toggle). Selection state is owned right here —
 * nothing outside this component's single `RunTable` instance needs
 * to read or write it, so it stays local rather than lifted to
 * `ExperimentDetailPage` or global state.
 *
 * Zero runs is valid, not broken (Architecture §13) — an inline
 * "No runs yet" state, not a blank list.
 */
export function RunTable({ experimentId, runIds }: RunTableProps) {
  const { selected, isSelected, canSelectMore, toggle, clear } = useRunSelection()
  const navigate = useNavigate()

  if (runIds.length === 0) {
    return (
      <EmptyState
        title="No runs yet for this experiment"
        message="Runs will appear here once training has started."
      />
    )
  }

  const [runAId, runBId] = selected

  return (
    <div className="flex flex-col gap-2">
      {selected.length === 2 && (
        <CompareBar
          runAId={runAId}
          runBId={runBId}
          onClear={clear}
          onCompare={() =>
            navigate(`/compare/${encodeURIComponent(runAId)}/${encodeURIComponent(runBId)}`)
          }
        />
      )}

      {runIds.map((runId) => (
        <RunRow
          key={runId}
          experimentId={experimentId}
          runId={runId}
          selected={isSelected(runId)}
          selectDisabled={!canSelectMore && !isSelected(runId)}
          onToggleSelect={() => toggle(runId)}
        />
      ))}
    </div>
  )
}