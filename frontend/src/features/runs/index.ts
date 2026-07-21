/**
 * Public API of the "runs" feature. Other features and `app/` must
 * import only from here (`@/features/runs`), never from a deeper
 * path like `@/features/runs/api/queries` or
 * `@/features/runs/hooks/useRunDetail` — see ADR-002. This is what
 * makes `features/experiments`'s `RunTable` calling into `runs` a
 * sanctioned cross-feature dependency rather than a violation: it
 * goes through this barrel.
 */
export * from "./types"
export * from "./api/queries"
export * from "./hooks/useRunDetail"
export * from "./utils/deriveRunStatus"
