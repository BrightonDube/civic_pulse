import { useEffect } from "react";
import { syncDrafts } from "./services/sync";
import { useOnlineStatus } from "./hooks/useOnlineStatus";

/**
 * Main App component that handles draft synchronization based on online status
 * @param children - React child components to render
 */
function App({ children }: { children: React.ReactNode }) {
  // Track the current online/offline status of the user
  const isOnline = useOnlineStatus();

  // Sync drafts whenever the user comes back online
  useEffect(() => {
    if (isOnline) {
      // Trigger draft synchronization when connection is restored
      syncDrafts();
    }
  }, [isOnline]); // Re-run effect when online status changes

  // Render child components without any wrapper elements
  return <>{children}</>;
}

export default App;
