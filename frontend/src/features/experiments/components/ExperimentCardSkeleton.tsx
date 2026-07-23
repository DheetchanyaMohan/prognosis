import { Card, Skeleton } from "@/components/ui"

export function ExperimentCardSkeleton() {
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-baseline justify-between gap-4">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-3 w-20" />
      </div>
      <Skeleton className="mt-2 h-3.5 w-64" />
      <Skeleton className="mt-4 h-3 w-16" />
    </Card>
  )
}
