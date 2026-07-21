import { Link } from "react-router-dom"
import { Card } from "@/components/ui"
import { formatBackendDate } from "@/lib/format-date"
import type { ExperimentRecord } from "../types"

interface ExperimentCardProps {
  experiment: ExperimentRecord
}

/**
 * A single-column list of cards, not a dense table — there are few
 * experiments and each deserves presence (Architecture §7). The whole
 * card is a link (keyboard-operable, focus-visible) rather than a
 * clickable div.
 */
export function ExperimentCard({ experiment }: ExperimentCardProps) {
  return (
    <Link
      to={`/experiments/${encodeURIComponent(experiment.experiment_name)}`}
      className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded-lg"
    >
      <Card className="p-4 transition-colors hover:border-foreground/20 sm:p-5">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4">
          <span className="font-mono text-sm font-medium text-foreground">
            {experiment.experiment_name}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatBackendDate(experiment.created_at)}
          </span>
        </div>
        <p className="mt-1.5 text-sm text-muted-foreground">
          {experiment.description ?? "No description"}
        </p>
        <p className="mt-3 text-xs text-muted-foreground">
          {experiment.run_ids.length}{" "}
          {experiment.run_ids.length === 1 ? "run" : "runs"}
        </p>
      </Card>
    </Link>
  )
}
