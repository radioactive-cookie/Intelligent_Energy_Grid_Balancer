import { useEffect, useState } from 'react';
import { Bell, BellOff, X, AlertTriangle, Info, XCircle } from 'lucide-react';

const SEVERITY_CONFIG = {
  critical: {
    border: 'border-red-500/40',
    bg: 'bg-red-500/10',
    icon: XCircle,
    iconColor: 'text-red-400',
    label: 'Critical',
    labelColor: 'text-red-400',
    animate: 'alert-critical',
  },
  warning: {
    border: 'border-yellow-500/40',
    bg: 'bg-yellow-500/10',
    icon: AlertTriangle,
    iconColor: 'text-yellow-400',
    label: 'Warning',
    labelColor: 'text-yellow-400',
    animate: '',
  },
  info: {
    border: 'border-blue-500/40',
    bg: 'bg-blue-500/10',
    icon: Info,
    iconColor: 'text-blue-400',
    label: 'Info',
    labelColor: 'text-blue-400',
    animate: '',
  },
};

const AUTO_DISMISS_MS = 30_000;

function AlertItem({ alert, onDismiss }) {
  const SEVERITY_MAP = { critical: 'critical', high: 'warning', warning: 'warning', medium: 'warning', low: 'info', info: 'info' };
  const severityKey = SEVERITY_MAP[alert.severity] || SEVERITY_MAP[alert.type] || 'info';
  const cfg = SEVERITY_CONFIG[severityKey] || SEVERITY_CONFIG.info;
  const Icon = cfg.icon;

  useEffect(() => {
    const timer = setTimeout(() => onDismiss(alert.id), AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [alert.id, onDismiss]);

  const time = alert.timestamp
    ? new Date(alert.timestamp).toLocaleTimeString()
    : '';

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border ${cfg.border} ${cfg.bg} ${cfg.animate} animate-[slideUp_0.3s_ease-out]`}
    >
      <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${cfg.iconColor}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-semibold uppercase ${cfg.labelColor}`}>
            {cfg.label}
          </span>
          {time && <span className="text-xs text-slate-600 tabular-nums">{time}</span>}
        </div>
        <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{alert.message}</p>
      </div>
      <button
        onClick={() => onDismiss(alert.id)}
        className="text-slate-600 hover:text-slate-300 transition-colors flex-shrink-0"
        aria-label="Dismiss alert"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export default function AlertsPanel({ alerts = [], onDismiss }) {
  if (!alerts.length) {
    return (
      <div className="glass-card p-5 flex items-center gap-3 text-slate-500">
        <BellOff className="w-4 h-4" />
        <span className="text-sm">No active alerts — grid is operating normally.</span>
      </div>
    );
  }

  return (
    <div className="glass-card p-5 space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Bell className="w-4 h-4 text-yellow-400" />
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Active Alerts
        </h3>
        <span className="ml-auto text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded-full">
          {alerts.length}
        </span>
      </div>
      {alerts.map((alert) => (
        <AlertItem key={alert.id} alert={alert} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
