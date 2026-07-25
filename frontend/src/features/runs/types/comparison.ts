import type { RunDiagnostics } from "./run"

/**
 * Mirrors the comparison-response models from FRONTEND_INTEGRATION.md
 * §2 exactly. Unlike `DiagnosisResponse`, this is fully deterministic
 * and cacheable — the same two run IDs always produce the same result
 * (§1 "Important behavioral notes").
 */

export interface ConfigDiffEntry {
    field: string
    run_a_value: number | string | boolean
    run_b_value: number | string | boolean
}

export interface RunComparisonResult {
    run_a_id: string
    run_b_id: string
    run_a_diagnostics: RunDiagnostics
    run_b_diagnostics: RunDiagnostics
    /**
     * Only fields that actually differ. An empty array is a valid,
     * meaningful result ("these runs are configured identically"), not
     * a broken/empty state.
     */
    config_differences: ConfigDiffEntry[]
}