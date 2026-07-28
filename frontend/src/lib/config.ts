/**
 * Central configuration module. All environment variables are read
 * here and nowhere else (Engineering Spec §22) — components and the
 * API layer import from this module instead of touching
 * `import.meta.env` directly.
 */

function requireEnv(name: string, fallback?: string): string {
  const value = import.meta.env[name] ?? fallback
  if (value === undefined) {
    throw new Error(`Missing required environment variable: ${name}`)
  }
  return value
}

export const config = {
  apiBaseUrl: requireEnv("VITE_API_BASE_URL", "http://localhost:8000"),
  appName: requireEnv("VITE_APP_NAME", "Prognosis"),
  /**
   * No real repository URL is known to this codebase, so this is
   * NOT given a fabricated fallback the way `apiBaseUrl`/`appName`
   * are — it's `undefined` until you set it, and `TopNav` hides the
   * GitHub link entirely rather than pointing it at a guessed or
   * placeholder URL.
   */
  githubUrl: import.meta.env.VITE_GITHUB_URL as string | undefined,
} as const