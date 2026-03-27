import { Zap, TrendingUp, Battery, Activity } from 'lucide-react';
import EnergyGenerationPanel from './EnergyGenerationPanel';
import EnergyConsumptionPanel from './EnergyConsumptionPanel';
import GridStatusIndicator from './GridStatusIndicator';
import BatteryStorage from './BatteryStorage';
import DemandSupplyChart from './DemandSupplyChart';
import EnergySourcesChart from './EnergySourcesChart';
import AlertsPanel from './AlertsPanel';

function StatCard({ icon: Icon, label, value, unit, color, sublabel }) {
  return (
    <div className="glass-card p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="stat-label">{label}</span>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div>
        <div className="flex items-end gap-1">
          <span className="stat-value">{value}</span>
          <span className="text-sm text-slate-400 mb-1">{unit}</span>
        </div>
        {sublabel && <p className="text-xs text-slate-500 mt-1">{sublabel}</p>}
      </div>
    </div>
  );
}

export default function Dashboard({ gridData, alerts, onDismissAlert }) {
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

  return (
    <div className="space-y-6 animate-[fadeIn_0.4s_ease-out]">
      {/* Stat cards row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Zap}
          label="Total Generation"
          value={totalGeneration.toFixed(1)}
          unit="kW"
          color="bg-emerald-500/20 text-emerald-400"
          sublabel={`☀ ${(energy.solar ?? 0).toFixed(1)} kW · 💨 ${(energy.wind ?? 0).toFixed(1)} kW`}
        />
        <StatCard
          icon={TrendingUp}
          label="Total Demand"
          value={totalDemand.toFixed(1)}
          unit="kW"
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
          sublabel={`${(battery.level ?? 0).toFixed(0)} / ${battery.capacity ?? 1000} kWh`}
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

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <DemandSupplyChart gridData={gridData} />
        </div>
        <div>
          <EnergySourcesChart energy={energy} battery={battery} />
        </div>
      </div>

      {/* Panels row */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <EnergyGenerationPanel energy={energy} />
        <EnergyConsumptionPanel demand={demand} />
        <BatteryStorage battery={battery} />
        <GridStatusIndicator grid={grid} />
      </div>

      {/* Alerts */}
      <AlertsPanel alerts={alerts} onDismiss={onDismissAlert} />
    </div>
  );
}
