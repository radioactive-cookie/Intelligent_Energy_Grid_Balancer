import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { simulateScenario } from '../services/api';

function round1(value) {
  return Number((Number(value) || 0).toFixed(1));
}

function demandScenarioLabel(multiplier) {
  if (multiplier <= 0.8) return 'off-peak night scenario';
  if (multiplier <= 1.1) return 'normal baseline';
  if (multiplier <= 1.5) return 'morning rush';
  if (multiplier <= 2.0) return 'evening peak';
  return 'extreme demand event';
}

function estimateScenario({ demandMultiplier, loadSheddingPercent, hour, baseData }) {
  const energy = baseData?.energy || {};
  const battery = baseData?.battery || {};

  const solar = round1(energy.solar ?? 0);
  const wind = round1(energy.wind ?? 0);
  const totalSupply = round1(solar + wind);
  const baseDemand = round1(baseData?.demand?.predicted ?? baseData?.demand?.actual ?? 600);
  const scaled = round1(baseDemand * demandMultiplier);

  const industrialDemand = round1(scaled * 0.4);
  const commercialDemand = round1(scaled * 0.3);
  const residentialDemand = round1(scaled * 0.3);

  const industrialShed = round1(industrialDemand * (loadSheddingPercent / 100));
  const commercialShed = round1(commercialDemand * ((loadSheddingPercent / 2) / 100));
  const totalShed = round1(industrialShed + commercialShed);
  const afterShedding = round1(scaled - totalShed);
  const gap = round1(afterShedding - totalSupply);

  const batteryCurrent = round1(battery.level ?? 0);
  const batteryCapacity = round1(battery.capacity ?? 1000);
  const batteryPercent = batteryCapacity > 0 ? round1((batteryCurrent / batteryCapacity) * 100) : 0;
  const drain = gap > 0 ? gap : 0;

  let strategyLabel = 'SURPLUS_STORE';
  if (gap > 400) strategyLabel = 'CRITICAL_SHED_ALL';
  else if (gap > 100) strategyLabel = 'LOAD_SHEDDING_AND_BATTERY';
  else if (gap > 0) strategyLabel = 'MINOR_DEFICIT_BATTERY_ONLY';

  return {
    scenario: { demandMultiplier: round1(demandMultiplier), hour },
    supply: { solar, wind, total: totalSupply },
    demand: {
      base: baseDemand,
      scaled,
      afterShedding,
      loadShedKw: totalShed,
    },
    gap,
    gridStatus: gap > 0 ? 'DEFICIT' : 'SURPLUS',
    battery: {
      currentKwh: batteryCurrent,
      capacityKwh: batteryCapacity,
      percentCharged: batteryPercent,
      netDrainRateKw: drain,
      survivalHours: drain > 0 ? round1(batteryCurrent / Math.max(drain, 1)) : null,
      survivalHoursWithSolar: drain > 0 ? round1(batteryCurrent / Math.max(drain - solar * 0.3, 1)) : null,
    },
    zones: {
      industrial: { demandKw: industrialDemand, shedKw: industrialShed, shedPercent: loadSheddingPercent },
      commercial: { demandKw: commercialDemand, shedKw: commercialShed, shedPercent: round1(loadSheddingPercent / 2) },
      residential: { demandKw: residentialDemand, shedKw: 0, shedPercent: 0 },
    },
    strategy: {
      label: strategyLabel,
      steps: [
        {
          order: 1,
          action: 'Maximise renewable harvest',
          detail: `Solar + wind at full output: ${round1(totalSupply)} kW`,
        },
      ],
    },
    alerts: gap > 0 ? ['DEFICIT', 'BATTERY_DRAW_ACTIVE'] : ['SURPLUS'],
    timestamp: new Date().toISOString(),
  };
}

function MetricCard({ label, value, unit, valueClassName = 'text-white', subLabel }) {
  return (
    <div className="glass-card p-4">
      <p className="text-[11px] uppercase tracking-widest text-slate-400">{label}</p>
      <div className="mt-2 flex items-end gap-1">
        <span className={`text-2xl font-bold tabular-nums ${valueClassName}`}>{value}</span>
        <span className="text-xs text-slate-400 mb-1">{unit}</span>
      </div>
      {subLabel ? <p className="text-xs text-slate-500 mt-1">{subLabel}</p> : null}
    </div>
  );
}

export default function ScenarioPlanner({ gridData }) {
  const navigate = useNavigate();
  const [demandMultiplier, setDemandMultiplier] = useState(1.0);
  const [loadSheddingPercent, setLoadSheddingPercent] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorFallback, setErrorFallback] = useState(false);

  const scenarioMeaning = useMemo(() => demandScenarioLabel(demandMultiplier), [demandMultiplier]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      setLoading(true);
      setErrorFallback(false);
      const hour = new Date().getHours();

      try {
        const response = await simulateScenario({
          demandMultiplier,
          loadSheddingPercent,
          hour,
        });
        setResult(response);
      } catch (error) {
        setErrorFallback(true);
        setResult(
          estimateScenario({
            demandMultiplier,
            loadSheddingPercent,
            hour,
            baseData: gridData,
          }),
        );
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [demandMultiplier, loadSheddingPercent, gridData]);

  const gridStatusBadge = useMemo(() => {
    const gap = result?.gap ?? 0;
    if (gap <= 0) {
      return { label: 'SURPLUS', className: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' };
    }
    if (gap <= 100) {
      return { label: 'MINOR DEFICIT', className: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
    }
    if (gap <= 400) {
      return { label: 'MAJOR DEFICIT', className: 'bg-red-500/20 text-red-300 border-red-500/40' };
    }
    return { label: 'CRITICAL', className: 'bg-red-600/30 text-red-200 border-red-500/60 animate-pulse' };
  }, [result]);

  const gapValue = round1(result?.gap ?? 0);

  return (
    <section className="glass-card p-4 md:p-6 mt-6">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Scenario Planner</h3>
          <p className="text-xs text-slate-500 mt-1">Tune demand and demand response to preview balancing strategy.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="text-xs text-slate-300">
          <div>Demand multiplier: x{demandMultiplier.toFixed(1)}</div>
          <input
            type="range"
            min="0.5"
            max="3.0"
            step="0.1"
            value={demandMultiplier}
            onChange={(e) => setDemandMultiplier(Number(e.target.value))}
            className="w-full mt-2"
          />
          <p className="text-slate-500 mt-1">Simulating {scenarioMeaning}</p>
        </label>

        <label className="text-xs text-slate-300">
          <div>Demand response: {loadSheddingPercent}% industrial reduction</div>
          <input
            type="range"
            min="0"
            max="40"
            step="5"
            value={loadSheddingPercent}
            onChange={(e) => setLoadSheddingPercent(Number(e.target.value))}
            className="w-full mt-2"
          />
        </label>
      </div>

      {errorFallback ? (
        <p className="text-xs text-amber-300 mt-3">Backend unavailable — showing estimated values</p>
      ) : null}

      {loading && !result ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-5">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="glass-card p-4 animate-pulse">
              <div className="h-3 w-24 bg-slate-700/50 rounded" />
              <div className="h-7 w-20 bg-slate-700/60 rounded mt-3" />
              <div className="h-2 w-28 bg-slate-800/70 rounded mt-2" />
            </div>
          ))}
        </div>
      ) : null}

      {result ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-5">
            <MetricCard label="Required supply" value={round1(result.demand?.afterShedding ?? 0).toFixed(1)} unit="kW" />
            <MetricCard label="Current renewable supply" value={round1(result.supply?.total ?? 0).toFixed(1)} unit="kW" />
            <MetricCard
              label="Gap to cover"
              value={Math.abs(gapValue).toFixed(1)}
              unit="kW"
              valueClassName={gapValue > 0 ? 'text-red-300' : 'text-emerald-300'}
            />
            <MetricCard
              label="Battery survival time"
              value={result.battery?.survivalHours == null ? '—' : round1(result.battery.survivalHours).toFixed(1)}
              unit="hrs"
              subLabel="at current drain rate"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 mt-4">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${gridStatusBadge.className}`}>
              {gridStatusBadge.label}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-semibold border border-cyan-500/40 bg-cyan-500/10 text-cyan-200">
              {result.strategy?.label ?? '—'}
            </span>
          </div>

          <div className="mt-4">
            <p className="text-xs uppercase tracking-widest text-slate-400 mb-2">Recommended strategy steps</p>
            <ol className="space-y-2">
              {(result.strategy?.steps ?? []).map((step) => (
                <li key={step.order} className="text-sm text-slate-200">
                  <span className="font-semibold mr-2">{step.order}.</span>
                  <span className="font-semibold">{step.action}</span>
                  <span className="text-slate-400"> — {step.detail}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="mt-5">
            <button
              type="button"
              onClick={() => navigate(`/strategy?mult=${demandMultiplier.toFixed(1)}&shed=${loadSheddingPercent}`)}
              className="px-4 py-2 rounded-lg border border-cyan-400/70 text-cyan-200 hover:bg-cyan-500/10 transition-colors font-semibold"
            >
              View full strategy flowchart
            </button>
          </div>
        </>
      ) : null}
    </section>
  );
}
