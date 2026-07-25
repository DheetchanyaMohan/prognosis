import type { RunDiagnostics } from "./run"
import type { RunComparisonResult } from "./comparison"

/**
 * Mirrors the diagnosis-response models from FRONTEND_INTEGRATION.md
 * §2 exactly. This is the richest, and only non-deterministic,
 * response in the API — two identical requests can return different
 * hypotheses/recommendations, since it's a real LLM invocation
 * (§1 "Important behavioral notes").
 */

export interface ChunkMetadata {
  source: string
  source_type: "knowledge_base" | "run_summary"
  chunk_index: number
  section_title: string | null
  /** Present only for run_summary chunks. */
  run_id: string | null
}

export interface RetrievedChunk {
  chunk_id: string
  text: string
  /** Cosine similarity: 1.0 = identical, -1.0 = opposite. */
  score: number
  metadata: ChunkMetadata
}

export interface Hypothesis {
  title: string
  explanation: string
  /** At most 3 items. */
  supporting_evidence: string[]
  /** 0.0–1.0 */
  confidence: number
}

export type EffortLevel = "low" | "medium" | "high"

export interface Recommendation {
  title: string
  rationale: string
  supporting_evidence: string[]
  expected_benefit: string
  estimated_effort: EffortLevel
  /** 0.0–1.0 */
  confidence: number
  /** Traceable evidence sources — always render these, never hide behind a "details" toggle. */
  provenance: string[]
  /**
   * Set by `self_check`, never by the LLM itself — the one field that
   * proves the system checked its own work rather than just
   * asserting an answer. Always render as a visible badge, per
   * FRONTEND_INTEGRATION.md §1: "✓ Grounded" / "⚠ Needs review".
   */
  is_grounded: boolean
}

export interface TraceEntry {
  /** e.g. "router", "retrieve_context", "self_check". */
  node: string
  /** Fully-qualified tool names, e.g. "metrics_tool.analyze_run". */
  tools_called: string[]
  /** Why this node did what it did, in plain language. */
  reasoning: string
  /** Concrete description of what this step produced. */
  evidence_summary: string
  timestamp: string
}

/**
 * The flattened, tool-layer config view the agent uses — a distinct
 * shape from `RunConfig` (the grouped dataset/model/training view the
 * rest of the app renders), not a duplicate to reconcile.
 */
export interface RunConfigSummary {
  train_size: number
  val_size: number
  augmentation: boolean
  dropout: number
  optimizer: string
  lr: number
  lr_scheduler: string
  batch_size: number
  weight_decay: number
  epochs: number
}

export interface RunSummaryView {
  run_id: string
  experiment_name: string
  status: string
  created_at: string
  config: RunConfigSummary
  diagnostics: RunDiagnostics
}

export type RequestType = "diagnose_run" | "compare_runs" | "general_question"

export interface DiagnoseRequest {
  /** Omit entirely, or send `{}`, for the default diagnostic query. */
  query?: string | null
}

export interface DiagnosisResponse {
  run_id: string
  generated_at: string

  user_query: string
  request_type: RequestType
  selected_run: string | null
  comparison_run: string | null

  retrieved_knowledge: RetrievedChunk[]
  similar_runs: RetrievedChunk[]

  /** Present when request_type needed it — null is not an error. */
  diagnostics: RunDiagnostics | null
  /** Present when request_type === "diagnose_run". */
  run_summary: RunSummaryView | null
  /** Present when request_type === "compare_runs". */
  comparison: RunComparisonResult | null

  /** Can be empty for a general_question — not an error. */
  hypotheses: Hypothesis[]
  recommendations: Recommendation[]

  retry_count: number
  /** Always false once the response is returned. */
  needs_more_evidence: boolean

  /** Ordered exactly as the nodes executed — safe to render as a literal step-by-step list. */
  trace: TraceEntry[]
}