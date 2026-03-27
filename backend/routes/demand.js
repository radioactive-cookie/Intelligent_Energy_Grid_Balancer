const express = require('express');
const router = express.Router();
const { predictDemand } = require('../services/demandPredictor');
const logger = require('../utils/logger');

// GET /api/predict-demand
router.get('/predict-demand', (req, res) => {
  try {
    const hour = req.query.hour !== undefined ? parseInt(req.query.hour, 10) : new Date().getHours();
    if (isNaN(hour) || hour < 0 || hour > 23) {
      return res.status(400).json({ error: 'Invalid hour. Must be between 0 and 23.' });
    }
    const data = predictDemand(hour);
    logger.info(`Demand predicted for hour ${hour}: predicted=${data.predicted}kW, actual=${data.actual}kW`);
    res.json(data);
  } catch (err) {
    logger.error('Error in /predict-demand:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
