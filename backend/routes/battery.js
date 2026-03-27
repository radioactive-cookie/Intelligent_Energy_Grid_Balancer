const express = require('express');
const router = express.Router();
const { getBatteryStatus, resetBattery } = require('../services/batteryManager');
const logger = require('../utils/logger');

// GET /api/battery-status
router.get('/battery-status', (req, res) => {
  try {
    const status = getBatteryStatus();
    logger.info(`Battery status: ${status.percentage.toFixed(1)}%`);
    res.json(status);
  } catch (err) {
    logger.error('Error in GET /battery-status:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/battery-status/reset
router.post('/battery-status/reset', (req, res) => {
  try {
    const status = resetBattery();
    logger.info('Battery reset to initial level');
    res.json({ message: 'Battery reset successfully', battery: status });
  } catch (err) {
    logger.error('Error in POST /battery-status/reset:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
