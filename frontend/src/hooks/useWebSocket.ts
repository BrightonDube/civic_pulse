import { useEffect, useRef, useCallback } from "react";
import { Report } from "../types";

interface WebSocketMessage {
  event: "new_report" | "status_change" | "leaderboard_update";
  data: Report;
}

interface UseWebSocketOptions {
  onNewReport?: (report: Report) => void;
  onStatusChange?: (report: Report) => void;
  onLeaderboardUpdate?: () => void;
}

export const useWebSocket = (options: UseWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname;
    const port = "8000";
    const url = `${protocol}//${host}:${port}/ws`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const msg: WebSocketMessage = JSON.parse(event.data);
          switch (msg.event) {
            case "new_report":
              options.onNewReport?.(msg.data);
              break;
            case "status_change":
              options.onStatusChange?.(msg.data);
              break;
            case "leaderboard_update":
              options.onLeaderboardUpdate?.();
              break;
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        // Reconnect after 5 seconds
        reconnectTimer.current = setTimeout(connect, 5000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // WebSocket not available, try reconnect
      reconnectTimer.current = setTimeout(connect, 5000);
    }
  }, [options]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);
};
