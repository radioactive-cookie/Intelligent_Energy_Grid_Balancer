import { useState, useEffect, useRef } from 'react';
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
} from 'recharts';

const MAX_POINTS = 20;

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-600/50 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-slate-400 mb-2 font-medium">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-slate-300 capitalize">{p.name}</span>
          </div>
          <span className="font-bold tabular-nums" style={{ color: p.color }}>
            {Number(p.value).toFixed(1)} kW
          </span>
        </div>
      ))}
    </div>
  );
}

export default function DemandSupplyChart({ gridData }) {
  const [history, setHistory] = useState([]);
  const counterRef = useRef(0);

  useEffect(() => {
    if (!gridData) return;

    const energy = gridData.energy || {};
    const demand = gridData.demand || {};
    const battery = gridData.battery || {};

    const supply = energy.total ?? 0;
    const demandVal = typeof demand === 'object' ? (demand.actual ?? 0) : (demand ?? 0);
    const battPct = battery.percentage ?? 0;

    counterRef.current += 1;
    const label = `T-${counterRef.current}`;

    setHistory((prev) => {
      const next = [
        ...prev,
        {
          time: label,
          Supply: parseFloat(supply.toFixed(1)),
          Demand: parseFloat(demandVal.toFixed(1)),
          Battery: parseFloat(battPct.toFixed(1)),
        },
      ].slice(-MAX_POINTS);
      return next;
    });
  }, [gridData]);

  return (
    <div className="glass-card p-5 h-full flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Supply vs Demand
        </h3>
        <span className="text-xs text-slate-500">Last {MAX_POINTS} updates</span>
      </div>

      <div className="flex-1 min-h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={history} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
            <XAxis
              dataKey="time"
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={{ stroke: '#334155' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={{ stroke: '#334155' }}
              tickLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', color: '#94a3b8', paddingTop: '8px' }}
              iconType="circle"
              iconSize={8}
            />
            <Line
              type="monotone"
              dataKey="Supply"
              stroke="#22d3ee"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, fill: '#22d3ee' }}
              style={{ filter: 'drop-shadow(0px 0px 6px rgba(34,211,238,0.8))' }}
            />
            <Line
              type="monotone"
              dataKey="Demand"
              stroke="#f472b6"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, fill: '#f472b6' }}
              style={{ filter: 'drop-shadow(0px 0px 6px rgba(244,114,182,0.8))' }}
            />
            <Line
              type="monotone"
              dataKey="Battery"
              stroke="#3b82f6"
              strokeWidth={2}
              strokeDasharray="5 3"
              dot={false}
              activeDot={{ r: 4, fill: '#3b82f6' }}
              yAxisId={0}
              style={{ filter: 'drop-shadow(0px 0px 4px rgba(59,130,246,0.6))' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
