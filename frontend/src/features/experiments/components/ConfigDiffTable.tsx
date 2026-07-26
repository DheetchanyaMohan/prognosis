import { EmptyState } from "@/components/ui"
import type { ConfigDiffEntry } from "../types"

interface ConfigDiffTableProps {
  differences: ConfigDiffEntry[]
}

/**
 * A real `<table>` — unlike the run list (which uses link-rows for
 * keyboard-navigation reasons), this has no per-row navigation, so
 * semantic table markup is both correct and more accessible here.
 *
 * An empty `differences` array means "these runs are configured
 * identically" — a valid, meaningful result (mirrors the precedent
 * set by `instability.spike_epochs: []`), rendered as a reassuring
 * empty state, never as a broken/missing-data one.
 */
export function ConfigDiffTable({ differences }: ConfigDiffTableProps) {
  if (differences.length === 0) {
    return (
      <EmptyState
        title="Configurations are identical"
        message="No hyperparameter differences were found between these two runs."
      />
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-secondary/50 text-xs text-muted-foreground">
          <tr>
            <th scope="col" className="px-4 py-2 text-left font-medium">
              Field
            </th>
            <th scope="col" className="px-4 py-2 text-left font-medium">
              Run A
            </th>
            <th scope="col" className="px-4 py-2 text-left font-medium">
              Run B
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {differences.map((diff) => (
            <tr key={diff.field}>
              <td className="px-4 py-2 text-muted-foreground">{diff.field}</td>
              <td className="px-4 py-2 font-mono text-foreground">{String(diff.run_a_value)}</td>
              <td className="px-4 py-2 font-mono text-foreground">{String(diff.run_b_value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}