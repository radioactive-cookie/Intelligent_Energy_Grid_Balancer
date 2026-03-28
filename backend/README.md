# ⚡ Intelligent Energy Grid Balancer

A **production-ready** backend system for intelligent energy grid management, balancing, and optimization. Built with Python, FastAPI, and advanced decision-making algorithms.

## 🌐 Hosted Links

1. **Vercel (frontend host):** https://intelligent-energy-grid-balancer.vercel.app/
2. **Render (backend host):** https://intelligent-energy-grid-balancer-fdxg.onrender.com

## 🎯 Overview

The Intelligent Energy Grid Balancer is a sophisticated system designed to:
- Monitor real-time grid status (frequency, generation, demand)
- Manage battery storage intelligently
- Predict energy generation and demand
- Make autonomous decisions for grid balancing
- Simulate various grid scenarios
- Generate intelligent alerts
- Provide comprehensive metrics and analytics

## ⭐ Key Features

### 1. **Real-Time Grid Monitoring with Real Dashboard Values**
- Track grid frequency (nominal: 50 Hz) using real calculations
- Monitor total generation vs. demand with real input values
- Calculate renewable energy percentage
- Detect frequency deviations and critical conditions
- Compute grid stability score (0-100)
- **New:** Update solar, wind, demand, battery inputs dynamically
- **New:** Dashboard values computed using real formulas (not mock data)

### 2. **Intelligent Balancing Engine**
- Autonomous decision-making based on grid state
- Actions: `store`, `release`, `shed_load`, `demand_response`, `ramp_up`, `ramp_down`, `none`
- Multi-factor consideration: frequency, generation-demand imbalance, battery SOC, emergency conditions

### 3. **Battery Storage Management**
- Real-time SOC (State of Charge) tracking
- Charge/discharge operations
- Health monitoring
- Cycle counting

### 4. **AI/ML Prediction Engine**
- Solar generation forecasting (hour-based model)
- Wind generation prediction (stochastic model)
- Electricity demand forecasting (pattern-based)
- 24-hour horizon with confidence intervals

### 5. **Scenario Simulation & Alerts**
- Test grid responses to hypothetical conditions
- 7 alert types with 4 severity levels
- Alert history and resolution tracking

## 📦 Project Structure

```
Intelligent_Energy_GridBalancer/
├── README.md                    # This file
├── DEPLOYMENT.md                # Production deployment guide
├── QUICK_START.md               # Quick start instructions
└── backend/                     # All backend code
    ├── main.py                  # FastAPI application
    ├── requirements.txt         # Python dependencies
    ├── .env                     # Configuration
    ├── Dockerfile & docker-compose.yml
    ├── example_client.py        # Test client
    ├── models/                  # 6 data models
    ├── services/                # 5 service modules
    ├── controllers/             # 8 controller classes
    ├── routes/                  # 25+ API endpoints
    ├── utils/                   # Helpers & mock data
    ├── config/                  # Configuration management
    └── data/                    # JSON storage
```

## 🚀 Quick Start

### Installation
```bash
cd backend
pip install -r requirements.txt
```

### Run Server
```bash
python main.py
# or with auto-reload (development):
uvicorn main:app --reload
```

### Access API
- **Swagger UI:** https://intelligent-energy-grid-balancer-fdxg.onrender.com/docs
- **ReDoc:** https://intelligent-energy-grid-balancer-fdxg.onrender.com/redoc
- **Home:** https://intelligent-energy-grid-balancer-fdxg.onrender.com/

### Test System
```bash
python example_client.py
```

## 📊 API Endpoints

### Real-Time Dashboard Configuration (NEW)
```
GET  /grid/status               - Get current dashboard with calculated values
GET  /grid/inputs               - Get current simulation inputs
POST /grid/update-inputs        - Update inputs & recalculate dashboard
POST /grid/simulate-step        - Simulate time step with new values
```

**Example Dashboard Response:**
```json
{
  "total_generation": 300.0,
  "demand": 200.0,
  "frequency": 50.5,
  "efficiency": 66.67,
  "battery_percent": 70.0,
  "battery_current": 350.0,
  "battery_capacity": 500.0,
  "status": "stable",
  "surplus": 100.0,
  "deficit": 0.0,
  "imbalance": 100.0,
  "solar_generation": 150.0,
  "wind_generation": 150.0
}
```

### Grid Operations
```
GET  /grid/history          - Historical states
```

### Energy Sources
```
GET  /energy/solar          - Solar generation
GET  /energy/wind           - Wind generation
GET  /energy/total          - Total generation
```

### Battery Management
```
GET  /battery/status        - Battery status
POST /battery/charge        - Charge battery (amount_kw param)
POST /battery/discharge     - Discharge battery (amount_kw param)
```

### Balancing Engine
```
POST /balance/run           - Run decision engine
GET  /balance/history       - Past decisions
```

### Predictions
```
POST /predict/generation/solar   - Solar forecast (hours param)
POST /predict/generation/wind    - Wind forecast (hours param)
POST /predict/demand            - Demand forecast (hours param)
```

### Simulation (MW-Based)
```
POST /simulate/scenario          - Single scenario simulation (MW-based)
POST /simulate/multi-step        - Multi-step time series simulation
GET  /simulate/history           - Get previous simulation runs
POST /simulate/reset-state       - Reset battery state between tests
```

**Simulation Response Format:**
```json
{
  "inputs": {
    "solar_mw": 150.0,
    "wind_mw": 200.0,
    "demand_mw": 350.0
  },
  "results": {
    "total_generation": 350.0,
    "surplus": 0.0,
    "deficit": 0.0,
    "battery_before": 250.0,
    "battery_after": 250.0,
    "battery_percent": 50.0,
    "battery_action": "idle",
    "charge_discharge_amount": 0.0,
    "load_shedding": 0.0,
    "frequency": 50.0,
    "efficiency": 100.0,
    "grid_status": "stable",
    "grid_stability_score": 83.33
  },
  "timestamp": "2026-03-27T10:30:00"
}
```

### Alerts & Metrics
```
GET  /alerts                - Current alerts
GET  /alerts/history        - Alert history
POST /alerts/{id}/resolve   - Resolve alert
GET  /metrics               - System metrics
GET  /health                - Health check
```

### WebSocket (Real-time)
```
WS   /ws                    - Real-time system updates
WS   /ws/grid              - Grid status updates only
```

## 🎯 MW-Based Simulation Engine

The simulation module uses **realistic MW-based energy calculations** instead of percentage values. This enables accurate power grid behavior modeling.

### System Configuration
```
Battery Capacity: 500 MWh
Battery Initial: 250 MWh
Max Charge Rate: 50 MW per cycle
Max Discharge Rate: 50 MW per cycle
Nominal Frequency: 50 Hz
Frequency Constant (k): 0.01
Max Realistic Generation: 5000 MW (hackathon limit)
```

### Simulation Calculations

**1. Total Generation**
```
total_generation = solar_mw + wind_mw
```

**2. Power Difference**
```
difference = total_generation - demand_mw
```

**3. Battery Logic**
```
IF difference > 0 (surplus):
  charge_amount = min(difference, max_charge_rate)
  battery_current += charge_amount
  battery_action = "charging"
  
ELIF difference < 0 (deficit):
  deficit = abs(difference)
  discharge_amount = min(deficit, max_discharge_rate, battery_current)
  battery_current -= discharge_amount
  battery_action = "discharging"
  
  IF discharge_amount < deficit:
    load_shedding = deficit - discharge_amount
  ELSE:
    load_shedding = 0
    
ELSE (balanced):
  battery_action = "idle"
  load_shedding = 0
```

**4. Battery Clamping**
```
battery_current = max(0, min(battery_current, battery_capacity))
```

**5. Battery Percent**
```
battery_percent = (battery_current / battery_capacity) × 100
```

**6. Grid Frequency**
```
frequency = 50 + (0.01 × (total_generation - demand_mw))
frequency = CLAMP(frequency, 49.5, 50.5)
```

**7. Efficiency**
```
IF total_generation > 0:
  efficiency = (min(demand_mw, total_generation) / total_generation) × 100
ELSE:
  efficiency = 0
```

**8. Grid Status**
```
IF 49.8 ≤ frequency ≤ 50.2:
  status = "stable"
ELIF (49.5 ≤ f < 49.8) OR (50.2 < f ≤ 50.5):
  status = "warning"
ELSE:
  status = "critical"
```

**9. Grid Stability Score (0-100)**
```
Based on:
- Frequency deviation from 50 Hz
- Grid balance (generation vs demand)
- Battery health (charge percent)
```

### Input Validation Rules
- solar_mw >= 0
- wind_mw >= 0
- demand_mw >= 0
- total_generation <= 5000 MW (hackathon limit)
- demand_mw <= 5000 MW

### Simulation API Examples

**Single Scenario (MW-based):**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/scenario" \
  -H "Content-Type: application/json" \
  -d '{
    "solar_mw": 150.0,
    "wind_mw": 200.0,
    "demand_mw": 350.0
  }'
```

**Multi-Step Time Series (1-10 steps):**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/multi-step" \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"solar_mw": 150.0, "wind_mw": 200.0, "demand_mw": 350.0},
      {"solar_mw": 160.0, "wind_mw": 210.0, "demand_mw": 360.0},
      {"solar_mw": 140.0, "wind_mw": 190.0, "demand_mw": 340.0}
    ]
  }'
```

**Get Simulation History:**
```bash
curl "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/history?limit=50"
```

**Reset Battery State:**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/reset-state?battery_current=250.0"
```

### Response Examples

**Balanced Grid Response:**
```json
{
  "inputs": {
    "solar_mw": 150.0,
    "wind_mw": 150.0,
    "demand_mw": 300.0
  },
  "results": {
    "total_generation": 300.0,
    "surplus": 0.0,
    "deficit": 0.0,
    "battery_before": 250.0,
    "battery_after": 250.0,
    "battery_percent": 50.0,
    "battery_action": "idle",
    "load_shedding": 0.0,
    "frequency": 50.0,
    "efficiency": 100.0,
    "grid_status": "stable",
    "grid_stability_score": 83.33
  },
  "timestamp": "2026-03-27T10:30:00"
}
```

**Surplus (Charging) Response:**
```json
{
  "inputs": {
    "solar_mw": 250.0,
    "wind_mw": 200.0,
    "demand_mw": 350.0
  },
  "results": {
    "total_generation": 450.0,
    "surplus": 100.0,
    "deficit": 0.0,
    "battery_before": 250.0,
    "battery_after": 300.0,
    "battery_percent": 60.0,
    "battery_action": "charging",
    "charge_discharge_amount": 50.0,
    "load_shedding": 0.0,
    "frequency": 50.5,
    "efficiency": 77.78,
    "grid_status": "warning",
    "grid_stability_score": 75.4
  },
  "timestamp": "2026-03-27T10:30:00"
}
```

**Deficit (Discharging) Response:**
```json
{
  "inputs": {
    "solar_mw": 80.0,
    "wind_mw": 70.0,
    "demand_mw": 200.0
  },
  "results": {
    "total_generation": 150.0,
    "surplus": 0.0,
    "deficit": 50.0,
    "battery_before": 300.0,
    "battery_after": 250.0,
    "battery_percent": 50.0,
    "battery_action": "discharging",
    "charge_discharge_amount": 50.0,
    "load_shedding": 0.0,
    "frequency": 49.5,
    "efficiency": 100.0,
    "grid_status": "warning",
    "grid_stability_score": 73.33
  },
  "timestamp": "2026-03-27T10:30:00"
}
```

**Multi-Step Response with Summary:**
```json
{
  "steps": [
    {/* step 1 result */},
    {/* step 2 result */},
    {/* step 3 result */}
  ],
  "summary": {
    "total_steps": 3,
    "stable_steps": 1,
    "warning_steps": 2,
    "critical_steps": 0,
    "avg_frequency": 49.9,
    "avg_stability_score": 76.5,
    "final_battery_percent": 52.0,
    "final_battery_mwh": 260.0,
    "total_load_shedding": 0.0
  },
  "timestamp": "2026-03-27T10:30:00"
}
```

WS   /ws                    - Real-time system updates
WS   /ws/grid              - Grid status updates only
```

## 🔧 Real Dashboard Calculation Engine

The system computes all dashboard values from real input parameters using physical grid formulas.

### Input Parameters
- `solar_mw` - Solar generation in megawatts (MW)
- `wind_mw` - Wind generation in megawatts (MW)
- `demand_mw` - Total energy demand in megawatts (MW)
- `battery_current` - Current battery charge in megawatt-hours (MWh)
- `battery_capacity` - Total battery capacity in megawatt-hours (MWh)

### Calculation Formulas

**1. Total Generation**
```
total_generation = solar_mw + wind_mw
```

**2. Surplus / Deficit**
```
difference = total_generation - demand_mw
IF difference > 0:
  surplus = difference
  deficit = 0
ELSE:
  surplus = 0
  deficit = abs(difference)
```

**3. Battery Update**
```
IF surplus > 0:
  battery_current += surplus

IF deficit > 0:
  battery_current -= deficit

// Clamp battery between 0 and capacity
battery_current = CLAMP(battery_current, 0, battery_capacity)
```

**4. Battery Percent**
```
battery_percent = (battery_current / battery_capacity) * 100
```

**5. Grid Frequency**
```
k = 0.01
frequency = 50 + (k * (total_generation - demand_mw))

// Clamp frequency between 49.5 and 50.5 Hz
frequency = CLAMP(frequency, 49.5, 50.5)
```

**6. Efficiency**
```
efficiency = (demand_mw / total_generation) * 100
```

**7. Grid Status**
```
IF frequency between 49.8 and 50.2:
  status = "stable"
ELIF frequency between 49.5–49.8 or 50.2–50.5:
  status = "warning"
ELSE:
  status = "critical"
```

### Example API Usage

**Update inputs and get dashboard:**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/grid/update-inputs" \
  -H "Content-Type: application/json" \
  -d '{
    "solar_mw": 150.0,
    "wind_mw": 200.0,
    "demand_mw": 350.0,
    "battery_current": 350.0,
    "battery_capacity": 500.0
  }'
```

**Get current inputs:**
```bash
curl "https://intelligent-energy-grid-balancer-fdxg.onrender.com/grid/inputs"
```

**Simulate one time step:**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/grid/simulate-step" \
  -H "Content-Type: application/json" \
  -d '{
    "solar_mw": 160.0,
    "wind_mw": 210.0,
    "demand_mw": 345.0
  }'
```

## 🧠 Core Decision Logic

The balancing engine follows this hierarchy:

```
1. CHECK FREQUENCY CRITICAL (±1.5 Hz)
   ├─ YES → Emergency demand response or load shedding
   └─ NO → Continue

2. CHECK BATTERY LEVEL
   ├─ < 20% SOC → Trigger demand response
   ├─ > 95% SOC → Limit charging
   └─ OK → Continue

3. CHECK GENERATION vs DEMAND
   ├─ Generation >> Demand → STORE excess in battery
   ├─ Demand >> Generation → RELEASE from battery
   └─ Balanced → NO ACTION needed
```

### Example Scenarios

| Scenario | Inputs | Action |
|----------|--------|--------|
| Peak solar, high wind, low demand | Solar: 450 kW, Wind: 150 kW, Demand: 400 kW | **STORE** (charge battery) |
| Low generation, high demand | Solar: 50 kW, Wind: 30 kW, Demand: 1800 kW | **RELEASE** (discharge battery) |
| Battery critical & high demand | Solar: 50 kW, Wind: 30 kW, Demand: 2000 kW, SOC: 15% | **DEMAND_RESPONSE** |
| Frequency drops to 48 Hz | Frequency deviation: 2 Hz | **SHED_LOAD** (emergency) |
| Balanced | Generation ≈ Demand | **NONE** (no action) |

## 📈 Grid Stability Score

The stability score (0-100) is calculated as:

```
Score = (Frequency_Score × 0.4) + 
         (Balance_Score × 0.3) + 
         (Battery_Health × 0.2) + 
         (Battery_SOC × 0.1)

Where:
- Frequency_Score = 100 - (|frequency - 50| × 50)
- Balance_Score = 100 - (|imbalance| / demand × 100)
```

## 🔔 Alert Types

| Type | Trigger | Severity |
|------|---------|----------|
| `frequency_critical` | \|Hz - 50\| > 1.5 | Critical |
| `frequency_deviation` | \|Hz - 50\| > 0.5 | High |
| `battery_low` | SOC < 20% | High |
| `battery_critical` | SOC < 10% | Critical |
| `demand_spike` | Demand > 2000 kW | High/Critical |
| `generation_drop` | Generation < 200 kW (daytime) | Medium |
| `imbalance` | \|Imbalance\| / Demand > 15% | High/Critical |

## 📝 API Examples

### Get Grid Status
```bash
curl https://intelligent-energy-grid-balancer-fdxg.onrender.com/grid/status
```

### Run Balancing Engine
```bash
curl -X POST https://intelligent-energy-grid-balancer-fdxg.onrender.com/balance/run
```

### Simulate Scenario (high solar, moderate wind, normal demand)
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/scenario?sunlight_level=0.8&wind_speed=12&demand_spike=0"
```

### Get System Metrics
```bash
curl https://intelligent-energy-grid-balancer-fdxg.onrender.com/metrics
```

### Predict Solar Generation (48 hours)
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/predict/generation/solar?hours=48"
```

### WebSocket Connection (JavaScript)
```javascript
const ws = new WebSocket('wss://intelligent-energy-grid-balancer-fdxg.onrender.com/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Grid Update:', data);
};
```

## 💾 Data Storage

The system automatically stores data in JSON format:

- **actions.json** - Balancing decisions (unlimited)
- **grid_states.json** - Grid states (last 1000)
- **alerts.json** - All alerts (unlimited)
- **metrics.json** - Performance metrics (last 500)

All data is stored in the `backend/data/` directory.

## ⚙️ Configuration

Edit `backend/.env` to customize (optional, defaults provided):

```env
DEBUG=False
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
GRID_NOMINAL_FREQUENCY=50.0
FREQUENCY_TOLERANCE=0.5
FREQUENCY_CRITICAL_THRESHOLD=1.5
BATTERY_MIN_SOC_THRESHOLD=20.0
BATTERY_MAX_SOC_THRESHOLD=95.0
```

## 📝 Logging

All events are logged to `backend/logs/app.log`:

```
2026-03-27 10:30:00 - balancing_engine - INFO - Decision #123: store
2026-03-27 10:30:05 - monitoring_service - WARNING - ALERT: frequency_deviation
```

## 🧪 Test Scenarios

### Scenario 1: Peak Solar Generation
Conditions: Noon, strong sunlight (95%), strong wind (15 m/s), normal demand  
Expected Solar: 475 kW, Wind: 133 kW  
**Test:**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/scenario?sunlight_level=0.95&wind_speed=15&demand_spike=0"
```

### Scenario 2: Excess Generation (Battery Storage)
Conditions: Afternoon, strong sunlight (90%), high wind (18 m/s), low demand  
Expected Action: **STORE** (charge battery with ~180 kW excess)  
**Test:**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/scenario?sunlight_level=0.9&wind_speed=18&demand_spike=-0.2"
```

### Scenario 3: High Demand with Low Generation
Conditions: Evening, low sunlight (20%), low wind (3 m/s), high demand  
Expected Action: **RELEASE** (discharge battery heavily)  
**Test:**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/scenario?sunlight_level=0.2&wind_speed=3&demand_spike=0.4"
```

### Scenario 4: Critical Battery + High Demand
Conditions: Night, no sunlight, low wind, very high demand, battery critically low (15%)  
Expected Action: **DEMAND_RESPONSE** (critical)  
Alerts: battery_low, demand_spike  
**Test:**
```bash
curl -X POST "https://intelligent-energy-grid-balancer-fdxg.onrender.com/simulate/scenario?sunlight_level=0&wind_speed=2&demand_spike=0.5"
```

## 📚 Project Statistics

- **Lines of Code:** 2500+
- **Python Files:** 20+
- **Data Models:** 6
- **Service Modules:** 5
- **Controller Classes:** 8
- **API Endpoints:** 25+
- **Alert Types:** 7
- **Decision Actions:** 7

## 🔐 Security Considerations

1. **Input Validation:** All inputs validated using Pydantic
2. **CORS:** Currently allows all origins (configure for production)
3. **Rate Limiting:** Implement for production
4. **Authentication:** Add API keys or JWT tokens
5. **HTTPS:** Use SSL/TLS in production
6. **Logging:** Ensure sensitive data is not logged

## 🚀 Deployment

### Docker (Quick)
```bash
cd backend
docker-compose up -d
```

### Production Deployment
See `DEPLOYMENT.md` for:
- Systemd service setup
- Nginx reverse proxy configuration
- SSL/TLS with Let's Encrypt
- Load balancing
- Monitoring and alerting
- Backup strategy

## 🤝 Use Cases

✅ Hackathons  
✅ Production Deployment  
✅ Research & Development  
✅ Energy Management Systems  
✅ Smart Grid Applications  
✅ IoT Integrations  
✅ Educational Purposes  

## 📞 Support

1. Check the logs in `backend/logs/app.log`
2. Review the API documentation at `/docs`
3. Test endpoints using provided examples
4. See QUICK_START.md for setup help
5. See DEPLOYMENT.md for production setup

## 📄 License

This project is built for educational and hackathon purposes.

---

**Version:** 1.0.0  
**Status:** Production-Ready  
**Built with ⚡ for Intelligent Energy Management**
