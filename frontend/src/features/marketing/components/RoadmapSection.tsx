import { Card } from "@/components/ui"

const ROADMAP_ITEMS = [
  {
    title: "Streaming execution",
    description: "Live, incremental updates as the agent runs, instead of a single request/response.",
  },
  {
    title: "Multi-agent orchestration",
    description: "Specialized agents collaborating on more complex diagnoses.",
  },
  {
    title: "Human feedback",
    description: "Letting engineers confirm or correct recommendations to improve future runs.",
  },
  {
    title: "Automated experiment planning",
    description: "Agent-proposed follow-up experiments, not just analysis of ones that already ran.",
  },
  {
    title: "Hyperparameter optimization",
    description: "Turning recommendations into an automated search.",
  },
  {
    title: "Live LangGraph visualization",
    description: "Watching the agent's reasoning graph execute in real time.",
  },
]

/**
 * None of these are built yet — every item here is future direction,
 * matching the "Future Enhancement" framing already used throughout
 * the project's own architecture documentation, not a claim about
 * current capability.
 */
export function RoadmapSection() {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-medium text-foreground">Roadmap</h2>
      <Card className="p-4">
        <ul className="flex flex-col gap-3">
          {ROADMAP_ITEMS.map((item) => (
            <li key={item.title}>
              <p className="text-sm font-medium text-foreground">{item.title}</p>
              <p className="text-xs text-muted-foreground">{item.description}</p>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}