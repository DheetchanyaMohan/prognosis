import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Merge Tailwind class names conditionally, resolving conflicting
 * utility classes. Used across shared UI primitives instead of
 * hand-concatenating class strings (Engineering Spec §9).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
