import { useState, useEffect, useRef, useCallback } from 'react';

function getWsUrl() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  return '/ws';
}

const WS_URL = getWsUrl();

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
          // Support both the legacy GRID_UPDATE type and the backend's metrics_update type
          if (parsed.type === 'GRID_UPDATE') {
            setData(parsed.data);
          } else if (parsed.type === 'metrics_update' && parsed.data) {
            const m = parsed.data;
            const battUnits = m.battery_current ?? 0;
            const battCap = m.battery_capacity ?? 1000;
            const battSoc = m.battery_soc ?? ((battUnits / (battCap || 1)) * 100);
            
              setData({
                energy: {
                  total: m.total_gen ?? 0,
                  solar: m.solar_gen ?? 0,
                  wind: m.wind_gen ?? 0,
                  dataSource: m.dataSource ?? 'simulated',
                  rawWeather: m.rawWeather ?? {},
                },
                demand: {
                  actual: m.total_demand ?? 0,
                  predicted: m.total_demand ?? 0,
                pattern: 'off-peak',
                hour: new Date().getHours(),
              },
              battery: {
                percentage: battSoc,
                level: battUnits,
                capacity: battCap,
                isCharging: (m.total_gen ?? 0) > (m.total_demand ?? 0),
                isDraining: (m.total_gen ?? 0) < (m.total_demand ?? 0),
                chargingRate: Math.abs((m.total_gen ?? 0) - (m.total_demand ?? 0)),
              },
                grid: {
                  frequency: m.frequency ?? 50.0,
                  gridStatus:
                    m.stability_score >= 80
                      ? 'BALANCED'
                    : m.stability_score >= 50
                    ? 'DEFICIT'
                    : 'CRITICAL',
                efficiency: m.stability_score ?? 0,
                  action: 'balanced',
                  delta: (m.total_gen ?? 0) - (m.total_demand ?? 0),
                  alerts: m.alerts?.active || [],
                  carbonIntensity: m.carbonIntensity ?? null,
                },
                timestamp: m.timestamp,
              });
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onerror = () => {
        if (unmounted.current) return;
        console.error('[WebSocket] Connection error:', WS_URL);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        if (unmounted.current) return;
        setIsConnected(false);
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
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
