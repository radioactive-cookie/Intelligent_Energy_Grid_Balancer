import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  BarChart,
  Bar,
} from 'recharts';
import { ArrowLeft } from 'lucide-react';
import { simulateScenario } from '../services/api';

function round1(value) {
  return Number((Number(value) || 0).toFixed(1));
}

function estimateScenario({ demandMultiplier, loadSheddingPercent, hour }) {
  const baseDemand = 600;
  const solar = 200;
  const wind = 150;
  const total = solar + wind;
  const scaled = round1(baseDemand * demandMultiplier);

  const industrial = round1(scaled * 0.4);
  const commercial = round1(scaled * 0.3);
  const residential = round1(scaled * 0.3);

  const industrialShed = round1(industrial * (loadSheddingPercent / 100));
  const commercialShed = round1(commercial * ((loadSheddingPercent / 2) / 100));
  const loadShedKw = round1(industrialShed + commercialShed);
  const afterShedding = round1(scaled - loadShedKw);
  const gap = round1(afterShedding - total);

  const currentKwh = 350;
  const capacityKwh = 500;
  const percentCharged = round1((currentKwh / capacityKwh) * 100);

  let label = 'SURPLUS_STORE';
  if (gap > 400) label = 'CRITICAL_SHED_ALL';
  else if (gap > 100) label = 'LOAD_SHEDDING_AND_BATTERY';
  else if (gap > 0) label = 'MINOR_DEFICIT_BATTERY_ONLY';

  return {
    scenario: { demandMultiplier: round1(demandMultiplier), hour },
    supply: { solar, wind, total },
    demand: { base: baseDemand, scaled, afterShedding, loadShedKw },
    gap,
    gridStatus: gap > 0 ? 'DEFICIT' : 'SURPLUS',
    battery: {
      currentKwh,
      capacityKwh,
      percentCharged,
      netDrainRateKw: gap > 0 ? gap : 0,
      survivalHours: gap > 0 ? round1(currentKwh / Math.max(gap, 1)) : null,
      survivalHoursWithSolar: gap > 0 ? round1(currentKwh / Math.max(gap - solar * 0.3, 1)) : null,
    },
    zones: {
      industrial: { demandKw: industrial, shedKw: industrialShed, shedPercent: loadSheddingPercent },
      commercial: { demandKw: commercial, shedKw: commercialShed, shedPercent: round1(loadSheddingPercent / 2) },
      residential: { demandKw: residential, shedKw: 0, shedPercent: 0 },
    },
    strategy: {
      label,
      steps: [
        { order: 1, action: 'Maximise renewable harvest', detail: `Solar + wind at full output: ${round1(total)} kW` },
      ],
    },
    alerts: gap > 0 ? ['DEFICIT', 'BATTERY_DRAW_ACTIVE'] : ['SURPLUS'],
    timestamp: new Date().toISOString(),
  };
}

function buildBatteryTimeline({ percentCharged, netDrainRateKw, currentKwh, survivalHoursWithSolar }) {
  const points = [];
  const noSolarDrainPercentPerHour = currentKwh > 0 ? ((netDrainRateKw / currentKwh) * percentCharged) : 0;
  const withSolarDrainPercentPerHour =
    survivalHoursWithSolar && survivalHoursWithSolar > 0 ? percentCharged / survivalHoursWithSolar : noSolarDrainPercentPerHour;

  for (let h = 0; h <= 12; h += 1) {
    const withoutSolar = Math.max(0, round1(percentCharged - noSolarDrainPercentPerHour * h));
    const withSolar = Math.max(0, round1(percentCharged - withSolarDrainPercentPerHour * h));
    points.push({ hour: h, withoutSolar, withSolar });
  }

  return points;
}

function getCriticalHour(points, key) {
  const match = points.find((p) => p[key] <= 10);
  return match ? match.hour : null;
}

function StrategyFlowSvg({ scenario }) {
  const deficit = (scenario?.gap ?? 0) > 0;
  const batteryLow = (scenario?.battery?.percentCharged ?? 0) < 20;
  const supplyTotal = round1(scenario?.supply?.total ?? 0);
  const demandScaled = round1(scenario?.demand?.scaled ?? 0);
  const chargeRate = !deficit ? round1(Math.abs(scenario?.gap ?? 0)) : 0;
  const netDrain = round1(scenario?.battery?.netDrainRateKw ?? 0);

  return (
    <div className="glass-card p-4 overflow-x-auto">
      <svg width="1200" height="760" viewBox="0 0 1200 760" className="min-w-[1000px]">
        <defs>
          <marker id="arrowGreen" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="#34d399" />
          </marker>
          <marker id="arrowRed" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="#f87171" />
          </marker>
          <marker id="arrowGray" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="#94a3b8" />
          </marker>
        </defs>

        <rect x="80" y="40" width="220" height="70" fill="#f59e0b22" stroke="#f59e0b" rx="12" ry="12" strokeWidth="2" />
        <text x="190" y="67" textAnchor="middle" fill="#fcd34d" fontSize="14" fontWeight="700">Solar source</text>
        <text x="190" y="90" textAnchor="middle" fill="#f1f5f9" fontSize="13">{round1(scenario?.supply?.solar ?? 0)} kW</text>

        <rect x="360" y="40" width="220" height="70" fill="#14b8a622" stroke="#14b8a6" rx="12" ry="12" strokeWidth="2" />
        <text x="470" y="67" textAnchor="middle" fill="#5eead4" fontSize="14" fontWeight="700">Wind source</text>
        <text x="470" y="90" textAnchor="middle" fill="#f1f5f9" fontSize="13">{round1(scenario?.supply?.wind ?? 0)} kW</text>

        <rect
          x="640"
          y="40"
          width="240"
          height="70"
          fill={batteryLow ? '#ef444422' : '#3b82f622'}
          stroke={batteryLow ? '#ef4444' : '#3b82f6'}
          rx="12"
          ry="12"
          strokeWidth="2"
        />
        <text x="760" y="67" textAnchor="middle" fill={batteryLow ? '#fca5a5' : '#93c5fd'} fontSize="14" fontWeight="700">Battery</text>
        <text x="760" y="90" textAnchor="middle" fill="#f1f5f9" fontSize="13">
          {round1(scenario?.battery?.currentKwh ?? 0)} / {round1(scenario?.battery?.capacityKwh ?? 0)} kWh ({round1(scenario?.battery?.percentCharged ?? 0)}%)
        </text>

        <rect x="330" y="170" width="360" height="80" fill="#8b5cf622" stroke="#8b5cf6" rx="12" ry="12" strokeWidth="2" />
        <text x="510" y="200" textAnchor="middle" fill="#c4b5fd" fontSize="16" fontWeight="700">Main grid bus</text>
        <text x="510" y="225" textAnchor="middle" fill="#f1f5f9" fontSize="13">
          Supply {supplyTotal} kW vs demand {demandScaled} kW
        </text>

        <line x1="190" y1="110" x2="430" y2="170" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#arrowGray)" />
        <line x1="470" y1="110" x2="500" y2="170" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#arrowGray)" />
        <line x1="760" y1="110" x2="590" y2="170" stroke={deficit ? '#f87171' : '#34d399'} strokeWidth={deficit ? 4 : 2} markerEnd={deficit ? 'url(#arrowRed)' : 'url(#arrowGreen)'} />
        <text x="680" y="140" fill={deficit ? '#fca5a5' : '#86efac'} fontSize="12">{deficit ? `${netDrain} kW draw` : `${chargeRate} kW charge`}</text>

        <polygon points="510,300 620,360 510,420 400,360" fill="#1e293b" stroke="#94a3b8" strokeWidth="2" />
        <text x="510" y="355" textAnchor="middle" fill="#e2e8f0" fontSize="14" fontWeight="700">Supply ≥ Demand?</text>

        <line x1="510" y1="250" x2="510" y2="300" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#arrowGray)" />

        <text x="350" y="330" fill="#86efac" fontSize="12" fontWeight="700">YES</text>
        <line x1="400" y1="360" x2="250" y2="360" stroke={deficit ? '#64748b' : '#34d399'} strokeWidth={deficit ? 1.5 : 5} markerEnd={deficit ? 'url(#arrowGray)' : 'url(#arrowGreen)'} />
        <rect x="120" y="330" width="120" height="60" fill={deficit ? '#33415555' : '#16a34a22'} stroke={deficit ? '#64748b' : '#22c55e'} rx="10" ry="10" strokeWidth="2" />
        <text x="180" y="355" textAnchor="middle" fill="#e2e8f0" fontSize="13" fontWeight="700">Charge battery</text>
        <text x="180" y="375" textAnchor="middle" fill="#cbd5e1" fontSize="12">{chargeRate} kW</text>

        <text x="665" y="330" fill="#fca5a5" fontSize="12" fontWeight="700">NO</text>
        <line x1="620" y1="360" x2="760" y2="360" stroke={deficit ? '#ef4444' : '#64748b'} strokeWidth={deficit ? 5 : 1.5} markerEnd={deficit ? 'url(#arrowRed)' : 'url(#arrowGray)'} />

        <rect x="760" y="330" width="150" height="60" fill={deficit ? '#7f1d1d44' : '#33415566'} stroke={deficit ? '#ef4444' : '#64748b'} rx="10" ry="10" strokeWidth="2" />
        <text x="835" y="355" textAnchor="middle" fill="#e2e8f0" fontSize="13" fontWeight="700">Deficit detected</text>
        <text x="835" y="375" textAnchor="middle" fill="#fca5a5" fontSize="12">{Math.max(round1(scenario?.gap ?? 0), 0)} kW</text>

        <rect x="940" y="330" width="140" height="60" fill={deficit ? '#991b1b44' : '#33415566'} stroke={deficit ? '#ef4444' : '#64748b'} rx="10" ry="10" strokeWidth="2" />
        <text x="1010" y="355" textAnchor="middle" fill="#e2e8f0" fontSize="13" fontWeight="700">Industrial shed</text>
        <text x="1010" y="375" textAnchor="middle" fill="#fca5a5" fontSize="12">-{round1(scenario?.zones?.industrial?.shedKw ?? 0)} kW</text>

        <line x1="910" y1="360" x2="940" y2="360" stroke={deficit ? '#ef4444' : '#64748b'} strokeWidth={deficit ? 5 : 1.5} markerEnd={deficit ? 'url(#arrowRed)' : 'url(#arrowGray)'} />

        <rect x="940" y="420" width="140" height="60" fill={deficit ? '#991b1b44' : '#33415566'} stroke={deficit ? '#ef4444' : '#64748b'} rx="10" ry="10" strokeWidth="2" />
        <text x="1010" y="445" textAnchor="middle" fill="#e2e8f0" fontSize="13" fontWeight="700">Commercial shed</text>
        <text x="1010" y="465" textAnchor="middle" fill="#fca5a5" fontSize="12">-{round1(scenario?.zones?.commercial?.shedKw ?? 0)} kW</text>

        <line x1="1010" y1="390" x2="1010" y2="420" stroke={deficit ? '#ef4444' : '#64748b'} strokeWidth={deficit ? 5 : 1.5} markerEnd={deficit ? 'url(#arrowRed)' : 'url(#arrowGray)'} />

        <rect x="940" y="510" width="170" height="70" fill={deficit ? '#7f1d1d44' : '#33415566'} stroke={deficit ? '#ef4444' : '#64748b'} rx="10" ry="10" strokeWidth="2" />
        <text x="1025" y="535" textAnchor="middle" fill="#e2e8f0" fontSize="13" fontWeight="700">Battery draw</text>
        <text x="1025" y="555" textAnchor="middle" fill="#fca5a5" fontSize="12">{round1(scenario?.battery?.netDrainRateKw ?? 0)} kW</text>
        <text x="1025" y="572" textAnchor="middle" fill="#fca5a5" fontSize="12">
          {scenario?.battery?.survivalHours == null ? '—' : round1(scenario.battery.survivalHours)} hrs
        </text>

        <line x1="1010" y1="480" x2="1010" y2="510" stroke={deficit ? '#ef4444' : '#64748b'} strokeWidth={deficit ? 5 : 1.5} markerEnd={deficit ? 'url(#arrowRed)' : 'url(#arrowGray)'} />

        <rect x="220" y="640" width="220" height="80" fill="#33415566" stroke="#64748b" rx="12" ry="12" strokeWidth="2" />
        <text x="330" y="668" textAnchor="middle" fill="#e2e8f0" fontSize="14" fontWeight="700">Industrial</text>
        <text x="330" y="690" textAnchor="middle" fill="#cbd5e1" fontSize="12">Demand {round1(scenario?.zones?.industrial?.demandKw ?? 0)} kW</text>
        <text x="330" y="706" textAnchor="middle" fill="#fca5a5" fontSize="12">Shed {round1(scenario?.zones?.industrial?.shedKw ?? 0)} kW</text>

        <rect x="490" y="640" width="220" height="80" fill="#33415566" stroke="#64748b" rx="12" ry="12" strokeWidth="2" />
        <text x="600" y="668" textAnchor="middle" fill="#e2e8f0" fontSize="14" fontWeight="700">Commercial</text>
        <text x="600" y="690" textAnchor="middle" fill="#cbd5e1" fontSize="12">Demand {round1(scenario?.zones?.commercial?.demandKw ?? 0)} kW</text>
        <text x="600" y="706" textAnchor="middle" fill="#fca5a5" fontSize="12">Shed {round1(scenario?.zones?.commercial?.shedKw ?? 0)} kW</text>

        <rect x="760" y="640" width="220" height="80" fill="#33415566" stroke="#64748b" rx="12" ry="12" strokeWidth="2" />
        <text x="870" y="668" textAnchor="middle" fill="#e2e8f0" fontSize="14" fontWeight="700">Residential</text>
        <text x="870" y="690" textAnchor="middle" fill="#cbd5e1" fontSize="12">Demand {round1(scenario?.zones?.residential?.demandKw ?? 0)} kW</text>
        <text x="870" y="706" textAnchor="middle" fill="#86efac" fontSize="12">Protected — no shedding</text>

        <line x1="510" y1="420" x2="510" y2="610" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#arrowGray)" />
        <line x1="510" y1="610" x2="330" y2="640" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#arrowGray)" />
        <line x1="510" y1="610" x2="600" y2="640" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#arrowGray)" />
        <line x1="510" y1="610" x2="870" y2="640" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#arrowGray)" />

        {deficit ? (
          <>
            <line x1="1025" y1="580" x2="870" y2="640" stroke="#ef4444" strokeWidth="5" markerEnd="url(#arrowRed)" />
            <line x1="1025" y1="580" x2="600" y2="640" stroke="#ef4444" strokeWidth="4" markerEnd="url(#arrowRed)" />
            <line x1="1025" y1="580" x2="330" y2="640" stroke="#ef4444" strokeWidth="4" markerEnd="url(#arrowRed)" />
          </>
        ) : (
          <>
            <line x1="180" y1="390" x2="760" y2="70" stroke="#34d399" strokeWidth="5" markerEnd="url(#arrowGreen)" />
          </>
        )}
      </svg>
    </div>
  );
}

function MetricCard({ label, value, unit, subLabel, valueClassName = 'text-white' }) {
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

export default function StrategyPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const multParam = Number(searchParams.get('mult') ?? 1);
  const shedParam = Number(searchParams.get('shed') ?? 0);

  const [demandMultiplier, setDemandMultiplier] = useState(Number.isFinite(multParam) ? multParam : 1);
  const [loadSheddingPercent, setLoadSheddingPercent] = useState(Number.isFinite(shedParam) ? shedParam : 0);
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    setSearchParams({ mult: demandMultiplier.toFixed(1), shed: String(loadSheddingPercent) });
  }, [demandMultiplier, loadSheddingPercent, setSearchParams]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      setLoading(true);
      setFallback(false);
      const hour = new Date().getHours();
      try {
        const data = await simulateScenario({
          demandMultiplier,
          loadSheddingPercent,
          hour,
        });
        setScenario(data);
      } catch {
        setFallback(true);
        setScenario(
          estimateScenario({
            demandMultiplier,
            loadSheddingPercent,
            hour,
          }),
        );
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [demandMultiplier, loadSheddingPercent]);

  const timeline = useMemo(() => {
    if (!scenario) return [];
    return buildBatteryTimeline({
      percentCharged: round1(scenario.battery?.percentCharged ?? 0),
      netDrainRateKw: round1(scenario.battery?.netDrainRateKw ?? 0),
      currentKwh: round1(scenario.battery?.currentKwh ?? 0),
      survivalHoursWithSolar: Number(scenario.battery?.survivalHoursWithSolar ?? 0),
    });
  }, [scenario]);

  const criticalNoSolar = useMemo(() => getCriticalHour(timeline, 'withoutSolar'), [timeline]);
  const criticalWithSolar = useMemo(() => getCriticalHour(timeline, 'withSolar'), [timeline]);

  const demandImpact = useMemo(() => {
    if (!scenario) return [{ name: 'Coverage', renewable: 0, battery: 0, uncovered: 0 }];

    const required = round1(scenario.demand?.afterShedding ?? 0);
    const renewable = Math.min(round1(scenario.supply?.total ?? 0), required);
    const battery = Math.min(required - renewable, round1(scenario.battery?.netDrainRateKw ?? 0));
    const uncovered = Math.max(required - renewable - battery, 0);

    return [{
      name: 'Coverage',
      renewable: round1(Math.max(renewable, 0)),
      battery: round1(Math.max(battery, 0)),
      uncovered: round1(uncovered),
    }];
  }, [scenario]);

  return (
    <div className="min-h-screen bg-transparent text-slate-100">
      <header className="sticky top-0 z-50 border-b border-cyan-500/30 bg-black/50 backdrop-blur-md">
        <div className="max-w-[1400px] mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="inline-flex items-center gap-2 text-cyan-200 hover:text-cyan-100"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to dashboard
          </button>
          <Link to="/" className="text-xs text-slate-400 hover:text-slate-200">Dashboard home</Link>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-4 py-6 space-y-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">Energy strategy flowchart</h1>
          <p className="text-sm text-slate-400 mt-1">
            Demand multiplier x{demandMultiplier.toFixed(1)} — {scenario?.strategy?.label ?? 'Loading strategy...'}
          </p>
        </div>

        {fallback ? (
          <p className="text-xs text-amber-300">Backend unavailable — showing estimated values</p>
        ) : null}

        <div className="glass-card p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="text-xs text-slate-300">
              Demand multiplier: x{demandMultiplier.toFixed(1)}
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={demandMultiplier}
                onChange={(e) => setDemandMultiplier(Number(e.target.value))}
                className="w-full mt-2"
              />
            </label>
            <label className="text-xs text-slate-300">
              Demand response: {loadSheddingPercent}% industrial reduction
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
        </div>

        <section>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <MetricCard label="Required supply" value={round1(scenario?.demand?.afterShedding ?? 0).toFixed(1)} unit="kW" />
            <MetricCard label="Current renewable supply" value={round1(scenario?.supply?.total ?? 0).toFixed(1)} unit="kW" />
            <MetricCard
              label="Gap to cover"
              value={Math.abs(round1(scenario?.gap ?? 0)).toFixed(1)}
              unit="kW"
              valueClassName={(scenario?.gap ?? 0) > 0 ? 'text-red-300' : 'text-emerald-300'}
            />
            <MetricCard
              label="Battery survival time"
              value={scenario?.battery?.survivalHours == null ? '—' : round1(scenario.battery.survivalHours).toFixed(1)}
              unit="hrs"
              subLabel="at current drain rate"
            />
          </div>
        </section>

        <section>
          <h2 className="text-sm uppercase tracking-widest text-slate-400 mb-2">Interactive energy flow diagram</h2>
          {loading && !scenario ? (
            <div className="glass-card p-6 animate-pulse text-slate-400">Loading flowchart...</div>
          ) : (
            <StrategyFlowSvg scenario={scenario} />
          )}
        </section>

        <section className="glass-card p-4">
          <h2 className="text-sm uppercase tracking-widest text-slate-400 mb-3">Battery timeline (0–12 hours)</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeline} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis dataKey="hour" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <ReferenceLine y={10} stroke="#ef4444" strokeDasharray="5 5" label={{ value: '10% critical', fill: '#f87171', fontSize: 11 }} />
                {criticalNoSolar != null ? <ReferenceLine x={criticalNoSolar} stroke="#f97316" strokeDasharray="3 3" /> : null}
                {criticalWithSolar != null ? <ReferenceLine x={criticalWithSolar} stroke="#22c55e" strokeDasharray="3 3" /> : null}
                <Line type="monotone" dataKey="withoutSolar" name="Without solar assist" stroke="#f97316" strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="withSolar" name="With partial solar" stroke="#22c55e" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="glass-card p-4">
          <h2 className="text-sm uppercase tracking-widest text-slate-400 mb-3">Demand response impact</h2>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={demandImpact} layout="vertical" margin={{ top: 10, right: 20, left: 20, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip formatter={(value) => `${round1(value)} kW`} />
                <Legend />
                <Bar dataKey="renewable" stackId="a" fill="#94a3b8" name="Renewables coverage" />
                <Bar dataKey="battery" stackId="a" fill="#f59e0b" name="Battery coverage" />
                <Bar dataKey="uncovered" stackId="a" fill="#ef4444" name="Uncovered deficit" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </main>
    </div>
  );
}
