"""Controllers for handling business logic"""
from fastapi import HTTPException
from typing import List, Dict
from datetime import datetime
from models.energy_source import EnergySource
from models.balancing_action import BalancingAction
from models.grid_state import GridState
from models.battery_storage import BatteryStorage
from models.demand_profile import DemandProfile
from models.alert import Alert
from services import (
    balancing_engine,
    prediction_service,
    monitoring_service,
    data_storage_service,
    simulation_state,
    simulation_engine
)
from utils import mock_generator, get_logger

logger = get_logger(__name__)

# Global state simulation
current_solar = 250.0
current_wind = 180.0
current_battery_soc = 70.0
action_history = []

class GridController:
    """Controller for grid operations"""
    
    @staticmethod
    def get_grid_status() -> Dict:
        """Get current grid status with real calculated values"""
        try:
            # Get calculated dashboard values
            dashboard = simulation_state.get_dashboard()
            
            # Also save to storage for history
            grid_state = GridState(
                grid_id="MAIN_GRID_01",
                frequency=dashboard["frequency"],
                total_generation=dashboard["total_generation"],
                total_demand=dashboard["demand"],
                load_percentage=(dashboard["demand"] / (dashboard["total_generation"] + 0.1)) * 100,
                renewable_percentage=100.0,
                imbalance=dashboard["imbalance"],
                grid_stability_score=95.0 if dashboard["status"] == "stable" else (85.0 if dashboard["status"] == "warning" else 50.0),
                is_stable=dashboard["status"] == "stable"
            )
            
            data_storage_service.save_grid_state(grid_state)
            
            # Return dashboard values
            return dashboard
            
        except Exception as e:
            logger.error(f"Error getting grid status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def get_grid_history(limit: int = 100) -> List[Dict]:
        """Get grid state history"""
        return data_storage_service.get_grid_states(limit)
    
    @staticmethod
    def get_grid_inputs() -> Dict:
        """Get current simulation inputs"""
        return simulation_state.get_inputs()
    
    @staticmethod
    def update_grid_inputs(solar_mw: float = None, wind_mw: float = None, 
                          demand_mw: float = None, battery_current: float = None,
                          battery_capacity: float = None) -> Dict:
        """Update simulation inputs and return new dashboard values"""
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
        """Simulate one time step with new values"""
        try:
            return simulation_state.simulate_step(solar_mw, wind_mw, demand_mw)
        except Exception as e:
            logger.error(f"Error simulating step: {e}")
            raise HTTPException(status_code=500, detail=str(e))

class EnergyController:
    """Controller for energy operations"""
    
    @staticmethod
    def get_solar_generation() -> EnergySource:
        """Get current solar generation"""
        return mock_generator.generate_solar_data()
    
    @staticmethod
    def get_wind_generation() -> EnergySource:
        """Get current wind generation"""
        return mock_generator.generate_wind_data()
    
    @staticmethod
    def get_total_generation() -> Dict:
        """Get total energy generation"""
        solar = mock_generator.generate_solar_data()
        wind = mock_generator.generate_wind_data()
        total = solar.generation_value + wind.generation_value
        
        return {
            "solar": solar.generation_value,
            "wind": wind.generation_value,
            "total": total,
            "timestamp": datetime.utcnow().isoformat()
        }

class BatteryController:
    """Controller for battery operations"""
    
    @staticmethod
    def get_battery_status() -> BatteryStorage:
        """Get current battery status"""
        try:
            battery = mock_generator.generate_battery_status(current_battery_soc, 500.0)
            return battery
        except Exception as e:
            logger.error(f"Error getting battery status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def charge_battery(amount_kw: float) -> Dict:
        """Charge battery"""
        global current_battery_soc
        battery = mock_generator.generate_battery_status(current_battery_soc, 500.0)
        
        max_charge = min(amount_kw, battery.charge_rate)
        charge_percentage = (max_charge / 500.0) * 100
        current_battery_soc = min(100, current_battery_soc + charge_percentage)
        
        return {
            "status": "charging",
            "amount": max_charge,
            "new_soc": current_battery_soc,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def discharge_battery(amount_kw: float) -> Dict:
        """Discharge battery"""
        global current_battery_soc
        battery = mock_generator.generate_battery_status(current_battery_soc, 500.0)
        
        max_discharge = min(amount_kw, battery.discharge_rate)
        discharge_percentage = (max_discharge / 500.0) * 100
        current_battery_soc = max(0, current_battery_soc - discharge_percentage)
        
        return {
            "status": "discharging",
            "amount": max_discharge,
            "new_soc": current_battery_soc,
            "timestamp": datetime.utcnow().isoformat()
        }

class BalancingController:
    """Controller for balancing operations"""
    
    @staticmethod
    def run_balancing() -> BalancingAction:
        """Run balancing decision engine"""
        try:
            grid_state = GridController.get_grid_status()
            battery = BatteryController.get_battery_status()
            demand = mock_generator.generate_demand_profile()
            solar = mock_generator.generate_solar_data()
            wind = mock_generator.generate_wind_data()
            
            # Make balancing decision
            action = balancing_engine.decide_action(
                grid_state,
                battery,
                demand,
                solar.generation_value,
                wind.generation_value
            )
            
            # Check for alerts
            alerts = monitoring_service.check_grid_health(
                grid_state,
                battery,
                solar.generation_value + wind.generation_value,
                demand.current_demand
            )
            
            # Save to storage
            data_storage_service.save_action(action)
            for alert in alerts:
                data_storage_service.save_alert(alert)
            
            action_history.append(action)
            return action
        except Exception as e:
            logger.error(f"Error running balancing: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def get_action_history(limit: int = 100) -> List[Dict]:
        """Get action history"""
        return data_storage_service.get_actions(limit)

class PredictionController:
    """Controller for prediction operations"""
    
    @staticmethod
    def predict_solar_generation(hours: int = 24) -> Dict:
        """Predict solar generation"""
        predictions = prediction_service.predict_solar_generation(hours)
        return {
            "type": "solar",
            "hours": hours,
            "predictions": predictions,
            "unit": "kW",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def predict_wind_generation(hours: int = 24) -> Dict:
        """Predict wind generation"""
        predictions = prediction_service.predict_wind_generation(hours)
        return {
            "type": "wind",
            "hours": hours,
            "predictions": predictions,
            "unit": "kW",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def predict_demand(hours: int = 24) -> Dict:
        """Predict demand"""
        predictions = prediction_service.predict_demand(hours)
        return {
            "type": "demand",
            "hours": hours,
            "predictions": predictions,
            "unit": "kW",
            "timestamp": datetime.utcnow().isoformat()
        }

class SimulationController:
    """Controller for simulation operations"""
    
    @staticmethod
    def run_scenario(solar_mw: float, wind_mw: float, demand_mw: float) -> Dict:
        """
        Run simulation scenario with MW-based inputs.
        
        Implements realistic power grid calculations:
        - Total generation = solar + wind
        - Battery charge/discharge based on surplus/deficit
        - Grid frequency calculation
        - Efficiency and grid status determination
        - Load shedding calculation if needed
        
        Args:
            solar_mw: Solar generation in MW
            wind_mw: Wind generation in MW
            demand_mw: Total demand in MW
        
        Returns:
            Comprehensive simulation result with all calculations
        """
        try:
            result = simulation_engine.run_scenario(solar_mw, wind_mw, demand_mw)
            logger.info(f"Scenario simulation complete: {result['results']['grid_status']}")
            return result
        except ValueError as e:
            logger.error(f"Invalid simulation inputs: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error running simulation: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def run_multi_step_simulation(steps_data: list) -> Dict:
        """
        Simulate multiple time steps sequentially.
        
        Each step can have different solar_mw, wind_mw, demand_mw values.
        Battery state updates across steps.
        
        Args:
            steps_data: List of dicts with solar_mw, wind_mw, demand_mw for each step
        
        Returns:
            List of results for each step + summary statistics
        """
        try:
            if not steps_data or len(steps_data) == 0:
                raise ValueError("steps_data must contain at least one step")
            if len(steps_data) > 10:
                raise ValueError("Maximum 10 steps allowed per simulation")
            
            results = simulation_engine.simulate_steps(steps_data, update_state=True)
            
            # Calculate summary statistics
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
            
            logger.info(f"Multi-step simulation complete: {len(results)} steps, "
                       f"avg_stability={summary['avg_stability_score']}")
            
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
        """Get simulation history"""
        return {
            "history": simulation_engine.get_history(limit),
            "count": len(simulation_engine.get_history(limit))
        }
    
    @staticmethod
    def reset_simulation_state(battery_current: float = 250.0) -> Dict:
        """Reset simulation state"""
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
    """Controller for alert operations"""
    
    @staticmethod
    def get_all_alerts() -> Dict:
        """Get all alerts"""
        return {
            "alerts": [a.model_dump() for a in monitoring_service.get_active_alerts()],
            "stats": monitoring_service.get_alert_stats()
        }
    
    @staticmethod
    def get_alert_history(limit: int = 100) -> List[Dict]:
        """Get alert history"""
        return data_storage_service.get_alerts(limit)
    
    @staticmethod
    def resolve_alert(alert_id: str) -> Dict:
        """Resolve an alert"""
        monitoring_service.resolve_alert(alert_id)
        return {"status": "resolved", "alert_id": alert_id}

class MetricsController:
    """Controller for metrics and statistics"""
    
    @staticmethod
    def get_system_metrics() -> Dict:
        """Get system metrics"""
        grid_state = GridController.get_grid_status()
        battery = BatteryController.get_battery_status()
        alerts = monitoring_service.get_alert_stats()
        
        stability_score = balancing_engine.get_grid_stability_score(grid_state, battery)
        
        metrics = {
            "grid_frequency": grid_state.frequency,
            "grid_stability_score": stability_score,
            "total_generation": grid_state.total_generation,
            "total_demand": grid_state.total_demand,
            "battery_soc": battery.state_of_charge,
            "battery_health": battery.health,
            "renewable_percentage": grid_state.renewable_percentage,
            "load_percentage": grid_state.load_percentage,
            "alerts": alerts,
            "decisions_made": balancing_engine.decision_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        data_storage_service.save_metrics(metrics)
        return metrics
