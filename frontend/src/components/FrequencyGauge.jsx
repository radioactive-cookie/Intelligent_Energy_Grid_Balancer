import { motion } from 'framer-motion';

export default function FrequencyGauge({ frequency = 50.0 }) {
  // Cap between 48 and 52
  const cappedFrequency = Math.min(Math.max(frequency, 48), 52);
  
  // Calculate angle: 48Hz = -90deg, 50Hz = 0deg, 52Hz = 90deg
  const angle = ((cappedFrequency - 48) / 4) * 180 - 90;

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-slate-800/40 rounded-xl border border-slate-700/50 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-cyan-900/10 to-transparent pointer-events-none" />
      
      <div className="relative w-40 h-20 overflow-hidden mb-2">
        {/* Gauge Arc */}
        <svg className="w-full h-full" viewBox="0 0 100 50">
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="rgba(51, 65, 85, 0.5)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          {/* Danger zones */}
          <path
            d="M 10 50 A 40 40 0 0 1 21.7 21.7"
            fill="none"
            stroke="rgb(239, 68, 68)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          <path
            d="M 78.3 21.7 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="rgb(239, 68, 68)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          {/* Warning zones */}
          <path
            d="M 21.7 21.7 A 40 40 0 0 1 35.8 10"
            fill="none"
            stroke="rgb(234, 179, 8)"
            strokeWidth="10"
          />
          <path
            d="M 64.2 10 A 40 40 0 0 1 78.3 21.7"
            fill="none"
            stroke="rgb(234, 179, 8)"
            strokeWidth="10"
          />
          {/* Safe zone */}
          <path
            d="M 35.8 10 A 40 40 0 0 1 64.2 10"
            fill="none"
            stroke="rgb(16, 185, 129)"
            strokeWidth="10"
          />
        </svg>

        {/* Needle */}
        <motion.div
          className="absolute bottom-0 left-[calc(50%-2px)] w-1 h-14 bg-white rounded-t-full origin-bottom"
          initial={{ rotate: 0 }}
          animate={{ rotate: angle }}
          transition={{ type: 'spring', stiffness: 50, damping: 10, mass: 1 }}
          style={{
            boxShadow: '0 0 10px rgba(255,255,255,0.8)'
          }}
        />
        
        {/* Pivot */}
        <div className="absolute bottom-[-6px] left-[calc(50%-6px)] w-3 h-3 bg-cyan-400 rounded-full border-2 border-slate-900 shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
      </div>

      <div className="text-center z-10">
        <span className="text-2xl font-bold font-mono text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]">
          {frequency.toFixed(2)}
        </span>
        <span className="text-sm text-cyan-400 ml-1">Hz</span>
      </div>
    </div>
  );
}
