import { SystemArchitectureFlow } from "@/features/marketing/components/SystemArchitectureFlow"
import { KeyConceptsSection } from "@/features/marketing/components/KeyConceptsSection"
import { TechStackSection } from "@/features/marketing/components/TechStackSection"
import { RoadmapSection } from "@/features/marketing/components/RoadmapSection"
import { pageHeadingClass } from "@/lib/utils"

/**
 * `/architecture` — the secondary CTA target from the landing page's
 * hero. Unlike `HomePage`, this reuses the app's own internal-page
 * heading convention (`pageHeadingClass`, no `font-mono` override
 * since "Architecture" isn't a backend identifier) — it reads as
 * another page within the product, not a second marketing hero.
 *
 * `SystemArchitectureFlow` and `KeyConceptsSection` lead the page
 * (this page's stated purpose is demonstrating real AI-engineering
 * knowledge), with the pre-existing Tech Stack/Roadmap material
 * following as supporting reference detail.
 */
export function ArchitecturePage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <h1 className={pageHeadingClass}>Architecture</h1>
        <p className="text-sm text-muted-foreground">
          What Prognosis is built with today, and where it's headed next.
        </p>
      </div>
      <SystemArchitectureFlow />
      <KeyConceptsSection />
      <TechStackSection />
      <RoadmapSection />
    </div>
  )
}