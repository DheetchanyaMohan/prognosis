/**
 * Mirrors the nested models returned by GET /api/v1/runs/{runId}
 * exactly (Frontend Integration Guide §3, §4). These three top-level
 * fields load independently in the UI: `config` is always present;
 * `summary` and `diagnostics` are nullable until a run finishes
 * training/analysis.
 */

// ---- config (always present) ----------------------------------------

export interface RunDatasetConfig {
  train_size: number
  val_size: number
  augmentation: boolean
}

export interface RunModelConfig {
  dropout: number
}

export interface RunTrainingConfig {
  optimizer: "adam" | "sgd"
  lr: number
  lr_scheduler: "none" | "cosine" | "step"
  batch_size: number
  weight_decay: number
  epochs: number
  /** `null` means gradient clipping is disabled — display as "disabled", not "0"/"N/A". */
  gradient_clip_norm: number | null
  early_stop_on_divergence: boolean
  divergence_loss_threshold: number
}

export interface RunConfig {
  run_id: string
  experiment_name: string
  seed: number
  /** Human-authored, max 280 chars. Never contains a ground-truth pathology label. */
  description: string
  dataset: RunDatasetConfig
  model: RunModelConfig
  training: RunTrainingConfig
}

// ---- summary (nullable) ----------------------------------------------

export interface RunSummaryResponse {
  run_id: string
  total_epochs_completed: number
  best_epoch: number
  best_val_loss: number
  final_train_loss: number
  final_val_loss: number
  /** In [0, 1] — the backend does not multiply by 100 for you. */
  final_train_acc: number
  final_val_acc: number
  wall_clock_sec: number
  diverged: boolean
  /** Full-sentence, human-readable prose — safe to render directly. */
  description: string
}

// ---- diagnostics (nullable) -------------------------------------------

export interface GeneralizationGap {
  epoch: number
  train_loss: number
  val_loss: number
  loss_gap: number
  /** Can be very large when train_loss is near zero — don't assume 0–100. */
  loss_gap_pct: number
  train_acc: number
  val_acc: number
  /** train_acc - val_acc; positive means overfitting-direction. */
  accuracy_gap: number
  /**
   * "stable" is also returned when there's insufficient history
   * (<4 epochs) to call a trend — don't over-interpret it as
   * "healthy" without also checking `total_epochs`.
   */
  trend: "widening" | "narrowing" | "stable"
}

export interface PlateauDiagnostic {
  metric: string
  window: number
  threshold: number
  plateaued: boolean
  /** `null` whenever `plateaued` is false or `insufficient_data` is true. */
  plateau_start_epoch: number | null
  /** `null` only when `insufficient_data` is true. */
  observed_range: number | null
  /** True when the run has fewer epochs than the analysis window (5). */
  insufficient_data: boolean
}

export interface InstabilityDiagnostic {
  metric: string
  spike_relative_threshold: number
  coefficient_of_variation_threshold: number
  is_unstable: boolean
  /** Can legitimately be an empty array — that's a *good* result, not missing data. */
  spike_epochs: number[]
  coefficient_of_variation: number
}

export interface BestEpochDiagnostic {
  epoch: number
  val_loss: number
  train_loss: number
  val_acc: number
  train_acc: number
}

export interface RunDiagnostics {
  run_id: string
  total_epochs: number
  generalization_gap: GeneralizationGap
  plateau: PlateauDiagnostic
  instability: InstabilityDiagnostic
  best_epoch: BestEpochDiagnostic
}

// ---- top-level response -----------------------------------------------

export interface RunDetailResponse {
  run_id: string
  config: RunConfig
  summary: RunSummaryResponse | null
  diagnostics: RunDiagnostics | null
}