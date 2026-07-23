import type { ButtonHTMLAttributes } from "react"
import { buttonClasses, type ButtonVariant } from "@/lib/utils"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

/**
 * Shared button primitive (Engineering Spec §8 "UI Components").
 * Plain HTML `<button>` under the hood — no Radix `Slot`/`asChild`
 * indirection until a concrete use case needs it (composition over
 * inheritance, but only the composition actually required today).
 * Variant class logic lives in `lib/utils.ts` (`buttonClasses`), not
 * here, so this file exports only the component itself.
 */
export function Button({ variant = "default", className, ...props }: ButtonProps) {
  return <button type="button" className={buttonClasses(variant, className)} {...props} />
}
