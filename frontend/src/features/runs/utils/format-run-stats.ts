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
