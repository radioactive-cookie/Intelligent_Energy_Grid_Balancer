import { Activity, CheckCircle, AlertTriangle, XCircle, ArrowUpDown } from 'lucide-react';

const STATUS_CONFIG = {
  BALANCED: {
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/20',
    border: 'border-emerald-500/30',
    dot: 'bg-emerald-400',
    icon: CheckCircle,
    label: 'Balanced',
  },
  SURPLUS: {
    color: 'text-blue-400',
    bg: 'bg-blue-500/20',
    border: 'border-blue-500/30',
    dot: 'bg-blue-400',
    icon: ArrowUpDown,
    label: 'Surplus',
  },
  DEFICIT: {
    color: 'text-orange-400',
    bg: 'bg-orange-500/20',
    border: 'border-orange-500/30',
    dot: 'bg-orange-400',
    icon: AlertTriangle,
    label: 'Deficit',
  },
  CRITICAL: {
    color: 'text-red-400',
    bg: 'bg-red-500/20',
    border: 'border-red-500/30',
    dot: 'bg-red-400',
    icon: XCircle,
    label: 'Critical',
  },
};

export default function GridStatusIndicator({ grid = {} }) {
  const status = grid.gridStatus ?? 'BALANCED';
  const efficiency = grid.efficiency ?? 0;
  const action = grid.action ?? 'balanced';
  const delta = grid.delta ?? 0;

  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.BALANCED;
  const Icon = cfg.icon;

  return (
    <div className="glass-card p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Grid Health
        </h3>
        <Activity className="w-4 h-4 text-cyan-400" />
      </div>

      {/* Status badge */}
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${cfg.bg} ${cfg.border}`}>
        <span className={`relative flex h-2.5 w-2.5`}>
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full ${cfg.dot} opacity-75`}
          />
          <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${cfg.dot}`} />
        </span>
        <Icon className={`w-5 h-5 ${cfg.color}`} />
        <span className={`font-bold text-sm ${cfg.color}`}>{cfg.label}</span>
      </div>

      {/* Efficiency */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">Grid Efficiency</span>
          <span className="text-xs font-semibold text-slate-200 tabular-nums">
            {efficiency.toFixed(1)}%
          </span>
        </div>
        <div className="progress-track">
          <div
            className={`progress-fill ${
              efficiency > 80
                ? 'bg-gradient-to-r from-emerald-500 to-cyan-500'
                : efficiency > 60
                ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                : 'bg-gradient-to-r from-red-600 to-red-500'
            }`}
            style={{ width: `${efficiency}%` }}
          />
        </div>
      </div>

      {/* Action */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-slate-700/30 rounded-lg p-2.5">
          <p className="text-xs text-slate-500">Action</p>
          <p className="text-xs font-semibold text-slate-200 mt-0.5 capitalize">{action}</p>
        </div>
        <div className="bg-slate-700/30 rounded-lg p-2.5">
          <p className="text-xs text-slate-500">Net Delta</p>
          <p
            className={`text-xs font-semibold mt-0.5 tabular-nums ${
              delta >= 0 ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {delta >= 0 ? '+' : ''}
            {delta.toFixed(1)} kW
          </p>
        </div>
      </div>
    </div>
  );
}
