require('dotenv').config();
const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');
const config = require('./config/config');
const logger = require('./utils/logger');

const energyRoutes = require('./routes/energy');
const demandRoutes = require('./routes/demand');
const gridRoutes = require('./routes/grid');
const batteryRoutes = require('./routes/battery');

const { simulateEnergy } = require('./services/energySimulator');
const { predictDemand } = require('./services/demandPredictor');
const { balanceGrid } = require('./services/gridBalancer');
const { getBatteryStatus } = require('./services/batteryManager');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// ── Middleware ────────────────────────────────────────────────────────────────
app.use(cors({ origin: config.frontendUrl, credentials: true }));
app.use(express.json());

// Request logger
app.use((req, _res, next) => {
  logger.info(`${req.method} ${req.url}`);
  next();
});

// ── Routes ────────────────────────────────────────────────────────────────────
app.use('/api', energyRoutes);
app.use('/api', demandRoutes);
app.use('/api', gridRoutes);
app.use('/api', batteryRoutes);

// Health check
app.get('/health', (_req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));

// ── Error handling ────────────────────────────────────────────────────────────
app.use((err, _req, res, _next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ── WebSocket ─────────────────────────────────────────────────────────────────
wss.on('connection', (ws, req) => {
  logger.info(`WebSocket client connected from ${req.socket.remoteAddress}`);

  ws.on('close', () => logger.info('WebSocket client disconnected'));
  ws.on('error', (err) => logger.error('WebSocket error:', err));

  // Send initial snapshot immediately on connect
  sendGridUpdate(ws);
});

function buildGridUpdate() {
  const hour = new Date().getHours();
  const energy = simulateEnergy(hour);
  const demandData = predictDemand(hour);
  const grid = balanceGrid(energy.total, demandData.actual, hour);
  const battery = getBatteryStatus();

  return {
    type: 'GRID_UPDATE',
    data: {
      energy,
      demand: demandData,
      battery,
      grid,
      timestamp: new Date().toISOString(),
    },
  };
}

function sendGridUpdate(ws) {
  if (ws.readyState === WebSocket.OPEN) {
    try {
      ws.send(JSON.stringify(buildGridUpdate()));
    } catch (err) {
      logger.error('Error sending WebSocket message:', err);
    }
  }
}

function broadcastGridUpdate() {
  const payload = JSON.stringify(buildGridUpdate());
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  });
}

// Broadcast every UPDATE_INTERVAL ms
setInterval(broadcastGridUpdate, config.updateInterval);

// ── Start server ──────────────────────────────────────────────────────────────
server.listen(config.port, () => {
  logger.info(`⚡ Energy Grid Balancer backend running on http://localhost:${config.port}`);
  logger.info(`🔌 WebSocket server ready on ws://localhost:${config.port}`);
});

module.exports = { app, server };
