import { useState } from "react"

/**
 * Selection state for "pick two runs to compare" (Architecture §7/§8
 * extended for the Compare flow). Deliberately capped at 2 rather than
 * allowing an arbitrary set and letting the Compare action disable
 * itself — a hard cap means the UI can disable the *other* checkboxes
 * once 2 are selected, which is a clearer signal ("you can compare at
 * most 2 at a time") than a silently-ignored click on an
 * enabled-looking checkbox.
 *
 * Pure client-side UI state (Eng. Spec §7) — no query, no cache, no
 * server round-trip. Scoped to wherever it's called (one `RunTable`
 * instance), not lifted to global state.
 */
export function useRunSelection() {
  const [selected, setSelected] = useState<string[]>([])

  const canSelectMore = selected.length < 2
  const isSelected = (runId: string) => selected.includes(runId)

  function toggle(runId: string) {
    setSelected((prev) => {
      if (prev.includes(runId)) return prev.filter((id) => id !== runId)
      if (prev.length >= 2) return prev
      return [...prev, runId]
    })
  }

  function clear() {
    setSelected([])
  }

  return { selected, isSelected, canSelectMore, toggle, clear }
}