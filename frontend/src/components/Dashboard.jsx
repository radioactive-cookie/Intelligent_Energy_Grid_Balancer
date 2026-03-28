import { Zap, TrendingUp, Battery, Activity } from 'lucide-react';
import EnergyGenerationPanel from './EnergyGenerationPanel';
import EnergyConsumptionPanel from './EnergyConsumptionPanel';
import GridStatusIndicator from './GridStatusIndicator';
import BatteryStorage from './BatteryStorage';
import DemandSupplyChart from './DemandSupplyChart';
import EnergySourcesChart from './EnergySourcesChart';
import AlertsPanel from './AlertsPanel';
import EnergyPath from './EnergyPath';
import ScenarioPlanner from './ScenarioPlanner';

function StatCard({ icon: Icon, label, value, unit, color, sublabel }) {
  return (
    <div className="glass-card glass-card-hover p-6 flex flex-col gap-3 group">
      <div className="flex items-center justify-between z-10">
        <span className="stat-label text-cyan-500 group-hover:text-cyan-400 group-hover:drop-shadow-[0_0_5px_rgba(34,211,238,0.8)] transition-all">{label}</span>
        <div className={`p-2 rounded-lg ${color} bg-opacity-20 backdrop-blur-md border border-white/5`}>
          <Icon className="w-5 h-5 animate-pulse" />
        </div>
      </div>
      <div className="z-10">
        <div className="flex items-end gap-1">
          <span className="stat-value font-mono text-4xl text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.8)] group-hover:scale-105 origin-left transition-transform">{value}</span>
          <span className="text-sm font-bold text-cyan-400 mb-1 tracking-widest uppercase">{unit}</span>
        </div>
        {sublabel && <p className="text-xs font-mono text-slate-400 mt-2 tracking-wide opacity-80 group-hover:opacity-100">{sublabel}</p>}
      </div>
    </div>
  );
}

export default function Dashboard({ gridData, alerts, onDismissAlert, onRunAIBalancer }) {
  const energy = gridData?.energy || {};
  const demand = gridData?.demand || {};
  const battery = gridData?.battery || {};
  const grid = gridData?.grid || {};

  const totalGeneration = energy.total ?? 0;
  const totalDemand = typeof demand === 'object' ? (demand.actual ?? 0) : (demand ?? 0);
  const batteryPct = battery.percentage ?? 0;
  const gridStatus = grid.gridStatus ?? 'BALANCED';

  const statusColor = {
    BALANCED: 'text-emerald-400',
    SURPLUS: 'text-blue-400',
    DEFICIT: 'text-orange-400',
    CRITICAL: 'text-red-400',
  }[gridStatus] || 'text-slate-400';
  const dataSource = energy.dataSource ?? 'simulated';
  const carbonIntensity = grid.carbonIntensity;
  const carbonLevel =
    carbonIntensity == null
      ? 'unknown'
      : carbonIntensity < 150
      ? 'low'
      : carbonIntensity < 400
      ? 'medium'
      : 'high';

  return (
    <div className="space-y-6 animate-[fadeIn_0.4s_ease-out]">
      {/* Stat cards row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Zap}
          label="Total Generation"
          value={totalGeneration.toFixed(1)}
          unit="MW"
          color="bg-emerald-500/20 text-emerald-400"
          sublabel={`☀ ${(energy.solar ?? 0).toFixed(1)} MW · 💨 ${(energy.wind ?? 0).toFixed(1)} MW`}
        />
        <StatCard
          icon={TrendingUp}
          label="Total Demand"
          value={totalDemand.toFixed(1)}
          unit="MW"
          color="bg-orange-500/20 text-orange-400"
          sublabel={`Pattern: ${typeof demand === 'object' ? (demand.pattern ?? '—') : '—'}`}
        />
        <StatCard
          icon={Battery}
          label="Battery Level"
          value={batteryPct.toFixed(1)}
          unit="%"
          color={
            batteryPct > 50
              ? 'bg-blue-500/20 text-blue-400'
              : batteryPct > 20
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-red-500/20 text-red-400'
          }
          sublabel={`${(battery.level ?? 0).toFixed(0)} / ${battery.capacity ?? 1000} MWh`}
        />
        <StatCard
          icon={Activity}
          label="Grid Status"
          value={gridStatus}
          unit=""
          color="bg-slate-700/50 text-slate-300"
          sublabel={`Efficiency: ${(grid.efficiency ?? 0).toFixed(1)}%`}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-4 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider">Data Source</p>
            <p className="text-sm text-slate-200 mt-1">Weather + generation feed</p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
              dataSource === 'real'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
            }`}
          >
            {dataSource}
          </span>
        </div>
        <div className="glass-card p-4 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider">Carbon Intensity</p>
            <p className="text-lg font-bold text-white mt-1">
              {carbonIntensity == null ? '—' : `${Number(carbonIntensity).toFixed(0)} gCO2/kWh`}
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
              carbonLevel === 'low'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : carbonLevel === 'medium'
                ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40'
                : carbonLevel === 'high'
                ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                : 'bg-slate-500/20 text-slate-300 border border-slate-500/40'
            }`}
          >
            {carbonLevel}
          </span>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <DemandSupplyChart gridData={gridData} />
        </div>
        <div>
          <EnergySourcesChart energy={energy} battery={battery} />
        </div>
      </div>

      {/* Energy Flow Animation */}
      <div className="glass-card hidden xl:block">
        <EnergyPath generation={totalGeneration} demand={totalDemand} />
      </div>

      {/* Panels row */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <EnergyGenerationPanel energy={energy} />
        <EnergyConsumptionPanel demand={demand} />
        <BatteryStorage battery={battery} />
        <GridStatusIndicator grid={grid} onRunAIBalancer={onRunAIBalancer} />
      </div>

      {/* Alerts */}
      <AlertsPanel alerts={alerts} onDismiss={onDismissAlert} />

      {/* Scenario Planner */}
      <ScenarioPlanner gridData={gridData} />
    </div>
  );
}
