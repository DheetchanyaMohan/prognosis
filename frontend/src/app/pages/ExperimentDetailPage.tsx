/**
 * `/experiments/:experimentId` — Architecture §7 "Experiment Detail".
 *
 * TODO (next slice):
 *  - useExperimentQuery(experimentId) → header (name, description, created_at)
 *  - <RunTable> rendering experiment.run_ids
 *  - Loading: skeleton rows matching final layout.
 *  - Empty: "No runs yet for this experiment" (valid, not broken).
 *  - Error: 404 (unknown experimentId) vs. network vs. generic — distinct
 *    (Architecture §15), never a generic error boundary for a 404.
 */
export function ExperimentDetailPage() {
  return null
}
