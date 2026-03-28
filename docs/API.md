# API Documentation

Base URL: `http://localhost:3001/api`

---

## Energy Generation

### `GET /api/generate-energy`

Returns the current simulated solar and wind energy generation.

**Query Parameters**

| Parameter | Type   | Required | Description              |
|-----------|--------|----------|--------------------------|
| `hour`    | number | No       | Hour 0–23 (default: now) |

**Response 200**
```json
{
  "solar": 423.5,
  "wind": 198.2,
  "total": 621.7,
  "timestamp": "2024-07-01T14:00:00.000Z",
  "hour": 14
}
```

---

## Demand Prediction

### `GET /api/predict-demand`

Returns the predicted and actual energy demand for a given hour.

**Query Parameters**

| Parameter | Type   | Required | Description              |
|-----------|--------|----------|--------------------------|
| `hour`    | number | No       | Hour 0–23 (default: now) |

**Response 200**
```json
{
  "predicted": 720.0,
  "actual": 735.4,
  "timestamp": "2024-07-01T14:00:00.000Z",
  "hour": 14,
  "pattern": "midday"
}
```

`pattern` values: `morning-rush`, `midday`, `evening-peak`, `night`, `off-peak`

---

## Grid Balancing

### `GET /api/balance-grid`

Returns the current grid balance status using live simulated data.

**Response 200**
```json
{
  "action": "storing",
  "surplus": 85.3,
  "deficit": 0,
  "batteryUsed": 85.3,
  "gridStatus": "SURPLUS",
  "efficiency": 95.7,
  "supply": 621.7,
  "demandValue": 536.4,
  "delta": 85.3,
  "hour": 14,
  "timestamp": "2024-07-01T14:00:00.000Z",
  "alerts": ["SURPLUS"],
  "battery": { "level": 685.3, "percentage": 68.5, "capacity": 1000, "isCharging": true, "isDraining": false, "chargingRate": 85.3 },
  "energy": { "solar": 423.5, "wind": 198.2, "total": 621.7 },
  "demand": { "predicted": 540.0, "actual": 536.4, "pattern": "midday", "hour": 14 }
}
```

### `POST /api/balance-grid`

Balance the grid with custom supply/demand values.

**Request Body**
```json
{
  "supply": 700,
  "demand": 500,
  "hour": 14
}
```

**Response 200** — same shape as `GET /api/balance-grid`

---

## Battery Management

### `GET /api/battery-status`

Returns the current battery state.

**Response 200**
```json
{
  "level": 685.3,
  "percentage": 68.5,
  "capacity": 1000,
  "chargingRate": 85.3,
  "isCharging": true,
  "isDraining": false,
  "timestamp": "2024-07-01T14:00:00.000Z"
}
```

---

## History

### `GET /api/history`

Returns the rolling snapshot history (up to 20 latest records).

**Response 200**
```json
{
  "history": [
    {
      "energy": { "solar": 423.5, "wind": 198.2, "total": 621.7, "hour": 14 },
      "demand": { "predicted": 720.0, "actual": 735.4, "pattern": "midday", "hour": 14 },
      "battery": { "level": 685.3, "percentage": 68.5, "capacity": 1000, "isCharging": true, "isDraining": false, "chargingRate": 85.3 },
      "grid": { "action": "storing", "gridStatus": "SURPLUS", "efficiency": 95.7, "delta": 85.3, "alerts": ["SURPLUS"] },
      "timestamp": "2024-07-01T14:00:00.000Z"
    }
  ],
  "count": 1
}
```

### `POST /api/battery-status/reset`

Resets the battery to its configured initial level.

**Response 200**
```json
{
  "message": "Battery reset successfully",
  "battery": { "level": 600, "percentage": 60.0, "capacity": 1000, ... }
}
```

---

## Health Check

### `GET /health`

**Response 200**
```json
{
  "status": "ok",
  "timestamp": "2024-07-01T14:00:00.000Z"
}
```

---

## WebSocket

Connect to `ws://localhost:3001`.

The server broadcasts a `GRID_UPDATE` message every 5 seconds:

```json
{
  "type": "GRID_UPDATE",
  "data": {
    "energy": { "solar": 423.5, "wind": 198.2, "total": 621.7, "hour": 14 },
    "demand": { "predicted": 720.0, "actual": 735.4, "pattern": "midday", "hour": 14 },
    "battery": { "level": 685.3, "percentage": 68.5, "capacity": 1000, "isCharging": true, "isDraining": false, "chargingRate": 85.3 },
    "grid": { "action": "storing", "gridStatus": "SURPLUS", "efficiency": 95.7, "delta": 85.3, "alerts": ["SURPLUS"] },
    "timestamp": "2024-07-01T14:00:00.000Z"
  }
}
```
