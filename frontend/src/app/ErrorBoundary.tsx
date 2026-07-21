import { Component, type ErrorInfo, type ReactNode } from "react"
import { ErrorState } from "@/components/ui"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

/**
 * The outermost safety net (Engineering Spec §13 "App Error"). Error
 * boundaries must be class components — React has no Hook equivalent
 * for `componentDidCatch`. Catches unexpected render-time exceptions
 * only; it does not and should not handle expected states like 404 or
 * `summary`/`diagnostics: null` — those are handled explicitly by each
 * page/component (Architecture §15).
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Engineering Spec §23: log, don't leave stray console.log in
    // production, never expose the raw stack to the end user.
    console.error("Unhandled render error:", error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorState
          variant="generic"
          title="Something went wrong"
          message="Please reload the page. If this keeps happening, it's worth reporting."
        />
      )
    }
    return this.props.children
  }
}
