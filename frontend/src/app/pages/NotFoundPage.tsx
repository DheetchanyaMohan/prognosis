import { Link } from "react-router-dom"
import { ErrorState } from "@/components/ui"
import { buttonClasses } from "@/lib/utils"

export function NotFoundPage() {
  return (
    <ErrorState
      variant="not-found"
      action={
        <Link to="/experiments" className={buttonClasses("outline")}>
          Back to experiments
        </Link>
      }
    />
  )
}
