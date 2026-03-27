const BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const generateEnergy = (hour) => {
  const query = hour !== undefined ? `?hour=${hour}` : '';
  return request(`/generate-energy${query}`);
};

export const predictDemand = (hour) => {
  const query = hour !== undefined ? `?hour=${hour}` : '';
  return request(`/predict-demand${query}`);
};

export const balanceGrid = (supply, demand, hour) =>
  request('/balance-grid', {
    method: 'POST',
    body: JSON.stringify({ supply, demand, hour }),
  });

export const getGridStatus = () => request('/balance-grid');

export const getBatteryStatus = () => request('/battery-status');

export const resetBattery = () =>
  request('/battery-status/reset', { method: 'POST' });
