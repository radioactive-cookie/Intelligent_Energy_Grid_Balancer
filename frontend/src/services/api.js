const API_BASE = import.meta.env.VITE_API_URL?.trim()?.replace(/\/+$/, '') || '/api';

async function request(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
  } catch (err) {
    console.error(`[API] Request failed for ${path}:`, err);
    throw err;
  }
}

export const generateEnergy = () => request('/energy/total');

export const predictDemand = (hours = 24) =>
  request(`/predict/demand?hours=${hours}`, { method: 'POST' });

export const balanceGrid = () => request('/balance/run', { method: 'POST' });

export const getGridStatus = () => request('/metrics');

export const getBatteryStatus = () => request('/battery/status');

export const resetBattery = () =>
  request('/simulate/reset-state', { method: 'POST' });
