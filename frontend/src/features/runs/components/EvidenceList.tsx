import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui"
import type { RetrievedChunk } from "../types"

interface EvidenceListProps {
  title: string
  chunks: RetrievedChunk[]
}

const sourceTypeLabel: Record<RetrievedChunk["metadata"]["source_type"], string> = {
  knowledge_base: "Knowledge base",
  run_summary: "Run summary",
}

/**
 * `retrieved_knowledge` and `similar_runs` are both `RetrievedChunk[]`
 * with an identical shape — one reusable component instead of two
 * near-duplicate renderers, used twice with different titles.
 *
 * An empty array is a valid, informative result, not an error: even
 * "no evidence retrieved" supports trustworthiness by being honest
 * about what did (or didn't) ground the response.
 */
export function EvidenceList({ title, chunks }: EvidenceListProps) {
  return (
    <Card className="p-4">
      <CardHeader className="p-0">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-0 pt-3">
        {chunks.length === 0 ? (
          <p className="text-sm text-muted-foreground">No evidence of this type was retrieved.</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {chunks.map((chunk) => (
              <li key={chunk.chunk_id} className="border-b border-border pb-3 last:border-0 last:pb-0">
                <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>
                    {sourceTypeLabel[chunk.metadata.source_type]}
                    {chunk.metadata.section_title ? ` — ${chunk.metadata.section_title}` : ""}
                  </span>
                  <span className="font-mono tabular-nums">score {chunk.score.toFixed(2)}</span>
                </div>
                <p className="mt-1 text-sm text-foreground">{chunk.text}</p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}