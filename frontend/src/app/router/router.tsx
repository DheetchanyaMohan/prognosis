import { createBrowserRouter } from "react-router-dom"
import { AppLayout } from "../layouts/AppLayout"
import { HomePage } from "../pages/HomePage"
import { ArchitecturePage } from "../pages/ArchitecturePage"
import { ExperimentListPage } from "../pages/ExperimentListPage"
import { ExperimentDetailPage } from "../pages/ExperimentDetailPage"
import { RunDetailPage } from "../pages/RunDetailPage"
import { RunComparisonPage } from "../pages/RunComparisonPage"
import { NotFoundPage } from "../pages/NotFoundPage"

/**
 * Route tree per Product Architecture §6 / Engineering Spec §4,
 * extended for the Compare flow and, in Milestone 6, for a real
 * landing experience.
 *
 *   /                                          → Home (landing page)      ✅
 *   /architecture                              → Architecture              ✅
 *   /experiments                               → Experiment List            ✅
 *   /experiments/:experimentId                 → Experiment Detail          ✅
 *   /experiments/:experimentId/runs/:runId     → Run Detail                  ✅
 *   /compare/:runAId/:runBId                   → Run Comparison               ✅
 *   *                                          → 404                        ✅
 *
 * `/` used to redirect straight to `/experiments` — a deliberate,
 * documented product change: the root now shows a real home page
 * instead of skipping past it, per Milestone 6 §1.
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "architecture", element: <ArchitecturePage /> },
      { path: "experiments", element: <ExperimentListPage /> },
      { path: "experiments/:experimentId", element: <ExperimentDetailPage /> },
      { path: "experiments/:experimentId/runs/:runId", element: <RunDetailPage /> },
      { path: "compare/:runAId/:runBId", element: <RunComparisonPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
])