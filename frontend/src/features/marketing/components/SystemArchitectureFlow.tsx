import { ArrowDown } from "lucide-react"
import { Card } from "@/components/ui"

interface ArchitectureStage {
  name: string
  description: string
}

/**
 * The actual request/response pipeline, not a simplified product
 * narrative (that's `WorkflowOverview` on the Home page — a
 * deliberately different, higher-level, non-technical 7-stage view).
 * Every stage here corresponds to a real, implemented part of the
 * system; nothing is aspirational (that's the Roadmap section).
 */
const STAGES: ArchitectureStage[] = [
  {
    name: "User",
    description: "Browses experiments, opens a run, or requests a diagnosis.",
  },
  {
    name: "React Frontend",
    description: "The client you're using now — renders data, manages state, calls the backend API.",
  },
  {
    name: "FastAPI Backend",
    description: "The REST API layer exposing experiments, runs, comparisons, and the diagnose endpoint.",
  },
  {
    name: "LangGraph",
    description: "Orchestrates the agent's reasoning as an explicit graph of steps, not one opaque LLM call.",
  },
  {
    name: "Knowledge Retrieval",
    description: "The agent's retrieval step — pulls relevant documentation and similar past runs before reasoning.",
  },
  {
    name: "Chroma",
    description: "The vector store retrieval is performed against — embeddings of knowledge-base content and run summaries.",
  },
  {
    name: "Gemini",
    description: "gemini-3.6-flash — the LLM the agent invokes to generate hypotheses and recommendations from the retrieved evidence.",
  },
  {
    name: "Structured Output",
    description: "The LLM's response is constrained to a defined schema, not free-form text — titles, confidence, rationale, evidence.",
  },
  {
    name: "Diagnosis",
    description: "The assembled response: retrieved evidence, reasoning trace, hypotheses, and recommendations together.",
  },
  {
    name: "Grounded Recommendations",
    description: "Every recommendation is checked against the retrieved evidence before being shown, and flagged when it isn't.",
  },
]

export function SystemArchitectureFlow() {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-medium text-foreground">System Architecture</h2>
      <div className="flex flex-col items-center">
        {STAGES.map((stage, index) => (
          <div key={stage.name} className="flex w-full max-w-xl flex-col items-center">
            <Card className="w-full p-4">
              <p className="text-sm font-semibold text-foreground">{stage.name}</p>
              <p className="mt-1 text-xs text-muted-foreground">{stage.description}</p>
            </Card>
            {index < STAGES.length - 1 && (
              <ArrowDown className="my-1 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}