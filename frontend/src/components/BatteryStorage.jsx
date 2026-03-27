import { Battery, BatteryCharging, BatteryLow } from 'lucide-react';

export default function BatteryStorage({ battery = {} }) {
  const pct = battery.percentage ?? 0;
  const level = battery.level ?? 0;
  const capacity = battery.capacity ?? 1000;
  const isCharging = battery.isCharging ?? false;
  const isDraining = battery.isDraining ?? false;
  const chargingRate = battery.chargingRate ?? 0;

  const barColor =
    pct > 50
      ? 'from-emerald-500 to-cyan-500'
      : pct > 20
      ? 'from-yellow-500 to-orange-500'
      : 'from-red-600 to-red-500';

  const textColor =
    pct > 50 ? 'text-emerald-400' : pct > 20 ? 'text-yellow-400' : 'text-red-400';

  const BatteryIcon = pct < 20 ? BatteryLow : isCharging ? BatteryCharging : Battery;

  return (
    <div className="glass-card p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Battery Storage
        </h3>
        <BatteryIcon className={`w-5 h-5 ${textColor} ${isCharging ? 'animate-pulse' : ''}`} />
      </div>

      {/* Battery body */}
      <div className="flex flex-col items-center gap-3">
        {/* Visual battery */}
        <div className="relative w-full h-10 rounded-lg bg-slate-700/60 border border-slate-600/50 overflow-hidden">
          <div
            className={`absolute inset-y-0 left-0 bg-gradient-to-r ${barColor} transition-all duration-700 ease-out rounded-lg`}
            style={{ width: `${pct}%` }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-sm font-bold tabular-nums drop-shadow ${textColor}`}>
              {pct.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Level info */}
        <div className="w-full grid grid-cols-2 gap-2">
          <div className="bg-slate-700/30 rounded-lg p-2.5">
            <p className="text-xs text-slate-500">Stored</p>
            <p className={`text-sm font-bold tabular-nums mt-0.5 ${textColor}`}>
              {level.toFixed(0)} kWh
            </p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-2.5">
            <p className="text-xs text-slate-500">Capacity</p>
            <p className="text-sm font-bold tabular-nums mt-0.5 text-slate-200">
              {capacity} kWh
            </p>
          </div>
        </div>
      </div>

      {/* Charge status */}
      <div
        className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium ${
          isCharging
            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
            : isDraining
            ? 'bg-orange-500/15 text-orange-400 border border-orange-500/20'
            : 'bg-slate-700/30 text-slate-400 border border-slate-600/30'
        }`}
      >
        <span>{isCharging ? '⬆ Charging' : isDraining ? '⬇ Discharging' : '— Idle'}</span>
        <span className="tabular-nums">
          {Math.abs(chargingRate).toFixed(1)} kW
        </span>
      </div>
    </div>
  );
}
