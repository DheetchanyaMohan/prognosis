import { Button } from "@/components/ui"

interface CompareBarProps {
  runAId: string
  runBId: string
  onCompare: () => void
  onClear: () => void
}

/**
 * Surfaces automatically the instant a second checkbox is checked in
 * `RunTable` — there's no separate "Compare Mode" to enter first. A
 * click is still required to navigate (rather than auto-navigating on
 * the second checkbox), since teleporting the user away the moment
 * they check a box would be a jarring, easy-to-trigger-by-accident
 * interaction; this keeps it an explicit, undoable action instead
 * (the "Clear" button lets you back out before committing).
 */
export function CompareBar({ runAId, runBId, onCompare, onClear }: CompareBarProps) {
  return (
    <div className="animate-in fade-in slide-in-from-top-1 flex items-center justify-between gap-4 rounded-md border border-border bg-secondary/50 px-4 py-3 text-sm">
      <span className="text-foreground">
        Comparing <span className="font-mono">{runAId}</span> and{" "}
        <span className="font-mono">{runBId}</span>
      </span>
      <div className="flex items-center gap-2">
        <Button variant="ghost" onClick={onClear}>
          Clear
        </Button>
        <Button onClick={onCompare}>Compare runs</Button>
      </div>
    </div>
  )
}