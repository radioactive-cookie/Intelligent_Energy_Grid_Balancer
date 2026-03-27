const express = require('express');
const router = express.Router();
const { balanceGrid } = require('../services/gridBalancer');
const { simulateEnergy } = require('../services/energySimulator');
const { predictDemand } = require('../services/demandPredictor');
const { getBatteryStatus } = require('../services/batteryManager');
const logger = require('../utils/logger');

// POST /api/balance-grid
router.post('/balance-grid', (req, res) => {
  try {
    const { supply, demand, hour } = req.body;
    if (supply === undefined || demand === undefined) {
      return res.status(400).json({ error: 'supply and demand are required in request body.' });
    }
    const h = hour !== undefined ? parseInt(hour, 10) : new Date().getHours();
    const result = balanceGrid(parseFloat(supply), parseFloat(demand), h);
    logger.info(`Grid balanced: action=${result.action}, gridStatus=${result.gridStatus}`);
    res.json(result);
  } catch (err) {
    logger.error('Error in POST /balance-grid:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/balance-grid — current grid status using simulated values
router.get('/balance-grid', (req, res) => {
  try {
    const hour = new Date().getHours();
    const energy = simulateEnergy(hour);
    const demand = predictDemand(hour);
    const result = balanceGrid(energy.total, demand.actual, hour);
    res.json({ ...result, energy, demand: demand.actual, battery: getBatteryStatus() });
  } catch (err) {
    logger.error('Error in GET /balance-grid:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
