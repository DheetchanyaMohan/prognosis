/**
 * Public API of the "health" feature. Other features and `app/` must
 * import only from here (`@/features/health`), never from a deeper
 * path like `@/features/health/api/queries` — see ADR-002. This
 * barrel currently exposes types + queries; add components here
 * deliberately if another feature ever needs one.
 */
export * from "./types"
export * from "./api/queries"
