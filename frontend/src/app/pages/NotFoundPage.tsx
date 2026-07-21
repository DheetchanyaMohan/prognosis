import { Link } from "react-router-dom"
import { ErrorState } from "@/components/ui"

export function NotFoundPage() {
  return (
    <ErrorState
      variant="not-found"
      action={
        <Link
          to="/experiments"
          className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-secondary"
        >
          Back to experiments
        </Link>
      }
    />
  )
}
