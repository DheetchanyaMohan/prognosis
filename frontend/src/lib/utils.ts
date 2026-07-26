import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Merge Tailwind class names conditionally, resolving conflicting
 * utility classes. Used across shared UI primitives instead of
 * hand-concatenating class strings (Engineering Spec §9).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Standard `h1` typography for a page whose title is a backend
 * identifier (an experiment name, a run ID, or both) — e.g.
 * `ExperimentDetailPage`, `RunHeaderBand`, `RunComparisonPage`.
 * Extracted after the same `text-xl font-semibold text-foreground`
 * sequence was found hand-duplicated across those three. Monospacing
 * is intentionally NOT baked in here: pages whose `h1` is a single
 * identifier add `font-mono` themselves, while `RunComparisonPage`'s
 * `h1` mixes two identifiers with the plain word "vs" and only
 * monospaces the identifier `<span>`s.
 */
export const pageHeadingClass = "text-xl font-semibold text-foreground"

/**
 * Shared focus-visible ring treatment (Accessibility §17: focus must
 * always be visible) for custom interactive elements — Links styled
 * as cards or rows — that don't get this styling for free the way a
 * native `<button>` does via the `Button` primitive. Extracted after
 * the exact same class sequence was found duplicated verbatim across
 * `Button`, `ExperimentCard`, and `RunRow`.
 */
export const focusRingClass =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"

export type ButtonVariant = "default" | "outline" | "ghost"

const buttonVariantClasses: Record<ButtonVariant, string> = {
  default: "bg-primary text-primary-foreground hover:bg-primary/90",
  outline: "border border-border bg-transparent hover:bg-secondary",
  ghost: "bg-transparent hover:bg-secondary",
}

const buttonBaseClasses = cn(
  "inline-flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
  focusRingClass,
)

/**
 * The full class string for a given button variant. Lives here
 * (rather than in `Button.tsx`) so that file exports only the
 * `Button` component — mixing a component export with a plain
 * function export in the same file breaks React Fast Refresh
 * (oxlint's `react(only-export-components)` rule). Also lets
 * non-`<button>` elements that should *look* like a button (e.g.
 * `NotFoundPage`'s "back to experiments" navigation, which must be a
 * `Link`, not a `<button>`) match it exactly instead of
 * hand-duplicating these classes.
 */
export function buttonClasses(variant: ButtonVariant = "default", className?: string): string {
  return cn(buttonBaseClasses, buttonVariantClasses[variant], className)
}