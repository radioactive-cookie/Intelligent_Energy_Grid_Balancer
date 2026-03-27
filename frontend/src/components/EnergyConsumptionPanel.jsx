import { TrendingUp, Clock } from 'lucide-react';

const PATTERN_LABELS = {
  'morning-rush': { label: 'Morning Rush', color: 'text-orange-400', bg: 'bg-orange-500/20' },
  'midday': { label: 'Midday', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
  'evening-peak': { label: 'Evening Peak', color: 'text-red-400', bg: 'bg-red-500/20' },
  'night': { label: 'Night', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  'off-peak': { label: 'Off-Peak', color: 'text-slate-400', bg: 'bg-slate-500/20' },
};

export default function EnergyConsumptionPanel({ demand = {} }) {
  const predicted = demand.predicted ?? 0;
  const actual = typeof demand === 'object' ? (demand.actual ?? 0) : (demand ?? 0);
  const pattern = demand.pattern ?? 'off-peak';
  const hour = demand.hour ?? new Date().getHours();

  const MAX_DEMAND = 900; // kW ceiling
  const demandPct = Math.min(100, (actual / MAX_DEMAND) * 100);

  const patternInfo = PATTERN_LABELS[pattern] || PATTERN_LABELS['off-peak'];
  const deviation = predicted > 0 ? ((actual - predicted) / predicted) * 100 : 0;

  return (
    <div className="glass-card p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Energy Consumption
        </h3>
        <TrendingUp className="w-4 h-4 text-orange-400" />
      </div>

      {/* Current demand */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Current Demand</span>
          <span className="text-sm font-bold text-orange-400 tabular-nums">
            {actual.toFixed(1)} kW
          </span>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill bg-gradient-to-r from-orange-600 to-red-500"
            style={{ width: `${demandPct}%` }}
          />
        </div>
      </div>

      {/* Predicted vs actual */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-700/30 rounded-xl p-3">
          <p className="text-xs text-slate-500">Predicted</p>
          <p className="text-base font-semibold text-slate-200 tabular-nums mt-0.5">
            {predicted.toFixed(1)} kW
          </p>
        </div>
        <div className="bg-slate-700/30 rounded-xl p-3">
          <p className="text-xs text-slate-500">Deviation</p>
          <p
            className={`text-base font-semibold tabular-nums mt-0.5 ${
              Math.abs(deviation) < 5 ? 'text-emerald-400' : 'text-orange-400'
            }`}
          >
            {deviation >= 0 ? '+' : ''}
            {deviation.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Time indicator */}
      <div className={`flex items-center justify-between px-3 py-2 rounded-lg ${patternInfo.bg}`}>
        <div className="flex items-center gap-2">
          <Clock className={`w-3.5 h-3.5 ${patternInfo.color}`} />
          <span className={`text-xs font-medium ${patternInfo.color}`}>{patternInfo.label}</span>
        </div>
        <span className="text-xs text-slate-500 tabular-nums">{String(hour).padStart(2, '0')}:00</span>
      </div>
    </div>
  );
}
