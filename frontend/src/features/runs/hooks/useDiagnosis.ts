import { useEffect, useState } from "react"
import { ApiError } from "@/lib/api/errors"
import { useDiagnoseRunMutation } from "../api/mutations"
import { CONCEPTUAL_STAGES, buildConceptualStages, buildTraceStages } from "../utils/agent-workflow"
import type { PipelineStage } from "../utils/agent-workflow"
import type { DiagnosisResponse } from "../types"

/**
 * Drives which conceptual stage looks "active" while a diagnosis is
 * in flight — the same honest, timer-based mechanism used for
 * cycling loading-state text/pipeline position. Advances through the
 * real, documented stage count and caps at the last one for however
 * much longer the actual call takes; it never claims to know true
 * per-stage completion, only "roughly here."
 */
const STAGE_INTERVAL_MS = 6_000

function useActiveConceptualStage(isPending: boolean): number | null {
  const [index, setIndex] = useState<number | null>(null)

  useEffect(() => {
    if (!isPending) {
      setIndex(null)
      return
    }
    setIndex(0)
    const interval = setInterval(() => {
      setIndex((i) => Math.min((i ?? 0) + 1, CONCEPTUAL_STAGES.length - 1))
    }, STAGE_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [isPending])

  return index
}

export interface DiagnosisViewModel {
  run: () => void
  isIdle: boolean
  isPending: boolean
  isError: boolean
  isSuccess: boolean
  isDiagnosisFailure: boolean
  data: DiagnosisResponse | undefined
  pipelineStages: PipelineStage[]
}

/**
 * The single source of diagnosis state for Run Detail. Both
 * `AiDiagnosisSection` (the trigger + workflow visualization, shown
 * early on the page) and `DetailedAnalysisSection` (evidence,
 * reasoning, hypotheses, recommendations, shown near the bottom) need
 * the *same* mutation instance — calling `useDiagnoseRunMutation()`
 * twice would create two independent, out-of-sync mutation states.
 * `RunDetailPage` calls this once and passes the result to both.
 */
export function useDiagnosis(runId: string): DiagnosisViewModel {
  const mutation = useDiagnoseRunMutation()
  const activeConceptualStage = useActiveConceptualStage(mutation.isPending)

  const pipelineStages =
    mutation.isSuccess && mutation.data
      ? buildTraceStages(mutation.data.trace)
      : buildConceptualStages(mutation.isPending ? activeConceptualStage : null)

  return {
    run: () => mutation.mutate({ runId }),
    isIdle: mutation.isIdle,
    isPending: mutation.isPending,
    isError: mutation.isError,
    isSuccess: mutation.isSuccess,
    isDiagnosisFailure: mutation.error instanceof ApiError && mutation.error.status === 502,
    data: mutation.data,
    pipelineStages,
  }
}