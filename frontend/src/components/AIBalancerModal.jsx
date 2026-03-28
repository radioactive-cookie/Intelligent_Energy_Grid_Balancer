import { useState } from 'react';
import { X, Zap, Battery, AlertTriangle, CheckCircle, Loader2, Brain } from 'lucide-react';

const ACTION_STYLES = {
  STORE_EXCESS: { color: 'text-green-400', bg: 'bg-green-900/30', icon: '⬆️', label: 'Store Excess Energy' },
  DISCHARGE_BATTERY: { color: 'text-yellow-400', bg: 'bg-yellow-900/30', icon: '⬇️', label: 'Discharge Battery' },
  SHED_LOAD: { color: 'text-red-400', bg: 'bg-red-900/30', icon: '🔴', label: 'Shed Load — Critical' },
  REDUCE_LOAD: { color: 'text-orange-400', bg: 'bg-orange-900/30', icon: '🟠', label: 'Reduce Load' },
  BALANCED: { color: 'text-blue-400', bg: 'bg-blue-900/30', icon: '✅', label: 'Grid Balanced' },
  EMERGENCY: { color: 'text-red-500', bg: 'bg-red-900/50', icon: '🚨', label: 'EMERGENCY ACTION' },
};

export default function AIBalancerModal({ gridData, onClose, onApply }) {
  const [status, setStatus] = useState('idle');
  const [decision, setDecision] = useState(null);
  const [error, setError] = useState('');

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  const runBalancer = async () => {
    setStatus('loading');
    setError('');
    setDecision(null);

    const payload = {
      solar_kw: gridData?.energy?.solar ?? 0,
      wind_kw: gridData?.energy?.wind ?? 0,
      total_supply_kw: gridData?.energy?.total ?? 0,
      demand_kw: gridData?.demand?.actual ?? gridData?.demand?.predicted ?? 0,
      battery_percentage: gridData?.battery?.percentage ?? 0,
      battery_level_kwh: gridData?.battery?.level ?? 0,
      battery_capacity_kwh: gridData?.battery?.capacity ?? 1000,
      hour: gridData?.energy?.hour ?? new Date().getHours(),
      grid_status: gridData?.grid?.gridStatus ?? 'UNKNOWN',
      imbalance_threshold: 20,
    };

    try {
      const res = await fetch(`${backendUrl}/api/ai-balance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.error || `HTTP ${res.status}`);
      }

      setDecision(json.decision);
      setStatus('success');
    } catch (err) {
      setError(err.message || 'Unknown error');
      setStatus('error');
    }
  };

  const handleApply = () => {
    if (decision && onApply) onApply(decision);
    onClose();
  };

  const actionStyle = decision ? (ACTION_STYLES[decision.action] || ACTION_STYLES.BALANCED) : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-2xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 bg-gray-800/60">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            <h2 className="text-white font-semibold text-lg">AI Grid Balancer</h2>
            <span className="text-xs bg-purple-900/50 text-purple-300 border border-purple-700 px-2 py-0.5 rounded-full ml-1">
              GitHub Models · gpt-4o-mini
            </span>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          {status === 'idle' && (
            <div className="text-center py-6 space-y-3">
              <Zap className="w-12 h-12 text-yellow-400 mx-auto" />
              <p className="text-gray-300 text-sm leading-relaxed">
                The AI will analyze the current grid state in real-time and recommend
                the optimal balancing action — including battery operations, load shedding,
                and household demand-response messages.
              </p>
              <p className="text-gray-500 text-xs">Powered by GitHub Models (free tier)</p>
            </div>
          )}

          {status === 'loading' && (
            <div className="text-center py-8 space-y-3">
              <Loader2 className="w-10 h-10 text-purple-400 animate-spin mx-auto" />
              <p className="text-gray-300 text-sm">Analyzing grid state with AI...</p>
            </div>
          )}

          {status === 'error' && (
            <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2 text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <span className="font-medium text-sm">AI Balancer Error</span>
              </div>
              <p className="text-red-300 text-sm">{error}</p>
              {error.includes('GITHUB_TOKEN') && (
                <p className="text-gray-400 text-xs mt-2">
                  💡 Add GITHUB_TOKEN to your .env file. Create a PAT at{' '}
                  <a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="text-blue-400 underline">
                    github.com/settings/tokens
                  </a>{' '}
                  with <code className="bg-gray-800 px-1 rounded">models:read</code> scope.
                </p>
              )}
            </div>
          )}

          {status === 'success' && decision && actionStyle && (
            <div className="space-y-4">
              <div className={`flex items-center gap-3 p-4 rounded-xl border ${actionStyle.bg} border-gray-700`}>
                <span className="text-2xl">{actionStyle.icon}</span>
                <div>
                  <p className={`font-bold text-base ${actionStyle.color}`}>{actionStyle.label}</p>
                  <p className="text-gray-400 text-xs">
                    Confidence: {(decision.confidence * 100).toFixed(0)}% &nbsp;·&nbsp;
                    Grid Stability: {(decision.grid_stability_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              <div className="bg-gray-800/50 rounded-xl p-4 space-y-1">
                <p className="text-gray-400 text-xs font-semibold uppercase tracking-wide">AI Reasoning</p>
                <p className="text-gray-200 text-sm leading-relaxed">{decision.reasoning}</p>
              </div>

              <div className="bg-gray-800/50 rounded-xl p-4 space-y-1">
                <p className="text-gray-400 text-xs font-semibold uppercase tracking-wide flex items-center gap-1">
                  <Battery className="w-3 h-3" /> Battery Instruction
                </p>
                <p className="text-gray-200 text-sm">
                  <span className="capitalize">{decision.battery_instruction?.operation}</span>
                  {decision.battery_instruction?.operation !== 'hold' && (
                    <>
                      {' '}
                      to <strong className="text-white">{decision.battery_instruction?.target_percentage?.toFixed(0)}%</strong>{' '}
                      at <strong className="text-white">{decision.battery_instruction?.rate_kw?.toFixed(0)} kW</strong>
                    </>
                  )}
                </p>
              </div>

              {decision.demand_response?.active && (
                <div className="bg-orange-900/20 border border-orange-800 rounded-xl p-4 space-y-2">
                  <p className="text-orange-400 text-xs font-semibold uppercase tracking-wide flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Demand Response Active
                  </p>
                  <p className="text-gray-300 text-sm">
                    Zones: <strong className="text-white">{decision.demand_response.zones_affected?.join(', ')}</strong> &nbsp;·&nbsp;
                    Reduce by <strong className="text-white">{decision.demand_response.reduction_percentage?.toFixed(0)}%</strong>
                  </p>
                  <div className="bg-gray-900/50 rounded-lg p-3 text-sm text-gray-300 italic border-l-2 border-orange-500">
                    "{decision.demand_response.message_to_households}"
                  </div>
                </div>
              )}

              <div className="bg-gray-800/50 rounded-xl p-4">
                <p className="text-gray-400 text-xs font-semibold uppercase tracking-wide mb-1">30-Min Forecast</p>
                <p className="text-gray-300 text-sm">{decision.forecast_30min}</p>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-700 bg-gray-800/40">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-300 hover:text-white border border-gray-600 hover:border-gray-400 rounded-lg transition-colors"
          >
            Close
          </button>

          {status === 'idle' || status === 'error' ? (
            <button
              onClick={runBalancer}
              disabled={status === 'loading'}
              className="px-5 py-2 text-sm font-medium bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <Brain className="w-4 h-4" />
              {status === 'error' ? 'Retry Analysis' : 'Analyze & Balance'}
            </button>
          ) : status === 'success' ? (
            <button
              onClick={handleApply}
              className="px-5 py-2 text-sm font-medium bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Apply Recommendation
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
