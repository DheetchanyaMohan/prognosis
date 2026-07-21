import type { RunDiagnostics } from "../types"

/**
 * The status flags a run can carry simultaneously (Architecture §10).
 * "pending" applies only when `diagnostics` itself is `null`;
 * otherwise zero or more of the other flags can co-occur (e.g.
 * unstable *and* overfitting) — the UI must support a multi-flag
 * badge, never a single forced verdict.
 */
export type RunStatusFlag = "overfitting" | "stalled" | "unstable" | "healthy" | "pending"

/**
 * Derives the set of status flags for a run's `StatusBadge` from its
 * diagnostics, per the exact rules in Architecture §10:
 *
 *   overfitting  ⇐ generalization_gap.trend === "widening"
 *   stalled      ⇐ plateau.plateaued === true AND trend !== "widening"
 *   unstable     ⇐ instability.is_unstable === true
 *   healthy      ⇐ none of the above, diagnostics present
 *   pending      ⇐ diagnostics === null
 *
 * This is presentation logic derived client-side, not a new backend
 * field (Architecture §10) — it never mutates or re-labels the
 * underlying diagnostic data.
 */
export function deriveRunStatus(diagnostics: RunDiagnostics | null): RunStatusFlag[] {
  if (!diagnostics) return ["pending"]

  const isWidening = diagnostics.generalization_gap.trend === "widening"
  const flags: RunStatusFlag[] = []

  if (isWidening) flags.push("overfitting")
  if (diagnostics.plateau.plateaued && !isWidening) flags.push("stalled")
  if (diagnostics.instability.is_unstable) flags.push("unstable")

  if (flags.length === 0) flags.push("healthy")

  return flags
}
