import { Link, useParams } from "react-router-dom"
import { ChevronRight } from "lucide-react"
import { HealthIndicator } from "@/features/health/components/HealthIndicator"

/**
 * A minimal top bar, not a heavy sidebar — the IA is only two levels
 * deep (Architecture §5). Every breadcrumb level is a working
 * back-link. No search, no filters, no user menu — none are backed
 * by anything today.
 */
export function TopNav() {
  const { experimentId, runId, runAId, runBId } = useParams<{
    experimentId?: string
    runId?: string
    runAId?: string
    runBId?: string
  }>()

  return (
    <header className="flex h-14 items-center justify-between border-b border-border px-4 sm:px-6">
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <Link
          to="/experiments"
          className="shrink-0 font-semibold tracking-tight text-foreground hover:text-foreground/80"
        >
          Prognosis
        </Link>
        {experimentId && (
          <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-muted-foreground">
            <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
            <Link
              to={`/experiments/${encodeURIComponent(experimentId)}`}
              className="truncate font-mono hover:text-foreground"
            >
              {experimentId}
            </Link>
            {runId && (
              <>
                <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
                <span className="truncate font-mono text-foreground">{runId}</span>
              </>
            )}
          </nav>
        )}
        {runAId && runBId && (
          <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-muted-foreground">
            <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">
              Comparing <span className="font-mono text-foreground">{runAId}</span> vs{" "}
              <span className="font-mono text-foreground">{runBId}</span>
            </span>
          </nav>
        )}
      </div>
      <HealthIndicator />
    </header>
  )
}