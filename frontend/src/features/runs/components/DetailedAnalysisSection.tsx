import { DiagnosisSummary } from "./DiagnosisSummary"
import { WorkflowPerformanceSummary } from "./WorkflowPerformanceSummary"
import { RetrievalSummary } from "./RetrievalSummary"
import { HypothesesPanel } from "./HypothesesPanel"
import { RecommendationsPanel } from "./RecommendationsPanel"
import { EvidenceList } from "./EvidenceList"
import { SimilarRunsList } from "./SimilarRunsList"
import { AgentReasoningPanel } from "./AgentReasoningPanel"
import { ComparisonDiagnosticsGrid } from "./ComparisonDiagnosticsGrid"
import { ConfigDiffTable } from "./ConfigDiffTable"
import type { DiagnosisViewModel } from "../hooks/useDiagnosis"

interface DetailedAnalysisSectionProps {
  diagnosis: DiagnosisViewModel
}

/**
 * Only ever rendered by `RunDetailPage` once `diagnosis.isSuccess` —
 * there's nothing to show here otherwise, and no empty-state
 * placeholder is needed, since `AiDiagnosisSection` (further up the
 * page) already invites the user to run one.
 *
 * Reading order (Milestone 6): Diagnosis Summary (the executive
 * summary, "at the top of every completed diagnosis") → Workflow
 * Performance (real per-stage durations) → Retrieval Summary
 * (quality at a glance, before the raw items) → Retrieved Knowledge /
 * Similar Runs → Agent Reasoning → Hypotheses → Recommendations.
 * Recommendations still come last deliberately — the final output of
 * the reasoning process, not the first thing a reader notices.
 *
 * Does NOT re-render `diagnostics`/`run_summary` from the response —
 * both describe the exact same run already shown in full higher up
 * this page (via `DiagnosisPanel`/`ConfigPanel`), so repeating them
 * would be pure redundancy. `comparison` is rendered defensively at
 * the very end since nothing else on this page could show it.
 */
export function DetailedAnalysisSection({ diagnosis }: DetailedAnalysisSectionProps) {
  if (!diagnosis.isSuccess || !diagnosis.data) {
    return null
  }

  const data = diagnosis.data

  return (
    <div className="flex flex-col gap-6">
      <DiagnosisSummary data={data} />

      <WorkflowPerformanceSummary trace={data.trace} />

      <div className="flex flex-col gap-3">
        <RetrievalSummary retrievedKnowledge={data.retrieved_knowledge} similarRuns={data.similar_runs} />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <EvidenceList
            title="Retrieved Knowledge"
            chunks={data.retrieved_knowledge}
            countNoun="chunks"
          />
          <SimilarRunsList chunks={data.similar_runs} />
        </div>
      </div>

      <AgentReasoningPanel trace={data.trace} />

      <HypothesesPanel hypotheses={data.hypotheses} />
      <RecommendationsPanel recommendations={data.recommendations} />

      {/*
        Defensive only: `comparison` is populated when
        request_type === "compare_runs", which the single-run
        Diagnose button never explicitly requests — but the type
        permits it, and nothing else on this page could show a
        comparison, so render it rather than silently dropping real
        data if the backend ever returns it.
      */}
      {data.comparison && (
        <div className="flex flex-col gap-3">
          <ComparisonDiagnosticsGrid
            runAId={data.comparison.run_a_id}
            runBId={data.comparison.run_b_id}
            runADiagnostics={data.comparison.run_a_diagnostics}
            runBDiagnostics={data.comparison.run_b_diagnostics}
          />
          <ConfigDiffTable differences={data.comparison.config_differences} />
        </div>
      )}
    </div>
  )
}