import type { RetrievedChunk } from "../types"

export interface RetrievalStats {
  totalKnowledgeChunks: number
  totalSimilarRuns: number
  /** `null` when nothing was retrieved at all — not 0, which would misleadingly suggest a real zero-score result. */
  averageScore: number | null
  highestScore: number | null
}

/**
 * Computed once, before the raw retrieved items are listed
 * (Milestone 6 §3: "communicate retrieval quality before showing the
 * raw content") — plain arithmetic over the real `score` field on
 * every retrieved chunk, combined across both `retrieved_knowledge`
 * and `similar_runs` since both represent "what grounded this
 * diagnosis" collectively.
 */
export function computeRetrievalStats(
  retrievedKnowledge: RetrievedChunk[],
  similarRuns: RetrievedChunk[],
): RetrievalStats {
  const allScores = [...retrievedKnowledge, ...similarRuns].map((chunk) => chunk.score)

  return {
    totalKnowledgeChunks: retrievedKnowledge.length,
    totalSimilarRuns: similarRuns.length,
    averageScore: allScores.length > 0 ? allScores.reduce((sum, s) => sum + s, 0) / allScores.length : null,
    highestScore: allScores.length > 0 ? Math.max(...allScores) : null,
  }
}