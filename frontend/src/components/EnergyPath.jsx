import { motion } from 'framer-motion';

export default function EnergyPath({ generation, demand }) {
  // If generation > demand, flow to battery
  // If generation < demand, flow from battery
  const isSurplus = generation > demand;
  
  // To create flow direction:
  // Forward: dash offset from 0 to 100
  // Reverse: dash offset from 100 to 0
  
  return (
    <div className="w-full flex justify-center py-6 px-4">
      <div className="w-full max-w-4xl h-24 relative flex items-center justify-between">
        
        {/* SVG Flow Lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ filter: 'drop-shadow(0 0 8px rgba(34,211,238,0.5))' }}>
          {/* Generation -> Central Node */}
          <path
            d="M 100 48 Q 200 48, 400 48"
            fill="none"
            stroke="rgba(34,211,238,0.2)"
            strokeWidth="4"
          />
          <motion.path
            d="M 100 48 Q 200 48, 400 48"
            fill="none"
            stroke="rgba(34,211,238,0.8)"
            strokeWidth="4"
            strokeDasharray="20 15"
            animate={{ strokeDashoffset: [100, 0] }}
            transition={{ repeat: Infinity, ease: 'linear', duration: 1.5 }}
          />

          {/* Central Node -> Load */}
          <path
            d="M 400 48 Q 600 48, 800 48"
            fill="none"
            stroke="rgba(244,114,182,0.2)"
            strokeWidth="4"
          />
          <motion.path
            d="M 400 48 Q 600 48, 800 48"
            fill="none"
            stroke="rgba(244,114,182,0.8)"
            strokeWidth="4"
            strokeDasharray="20 15"
            animate={{ strokeDashoffset: [100, 0] }}
            transition={{ repeat: Infinity, ease: 'linear', duration: 1.5 }}
          />
          
          {/* Central Node <-> Battery */}
          <path
            d="M 400 48 Q 400 80, 400 96"
            fill="none"
            stroke="rgba(59,130,246,0.2)"
            strokeWidth="4"
          />
          <motion.path
            d="M 400 48 Q 400 80, 400 96"
            fill="none"
            stroke="rgba(59,130,246,0.8)"
            strokeWidth="4"
            strokeDasharray="15 10"
            animate={{ strokeDashoffset: isSurplus ? [100, 0] : [0, 100] }}
            transition={{ repeat: Infinity, ease: 'linear', duration: 1.5 }}
          />
        </svg>

        {/* Node Labels */}
        <div className="z-10 flex flex-col items-center justify-center w-24 h-12 bg-slate-800 rounded-lg border border-cyan-500/50 shadow-[0_0_15px_rgba(34,211,238,0.3)]">
          <span className="text-xs font-bold text-cyan-400">GENERATION</span>
        </div>
        
        <div className="z-10 absolute top-[110%] left-1/2 -translate-x-1/2 -translate-y-[20px] flex flex-col items-center justify-center w-24 h-12 bg-slate-800 rounded-lg border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
          <span className="text-xs font-bold text-blue-400">BATTERY</span>
        </div>

        <div className="z-10 flex flex-col items-center justify-center w-24 h-12 bg-slate-800 rounded-lg border border-pink-500/50 shadow-[0_0_15px_rgba(244,114,182,0.3)]">
          <span className="text-xs font-bold text-pink-400">LOAD</span>
        </div>

      </div>
    </div>
  );
}
