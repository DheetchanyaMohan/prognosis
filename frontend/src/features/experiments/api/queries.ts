import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api/client"
import { endpoints } from "@/lib/api/endpoints"
import type { ExperimentRecord } from "../types"

export const experimentKeys = {
  all: ["experiments"] as const,
  detail: (experimentId: string) => ["experiments", experimentId] as const,
}

export function getExperiments(): Promise<ExperimentRecord[]> {
  return apiGet<ExperimentRecord[]>(endpoints.experiments())
}

export function getExperiment(experimentId: string): Promise<ExperimentRecord> {
  return apiGet<ExperimentRecord>(endpoints.experiment(experimentId))
}

/**
 * GET /api/v1/experiments — changes rarely (only when a new
 * experiment is created). staleTime 5 minutes, refetch on window
 * focus (Engineering Spec §6).
 */
export function useExperimentsQuery() {
  return useQuery({
    queryKey: experimentKeys.all,
    queryFn: getExperiments,
    staleTime: 5 * 60_000,
  })
}

/**
 * GET /api/v1/experiments/{experimentId} — moderately cacheable;
 * `run_ids` can grow if new runs are added elsewhere, but that's an
 * acceptable staleness window at current data volumes.
 */
export function useExperimentQuery(experimentId: string) {
  return useQuery({
    queryKey: experimentKeys.detail(experimentId),
    queryFn: () => getExperiment(experimentId),
    staleTime: 5 * 60_000,
  })
}
