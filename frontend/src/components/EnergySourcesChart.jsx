import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600/50 rounded-lg p-3 text-xs shadow-xl transition-colors duration-300">
      <p className="text-slate-300 font-medium">{label}</p>
      <p className="font-bold tabular-nums mt-1" style={{ color: p.fill }}>
        {Number(p.value).toFixed(1)} MW
      </p>
    </div>
  );
}

export default function EnergySourcesChart({ energy = {}, battery = {} }) {
  const data = [
    { name: 'Solar', value: energy.solar ?? 0, fill: '#f59e0b' },
    { name: 'Wind', value: energy.wind ?? 0, fill: '#8b5cf6' },
    { name: 'Battery', value: battery.level ?? 0, fill: '#3b82f6' },
  ];

  return (
    <div className="glass-card p-5 h-full flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Energy Sources
        </h3>
        <span className="text-xs text-slate-500">Current (MW)</span>
      </div>

      <div className="flex-1 min-h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={{ stroke: '#334155' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={{ stroke: '#334155' }}
              tickLine={false}
              domain={[0, (dataMax) => Math.max(Math.ceil(dataMax / 500) * 500, 2000)]}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex justify-around pt-2 border-t border-slate-700/50">
        {data.map((d) => (
          <div key={d.name} className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.fill }} />
              <span className="text-xs text-slate-400">{d.name}</span>
            </div>
            <span className="text-xs font-semibold tabular-nums text-slate-200">
              {d.value.toFixed(1)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
