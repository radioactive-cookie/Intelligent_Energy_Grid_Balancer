"""Focused contract tests for frontend-compatible API payloads."""
import asyncio

import main as app_main

NOISE_OFFSET = app_main.DEMAND_NOISE_OFFSET_KW


def _assert_snapshot_shape(snapshot: dict):
    assert "energy" in snapshot
    assert "demand" in snapshot
    assert "battery" in snapshot
    assert "grid" in snapshot
    assert "timestamp" in snapshot

    demand = snapshot["demand"]
    battery = snapshot["battery"]
    grid = snapshot["grid"]

    assert "predicted" in demand
    assert "actual" in demand
    assert "pattern" in demand
    assert "hour" in demand
    assert (demand["predicted"] - NOISE_OFFSET) <= demand["actual"] <= (demand["predicted"] + NOISE_OFFSET)

    assert "level" in battery
    assert "percentage" in battery
    assert "capacity" in battery
    assert "isCharging" in battery
    assert "isDraining" in battery
    assert "chargingRate" in battery

    if battery["isCharging"] or battery["isDraining"]:
        assert battery["chargingRate"] == abs(grid["delta"])
    else:
        assert battery["chargingRate"] == 0

    assert isinstance(grid["alerts"], list)
    if grid["delta"] > app_main.IMBALANCE_THRESHOLD:
        assert "SURPLUS" in grid["alerts"]
    if grid["delta"] < -app_main.IMBALANCE_THRESHOLD:
        assert "DEFICIT" in grid["alerts"]
    if battery["percentage"] < 10:
        assert "BATTERY_CRITICAL" in grid["alerts"]


def test_compute_grid_snapshot_contract():
    snapshot = app_main.computeGridSnapshot()
    _assert_snapshot_shape(snapshot)


def test_api_predict_demand_has_predicted_and_actual():
    response = asyncio.run(app_main.get_api_predict_demand())
    assert "predicted" in response
    assert "actual" in response
    assert "pattern" in response
    assert "hour" in response
    assert (response["predicted"] - NOISE_OFFSET) <= response["actual"] <= (response["predicted"] + NOISE_OFFSET)


def test_api_battery_status_has_new_fields():
    response = asyncio.run(app_main.get_api_battery_status())
    assert "chargingRate" in response
    assert "isDraining" in response
    assert "isCharging" in response
    assert "timestamp" in response


def test_api_balance_grid_has_enriched_fields():
    response = asyncio.run(app_main.get_api_balance_grid())
    assert "efficiency" in response
    assert "alerts" in response
    assert isinstance(response["alerts"], list)

    assert "battery" in response
    assert "chargingRate" in response["battery"]
    assert "isDraining" in response["battery"]

    assert "demand" in response
    assert "predicted" in response["demand"]
    assert "actual" in response["demand"]


def test_history_buffer_is_rolling():
    app_main.gridHistory.clear()
    for _ in range(app_main.MAX_HISTORY + 5):
        snapshot = app_main.computeGridSnapshot()
        app_main.gridHistory.append(snapshot)
        if len(app_main.gridHistory) > app_main.MAX_HISTORY:
            app_main.gridHistory.pop(0)

    history_response = asyncio.run(app_main.get_api_history())
    assert history_response["count"] == app_main.MAX_HISTORY
    assert len(history_response["history"]) == app_main.MAX_HISTORY


if __name__ == "__main__":
    test_compute_grid_snapshot_contract()
    test_api_predict_demand_has_predicted_and_actual()
    test_api_battery_status_has_new_fields()
    test_api_balance_grid_has_enriched_fields()
    test_history_buffer_is_rolling()
    print("✅ Frontend contract tests passed")
