import { Card } from "@/components/ui"

export function ExperimentCardSkeleton() {
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-baseline justify-between gap-4">
        <div className="h-4 w-48 animate-pulse rounded bg-muted" />
        <div className="h-3 w-20 animate-pulse rounded bg-muted" />
      </div>
      <div className="mt-2 h-3.5 w-64 animate-pulse rounded bg-muted" />
      <div className="mt-4 h-3 w-16 animate-pulse rounded bg-muted" />
    </Card>
  )
}
