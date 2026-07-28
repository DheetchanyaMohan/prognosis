import { Link } from "react-router-dom"
import { buttonClasses } from "@/lib/utils"

/**
 * The hero deliberately does NOT reuse `pageHeadingClass` (the
 * internal app's understated "identifier heading" convention used on
 * Experiment/Run Detail). This is different content — a marketing
 * hero, not a page whose title is a backend identifier — and
 * warrants its own larger, bolder scale; reusing the internal
 * convention here would just be the wrong tool, not consistency.
 *
 * CTAs are `Link`s styled via `buttonClasses`, not real `<Button>`
 * elements — nesting a `<button>` inside an `<a>` (which `Link`
 * renders) is invalid HTML, the same issue already fixed for
 * `RunRow`'s checkbox in an earlier milestone.
 */
export function HeroSection() {
  return (
    <div className="flex flex-col items-center gap-4 py-12 text-center sm:py-16">
      <h1 className="text-4xl font-bold text-foreground sm:text-5xl">Prognosis</h1>
      <p className="max-w-2xl text-lg text-foreground sm:text-xl">
        An agentic AI system that diagnoses machine learning training runs — and shows its reasoning,
        not just its conclusions.
      </p>
      <p className="max-w-xl text-sm text-muted-foreground">
        Prognosis retrieves relevant evidence, reasons over your training metrics, and produces
        grounded, explainable recommendations. Built for ML engineers and researchers who need to
        trust an AI's diagnosis, not just read it.
      </p>
      <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
        <Link to="/experiments" className={buttonClasses("default")}>
          View Experiments
        </Link>
        <Link to="/architecture" className={buttonClasses("outline")}>
          Explore the Architecture
        </Link>
      </div>
    </div>
  )
}