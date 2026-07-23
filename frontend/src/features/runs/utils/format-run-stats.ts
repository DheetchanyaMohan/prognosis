/**
 * Format seconds as minutes/seconds for anything over ~90s
 * (Integration Guide §4), otherwise as whole seconds.
 */
export function formatWallClock(seconds: number): string {
  if (seconds < 90) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

/**
 * Loss values are shown to 3 decimal places consistently everywhere
 * they appear (GapCard, BestEpochCard, SummaryPanel, RunRow) — never
 * rounded to fewer, since small differences matter for this data.
 */
export function formatLoss(value: number): string {
  return value.toFixed(3)
}

/**
 * Converts a [0, 1] fraction to a fixed-decimal percentage string,
 * e.g. `0.9921` → `"99.2"`. The backend does not multiply by 100 for
 * you (Integration Guide §4). Callers append their own unit suffix
 * ("%" for an absolute accuracy, " pts" for a gap/delta) since those
 * mean different things even though the arithmetic is identical.
 */
export function formatPercent(fraction: number, decimals = 1): string {
  return (fraction * 100).toFixed(decimals)
}
