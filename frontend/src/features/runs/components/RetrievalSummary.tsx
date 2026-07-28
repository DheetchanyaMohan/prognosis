import { StatCard } from "@/components/ui"
import { computeRetrievalStats } from "../utils/retrieval-stats"
import type { RetrievedChunk } from "../types"

interface RetrievalSummaryProps {
  retrievedKnowledge: RetrievedChunk[]
  similarRuns: RetrievedChunk[]
}

export function RetrievalSummary({ retrievedKnowledge, similarRuns }: RetrievalSummaryProps) {
  const stats = computeRetrievalStats(retrievedKnowledge, similarRuns)

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium text-foreground">Retrieval Summary</h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Knowledge Chunks" value={stats.totalKnowledgeChunks} />
        <StatCard label="Similar Runs" value={stats.totalSimilarRuns} />
        <StatCard label="Avg Similarity" value={stats.averageScore !== null ? stats.averageScore.toFixed(2) : "—"} />
        <StatCard label="Highest Similarity" value={stats.highestScore !== null ? stats.highestScore.toFixed(2) : "—"} />
      </div>
    </div>
  )
}