import { QueryClient } from "@tanstack/react-query"
import { NotFoundError, ValidationError } from "@/lib/api/errors"

/**
 * Global QueryClient defaults (Engineering Spec §6). Per-query
 * `staleTime`/`refetchInterval` overrides (e.g. experiments vs. a
 * still-training run's summary/diagnostics) belong in each feature's
 * `api/queries.ts`, not here — this only sets the policy that should
 * hold everywhere unless a query says otherwise.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Retry temporary network failures and 5xx responses; never
      // retry a 404 or a validation error (Spec §6 "Retry Strategy").
      retry: (failureCount, error) => {
        if (error instanceof NotFoundError) return false
        if (error instanceof ValidationError) return false
        return failureCount < 2
      },
      refetchOnReconnect: true,
      refetchOnWindowFocus: true,
      staleTime: 60_000,
    },
  },
})
