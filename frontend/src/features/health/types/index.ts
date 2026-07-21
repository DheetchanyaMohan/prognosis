/**
 * Mirrors `HealthResponse` from GET /health exactly (Frontend
 * Integration Guide §3, §4). No frontend-only fields added here —
 * this type is a direct reflection of the backend's Pydantic model.
 */
export interface ComponentHealth {
  status: "ok" | "error" | "not_configured"
  detail: string | null
}

export interface HealthResponse {
  status: "ok" | "degraded"
  database: ComponentHealth
  chroma: ComponentHealth
  llm_provider: ComponentHealth
}
