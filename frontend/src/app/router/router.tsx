import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout } from "../layouts/AppLayout"
import { ExperimentListPage } from "../pages/ExperimentListPage"
import { ExperimentDetailPage } from "../pages/ExperimentDetailPage"
import { RunDetailPage } from "../pages/RunDetailPage"
import { RunComparisonPage } from "../pages/RunComparisonPage"
import { NotFoundPage } from "../pages/NotFoundPage"

/**
 * Route tree per Product Architecture §6 / Engineering Spec §4,
 * extended for the Compare flow (approved architecture amendment).
 *
 *   /                                          → redirect to /experiments   ✅
 *   /experiments                               → Experiment List            ✅
 *   /experiments/:experimentId                 → Experiment Detail          ✅
 *   /experiments/:experimentId/runs/:runId     → Run Detail                  ✅
 *   /compare/:runAId/:runBId                   → Run Comparison               ✅
 *   *                                          → 404                        ✅
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/experiments" replace /> },
      { path: "experiments", element: <ExperimentListPage /> },
      { path: "experiments/:experimentId", element: <ExperimentDetailPage /> },
      { path: "experiments/:experimentId/runs/:runId", element: <RunDetailPage /> },
      { path: "compare/:runAId/:runBId", element: <RunComparisonPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
])