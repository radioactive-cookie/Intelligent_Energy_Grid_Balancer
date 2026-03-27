import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  (typeof window !== 'undefined'
    ? `ws://${window.location.hostname}:3001`
    : 'ws://localhost:3001');

// 3s reconnect delay is intentionally shorter than the 5s backend broadcast interval
// so the client re-establishes the connection before the next update is missed.
const RECONNECT_DELAY = 3000;

export function useWebSocket() {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const unmounted = useRef(false);

  const connect = useCallback(() => {
    if (unmounted.current) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmounted.current) return;
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        if (unmounted.current) return;
        try {
          const parsed = JSON.parse(event.data);
          if (parsed.type === 'GRID_UPDATE') {
            setData(parsed.data);
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onerror = () => {
        if (unmounted.current) return;
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        if (unmounted.current) return;
        setIsConnected(false);
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
      };
    } catch (err) {
      setError(err.message);
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    }
  }, []);

  useEffect(() => {
    unmounted.current = false;
    connect();
    return () => {
      unmounted.current = true;
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { data, isConnected, error };
}
