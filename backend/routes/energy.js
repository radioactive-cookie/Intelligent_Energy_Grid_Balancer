const express = require('express');
const router = express.Router();
const { simulateEnergy } = require('../services/energySimulator');
const logger = require('../utils/logger');

// GET /api/generate-energy
router.get('/generate-energy', (req, res) => {
  try {
    const hour = req.query.hour !== undefined ? parseInt(req.query.hour, 10) : new Date().getHours();
    if (isNaN(hour) || hour < 0 || hour > 23) {
      return res.status(400).json({ error: 'Invalid hour. Must be between 0 and 23.' });
    }
    const data = simulateEnergy(hour);
    logger.info(`Energy generated for hour ${hour}: solar=${data.solar}kW, wind=${data.wind}kW`);
    res.json(data);
  } catch (err) {
    logger.error('Error in /generate-energy:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
