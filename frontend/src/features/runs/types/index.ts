/**
 * Barrel for the "runs" feature's types. Split across three files as
 * FRONTEND_INTEGRATION.md's type surface grew (config/summary/
 * diagnostics in `run.ts`, the agent's diagnosis response in
 * `diagnosis.ts`, the deterministic comparison response in
 * `comparison.ts`) — this file re-exports all three so every existing
 * `from "../types"` import within the feature keeps working unchanged.
 */
export * from "./run"
export * from "./diagnosis"
export * from "./comparison"