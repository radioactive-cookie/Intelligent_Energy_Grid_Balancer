<<<<<<< HEAD
import { useState, useEffect, useCallback } from 'react';
import { Zap, Moon, Sun, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { useWebSocket } from './hooks/useWebSocket';
import { getGridStatus } from './services/api';
import Dashboard from './components/Dashboard';

export default function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [gridData, setGridData] = useState(null);
  const [rawGridData, setRawGridData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [introPlaying, setIntroPlaying] = useState(true);
  const [scenario, setScenario] = useState({
    demandMultiplier: 1,
    solarMultiplier: 1,
    windMultiplier: 1,
  });

  // Force scroll to top when intro finishes
  useEffect(() => {
    if (!introPlaying) {
      window.scrollTo(0, 0);
    }
  }, [introPlaying]);

  // Force scroll to top on mount and start intro timer
  useEffect(() => {
    window.scrollTo(0, 0);
    const timer = setTimeout(() => {
      setIntroPlaying(false);
    }, 3500);
    return () => clearTimeout(timer);
  }, []);

  const { data: wsData, isConnected } = useWebSocket();

  const applyScenario = useCallback((base) => {
    if (!base) return base;
    
    // Core multipliers
    const demandActual = (base.demand?.actual ?? 0) * scenario.demandMultiplier;
    const solar = (base.energy?.solar ?? 0) * scenario.solarMultiplier;
    const wind = (base.energy?.wind ?? 0) * scenario.windMultiplier;
    const total = solar + wind;
    const delta = total - demandActual;
    const battery = base.battery || {};
    const nextStatus = delta > 0 ? 'SURPLUS' : delta < 0 ? 'DEFICIT' : 'BALANCED';

    // Calculate dynamic carbon intensity based on the shifted energy mix
    const I_SOLAR = 12.0;
    const I_WIND = 11.0;
    const I_GRID = base.grid?.carbonIntensity || 450.0;
    
    let carbonIntensity = I_GRID;
    if (total > 0 || demandActual > 0) {
      if (total >= demandActual) {
        // Fully renewable (excess goes to battery)
        carbonIntensity = (solar * I_SOLAR + wind * I_WIND) / (total || 1);
      } else {
        // Renewable + Grid Deficit (Thermal)
        const gridDeficit = demandActual - total;
        carbonIntensity = (solar * I_SOLAR + wind * I_WIND + gridDeficit * I_GRID) / (demandActual || 1);
      }
    }

    return {
      ...base,
      energy: {
        ...(base.energy || {}),
        solar,
        wind,
        total,
      },
      demand: {
        ...(base.demand || {}),
        actual: demandActual,
        predicted: demandActual,
      },
      battery: {
        ...battery,
        isCharging: delta > 0,
        isDraining: delta < 0,
        chargingRate: Math.abs(delta),
      },
      grid: {
        ...(base.grid || {}),
        delta,
        gridStatus: nextStatus,
        carbonIntensity: Math.round(carbonIntensity),
      },
    };
  }, [scenario]);

  // Merge WebSocket data - use directly as it's already mapped in the hook
  useEffect(() => {
    if (wsData) {
      setRawGridData(wsData);
      setGridData(applyScenario(wsData));
      setIsLoading(false);
      setLastUpdated(new Date());

      // Handle alerts if they exist in the raw message or mapped data
      const alertsList = wsData.grid?.alerts || wsData.alerts;
      if (alertsList?.length > 0) {
        setAlerts((prev) => {
          const incoming = alertsList.map((a) => ({
            ...a,
            id: `${a.type}-${Date.now()}-${Math.random()}`,
          }));
          const merged = [...incoming, ...prev].slice(0, 20);
          return merged;
        });
      }
    }
  }, [wsData, applyScenario]);

  // Fallback polling when WebSocket is disconnected
  const fetchData = useCallback(async () => {
    try {
      const data = await getGridStatus();
      // Map the backend dashboard response to the frontend state structure
      const supply = data.total_supply ?? data.total_generation ?? data.total_gen ?? 0;
      const demandActual = data.total_demand ?? data.demand ?? 0;
      const delta = supply - demandActual;
      const surplus = Math.max(0, delta);
      const deficit = Math.max(0, -delta);
      const gridStatusMap = {
        stable: surplus > 0 ? 'SURPLUS' : deficit > 0 ? 'DEFICIT' : 'BALANCED',
        warning: surplus > 0 ? 'SURPLUS' : deficit > 0 ? 'DEFICIT' : 'BALANCED',
        critical: 'CRITICAL',
      };
      const mappedData = {
        energy: {
          total: supply,
          solar: data.solar_gen ?? data.sources?.solar ?? 0,
          wind: data.wind_gen ?? data.sources?.wind ?? 0,
          dataSource: data.dataSource ?? 'simulated',
          rawWeather: data.rawWeather ?? {},
        },
        demand: {
          actual: demandActual,
          predicted: demandActual,
          pattern: 'off-peak',
          hour: new Date().getHours(),
        },
        battery: {
          percentage: data.battery_soc ?? data.battery_percent ?? data.battery_level ?? 0,
          level: data.battery_current ?? 0,
          capacity: data.battery_capacity ?? 1000,
          isCharging: surplus > 0,
          isDraining: deficit > 0,
          chargingRate: Math.abs(delta),
        },
        grid: {
          frequency: data.frequency ?? 50.0,
          gridStatus: gridStatusMap[data.status ?? data.grid_status] ?? 'BALANCED',
          efficiency: data.efficiency ?? 0,
          action: 'balanced',
          delta,
          alerts: [],
          carbonIntensity: data.carbonIntensity ?? 450,
        },
        timestamp: data.timestamp ?? new Date().toISOString(),
      };
      setRawGridData(mappedData);
      setGridData(applyScenario(mappedData));
      setLastUpdated(new Date());
    } catch (err) {
      console.error('[App] Grid status fetch failed:', err.message);
    } finally {
      setIsLoading(false);
    }
  }, [applyScenario]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (rawGridData) {
      setGridData(applyScenario(rawGridData));
    }
  }, [scenario, rawGridData, applyScenario]);

  useEffect(() => {
    if (!isConnected) {
      const interval = setInterval(fetchData, 5000);
      return () => clearInterval(interval);
    }
  }, [isConnected, fetchData]);

  const dismissAlert = useCallback((id) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

=======
import { Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import StrategyPage from './pages/StrategyPage';

export default function App() {
>>>>>>> 1f2a52ecf0159046cd2db518ab0f121bea39cd72
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/strategy" element={<StrategyPage />} />
    </Routes>
  );
}
