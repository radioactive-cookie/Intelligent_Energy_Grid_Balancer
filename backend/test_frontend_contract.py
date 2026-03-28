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
    assert "total_supply" in snapshot
    assert "total_demand" in snapshot
    assert "battery_level" in snapshot
    assert "grid_status" in snapshot
    assert "houses" in snapshot
    assert "alerts" in snapshot
    assert "sources" in snapshot
    assert "dataSource" in snapshot
    assert "rawWeather" in snapshot
    assert "carbonIntensity" in snapshot

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
    assert isinstance(snapshot["sources"], dict)
    assert "solar" in snapshot["sources"]
    assert "wind" in snapshot["sources"]
    assert snapshot["dataSource"] in ("real", "simulated")
    assert isinstance(snapshot["rawWeather"], dict)
    assert isinstance(snapshot["carbonIntensity"], (int, float))
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
    assert "sources" in response
    assert "total_supply" in response
    assert "total_demand" in response
    assert "battery_level" in response
    assert "grid_status" in response
    assert "houses" in response
    assert "dataSource" in response
    assert "rawWeather" in response
    assert "carbonIntensity" in response


def test_api_simulate_scenario_contract_and_calculations():
    request = app_main.ScenarioSimulationRequest(
        demandMultiplier=2.0,
        loadSheddingPercent=20,
        hour=14,
    )
    response = asyncio.run(app_main.post_api_simulate_scenario(request))

    assert response["scenario"]["demandMultiplier"] == 2.0
    assert response["scenario"]["hour"] == 14

    assert "supply" in response
    assert "demand" in response
    assert "battery" in response
    assert "zones" in response
    assert "strategy" in response

    expected_scaled = round(app_main.BASE_MAX_LOAD * 2.0, 1)
    assert response["demand"]["scaled"] == expected_scaled

    industrial = round(expected_scaled * 0.4, 1)
    commercial = round(expected_scaled * 0.3, 1)
    industrial_shed = round(industrial * 0.2, 1)
    commercial_shed = round(commercial * 0.1, 1)
    total_shed = round(industrial_shed + commercial_shed, 1)
    after_shedding = round(expected_scaled - total_shed, 1)

    assert response["zones"]["industrial"]["demandKw"] == industrial
    assert response["zones"]["industrial"]["shedKw"] == industrial_shed
    assert response["zones"]["commercial"]["demandKw"] == commercial
    assert response["zones"]["commercial"]["shedKw"] == commercial_shed
    assert response["demand"]["loadShedKw"] == total_shed
    assert response["demand"]["afterShedding"] == after_shedding

    expected_gap = round(after_shedding - response["supply"]["total"], 1)
    assert response["gap"] == expected_gap

    if expected_gap > 0:
        assert response["gridStatus"] == "DEFICIT"
        assert response["battery"]["netDrainRateKw"] == expected_gap
        assert response["strategy"]["label"] in {
            "MINOR_DEFICIT_BATTERY_ONLY",
            "LOAD_SHEDDING_AND_BATTERY",
            "CRITICAL_SHED_ALL",
        }
    else:
        assert response["gridStatus"] == "SURPLUS"
        assert response["battery"]["netDrainRateKw"] == 0
        assert response["strategy"]["label"] == "SURPLUS_STORE"


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
    test_api_simulate_scenario_contract_and_calculations()
    test_history_buffer_is_rolling()
    print("✅ Frontend contract tests passed")
