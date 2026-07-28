import { HeroSection } from "@/features/marketing/components/HeroSection"
import { DiagnosisPreviewSection } from "@/features/marketing/components/DiagnosisPreviewSection"
import { WorkflowOverview } from "@/features/marketing/components/WorkflowOverview"
import { WhyPrognosisSection } from "@/features/marketing/components/WhyPrognosisSection"
import { FeaturesSection } from "@/features/marketing/components/FeaturesSection"

/**
 * `/` — the landing page. `DiagnosisPreviewSection` sits immediately
 * below the hero (per its own explicit requirement) so a first-time
 * visitor sees what Prognosis actually produces before reading
 * anything else — a fully static, clearly-labeled example, not a
 * live result.
 */
export function HomePage() {
  return (
    <div className="flex flex-col gap-16">
      <HeroSection />
      <DiagnosisPreviewSection />
      <WorkflowOverview />
      <WhyPrognosisSection />
      <FeaturesSection />
    </div>
  )
}