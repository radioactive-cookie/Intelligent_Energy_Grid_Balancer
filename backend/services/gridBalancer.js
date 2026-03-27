const config = require('../config/config');
const { chargeBattery, dischargeBattery, getBatteryStatus } = require('./batteryManager');

/**
 * Balance the grid by comparing supply vs demand and acting on the battery.
 * @param {number} supply  - Total energy supply in kW
 * @param {number} demand  - Total energy demand in kW
 * @param {number} hour    - Hour of day (0-23)
 * @returns {object} Balancing result
 */
function balanceGrid(supply, demand, hour) {
  const h = typeof hour === 'number' ? hour : new Date().getHours();
  const delta = supply - demand; // positive = surplus, negative = deficit
  const alerts = [];
  let action = 'balanced';
  let batteryUsed = 0;
  let batteryStatus;

  const imbalancePct = Math.abs(delta / Math.max(demand, 1)) * 100;

  if (delta > 0) {
    // Surplus — store excess in battery
    batteryStatus = chargeBattery(delta);
    batteryUsed = batteryStatus.chargingRate;
    action = 'storing';
  } else if (delta < 0) {
    // Deficit — draw from battery
    const result = dischargeBattery(Math.abs(delta));
    batteryUsed = -result.drawnAmount;
    batteryStatus = result;
    action = 'discharging';

    if (result.percentage < 10) {
      alerts.push({
        type: 'BATTERY_CRITICAL',
        message: `Battery critically low at ${result.percentage.toFixed(1)}%`,
        severity: 'critical',
        timestamp: new Date().toISOString(),
      });
    }
  } else {
    batteryStatus = getBatteryStatus();
  }

  if (imbalancePct > config.imbalanceThreshold) {
    alerts.push({
      type: delta > 0 ? 'SURPLUS_ALERT' : 'DEFICIT_ALERT',
      message: `Grid imbalance of ${imbalancePct.toFixed(1)}% detected at hour ${h}. ${
        delta > 0 ? 'Excess energy being stored.' : 'Drawing from battery reserves.'
      }`,
      severity: imbalancePct > config.imbalanceThreshold * 2 ? 'critical' : 'warning',
      timestamp: new Date().toISOString(),
    });
  }

  const efficiency = Math.max(0, Math.min(100, 100 - imbalancePct * 0.5));

  let gridStatus = 'BALANCED';
  if (delta > config.imbalanceThreshold * 2) gridStatus = 'SURPLUS';
  else if (delta < -config.imbalanceThreshold * 2) gridStatus = 'CRITICAL';
  else if (delta < 0) gridStatus = 'DEFICIT';

  return {
    action,
    surplus: delta > 0 ? parseFloat(delta.toFixed(2)) : 0,
    deficit: delta < 0 ? parseFloat(Math.abs(delta).toFixed(2)) : 0,
    batteryUsed: parseFloat(batteryUsed.toFixed(2)),
    battery: batteryStatus || getBatteryStatus(),
    alerts,
    gridStatus,
    efficiency: parseFloat(efficiency.toFixed(2)),
    supply: parseFloat(supply.toFixed(2)),
    demand: parseFloat(demand.toFixed(2)),
    delta: parseFloat(delta.toFixed(2)),
    hour: h,
    timestamp: new Date().toISOString(),
  };
}

module.exports = { balanceGrid };
