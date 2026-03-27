const config = require('../config/config');
const mockDataset = require('../data/mockDataset');

/**
 * Simulate energy generation from solar and wind sources for a given hour.
 * @param {number} hour - Hour of the day (0-23)
 * @returns {{ solar: number, wind: number, total: number, timestamp: string, hour: number }}
 */
function simulateEnergy(hour) {
  const h = typeof hour === 'number' ? hour : new Date().getHours();
  const dataset = mockDataset[h % 24];

  // Solar curve peaks at noon with natural sinusoidal shape + random cloud variation
  const solarBase = config.maxSolarOutput * Math.max(0, Math.sin((h - 6) * Math.PI / 12));
  const solarOutput = parseFloat(
    (solarBase * (0.85 + Math.random() * 0.30)).toFixed(2)
  );

  // Wind is stochastic but follows day/night tendencies from dataset
  const windOutput = parseFloat(
    (config.maxWindOutput * dataset.windMultiplier * (0.7 + Math.random() * 0.6)).toFixed(2)
  );

  const total = parseFloat((solarOutput + windOutput).toFixed(2));

  return {
    solar: solarOutput,
    wind: windOutput,
    total,
    timestamp: new Date().toISOString(),
    hour: h,
  };
}

module.exports = { simulateEnergy };
