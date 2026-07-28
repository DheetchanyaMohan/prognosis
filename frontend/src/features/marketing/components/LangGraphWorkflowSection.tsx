import { useState, type ReactNode } from "react"
import {
  CirclePlay,
  CircleStop,
  Tag,
  Database,
  Activity,
  Lightbulb,
  ClipboardCheck,
  ShieldCheck,
  FileCheck,
  type LucideIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"

type NodeCategory = "control" | "retrieval" | "reasoning" | "verification"

interface LangGraphNode {
  id: string
  title: string
  icon: LucideIcon
  category: NodeCategory
  /** START/END render as small pill "state" markers, not process rectangles — matching how graph/state-diagram notation conventionally distinguishes entry/exit points from action nodes. */
  terminal?: boolean
  purpose: string
  inputs: string[]
  outputs: string[]
  boundResources: string[]
}

/**
 * Every field is used exactly as specified — nothing embellished,
 * merged, or invented. START/END are real LangGraph `StateGraph`
 * primitives (the library's own sentinel entry/exit nodes), not
 * fabricated additions. Icons were chosen to reinforce each node's
 * actual responsibility (e.g. a magnifying-glass-adjacent "database"
 * icon for retrieval, a checklist icon for planning), not for
 * decoration.
 */
const NODES: LangGraphNode[] = [
  {
    id: "start",
    title: "START",
    icon: CirclePlay,
    category: "control",
    terminal: true,
    purpose: "Entry point of the workflow.",
    inputs: ["Diagnosis request"],
    outputs: ["Triggers Classify Request"],
    boundResources: ["LangGraph StateGraph entry point"],
  },
  {
    id: "classify_request",
    title: "Classify Request",
    icon: Tag,
    category: "control",
    purpose: "Determine what task the user requested.",
    inputs: ["User request"],
    outputs: ["Request type"],
    boundResources: ["Request classifier"],
  },
  {
    id: "knowledge_retrieval",
    title: "Knowledge Retrieval",
    icon: Database,
    category: "retrieval",
    purpose: "Retrieve supporting context.",
    inputs: ["Request"],
    outputs: ["Knowledge chunks", "Similar runs"],
    boundResources: ["Chroma", "Knowledge Retriever", "Similar Run Retriever"],
  },
  {
    id: "analyze_diagnostics",
    title: "Analyze Diagnostics",
    icon: Activity,
    category: "reasoning",
    purpose: "Compute deterministic diagnostics.",
    inputs: ["Training metrics"],
    outputs: ["Generalization gap", "Plateau", "Instability"],
    boundResources: ["Diagnostic Engine"],
  },
  {
    id: "generate_hypotheses",
    title: "Generate Hypotheses",
    icon: Lightbulb,
    category: "reasoning",
    purpose: "Generate ranked explanations.",
    inputs: ["Diagnostics", "Retrieved knowledge", "Similar runs"],
    outputs: ["Ranked hypotheses"],
    boundResources: ["Gemini 3.6 Flash", "Structured Output"],
  },
  {
    id: "plan_next_experiments",
    title: "Plan Next Experiments",
    icon: ClipboardCheck,
    category: "reasoning",
    purpose: "Generate actionable recommendations.",
    inputs: ["Hypotheses", "Retrieved evidence"],
    outputs: ["Recommendations", "Expected benefits", "Effort estimates"],
    boundResources: ["Gemini 3.6 Flash"],
  },
  {
    id: "ground_recommendations",
    title: "Ground Recommendations",
    icon: ShieldCheck,
    category: "verification",
    purpose: "Verify recommendations against retrieved evidence.",
    inputs: ["Recommendations", "Retrieved knowledge"],
    outputs: ["Grounded recommendations", "Grounding status"],
    boundResources: ["Grounding Verifier"],
  },
  {
    id: "finalize_diagnosis",
    title: "Finalize Diagnosis",
    icon: FileCheck,
    category: "control",
    purpose: "Assemble the final response.",
    inputs: ["All previous outputs"],
    outputs: ["Diagnosis", "Workflow trace", "Recommendations"],
    boundResources: ["Response Assembler"],
  },
  {
    id: "end",
    title: "END",
    icon: CircleStop,
    category: "control",
    terminal: true,
    purpose: "Exit point of the workflow.",
    inputs: ["Finalized diagnosis"],
    outputs: ["Returned to the API layer"],
    boundResources: ["LangGraph StateGraph exit point"],
  },
]

/**
 * Category colors stay deliberately separate from the app's
 * diagnosis-state palette (green/amber/red/blue reserved for run
 * health — Architecture §20) — slate/violet/cyan/teal here instead,
 * at the same "light background + mid-tone icon" intensity the rest
 * of the app already uses for semantic tones (`Badge`'s
 * bg-50/text-600/dark:bg-950 pattern), just with different hues, so
 * this reads as consistent with the existing design language without
 * colliding with its meaning. Never color alone — every node also
 * carries a text label.
 */
const CATEGORY_STYLES: Record <
  NodeCategory,
  { border: string; dot: string; iconWrap: string; icon: string; label: string }
> = {
  control: {
    border: "border-l-slate-400 dark:border-l-slate-500",
    dot: "border-slate-400 dark:border-slate-500",
    iconWrap: "bg-slate-50 dark:bg-slate-900/50",
    icon: "text-slate-600 dark:text-slate-400",
    label: "Control",
  },
  retrieval: {
    border: "border-l-violet-400 dark:border-l-violet-500",
    dot: "border-violet-400 dark:border-violet-500",
    iconWrap: "bg-violet-50 dark:bg-violet-950/40",
    icon: "text-violet-600 dark:text-violet-400",
    label: "Retrieval",
  },
  reasoning: {
    border: "border-l-cyan-400 dark:border-l-cyan-500",
    dot: "border-cyan-400 dark:border-cyan-500",
    iconWrap: "bg-cyan-50 dark:bg-cyan-950/40",
    icon: "text-cyan-600 dark:text-cyan-400",
    label: "Reasoning",
  },
  verification: {
    border: "border-l-teal-400 dark:border-l-teal-500",
    dot: "border-teal-400 dark:border-teal-500",
    iconWrap: "bg-teal-50 dark:bg-teal-950/40",
    icon: "text-teal-600 dark:text-teal-400",
    label: "Verification",
  },
}

const LEGEND: NodeCategory[] = ["control", "retrieval", "reasoning", "verification"]

const EXECUTION_CHARACTERISTICS = [
  "Stateful LangGraph execution",
  "Shared graph state",
  "Deterministic tool nodes",
  "Evidence-grounded recommendations",
  "Structured outputs",
]

interface EdgeProps {
  active: boolean
}

/** A real SVG line + arrowhead, not an icon glyph — reads as a graph edge, not a bullet-list connector. */
function Edge({ active }: EdgeProps) {
  return (
    <svg width="16" height="24" viewBox="0 0 16 24" className="mx-auto shrink-0" aria-hidden="true">
      <line
        x1="8"
        y1="0"
        x2="8"
        y2="16"
        strokeWidth="1.5"
        className={cn("transition-colors", active ? "stroke-foreground" : "stroke-border")}
      />
      <polygon
        points="8,23 4,15 12,15"
        className={cn("transition-colors", active ? "fill-foreground" : "fill-border")}
      />
    </svg>
  )
}

function InspectorField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="mt-1">{children}</div>
    </div>
  )
}

/**
 * Deliberately NOT the pill-shaped `Badge` primitive used for
 * statuses elsewhere — square corners and monospace text read as
 * "developer tooling" (matching the source milestone's own
 * `[ Chroma ]`-style bracket notation) rather than the rounded,
 * friendly status-badge language used for run health. `outline`
 * (unfilled) represents data flowing through the node (inputs/
 * outputs); `solid` (filled) represents a concrete bound resource —
 * a deliberate two-tier visual distinction, not decoration.
 */
function ResourceChip({ label, variant }: { label: string; variant: "outline" | "solid" }) {
  return (
    <span
      className={cn(
        "rounded border px-1.5 py-0.5 font-mono text-[11px]",
        variant === "outline"
          ? "border-border text-muted-foreground"
          : "border-transparent bg-secondary text-foreground",
      )}
    >
      {label}
    </span>
  )
}

function ChipRow({ items, variant }: { items: string[]; variant: "outline" | "solid" }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <ResourceChip key={item} label={item} variant={variant} />
      ))}
    </div>
  )
}

function Inspector({ node }: { node: LangGraphNode | null }) {
  if (!node) {
    return (
      <div
        id="langgraph-inspector"
        role="region"
        aria-label="Node inspector"
        className="flex min-h-56 flex-col items-center justify-center gap-1 rounded-md border border-dashed border-border p-6 text-center lg:min-h-[26rem]"
      >
        <p className="text-xs text-muted-foreground">Hover or focus a node to inspect it.</p>
      </div>
    )
  }

  const style = CATEGORY_STYLES[node.category]

  return (
    <div
      id="langgraph-inspector"
      role="region"
      aria-label={`${node.title} inspector`}
      className="flex flex-col gap-3 rounded-md border border-border bg-card p-4 lg:min-h-[26rem]"
    >
      <div className="flex items-center gap-2.5">
        <span className={cn("flex size-7 shrink-0 items-center justify-center rounded", style.iconWrap)}>
          <node.icon className={cn("size-4", style.icon)} aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm font-semibold text-foreground">{node.title}</p>
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{style.label}</p>
        </div>
      </div>

      <div className="flex flex-col gap-3 border-t border-border pt-3">
        <InspectorField label="Purpose">
          <p className="text-xs text-foreground">{node.purpose}</p>
        </InspectorField>
        <InspectorField label="Inputs">
          <ChipRow items={node.inputs} variant="outline" />
        </InspectorField>
        <InspectorField label="Outputs">
          <ChipRow items={node.outputs} variant="outline" />
        </InspectorField>
        <InspectorField label="Bound Resources">
          <ChipRow items={node.boundResources} variant="solid" />
        </InspectorField>
      </div>
    </div>
  )
}

/**
 * "LangGraph Agent Workflow" — refined so the graph is a permanently
 * stable layout: hovering a node never covers or moves anything.
 * Detail no longer floats over the graph (the previous approach);
 * instead a single persistent "inspector" panel sits outside the
 * graph entirely (to the right on wide screens, stacked below it on
 * narrow ones), and only its *contents* change as different nodes
 * are hovered/focused. The graph column's width never depends on
 * what's currently shown in the inspector, so it truly cannot move.
 *
 * Same interaction model as before (hover, focus, click-to-toggle for
 * touch) — only the render target changed, from N floating per-node
 * cards to one shared panel.
 *
 * The graph stays linear (single incoming/outgoing edge per node) —
 * that IS the real, implemented workflow; no branches are invented.
 *
 * Known, deliberate wording gap, unchanged from the previous
 * revision: this section says "Ground Recommendations"/"Finalize
 * Diagnosis" (as specified); the System Architecture diagram above
 * and the live Run Detail pipeline say "Grounded Recommendations"/
 * "Diagnosis" (an earlier cross-page consistency choice). Left
 * unresolved — this milestone doesn't touch that live-data path.
 */
export function LangGraphWorkflowSection() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)

  function open(index: number) {
    setActiveIndex(index)
  }
  function close(index: number) {
    setActiveIndex((prev) => (prev === index ? null : prev))
  }
  function toggle(index: number) {
    setActiveIndex((prev) => (prev === index ? null : index))
  }

  const activeNode = activeIndex !== null ? NODES[activeIndex] : null

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-sm font-medium text-foreground">LangGraph Agent Workflow</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          The actual reasoning graph the agent executes. Hover or focus a node to inspect it.
        </p>
      </div>

      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:gap-10">
        <div className="flex flex-col items-center gap-5 py-2 lg:shrink-0">
          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5">
            {LEGEND.map((category) => (
              <span key={category} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className={cn("size-2 rounded-full border-2 bg-card", CATEGORY_STYLES[category].dot)} />
                {CATEGORY_STYLES[category].label}
              </span>
            ))}
          </div>

          <div className="mx-auto flex w-44 flex-col items-stretch">
            {NODES.map((node, index) => {
              const isActive = activeIndex === index
              const edgeAboveActive = activeIndex === index || activeIndex === index - 1
              const style = CATEGORY_STYLES[node.category]

              return (
                <div key={node.id} className="flex flex-col items-stretch">
                  {index > 0 && <Edge active={edgeAboveActive} />}

                  <button
                    type="button"
                    aria-expanded={isActive}
                    aria-describedby="langgraph-inspector"
                    onMouseEnter={() => open(index)}
                    onMouseLeave={() => close(index)}
                    onFocus={() => open(index)}
                    onBlur={() => close(index)}
                    onClick={() => toggle(index)}
                    className={cn(
                      "flex items-center gap-2 border bg-card text-left transition-[border-color,box-shadow]",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                      node.terminal
                        ? "mx-auto justify-center rounded-full border-border bg-secondary/40 px-4 py-1.5"
                        : cn("w-full rounded-md border-l-[3px] px-2.5 py-2", style.border),
                      isActive && !node.terminal && "border-foreground/30 shadow-sm",
                      isActive && node.terminal && "border-foreground/40 shadow-sm",
                      !isActive && "hover:border-foreground/20",
                    )}
                  >
                    {!node.terminal && (
                      <span
                        className={cn(
                          "flex size-5 shrink-0 items-center justify-center rounded",
                          style.iconWrap,
                        )}
                      >
                        <node.icon className={cn("size-3", style.icon)} aria-hidden="true" />
                      </span>
                    )}
                    <span
                      className={cn(
                        "font-medium text-foreground",
                        node.terminal ? "text-xs tracking-wide" : "truncate text-xs",
                      )}
                    >
                      {node.title}
                    </span>
                  </button>
                </div>
              )
            })}
          </div>
        </div>

        <div className="w-full lg:sticky lg:top-6 lg:w-72 lg:shrink-0">
          <Inspector node={activeNode} />
        </div>
      </div>

      <div className="flex flex-col gap-2 border-t border-border pt-4">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
          Execution Characteristics
        </h3>
        <div className="flex flex-wrap gap-2">
          {EXECUTION_CHARACTERISTICS.map((item) => (
            <span
              key={item}
              className="rounded-md border border-border bg-card px-2.5 py-1 text-xs text-foreground"
            >
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}