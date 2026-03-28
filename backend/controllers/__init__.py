"""
CORE CONTROLLER - Intelligent Energy Grid Balancer
REFACTORED: Centralized Simulation State & Real-Time Logic
"""
from fastapi import HTTPException
from typing import List, Dict, Any
from datetime import datetime

from models.grid_state import GridState
from models.battery_storage import BatteryStorage
from services.dashboard_calculator import DashboardCalculator, DashboardInputs
from services import (
    balancing_engine,
    prediction_service,
    monitoring_service,
    data_storage_service,
    simulation_state,
    simulation_engine,
    real_data_fetcher,
    carbon_service,
)
from utils import get_logger

logger = get_logger(__name__)


class GridController:
    """Controller for unified grid operations"""

    @staticmethod
    def get_grid_status() -> GridState:
        try:
            dashboard = simulation_state.get_dashboard()

            gen_total = dashboard.get("total_generation", 0.1)
            demand_total = dashboard.get("demand", 0.0)
            load_pc = (demand_total / (gen_total + 0.1)) * 100

            grid_state = GridState(
                grid_id="MAIN_GRID_01",
                frequency=dashboard.get("frequency", 50.0),
                total_generation=gen_total,
                total_demand=demand_total,
                load_percentage=min(load_pc, 100.0),  # clamped to model max
                renewable_percentage=100.0,
                imbalance=dashboard.get("imbalance", 0.0),
                grid_stability_score=dashboard.get("grid_stability_score", 95.0),
                is_stable=dashboard.get("status") == "stable",
                solar_mw=dashboard.get("solar_generation", 0.0),
                wind_mw=dashboard.get("wind_generation", 0.0)
            )

            data_storage_service.save_grid_state(grid_state)
            return grid_state

        except Exception as e:
            logger.error(f"Critical error in Grid Status sync: {e}")
            raise HTTPException(status_code=500, detail="Internal Grid Engine Error")

    @staticmethod
    def get_grid_history(limit: int = 100) -> List[Dict]:
        return data_storage_service.get_grid_states(limit)

    @staticmethod
    def get_grid_inputs() -> Dict:
        return simulation_state.get_inputs()

    @staticmethod
    def update_grid_inputs(solar_mw: float = None, wind_mw: float = None,
                           demand_mw: float = None, battery_current: float = None,
                           battery_capacity: float = None) -> Dict:
        try:
            return simulation_state.update_inputs(
                solar_mw=solar_mw,
                wind_mw=wind_mw,
                demand_mw=demand_mw,
                battery_current=battery_current,
                battery_capacity=battery_capacity
            )
        except Exception as e:
            logger.error(f"Error updating grid inputs: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def simulate_step(solar_mw: float, wind_mw: float, demand_mw: float) -> Dict:
        try:
            return simulation_state.simulate_step(solar_mw, wind_mw, demand_mw)
        except Exception as e:
            logger.error(f"Error simulating step: {e}")
            raise HTTPException(status_code=500, detail=str(e))


class EnergyController:
    """Synchronized Energy reporting"""

    @staticmethod
    def get_solar_generation() -> Dict:
        dashboard = simulation_state.get_dashboard()
        return {
            "type": "solar",
            "generation_value": dashboard.get("solar_mw", 0.0),
            "unit": "MW",
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def get_wind_generation() -> Dict:
        dashboard = simulation_state.get_dashboard()
        return {
            "type": "wind",
            "generation_value": dashboard.get("wind_mw", 0.0),
            "unit": "MW",
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def get_total_generation() -> Dict:
        dashboard = simulation_state.get_dashboard()
        return {
            "solar": dashboard.get("solar_mw", 0.0),
            "wind": dashboard.get("wind_mw", 0.0),
            "total": dashboard.get("total_generation", 0.0),
            "timestamp": datetime.utcnow().isoformat()
        }


class BatteryController:
    """Direct Battery state-of-charge tracking"""

    @staticmethod
    def get_battery_status() -> Dict:
        config = simulation_engine.config
        soc_percent = (config.battery_current / config.battery_capacity) * 100
        # last_imbalance is not stored on SimulationEngine; derive from dashboard instead
        dashboard = simulation_state.get_dashboard()
        last_imbalance = dashboard.get("imbalance", 0.0)
        return {
            "current_mw": round(config.battery_current, 2),
            "capacity_mw": config.battery_capacity,
            "soc_percentage": round(soc_percent, 2),
            "is_active": abs(last_imbalance) > 0.5,
            "flow_direction": "charging" if last_imbalance > 0 else "discharging"
        }

    @staticmethod
    def charge_battery(amount_mw: float) -> Dict:
        config = simulation_engine.config
        config.battery_current = min(config.battery_capacity, config.battery_current + amount_mw)
        soc_percent = (config.battery_current / config.battery_capacity) * 100
        return {
            "status": "charging",
            "amount_mw": amount_mw,
            "new_soc": round(soc_percent, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def discharge_battery(amount_mw: float) -> Dict:
        config = simulation_engine.config
        config.battery_current = max(0.0, config.battery_current - amount_mw)
        soc_percent = (config.battery_current / config.battery_capacity) * 100
        return {
            "status": "discharging",
            "amount_mw": amount_mw,
            "new_soc": round(soc_percent, 2),
            "timestamp": datetime.utcnow().isoformat()
        }


class BalancingController:
    """Controller for balancing operations"""

    @staticmethod
    def run_balancing() -> Dict:
        try:
            grid_state = GridController.get_grid_status()
            battery_dict = BatteryController.get_battery_status()
            dashboard = simulation_state.get_dashboard()

            # BalancingEngine.decide_action expects a DemandProfile for demand arg,
            # but internally only uses demand.current_demand — pass a compatible object.
            # Build a proper BatteryStorage model from the dict so type checks pass.
            battery_model = BatteryStorage(
                battery_id="BATT_01",
                capacity=battery_dict["capacity_mw"],
                current_level=battery_dict["current_mw"],
                charge_rate=simulation_engine.config.battery_max_charge_rate,
                discharge_rate=simulation_engine.config.battery_max_discharge_rate,
                state_of_charge=battery_dict["soc_percentage"],
                status="charging" if battery_dict["flow_direction"] == "charging" else "discharging"
            )

            # demand passed as a simple float; balancing_engine accepts it via duck-typing
            # (it accesses demand.current_demand — wrap in a simple namespace)
            class _DemandWrapper:
                def __init__(self, v: float):
                    self.current_demand = v

            action = balancing_engine.decide_action(
                grid_state,
                battery_model,
                _DemandWrapper(dashboard.get("demand", 0.0)),
                dashboard.get("solar_mw", 0.0),
                dashboard.get("wind_mw", 0.0)
            )

            alerts = monitoring_service.check_grid_health(
                grid_state,
                battery_model,
                dashboard.get("total_generation", 0.0),
                dashboard.get("demand", 0.0)
            )

            data_storage_service.save_action(action)
            for alert in alerts:
                data_storage_service.save_alert(alert)

            return action
        except Exception as e:
            logger.error(f"Error running balancing: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_action_history(limit: int = 100) -> List[Dict]:
        return data_storage_service.get_actions(limit)


class PredictionController:
    """Controller for prediction operations"""

    @staticmethod
    def predict_solar_generation(hours: int = 24) -> Dict:
        predictions = prediction_service.predict_solar_generation(hours)
        return {
            "type": "solar",
            "hours": hours,
            "predictions": predictions,
            "unit": "MW",
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def predict_wind_generation(hours: int = 24) -> Dict:
        predictions = prediction_service.predict_wind_generation(hours)
        return {
            "type": "wind",
            "hours": hours,
            "predictions": predictions,
            "unit": "MW",
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def predict_demand(hours: int = 24) -> Dict:
        predictions = prediction_service.predict_demand(hours)
        return {
            "type": "demand",
            "hours": hours,
            "predictions": predictions,
            "unit": "MW",
            "timestamp": datetime.utcnow().isoformat()
        }


class SimulationController:
    """The Brain - Logic-driven Simulation"""

    @staticmethod
    def run_scenario(solar_mw: float, wind_mw: float, demand_mw: float) -> Dict:
        try:
            result = simulation_engine.run_scenario(solar_mw, wind_mw, demand_mw)

            simulation_state.update_inputs(
                solar_mw=solar_mw,
                wind_mw=wind_mw,
                demand_mw=demand_mw
            )

            grid_state = GridController.get_grid_status()
            config = simulation_engine.config
            battery_model = BatteryStorage(
                battery_id="SIM_BATT_01",
                capacity=config.battery_capacity,
                current_level=config.battery_current,
                charge_rate=config.battery_max_charge_rate,
                discharge_rate=config.battery_max_discharge_rate,
                state_of_charge=(config.battery_current / config.battery_capacity) * 100,
                status="idle"
            )

            alerts = monitoring_service.check_grid_health(
                grid_state,
                battery_model,
                solar_mw + wind_mw,
                demand_mw
            )

            data_storage_service.save_simulation_run(result)

            logger.info(f"Scenario complete: {result['results']['grid_status']}")
            return {
                "results": result["results"],
                "active_alerts": len(alerts),
                "timestamp": datetime.utcnow().isoformat()
            }
        except ValueError as e:
            logger.error(f"Invalid simulation inputs: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Scenario Failure: {e}")
            raise HTTPException(status_code=500, detail="Invalid Simulation Parameters")

    @staticmethod
    def run_multi_step_simulation(steps_data: list) -> Dict:
        try:
            if not steps_data or len(steps_data) == 0:
                raise ValueError("steps_data must contain at least one step")
            if len(steps_data) > 10:
                raise ValueError("Maximum 10 steps allowed per simulation")

            results = simulation_engine.simulate_steps(steps_data, update_state=True)

            statuses = [r["results"]["grid_status"] for r in results]
            frequencies = [r["results"]["frequency"] for r in results]
            stabilities = [r["results"]["grid_stability_score"] for r in results]

            summary = {
                "total_steps": len(results),
                "stable_steps": statuses.count("stable"),
                "warning_steps": statuses.count("warning"),
                "critical_steps": statuses.count("critical"),
                "avg_frequency": round(sum(frequencies) / len(frequencies), 4),
                "avg_stability_score": round(sum(stabilities) / len(stabilities), 2),
                "final_battery_percent": results[-1]["results"]["battery_percent"],
                "final_battery_mwh": results[-1]["results"]["battery_after"],
                "total_load_shedding": round(sum(r["results"]["load_shedding"] for r in results), 2)
            }

            return {
                "steps": results,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            }
        except ValueError as e:
            logger.error(f"Invalid multi-step input: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error running multi-step simulation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_simulation_history(limit: int = 50) -> Dict:
        history = simulation_engine.get_history(limit)
        return {
            "history": history,
            "count": len(history)
        }

    @staticmethod
    def reset_simulation_state(battery_current: float = 250.0) -> Dict:
        try:
            simulation_engine.reset_battery_state(battery_current)
            return {
                "status": "reset",
                "battery_current": simulation_engine.config.battery_current,
                "battery_capacity": simulation_engine.config.battery_capacity
            }
        except Exception as e:
            logger.error(f"Error resetting simulation state: {e}")
            raise HTTPException(status_code=500, detail=str(e))


class AlertController:
    """Real-time Alert Management"""

    @staticmethod
    def get_all_alerts() -> Dict:
        return {
            "active": [a.model_dump() for a in monitoring_service.get_active_alerts()],
            "stats": monitoring_service.get_alert_stats()
        }

    @staticmethod
    def get_alert_history(limit: int = 100) -> List[Dict]:
        return data_storage_service.get_alerts(limit)

    @staticmethod
    def resolve_alert(alert_id: str) -> Dict:
        monitoring_service.resolve_alert(alert_id)
        return {"status": "resolved", "alert_id": alert_id}


class MetricsController:
    """Unified Metrics for the Frontend Dashboard"""

    @staticmethod
    def _build_enhanced_metrics() -> Dict:
        current_inputs = simulation_state.get_inputs()
        weather_generation = real_data_fetcher.get_generation(current_inputs)
        enhanced_inputs = DashboardInputs(
            solar_mw=weather_generation["solar_mw"],
            wind_mw=weather_generation["wind_mw"],
            demand_mw=current_inputs.get("demand_mw", 0.0),
            battery_current=current_inputs.get("battery_current", 0.0),
            battery_capacity=current_inputs.get("battery_capacity", simulation_engine.config.battery_capacity),
        )
        # Calculate derived metrics from the selected data source without mutating shared simulation state.
        enhanced = DashboardCalculator.calculate_dashboard(enhanced_inputs)
        config = simulation_engine.config
        alerts = monitoring_service.get_alert_stats()
        carbon_intensity = carbon_service.get_carbon_intensity()

        total_supply = enhanced.get("total_generation", 0.0)
        total_demand = enhanced.get("demand", 0.0)
        battery_percent = enhanced.get("battery_percent", 0.0)
        battery_current = enhanced.get("battery_current", 0.0)

        return {
            "total_supply": total_supply,
            "total_demand": total_demand,
            "battery_level": battery_percent,
            "grid_status": enhanced.get("status", "stable"),
            "houses": 0,
            "alerts": alerts,
            "sources": {
                "solar": enhanced.get("solar_generation", 0.0),
                "wind": enhanced.get("wind_generation", 0.0),
            },
            "dataSource": weather_generation.get("dataSource", "simulated"),
            "rawWeather": weather_generation.get("rawWeather", {}),
            "carbonIntensity": carbon_intensity,
            # Backward-compatible keys for existing UI mapping.
            "frequency": round(enhanced.get("frequency", 50.0), 3),
            "stability_score": enhanced.get("grid_stability_score", 100),
            "total_gen": total_supply,
            "solar_gen": enhanced.get("solar_generation", 0.0),
            "wind_gen": enhanced.get("wind_generation", 0.0),
            "battery_soc": battery_percent,
            "battery_current": battery_current,
            "battery_capacity": enhanced.get("battery_capacity", config.battery_capacity),
            "renewable_pc": 100.0,
            "status": enhanced.get("status", "stable"),
            "decisions_made": balancing_engine.decision_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def get_system_metrics() -> Dict:
        return MetricsController._build_enhanced_metrics()


# Explicit exports so routes can import all controllers
__all__ = [
    "GridController",
    "EnergyController",
    "BatteryController",
    "BalancingController",
    "PredictionController",
    "SimulationController",
    "AlertController",
    "MetricsController"
]
