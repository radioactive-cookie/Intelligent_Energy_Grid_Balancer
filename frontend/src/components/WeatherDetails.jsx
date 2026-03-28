import { Sun, Wind, Cloud, Thermometer, MapPin } from 'lucide-react';

export default function WeatherDetails({ weather }) {
  if (!weather) return null;

  const items = [
    { 
      label: 'Solar Irradiance', 
      value: `${Math.round(weather.solar_radiation)} W/m²`, 
      icon: Sun, 
      color: 'text-amber-400',
      description: 'Main solar scaling factor'
    },
    { 
      label: 'Wind Speed', 
      value: `${weather.wind_speed.toFixed(1)} km/h`, 
      icon: Wind, 
      color: 'text-blue-400',
      description: 'Wind turbine input'
    },
    { 
      label: 'Cloud Cover', 
      value: `${weather.cloud_cover}%`, 
      icon: Cloud, 
      color: 'text-slate-400',
      description: 'Solar reduction'
    },
    { 
      label: 'Temperature', 
      value: `${weather.temperature ? weather.temperature.toFixed(1) : '—'}°C`, 
      icon: Thermometer, 
      color: 'text-rose-400',
      description: 'Ambient conditions'
    }
  ];

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-400">
                <MapPin className="w-4 h-4" />
            </div>
            <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider leading-none">Regional Telemetry</h3>
                <p className="text-[10px] text-emerald-600 dark:text-emerald-500 font-mono mt-1">{weather.location || 'Bhubaneswar, IN'}</p>
            </div>
        </div>
        <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[9px] text-emerald-500/80 uppercase tracking-widest font-bold">Live Feed</span>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {items.map((item) => (
          <div key={item.label} className="p-3 rounded-xl bg-slate-500/5 dark:bg-white/5 border border-slate-500/10 dark:border-white/5 flex flex-col gap-2">
            <div className="flex items-center justify-between">
                <item.icon className={`w-4 h-4 ${item.color}`} />
                <span className="text-[10px] text-slate-500 uppercase font-mono">{item.label}</span>
            </div>
            <div>
                <p className="text-xl font-mono text-slate-900 dark:text-white tracking-tight">{item.value}</p>
                <p className="text-[9px] text-slate-500 dark:text-slate-600 uppercase mt-0.5">{item.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
