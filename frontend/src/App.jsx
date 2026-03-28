import { useState, useEffect, useCallback } from 'react';
import { Zap, Moon, Sun, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { useWebSocket } from './hooks/useWebSocket';
import { getGridStatus } from './services/api';
import Dashboard from './components/Dashboard';

export default function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [gridData, setGridData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [introPlaying, setIntroPlaying] = useState(true);

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

  // Merge WebSocket data - use directly as it's already mapped in the hook
  useEffect(() => {
    if (wsData) {
      setGridData(wsData);
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
  }, [wsData]);

  // Fallback polling when WebSocket is disconnected
  const fetchData = useCallback(async () => {
    try {
      const data = await getGridStatus();
      // Map the backend dashboard response to the frontend state structure
      const surplus = data.surplus ?? 0;
      const deficit = data.deficit ?? 0;
      const gridStatusMap = {
        stable: surplus > 0 ? 'SURPLUS' : deficit > 0 ? 'DEFICIT' : 'BALANCED',
        warning: surplus > 0 ? 'SURPLUS' : deficit > 0 ? 'DEFICIT' : 'BALANCED',
        critical: 'CRITICAL',
      };
      setGridData({
        energy: {
          total: data.total_generation ?? 0,
          solar: data.solar_mw ?? 0,
          wind: data.wind_mw ?? 0,
        },
        demand: {
          actual: data.demand ?? 0,
          predicted: data.demand ?? 0,
          pattern: 'off-peak',
          hour: new Date().getHours(),
        },
        battery: {
          percentage: data.battery_percent ?? 0,
          level: data.battery_current ?? 0,
          capacity: data.battery_capacity ?? 1000,
          isCharging: surplus > 0,
          isDraining: deficit > 0,
          chargingRate: Math.abs(data.imbalance ?? 0),
        },
        grid: {
          frequency: data.frequency ?? 50.0,
          gridStatus: gridStatusMap[data.status] ?? 'BALANCED',
          efficiency: data.efficiency ?? 0,
          action: 'balanced',
          delta: data.imbalance ?? 0,
          alerts: [],
        },
        timestamp: data.timestamp ?? new Date().toISOString(),
      });
      setLastUpdated(new Date());
    } catch (err) {
      console.error('[App] Grid status fetch failed:', err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!isConnected) {
      const interval = setInterval(fetchData, 5000);
      return () => clearInterval(interval);
    }
  }, [isConnected, fetchData]);

  const dismissAlert = useCallback((id) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="fixed inset-0 z-[-2] pointer-events-none perspective-container">
        <div className={`grid-floor ${introPlaying ? 'hyper-grid-floor' : ''}`}></div>
        <div className={`grid-ceiling ${introPlaying ? 'hyper-grid-ceiling' : ''}`}></div>
      </div>
      <div className="min-h-screen bg-transparent text-slate-100 relative z-0">
        <div className="tunnel-vignette"></div>
        <div className={`speed-lines ${introPlaying ? 'hyper-speed-lines' : ''}`}></div>

        {introPlaying && (
          <div className="fixed inset-0 z-50 flex items-center justify-center flex-col gap-6 bg-black/60 backdrop-blur-sm transition-opacity duration-1000">
             <div className="w-24 h-24 rounded-full border-4 border-cyan-500/30 border-t-cyan-400 animate-spin" style={{boxShadow: '0 0 30px rgba(6, 182, 212, 0.5)'}} />
             <h2 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-pink-500 tracking-[0.3em] animate-pulse">
               SYSTEM BOOTING
             </h2>
             <p className="text-cyan-400 tracking-widest text-sm md:text-base animate-pulse">
               ESTABLISHING NEURAL LINK TO GRID...
             </p>
          </div>
        )}

        <div className={`transition-all duration-1000 ease-out origin-center ${introPlaying ? 'opacity-0 scale-90 blur-md pointer-events-none' : 'opacity-100 scale-100 blur-0'}`}>
        {/* Header */}
        <header className="sticky top-0 z-50 border-b border-cyan-500/30 bg-black/40 backdrop-blur-md">
          <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/30">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-bold gradient-text leading-tight">
                  Intelligent Energy Grid Balancer
                </h1>
                <p className="text-xs text-slate-500 hidden sm:block">
                  Real-time renewable energy management
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Connection status */}
              <div
                className={`hidden sm:flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border ${
                  isConnected
                    ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
                    : 'text-red-400 border-red-500/30 bg-red-500/10'
                }`}
              >
                {isConnected ? (
                  <Wifi className="w-3 h-3" />
                ) : (
                  <WifiOff className="w-3 h-3" />
                )}
                {isConnected ? 'Live' : 'Reconnecting…'}
              </div>

              {/* Last updated */}
              {lastUpdated && (
                <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-500">
                  <RefreshCw className="w-3 h-3" />
                  {lastUpdated.toLocaleTimeString()}
                </div>
              )}

              {/* Dark mode toggle */}
              <button
                onClick={() => setDarkMode((d) => !d)}
                className="p-2 rounded-lg border border-slate-700 hover:border-slate-500 bg-slate-800 hover:bg-slate-700 transition-all"
                aria-label="Toggle dark mode"
              >
                {darkMode ? (
                  <Sun className="w-4 h-4 text-yellow-400" />
                ) : (
                  <Moon className="w-4 h-4 text-slate-300" />
                )}
              </button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className={`max-w-[1600px] mx-auto px-4 sm:px-6 py-6 transition-all duration-1000 ${!isConnected && !isLoading ? 'grayscale opacity-75' : ''}`}>
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-96 gap-4">
              <div className="w-16 h-16 rounded-full border-4 border-emerald-500/20 border-t-emerald-500 animate-spin" />
              <p className="text-slate-400 animate-pulse">Connecting to energy grid…</p>
            </div>
          ) : (
            <Dashboard
              gridData={gridData}
              alerts={alerts}
              onDismissAlert={dismissAlert}
            />
          )}
        </main>
        </div>
      </div>
    </div>
  );
}
