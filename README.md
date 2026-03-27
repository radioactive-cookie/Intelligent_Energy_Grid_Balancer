# Intelligent Energy Grid Balancer

[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js)](https://nodejs.org)
[![React](https://img.shields.io/badge/React-18-blue?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-purple?logo=vite)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-cyan?logo=tailwindcss)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

> **Real-time intelligent renewable energy management system** — balance solar, wind, and battery storage across a smart grid with live WebSocket data streams, demand prediction, and automated grid balancing.

---

## ✨ Features

- ⚡ **Real-time WebSocket** data streaming every 5 seconds
- ☀️ **Solar & Wind simulation** with realistic diurnal curves
- 🔋 **Smart battery management** — automatic charge/discharge
- 📊 **Interactive charts** — supply vs demand trend lines, energy source bars
- 🚨 **Automated alerts** — surplus, deficit, and battery-critical notifications
- 🌙 **Dark-first UI** with glassmorphism cards and gradient accents
- 📱 **Responsive layout** — works on mobile, tablet, and desktop
- 🔌 **REST API** with full documentation

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm 9+

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/intelligent-energy-grid-balancer.git
cd intelligent-energy-grid-balancer

# Install all dependencies
npm run install:all

# Start both backend and frontend (dev mode)
npm run dev
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:5173         |
| Backend  | http://localhost:3001         |
| WS       | ws://localhost:3001           |
| Health   | http://localhost:3001/health  |

---

## ⚙️ Configuration

Copy the example env file and edit as needed:

```bash
cp backend/.env.example backend/.env
```

| Variable                  | Default               | Description                               |
|---------------------------|-----------------------|-------------------------------------------|
| `PORT`                    | 3001                  | Backend HTTP/WS port                      |
| `BATTERY_CAPACITY`        | 1000                  | Battery capacity in kWh                   |
| `INITIAL_BATTERY_LEVEL`   | 60                    | Initial battery level (%)                 |
| `IMBALANCE_THRESHOLD`     | 20                    | Imbalance % that triggers alerts          |
| `UPDATE_INTERVAL`         | 5000                  | WebSocket broadcast interval (ms)         |
| `MAX_SOLAR_OUTPUT`        | 500                   | Peak solar generation (kW)                |
| `MAX_WIND_OUTPUT`         | 300                   | Max wind generation (kW)                  |
| `MAX_BASE_LOAD`           | 600                   | Max base load demand (kW)                 |
| `PEAK_DEMAND_MULTIPLIER`  | 1.5                   | Demand multiplier during peak hours       |
| `FRONTEND_URL`            | http://localhost:5173 | CORS allowed origin                       |

---

## 🏗️ Tech Stack

| Layer    | Technology                                          |
|----------|-----------------------------------------------------|
| Frontend | React 18, Vite 5, TailwindCSS 3, Recharts, Lucide   |
| Backend  | Node.js, Express 4, ws (WebSocket), Winston          |
| Comms    | REST API + WebSocket (ws://)                         |

---

## 📡 API Summary

See [docs/API.md](./docs/API.md) for full documentation.

| Method | Endpoint                    | Description                   |
|--------|-----------------------------|-------------------------------|
| GET    | `/api/generate-energy`      | Current solar + wind output   |
| GET    | `/api/predict-demand`       | Demand prediction for hour    |
| GET    | `/api/balance-grid`         | Current grid balance status   |
| POST   | `/api/balance-grid`         | Balance with custom values    |
| GET    | `/api/battery-status`       | Battery state                 |
| POST   | `/api/battery-status/reset` | Reset battery to initial      |

---

## 📁 Project Structure

```
/
├── backend/          Node.js + Express API + WebSocket server
├── frontend/         React + Vite + TailwindCSS SPA
├── docs/             API documentation
└── package.json      Monorepo root scripts
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## 📜 License

MIT — see [LICENSE](./LICENSE).
