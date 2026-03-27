const config = require('../config/config');

// Singleton battery state
const state = {
  capacity: config.batteryCapacity,
  level: config.batteryCapacity * (config.initialBatteryLevel / 100),
  chargingRate: 0,
  isCharging: false,
  isDraining: false,
};

function getBatteryStatus() {
  return {
    level: parseFloat(state.level.toFixed(2)),
    percentage: parseFloat(((state.level / state.capacity) * 100).toFixed(2)),
    capacity: state.capacity,
    chargingRate: parseFloat(state.chargingRate.toFixed(2)),
    isCharging: state.isCharging,
    isDraining: state.isDraining,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Charge the battery by `amount` kWh (capped at capacity).
 * @param {number} amount - Energy to add in kWh
 * @returns {object} Updated battery status
 */
function chargeBattery(amount) {
  const added = Math.min(amount, state.capacity - state.level);
  state.level = Math.min(state.capacity, state.level + added);
  state.chargingRate = added;
  state.isCharging = added > 0;
  state.isDraining = false;
  return getBatteryStatus();
}

/**
 * Discharge the battery by `amount` kWh (cannot go below 0).
 * @param {number} amount - Energy to draw in kWh
 * @returns {object} Updated battery status and actual amount drawn
 */
function dischargeBattery(amount) {
  const drawn = Math.min(amount, state.level);
  state.level = Math.max(0, state.level - drawn);
  state.chargingRate = -drawn;
  state.isDraining = drawn > 0;
  state.isCharging = false;
  return { ...getBatteryStatus(), drawnAmount: parseFloat(drawn.toFixed(2)) };
}

function resetBattery() {
  state.level = config.batteryCapacity * (config.initialBatteryLevel / 100);
  state.chargingRate = 0;
  state.isCharging = false;
  state.isDraining = false;
  return getBatteryStatus();
}

module.exports = { getBatteryStatus, chargeBattery, dischargeBattery, resetBattery };
