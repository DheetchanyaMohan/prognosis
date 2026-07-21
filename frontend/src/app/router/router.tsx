import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout } from "../layouts/AppLayout"
import { ExperimentListPage } from "../pages/ExperimentListPage"
import { ExperimentDetailPage } from "../pages/ExperimentDetailPage"
import { RunDetailPage } from "../pages/RunDetailPage"
import { NotFoundPage } from "../pages/NotFoundPage"

/**
 * Route tree per Product Architecture §6 / Engineering Spec §4.
 *
 *   /                                          → redirect to /experiments   ✅
 *   /experiments                               → Experiment List            ✅
 *   /experiments/:experimentId                 → Experiment Detail          (scaffold only — see page)
 *   /experiments/:experimentId/runs/:runId     → Run Detail                  (scaffold only — see page)
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
      { path: "*", element: <NotFoundPage /> },
    ],
  },
])
