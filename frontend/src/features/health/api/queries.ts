import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api/client"
import { endpoints } from "@/lib/api/endpoints"
import type { HealthResponse } from "../types"

export const healthKeys = {
  all: ["health"] as const,
}

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>(endpoints.health())
}

/**
 * GET /health — always refetched, never cached (Integration Guide §7,
 * Engineering Spec §6: "Health — Always fresh. staleTime: 0"). Cheap,
 * side-effect-free; safe to poll on an interval from a status
 * indicator without gating navigation on it.
 */
export function useHealthQuery() {
  return useQuery({
    queryKey: healthKeys.all,
    queryFn: getHealth,
    staleTime: 0,
    refetchInterval: 45_000,
  })
}
