import { Sun, Moon, Wind, Zap } from 'lucide-react';

export default function EnergyGenerationPanel({ energy = {} }) {
  const solar = energy.solar ?? 0;
  const wind = energy.wind ?? 0;
  const total = energy.total ?? 0;

  const MAX_SOLAR = 500;
  const MAX_WIND = 300;

  const solarPct = Math.min(100, (solar / MAX_SOLAR) * 100);
  const windPct = Math.min(100, (wind / MAX_WIND) * 100);

  return (
    <div className="glass-card p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Energy Generation
        </h3>
        <Zap className="w-4 h-4 text-emerald-400" />
      </div>

      {/* Solar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {solar > 0 ? (
              <Sun className="w-5 h-5 text-yellow-400 animate-pulse-slow" />
            ) : (
              <Moon className="w-5 h-5 text-slate-500" />
            )}
            <span className="text-sm text-slate-300">Solar</span>
          </div>
          <span className={`text-sm font-bold tabular-nums ${solar > 0 ? 'gradient-text-solar' : 'text-slate-500'}`}>
            {solar.toFixed(1)} kW
          </span>
        </div>
        <div className={`progress-track ${solar === 0 ? 'bg-slate-800/50' : ''}`}>
          <div
            className={`progress-fill ${solar > 0 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 'bg-slate-700'}`}
            style={{ width: `${solarPct}%` }}
          />
        </div>
        <p className="text-xs text-slate-500">{solarPct.toFixed(0)}% of peak capacity</p>
      </div>

      {/* Wind */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wind className="w-5 h-5 text-purple-400 animate-spin-slow" />
            <span className="text-sm text-slate-300">Wind</span>
          </div>
          <span className="text-sm font-bold gradient-text-wind tabular-nums">
            {wind.toFixed(1)} kW
          </span>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill bg-gradient-to-r from-purple-500 to-cyan-500"
            style={{ width: `${windPct}%` }}
          />
        </div>
        <p className="text-xs text-slate-500">{windPct.toFixed(0)}% of peak capacity</p>
      </div>

      {/* Total */}
      <div className="pt-2 border-t border-slate-700/50 flex items-center justify-between">
        <span className="text-xs text-slate-400 uppercase tracking-wide">Total Renewable</span>
        <span className="text-base font-bold text-emerald-400 tabular-nums">
          {total.toFixed(1)} kW
        </span>
      </div>
    </div>
  );
}
