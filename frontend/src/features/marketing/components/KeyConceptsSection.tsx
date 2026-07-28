import { Database, Workflow, Search, ShieldCheck, Braces, Eye, type LucideIcon } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui"

interface Concept {
  icon: LucideIcon
  title: string
  description: string
}

/**
 * Every explanation here is tied to a real, specific Prognosis
 * behavior (retrieved_knowledge/similar_runs, is_grounded/self_check,
 * the typed Hypothesis/Recommendation schema, the reasoning trace) —
 * not a generic textbook definition floating free of what this
 * system actually does.
 */
const CONCEPTS: Concept[] = [
  {
    icon: Database,
    title: "RAG (Retrieval-Augmented Generation)",
    description:
      "Instead of relying purely on what the model already knows, Prognosis retrieves real evidence — knowledge-base content and similar past runs — and gives it to the model as context before it reasons. Two different runs can surface different evidence, because the retrieval is real.",
  },
  {
    icon: Workflow,
    title: "LangGraph",
    description:
      "The agent's reasoning is built as an explicit graph of steps (retrieve, analyze, generate, verify), not one large prompt. Each step's execution shows up in the reasoning trace, so the process is inspectable rather than a black box.",
  },
  {
    icon: Search,
    title: "Retrieval",
    description:
      "Before generating hypotheses, the agent searches a vector store for the most relevant knowledge-base passages and the most similar past runs, ranked by similarity score.",
  },
  {
    icon: ShieldCheck,
    title: "Grounding",
    description:
      "A recommendation is \"grounded\" when a dedicated verification step confirms it's actually backed by the retrieved evidence — not just plausible-sounding. Ungrounded recommendations are flagged, never hidden.",
  },
  {
    icon: Braces,
    title: "Structured Outputs",
    description:
      "The agent doesn't return free-form prose. Every hypothesis and recommendation comes back in a fixed schema — title, confidence, rationale, supporting evidence — so the UI can render it reliably instead of parsing loose text.",
  },
  {
    icon: Eye,
    title: "Explainability",
    description:
      "Every stage the agent goes through, the evidence it retrieved, and its full reasoning trace are all visible — not just the final answer. A recommendation can always be traced back to what produced it.",
  },
]

export function KeyConceptsSection() {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-medium text-foreground">Key Concepts</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {CONCEPTS.map((concept) => (
          <Card key={concept.title} className="p-4">
            <CardHeader className="flex-row items-center gap-2 p-0">
              <concept.icon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <CardTitle className="text-foreground">{concept.title}</CardTitle>
            </CardHeader>
            <CardContent className="p-0 pt-2">
              <p className="text-xs text-muted-foreground">{concept.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}