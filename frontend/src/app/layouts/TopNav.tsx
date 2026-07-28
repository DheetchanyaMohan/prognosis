import { Link, NavLink, useParams } from "react-router-dom"
import { ChevronRight, ExternalLink } from "lucide-react"
import { HealthIndicator } from "@/features/health/components/HealthIndicator"
import { config } from "@/lib/config"
import { cn } from "@/lib/utils"

const NAV_LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/experiments", label: "Experiments", end: false },
  { to: "/architecture", label: "Architecture", end: false },
]

/**
 * A real product nav (Milestone 6 §6: "should feel like a real
 * product rather than a dashboard") — Home/Experiments/Architecture
 * plus an optional GitHub link, replacing what used to be just a
 * logo + breadcrumb. The breadcrumb (drill-down context like
 * Experiments / exp_001 / run_005) is kept, but demoted to a
 * secondary row below the primary nav rather than sharing space with
 * it — it's "where am I within this section," not "where can I go in
 * the product," and conflating the two would blur exactly the
 * distinction this milestone asks for.
 *
 * No hamburger menu: with only 3 primary links, wrapping to a second
 * line on the narrowest screens (`flex-wrap`) keeps every link
 * reachable without building a whole new mobile-menu subsystem for a
 * 3-item list.
 */
export function TopNav() {
  const { experimentId, runId, runAId, runBId } = useParams<{
    experimentId?: string
    runId?: string
    runAId?: string
    runBId?: string
  }>()

  const showBreadcrumb = Boolean(experimentId) || Boolean(runAId && runBId)

  return (
    <header className="border-b border-border">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <Link
            to="/"
            className="text-base font-semibold tracking-tight text-foreground hover:text-foreground/80"
          >
            Prognosis
          </Link>
          <nav aria-label="Primary" className="flex flex-wrap items-center gap-4 text-sm">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  cn(
                    "transition-colors hover:text-foreground",
                    isActive ? "font-medium text-foreground" : "text-muted-foreground",
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {config.githubUrl && (
            <a
              href={config.githubUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
            >
              GitHub
              <ExternalLink className="size-3.5" aria-hidden="true" />
            </a>
          )}
          <HealthIndicator />
        </div>
      </div>

      {showBreadcrumb && (
        <div className="flex min-w-0 items-center gap-2 border-t border-border px-4 py-2 text-sm sm:px-6">
          {experimentId && (
            <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-muted-foreground">
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
              <span className="truncate">
                Comparing <span className="font-mono text-foreground">{runAId}</span> vs{" "}
                <span className="font-mono text-foreground">{runBId}</span>
              </span>
            </nav>
          )}
        </div>
      )}
    </header>
  )
}