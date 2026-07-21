import { RouterProvider } from "react-router-dom"
import { AppProviders } from "./providers/AppProviders"
import { router } from "./router/router"
import { ErrorBoundary } from "./ErrorBoundary"

function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <RouterProvider router={router} />
      </AppProviders>
    </ErrorBoundary>
  )
}

export default App
