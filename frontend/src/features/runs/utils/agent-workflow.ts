import { toUtcDate } from "@/lib/format-date"
import type { TraceEntry } from "../types"

/**
 * Curated friendly labels for the LangGraph node names described in
 * FRONTEND_INTEGRATION.md's agent graph. `TraceEntry.node` is typed
 * as a plain `string` — the backend does not constrain it to a fixed
 * enum — so an unrecognized node name falls back to a readable
 * transform of the real string rather than being hidden or replaced
 * with something invented.
 *
 * Wording is kept identical to the Architecture page and Home page's
 * own workflow diagrams wherever they describe the same concept
 * ("Knowledge Retrieval", "Grounded Recommendations", "Diagnosis") —
 * a direct requirement so a reader recognizes these as the same
 * workflow shown from a different angle, not two different systems.
 */
const NODE_LABELS: Record<string, string> = {
  router: "Classify Request",
  retrieve_context: "Knowledge Retrieval",
  retrieve_similar_runs: "Similar Run Retrieval",
  analyze_metrics: "Analyze Diagnostics",
  generate_hypotheses: "Generate Hypotheses",
  plan_experiments: "Plan Next Experiments",
  self_check: "Grounded Recommendations",
  finalize: "Diagnosis",
}

export function labelForNode(node: string): string {
  return NODE_LABELS[node] ?? node.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

/**
 * The pipeline's conceptual shape, shown before a real trace exists
 * (idle) and while a diagnosis is in flight (pending). This is a
 * documented fact about how the backend agent is built, not invented
 * fiction — but it is NOT a claim about what has executed for *this*
 * request yet. The moment a real `trace` comes back, `buildTraceStages`
 * replaces it entirely with the actual, provable sequence.
 */
export const CONCEPTUAL_STAGES = [
  "Similar Run Retrieval",
  "Knowledge Retrieval",
  "Analyze Diagnostics",
  "Generate Hypotheses",
  "Grounded Recommendations",
]

export type PipelineStageStatus = "pending" | "active" | "complete"

export interface PipelineStage {
  key: string
  label: string
  status: PipelineStageStatus
  timestamp?: string
  deltaLabel?: string | null
  detail?: string
}

/**
 * Elapsed time between two real trace timestamps, e.g. "2.3s" — a
 * plain computation on genuine data, not a fabricated duration.
 * Returns `null` if the delta can't be trusted (no previous
 * timestamp, or a negative delta from clock skew) rather than
 * displaying something misleading.
 */
export function formatStageDelta(current: string, previous: string | null): string | null {
  if (!previous) return null
  const deltaMs = toUtcDate(current).getTime() - toUtcDate(previous).getTime()
  if (deltaMs < 0) return null
  return deltaMs < 1000 ? `${deltaMs}ms` : `${(deltaMs / 1000).toFixed(1)}s`
}

/**
 * The ONLY function in the app that produces "complete" pipeline
 * stages — and it only ever runs on a real, returned `trace` array,
 * documented as "ordered exactly as the nodes executed." Every stage
 * here corresponds to one real `TraceEntry`; nothing is inferred,
 * padded, or reordered. `detail` comes straight from the backend's
 * own `evidence_summary` for that node, not a client-side guess at
 * what the node produced.
 */
export function buildTraceStages(trace: TraceEntry[]): PipelineStage[] {
  return trace.map((entry, i) => ({
    key: `${entry.node}-${i}`,
    label: labelForNode(entry.node),
    status: "complete",
    timestamp: entry.timestamp,
    deltaLabel: i > 0 ? formatStageDelta(entry.timestamp, trace[i - 1].timestamp) : null,
    detail: entry.evidence_summary,
  }))
}

/**
 * The conceptual (idle/pending) stage list. `activeIndex` is `null`
 * in the idle state (a pure explainer of the pipeline's shape, with
 * nothing highlighted) or a timer-driven index while pending — the
 * same honest mechanism Milestone 3 used for the staged loading
 * messages, now expressed as a pipeline position instead of a
 * standalone string.
 *
 * Stages before AND after the active one render identically
 * ("pending") — earlier stages are deliberately NOT shown as more
 * "done" than later ones, since a timer advancing is not real
 * confirmation of what the backend has actually finished.
 */
export function buildConceptualStages(activeIndex: number | null): PipelineStage[] {
  return CONCEPTUAL_STAGES.map((label, i) => ({
    key: label,
    label,
    status: activeIndex === i ? "active" : "pending",
  }))
}

export interface StageDuration {
  label: string
  /** `null` for the last stage (no subsequent timestamp to measure against) or an untrustworthy (negative) delta. */
  durationMs: number | null
}

/**
 * "Duration of a stage" is derived as the time between this stage's
 * timestamp and the NEXT stage's timestamp — the only honest
 * definition available, since each `TraceEntry` carries a single
 * timestamp, not a start/end pair. The last stage always gets `null`,
 * not a fabricated 0 or an omitted row.
 */
export function computeStageDurations(trace: TraceEntry[]): StageDuration[] {
  return trace.map((entry, i) => {
    const next = trace[i + 1]
    if (!next) return { label: labelForNode(entry.node), durationMs: null }
    const deltaMs = toUtcDate(next.timestamp).getTime() - toUtcDate(entry.timestamp).getTime()
    return { label: labelForNode(entry.node), durationMs: deltaMs >= 0 ? deltaMs : null }
  })
}

/** `null` if there are fewer than 2 trace entries (nothing to measure a span across). */
export function computeTotalDurationMs(trace: TraceEntry[]): number | null {
  if (trace.length < 2) return null
  const deltaMs = toUtcDate(trace[trace.length - 1].timestamp).getTime() - toUtcDate(trace[0].timestamp).getTime()
  return deltaMs >= 0 ? deltaMs : null
}

export function formatDurationMs(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`
}