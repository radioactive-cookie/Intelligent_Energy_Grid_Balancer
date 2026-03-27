const config = require('../config/config');
const mockDataset = require('../data/mockDataset');

/**
 * Predict energy demand for a given hour using day pattern + random variation.
 * Demand peaks at 8 am (morning rush) and 6 pm (evening peak), troughs at 3 am.
 * @param {number} hour - Hour of the day (0-23)
 * @returns {{ predicted: number, actual: number, timestamp: string, hour: number, pattern: string }}
 */
function predictDemand(hour) {
  const h = typeof hour === 'number' ? hour : new Date().getHours();
  const dataset = mockDataset[h % 24];

  const baseLoad = config.maxBaseLoad;
  const predicted = parseFloat(
    (baseLoad * dataset.demandMultiplier * config.peakDemandMultiplier).toFixed(2)
  );

  // Actual demand has small random deviation from prediction (±8%)
  const actual = parseFloat(
    (predicted * (0.92 + Math.random() * 0.16)).toFixed(2)
  );

  let pattern = 'off-peak';
  if (h >= 7 && h <= 9) pattern = 'morning-rush';
  else if (h >= 10 && h <= 16) pattern = 'midday';
  else if (h >= 17 && h <= 20) pattern = 'evening-peak';
  else if (h >= 21 || h <= 5) pattern = 'night';

  return {
    predicted,
    actual,
    timestamp: new Date().toISOString(),
    hour: h,
    pattern,
  };
}

module.exports = { predictDemand };
