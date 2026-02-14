import { useOnlineStatus } from "../hooks/useOnlineStatus";

export const OfflineBanner = () => {
  const isOnline = useOnlineStatus();

  if (isOnline) return null;

  return (
    <div className="offline-banner">
      ⚠️ You are offline. Reports will sync later.
    </div>
  );
};
