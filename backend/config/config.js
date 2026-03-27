require('dotenv').config();

module.exports = {
  port: process.env.PORT || 3001,
  // Battery capacity in kWh
  batteryCapacity: parseFloat(process.env.BATTERY_CAPACITY) || 1000,
  // Initial battery level as percentage (0-100)
  initialBatteryLevel: parseFloat(process.env.INITIAL_BATTERY_LEVEL) || 60,
  // Imbalance threshold percentage that triggers alerts
  imbalanceThreshold: parseFloat(process.env.IMBALANCE_THRESHOLD) || 20,
  // Simulation update interval in ms
  updateInterval: parseInt(process.env.UPDATE_INTERVAL) || 5000,
  // Maximum solar generation in kW at peak (noon)
  maxSolarOutput: parseFloat(process.env.MAX_SOLAR_OUTPUT) || 500,
  // Maximum wind generation in kW
  maxWindOutput: parseFloat(process.env.MAX_WIND_OUTPUT) || 300,
  // Maximum base load demand in kW
  maxBaseLoad: parseFloat(process.env.MAX_BASE_LOAD) || 600,
  // Peak demand multiplier during day hours
  peakDemandMultiplier: parseFloat(process.env.PEAK_DEMAND_MULTIPLIER) || 1.5,
  // Frontend URL for CORS
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:5173',
};
