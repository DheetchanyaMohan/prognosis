import { format } from "date-fns"

/**
 * Backend timestamps are ISO 8601 without a timezone suffix, stored
 * as naive UTC (Frontend Integration Guide §2) — a rule that applies
 * to every timestamp field across the API (experiments' `created_at`,
 * runs' `generated_at`, trace entries' `timestamp`, etc.), not just
 * one feature's. Appending "Z" tells the JS Date constructor to treat
 * it as UTC rather than silently assuming the browser's local
 * timezone. Shared here so every feature that formats a backend
 * timestamp calls this instead of re-implementing the same suffix
 * check (previously duplicated verbatim in three separate files).
 */
export function toUtcDate(isoNoTz: string): Date {
  return new Date(isoNoTz.endsWith("Z") ? isoNoTz : `${isoNoTz}Z`)
}

export function formatBackendDate(isoNoTz: string): string {
  return format(toUtcDate(isoNoTz), "MMM d, yyyy")
}