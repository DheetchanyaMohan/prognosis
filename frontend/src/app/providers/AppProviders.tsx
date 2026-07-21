import type { ReactNode } from "react"
import { QueryClientProvider } from "@tanstack/react-query"
import { queryClient } from "./query-client"

interface AppProvidersProps {
  children: ReactNode
}

/**
 * Wraps the app in every cross-cutting provider it needs. Today
 * that's just TanStack Query. Nothing here should hold business/
 * server data itself (Engineering Spec §7) — it only wires up the
 * providers that do.
 */
export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
