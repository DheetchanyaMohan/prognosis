import {
  FolderKanban,
  Sparkles,
  GitCompare,
  Database,
  ClipboardCheck,
  ShieldCheck,
  Search,
  Eye,
  type LucideIcon,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui"

interface Feature {
  icon: LucideIcon
  title: string
  description: string
}

/**
 * Every feature listed here maps to something already built and
 * shipped (Experiments/Run Detail/Compare/Diagnose flows) — this is
 * not an aspirational features list; that's what the Roadmap section
 * is for.
 */
const FEATURES: Feature[] = [
  {
    icon: FolderKanban,
    title: "Experiment Tracking",
    description: "Browse experiments and drill into every run's configuration, metrics, and diagnostics.",
  },
  {
    icon: Sparkles,
    title: "AI Diagnosis",
    description: "An agent pipeline retrieves evidence, reasons over it, and generates hypotheses and recommendations.",
  },
  {
    icon: GitCompare,
    title: "Run Comparison",
    description: "Select any two runs for a true side-by-side diagnostic comparison.",
  },
  {
    icon: Database,
    title: "Retrieval-Augmented Reasoning",
    description: "Every diagnosis is grounded in retrieved knowledge-base content and similar past runs.",
  },
  {
    icon: ClipboardCheck,
    title: "Explainable Recommendations",
    description: "Every recommendation shows its confidence, rationale, and expected benefit.",
  },
  {
    icon: ShieldCheck,
    title: "Grounded Evidence",
    description: "Recommendations are verified against real evidence before being shown — flagged when they aren't.",
  },
  {
    icon: Search,
    title: "Similar Run Retrieval",
    description: "The agent surfaces past runs with comparable characteristics to inform its analysis.",
  },
  {
    icon: Eye,
    title: "Transparent Reasoning",
    description: "Every pipeline stage and the agent's full reasoning trace are inspectable, never a black box.",
  },
]

export function FeaturesSection() {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-medium text-foreground">Features</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((feature) => (
          <Card key={feature.title} className="p-4">
            <CardHeader className="flex-row items-center gap-2 p-0">
              <feature.icon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <CardTitle className="text-foreground">{feature.title}</CardTitle>
            </CardHeader>
            <CardContent className="p-0 pt-2">
              <p className="text-xs text-muted-foreground">{feature.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}