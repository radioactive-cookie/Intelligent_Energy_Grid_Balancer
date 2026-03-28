import { useState, useEffect, useRef, useCallback } from 'react';

function getWsUrl() {
<<<<<<< HEAD
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  // If running on localhost:5173 (Vite), point to the default backend port 8000
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return `ws://localhost:8000/ws`;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
=======
  const isSecurePage = window.location.protocol === 'https:';
  const wsScheme = isSecurePage ? 'wss' : 'ws';
  const wsProtocol = `${wsScheme}://`;
  const ensureLeadingSlash = (value) => `/${value.replace(/^\/+/, '')}`;

  const configuredWsUrl = import.meta.env.VITE_WS_URL?.trim();
  if (configuredWsUrl) {
    if (
      configuredWsUrl.startsWith('ws://') ||
      configuredWsUrl.startsWith('wss://')
    ) {
      return configuredWsUrl;
    }
    if (configuredWsUrl.startsWith('http://')) {
      return configuredWsUrl.replace(/^http:\/\//, 'ws://');
    }
    if (configuredWsUrl.startsWith('https://')) {
      return configuredWsUrl.replace(/^https:\/\//, 'wss://');
    }
    return `${wsProtocol}${window.location.host}${ensureLeadingSlash(configuredWsUrl)}`;
  }
  return `${wsProtocol}${window.location.host}/ws`;
>>>>>>> 1f2a52ecf0159046cd2db518ab0f121bea39cd72
}

const WS_URL = getWsUrl();

const RECONNECT_DELAY = 5000;

export function useWebSocket() {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const unmounted = useRef(false);
  const reconnectScheduled = useRef(false);

  const scheduleReconnect = useCallback(() => {
    if (unmounted.current || reconnectScheduled.current) return;
    reconnectScheduled.current = true;
    reconnectTimer.current = setTimeout(() => {
      reconnectScheduled.current = false;
      connect();
    }, RECONNECT_DELAY);
  }, []);

  const connect = useCallback(() => {
    if (unmounted.current) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmounted.current) return;
        clearTimeout(reconnectTimer.current);
        reconnectScheduled.current = false;
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
              weather: m.weather || { location: 'Bhubaneswar, IN', solar_radiation: 0, wind_speed: 0 }
            });
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onerror = (err) => {
        if (unmounted.current) return;
        console.error('[WebSocket] Connection error:', WS_URL, err);
        setError('WebSocket connection error');
        ws.close();
      };

      ws.onclose = () => {
        if (unmounted.current) return;
        setIsConnected(false);
        scheduleReconnect();
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      setError(err.message);
      scheduleReconnect();
    }
  }, [scheduleReconnect]);

  useEffect(() => {
    unmounted.current = false;
    connect();
    return () => {
      unmounted.current = true;
      clearTimeout(reconnectTimer.current);
      reconnectScheduled.current = false;
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { data, isConnected, error };
}
