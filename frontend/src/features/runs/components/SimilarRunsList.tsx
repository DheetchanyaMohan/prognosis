import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui"
import { SimilarRunCard } from "./SimilarRunCard"
import type { RetrievedChunk } from "../types"

interface SimilarRunsListProps {
  chunks: RetrievedChunk[]
}

/**
 * Similar Runs now need materially different per-item content than
 * plain knowledge chunks (real status/validation performance via
 * `useRunQuery`, Milestone 6 §4) — `EvidenceList` stays scoped to
 * `retrieved_knowledge` only, and this component takes over
 * `similar_runs`, reusing the same outer Card/list shell for visual
 * consistency.
 */
export function SimilarRunsList({ chunks }: SimilarRunsListProps) {
  return (
    <Card className="p-4">
      <CardHeader className="p-0">
        <CardTitle>Similar Runs</CardTitle>
      </CardHeader>
      <CardContent className="p-0 pt-3">
        {chunks.length === 0 ? (
          <p className="text-sm text-muted-foreground">No similar runs were retrieved.</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {chunks.map((chunk) => (
              <li key={chunk.chunk_id}>
                <SimilarRunCard chunk={chunk} />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}