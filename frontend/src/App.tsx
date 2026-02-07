import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";
import AppShell from "./components/AppShell";
import ErrorBoundary from "./components/ErrorBoundary";

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <AppShell>
          <AppRoutes />
        </AppShell>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
