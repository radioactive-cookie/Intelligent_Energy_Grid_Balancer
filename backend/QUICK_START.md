# 🚀 Quick Start Guide

Get the Intelligent Energy Grid Balancer running in 5 minutes!

## Prerequisites

- Python 3.8 or higher: https://www.python.org/
- pip (comes with Python)

Verify: `python --version` and `pip --version`

## Installation (2 minutes)

### Step 1: Navigate to Backend Directory
```bash
cd backend
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# Linux/Mac:
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Run the Server (1 minute)

### Option 1: Direct Python
```bash
python main.py
```

### Option 2: Uvicorn with Auto-Reload (Development)
```bash
uvicorn main:app --reload
```

### Expected Output
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## Access the System (1 minute)

### Open in Browser
- **Interactive API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### Test with cURL
```bash
# Check health
curl http://localhost:8000/health

# Get grid status
curl http://localhost:8000/grid/status

# Run balancing
curl -X POST http://localhost:8000/balance/run
```

## First API Call (30 seconds)

```bash
# Get current grid status
curl http://localhost:8000/grid/status

# Expected response:
{
  "grid_id": "MAIN_GRID_01",
  "frequency": 50.0,
  "total_generation": 550.5,
  "total_demand": 1450.2,
  "grid_stability_score": 92.3,
  "is_stable": true
}
```

## Test All Endpoints (2 minutes)

```bash
python example_client.py
```

This runs comprehensive tests of all endpoints and displays results.

## Try the System

### Get Grid Status
```bash
curl http://localhost:8000/grid/status
```

### Run Balancing Engine
```bash
curl -X POST http://localhost:8000/balance/run
```

### Simulate a Scenario
```bash
curl -X POST "http://localhost:8000/simulate/scenario?sunlight_level=0.8&wind_speed=12&demand_spike=0.2"
```

### Get Predictions (24 hours)
```bash
curl -X POST http://localhost:8000/predict/generation/solar?hours=24
curl -X POST http://localhost:8000/predict/demand?hours=24
```

### Get System Metrics
```bash
curl http://localhost:8000/metrics
```

### Connect to WebSocket (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Configuration (Optional)

Edit `backend/.env` to customize settings:

```env
DEBUG=False
SERVER_HOST=0.0.0.0
SERVER_PORT=8000              # Change port if needed
LOG_LEVEL=INFO
```

## Docker Deployment

```bash
cd backend
docker-compose up -d
# Access at http://localhost:8000
```

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

## Common Issues

### Issue: "Command not found: python"
**Solution:** Use `python3` or add Python to PATH

### Issue: "Port 8000 already in use"
**Solution:** Use different port: `uvicorn main:app --port 8001`

### Issue: "ModuleNotFoundError"
**Solution:** Make sure virtual environment is activated and `pip install -r requirements.txt` was run

### Issue: "Permission denied" (Linux/Mac)
**Solution:** Make executable: `chmod +x main.py`

## Next Steps

1. ✅ Explore API at `/docs`
2. ✅ Read full README.md for all features
3. ✅ Try different simulation scenarios
4. ✅ Check DEPLOYMENT.md for production setup
5. ✅ Monitor logs in `logs/app.log`

## API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/grid/status` | GET | Current grid state |
| `/balance/run` | POST | Run balancing engine |
| `/metrics` | GET | System metrics |
| `/simulate/scenario` | POST | Test scenario |
| `/alerts` | GET | Get alerts |
| `/battery/status` | GET | Battery info |
| `/predict/demand` | POST | Demand forecast |
| `/docs` | GET | Interactive API docs |

## Useful Resources

- **Full Documentation:** See README.md
- **API Reference:** http://localhost:8000/docs
- **Production Setup:** See DEPLOYMENT.md
- **Test Scenarios:** See README.md - Test Scenarios section

---

**Getting help?**
- Check logs: `backend/logs/app.log`
- Read README.md for details
- Review API docs at http://localhost:8000/docs

**Happy coding! ⚡**
