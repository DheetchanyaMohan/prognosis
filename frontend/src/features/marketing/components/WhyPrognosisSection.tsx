import { Eye, ShieldCheck, Search, MessageSquareText, type LucideIcon } from "lucide-react"
import { Card } from "@/components/ui"

interface Differentiator {
  icon: LucideIcon
  title: string
  description: string
}

/**
 * Every point here maps to a real, already-shipped behavior (the
 * reasoning trace, retrieved_knowledge/similar_runs, is_grounded/
 * self_check, provenance/supporting_evidence) — not aspirational
 * marketing claims.
 */
const DIFFERENTIATORS: Differentiator[] = [
  {
    icon: Eye,
    title: "Transparent reasoning",
    description: "See every stage the agent goes through, not just a final verdict.",
  },
  {
    icon: Search,
    title: "Real retrieval",
    description: "Evidence is retrieved from a knowledge base and past runs, not recalled from model memory alone.",
  },
  {
    icon: ShieldCheck,
    title: "Evidence grounding",
    description: "Recommendations are checked against retrieved evidence before being shown, and flagged when they aren't.",
  },
  {
    icon: MessageSquareText,
    title: "Explainability",
    description: "Every recommendation traces back to the evidence and reasoning that produced it.",
  },
]

/**
 * Milestone 6 §8: a landing-page section answering "Why Prognosis?"
 * against traditional experiment dashboards, plus a short audience
 * blurb. Kept to short phrases per card rather than paragraphs —
 * "reduce cognitive load" (§10) applies here too.
 */
export function WhyPrognosisSection() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <h2 className="text-2xl font-semibold text-foreground">Why Prognosis?</h2>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Traditional experiment dashboards show you numbers. Prognosis shows you reasoning.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {DIFFERENTIATORS.map((item) => (
          <Card key={item.title} className="p-4">
            <item.icon className="size-4 text-muted-foreground" aria-hidden="true" />
            <p className="mt-2 text-sm font-medium text-foreground">{item.title}</p>
            <p className="mt-1 text-xs text-muted-foreground">{item.description}</p>
          </Card>
        ))}
      </div>

      <Card className="p-4 text-center">
        <p className="text-sm font-medium text-foreground">Built for ML engineers and AI researchers</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Who need to trust an AI's diagnosis, not just read it — and want to verify the evidence
          behind every recommendation.
        </p>
      </Card>
    </div>
  )
}