import { format, parseISO } from "date-fns"

/**
 * Backend timestamps are ISO 8601 without a timezone suffix, stored
 * as naive UTC (Frontend Integration Guide §2). Appending "Z" before
 * parsing tells the JS Date object to treat it as UTC rather than
 * silently assuming the browser's local timezone.
 */
export function formatBackendDate(isoNoTz: string): string {
  const date = parseISO(isoNoTz.endsWith("Z") ? isoNoTz : `${isoNoTz}Z`)
  return format(date, "MMM d, yyyy")
}
