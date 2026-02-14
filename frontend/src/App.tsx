import { useEffect } from "react";
import { syncDrafts } from "./services/sync";
import { useOnlineStatus } from "./hooks/useOnlineStatus";

function App({ children }: { children: React.ReactNode }) {
  const isOnline = useOnlineStatus();

  useEffect(() => {
    if (isOnline) {
      syncDrafts();
    }
  }, [isOnline]);

  return <>{children}</>;
}

export default App;
