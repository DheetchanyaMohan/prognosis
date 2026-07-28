import { Search, Activity, ClipboardCheck, type LucideIcon } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui"

interface AgentRole {
  title: string
  icon: LucideIcon
  responsibilities: string[]
}

const AGENT_ROLES: AgentRole[] = [
  {
    title: "Knowledge Retrieval",
    icon: Search,
    responsibilities: [
      "Finds relevant documentation",
      "Retrieves similar past experiments",
      "Ranks evidence by relevance",
    ],
  },
  {
    title: "Diagnostic Analyst",
    icon: Activity,
    responsibilities: ["Analyzes training metrics", "Identifies failure patterns", "Generates hypotheses"],
  },
  {
    title: "Recommendation Planner",
    icon: ClipboardCheck,
    responsibilities: [
      "Proposes interventions",
      "Grounds every recommendation in evidence",
      "Ranks by confidence",
    ],
  },
]

/**
 * Conceptual responsibilities within the single agent pipeline
 * (Milestone 5 §2) — explicitly NOT three separate models or LLM
 * instances; the disclaimer below is load-bearing, not boilerplate.
 * Purely descriptive, static content that doesn't depend on any
 * request state — shown only in the idle state (before the first
 * "Diagnose" click) to orient a first-time visitor on what the
 * pipeline actually does before any live/real results exist. Once a
 * real result is showing, the actual trace-derived pipeline and real
 * evidence are more informative than this generic explainer, so it's
 * not repeated then (Milestone 5's "prioritize clarity over visual
 * complexity" constraint).
 */
export function AgentCards() {
  return (
    <div className="flex flex-col gap-2">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {AGENT_ROLES.map((role) => (
          <Card key={role.title} className="p-4">
            <CardHeader className="flex-row items-center gap-2 p-0">
              <role.icon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <CardTitle className="text-foreground">{role.title}</CardTitle>
            </CardHeader>
            <CardContent className="p-0 pt-2">
              <ul className="flex flex-col gap-1 text-xs text-muted-foreground">
                {role.responsibilities.map((responsibility) => (
                  <li key={responsibility}>{responsibility}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        These are logical responsibilities within a single agent pipeline, not separate AI models.
      </p>
    </div>
  )
}