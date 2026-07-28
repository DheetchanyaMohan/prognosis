import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui"

interface TechItem {
  name: string
  role: string
}

interface TechCategory {
  category: string
  items: TechItem[]
}

/**
 * Every entry here is grounded in the project's own documentation
 * (Engineering Spec §1, Frontend Integration Guide, FRONTEND_INTEGRATION.md,
 * and `/health`'s reported components) — nothing is assumed or
 * invented. Notably, no specific ML training framework (PyTorch,
 * TensorFlow, etc.) is named under "Machine Learning": nothing in any
 * source document confirms which one produced the training runs
 * being diagnosed, so that category describes the diagnostic
 * *technique* actually documented (deterministic metrics analysis)
 * rather than guessing at an unconfirmed framework.
 */
const TECH_CATEGORIES: TechCategory[] = [
  {
    category: "Frontend",
    items: [
      { name: "React 19", role: "Component-based UI" },
      { name: "TypeScript", role: "Strict-mode type safety across the whole app" },
      { name: "Vite", role: "Dev server and build tooling" },
      { name: "Tailwind CSS v4", role: "Utility-first styling" },
      { name: "TanStack Query", role: "Server-state caching, polling, and the app's mutation" },
      { name: "React Router", role: "Client-side routing" },
    ],
  },
  {
    category: "Backend",
    items: [
      { name: "FastAPI", role: "The REST API layer" },
      { name: "Pydantic", role: "Validated response models with guaranteed shapes" },
      { name: "SQLAlchemy", role: "ORM over the experiment/run metadata store" },
    ],
  },
  {
    category: "AI Engineering",
    items: [
      { name: "LangGraph", role: "Orchestrates the multi-step agent pipeline" },
      { name: "Gemini 3.6 Flash", role: "The LLM invoked by the agent" },
      { name: "Chroma", role: "Vector store powering retrieval-augmented generation" },
    ],
  },
  {
    category: "Machine Learning",
    items: [
      {
        name: "Deterministic diagnostics",
        role: "Generalization-gap trend, plateau, and instability detection computed directly from training metrics",
      },
    ],
  },
  {
    category: "Infrastructure",
    items: [
      { name: "Uvicorn", role: "ASGI server running the API" },
      { name: "Local-first deployment", role: "Single-tenant, no auth — built for focused demo and development use" },
    ],
  },
]

export function TechStackSection() {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-medium text-foreground">Technology Stack</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {TECH_CATEGORIES.map((category) => (
          <Card key={category.category} className="p-4">
            <CardHeader className="p-0">
              <CardTitle>{category.category}</CardTitle>
            </CardHeader>
            <CardContent className="p-0 pt-2">
              <dl className="flex flex-col gap-2">
                {category.items.map((item) => (
                  <div key={item.name}>
                    <dt className="text-sm font-medium text-foreground">{item.name}</dt>
                    <dd className="text-xs text-muted-foreground">{item.role}</dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}