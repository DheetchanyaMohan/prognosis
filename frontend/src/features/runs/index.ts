/**
 * Public API of the "runs" feature. Other features and `app/` must
 * import only from here (`@/features/runs`), never from a deeper
 * path like `@/features/runs/api/queries` or
 * `@/features/runs/hooks/useRunDetail` — see ADR-002. This is what
 * makes `features/experiments`'s `RunTable`/`RunRow` calling into
 * `runs` a sanctioned cross-feature dependency rather than a
 * violation: it goes through this barrel.
 *
 * `StatusBadge` is re-exported deliberately (ADR-002's "add here
 * deliberately if another feature ever needs one"): `RunRow` renders
 * the exact same status presentation as `RunHeaderBand`, so it reuses
 * this component rather than re-implementing flag→tone/icon mapping.
 * Other `runs/components` (GapCard, ConfigPanel, etc.) stay
 * un-exported since only `app/pages/RunDetailPage` consumes them
 * directly today.
 */
export * from "./types"
export * from "./api/queries"
export * from "./api/mutations"
export * from "./hooks/useRunDetail"
export * from "./hooks/useRunComparison"
export * from "./utils/deriveRunStatus"
export * from "./utils/format-run-stats"
export * from "./components/StatusBadge"