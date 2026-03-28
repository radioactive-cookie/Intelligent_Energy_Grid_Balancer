"""Simulation Engine - MW-based realistic energy grid calculations"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from utils import get_logger

logger = get_logger(__name__)


@dataclass
class SimulationInputs:
    """Real-world MW-based simulation inputs"""
    solar_mw: float  # MW
    wind_mw: float   # MW
    demand_mw: float  # MW


@dataclass
class SimulationConfig:
    """System configuration parameters"""
    battery_capacity: float = 500.0  # MWh
    battery_current: float = 250.0  # MWh
    battery_max_charge_rate: float = 50.0  # MW per cycle
    battery_max_discharge_rate: float = 50.0  # MW per cycle
    nominal_frequency: float = 50.0  # Hz
    frequency_constant: float = 0.01
    max_realistic_generation: float = 5000.0  # MW (hackathon limit)


@dataclass
class SimulationResult:
    """Complete simulation result"""
    inputs: Dict
    results: Dict
    timestamp: str
    step_number: int = 1


class SimulationValidator:
    """Validates simulation inputs"""
    
    @staticmethod
    def validate_inputs(solar_mw: float, wind_mw: float, demand_mw: float, 
                       config: SimulationConfig = None) -> tuple[bool, str]:
        """
        Validate MW-based inputs.
        Returns: (is_valid, error_message)
        """
        if config is None:
            config = SimulationConfig()
        
        # Check non-negative
        if solar_mw < 0:
            return False, "solar_mw must be >= 0"
        if wind_mw < 0:
            return False, "wind_mw must be >= 0"
        if demand_mw < 0:
            return False, "demand_mw must be >= 0"
        
        # Check realistic limits
        total_gen = solar_mw + wind_mw
        if total_gen > config.max_realistic_generation:
            return False, f"Total generation ({total_gen} MW) exceeds realistic limit ({config.max_realistic_generation} MW)"
        if demand_mw > config.max_realistic_generation:
            return False, f"Demand ({demand_mw} MW) exceeds realistic limit ({config.max_realistic_generation} MW)"
        
        return True, ""


class SimulationEngine:
    """Executes MW-based power grid simulations"""
    
    def __init__(self, config: SimulationConfig = None):
        """Initialize simulation engine with config"""
        self.config = config or SimulationConfig()
        self.simulation_history: List[SimulationResult] = []
    
    def run_scenario(self, solar_mw: float, wind_mw: float, demand_mw: float) -> Dict:
        """
        Run a single simulation scenario with MW-based inputs.
        
        Implements all 9 calculation steps:
        1. Total generation
        2. Power difference
        3. Battery logic (charge/discharge/idle)
        4. Battery clamping
        5. Battery percent
        6. Grid frequency
        7. Efficiency
        8. Grid status
        9. Optional: stability score
        """
        
        # Validate inputs
        is_valid, error_msg = SimulationValidator.validate_inputs(
            solar_mw, wind_mw, demand_mw, self.config
        )
        if not is_valid:
            logger.error(f"Invalid simulation inputs: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            # 1. TOTAL GENERATION
            total_generation = solar_mw + wind_mw
            logger.debug(f"Total generation: {total_generation} MW (Solar: {solar_mw}, Wind: {wind_mw})")
            
            # 2. POWER DIFFERENCE
            difference = total_generation - demand_mw
            
            # Initialize battery state and action
            battery_current = self.config.battery_current
            battery_action = "idle"
            load_shedding = 0.0
            charge_discharge_amount = 0.0
            
            # 3. BATTERY LOGIC
            if difference > 0:
                # Surplus - charging
                charge_amount = min(difference, self.config.battery_max_charge_rate)
                battery_current += charge_amount
                battery_action = "charging"
                charge_discharge_amount = charge_amount
                logger.debug(f"Surplus: {difference} MW -> Charging battery: {charge_amount} MW")
                surplus = difference
                deficit = 0.0
                
            elif difference < 0:
                # Deficit - discharging
                deficit = abs(difference)
                discharge_amount = min(deficit, self.config.battery_max_discharge_rate, battery_current)
                battery_current -= discharge_amount
                battery_action = "discharging"
                charge_discharge_amount = discharge_amount
                
                # Calculate load shedding if needed
                if discharge_amount < deficit:
                    load_shedding = deficit - discharge_amount
                
                logger.debug(f"Deficit: {deficit} MW -> Discharging battery: {discharge_amount} MW, Load shedding: {load_shedding} MW")
                surplus = 0.0
            else:
                # Balanced
                surplus = 0.0
                deficit = 0.0
                battery_action = "idle"
                load_shedding = 0.0
                logger.debug("Grid balanced - no battery action needed")
            
            # 4. CLAMP BATTERY
            battery_current = max(0, min(battery_current, self.config.battery_capacity))
            
            # 5. BATTERY PERCENT
            battery_percent = (battery_current / self.config.battery_capacity) * 100
            
            # 6. GRID FREQUENCY
            frequency = self.config.nominal_frequency + (self.config.frequency_constant * difference)
            frequency = max(49.5, min(50.5, frequency))  # Clamp 49.5-50.5 Hz
            
            # 7. EFFICIENCY
            if total_generation > 0:
                efficiency = (min(demand_mw, total_generation) / total_generation) * 100
            else:
                efficiency = 0.0
            
            # 8. GRID STATUS
            if 49.8 <= frequency <= 50.2:
                grid_status = "stable"
            elif (49.5 <= frequency < 49.8) or (50.2 < frequency <= 50.5):
                grid_status = "warning"
            else:
                grid_status = "critical"
            
            # OPTIONAL: Grid Stability Score (0-100)
            # Based on: frequency deviation + balance + battery health
            frequency_score = 100 - (abs(frequency - 50.0) * 20)  # ±0.5 Hz = 0-100
            balance_score = 100 if difference == 0 else max(0, 100 - (abs(difference) / total_generation * 100)) if total_generation > 0 else 50
            battery_score = battery_percent  # Battery health
            grid_stability_score = (frequency_score + balance_score + battery_score) / 3
            grid_stability_score = max(0, min(100, grid_stability_score))
            
            # Build result
            result = {
                "inputs": {
                    "solar_mw": solar_mw,
                    "wind_mw": wind_mw,
                    "demand_mw": demand_mw
                },
                "results": {
                    "total_generation": round(total_generation, 2),
                    "surplus": round(max(0, difference), 2),
                    "deficit": round(max(0, -difference), 2),
                    "battery_before": round(self.config.battery_current, 2),
                    "battery_after": round(battery_current, 2),
                    "battery_percent": round(battery_percent, 2),
                    "battery_action": battery_action,
                    "charge_discharge_amount": round(charge_discharge_amount, 2),
                    "load_shedding": round(load_shedding, 2),
                    "frequency": round(frequency, 4),
                    "efficiency": round(efficiency, 2),
                    "grid_status": grid_status,
                    "grid_stability_score": round(grid_stability_score, 2)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Scenario completed: Status={grid_status}, Frequency={frequency} Hz, Stability={grid_stability_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error running simulation scenario: {e}")
            raise
    
    def simulate_steps(self, steps_data: List[Dict], update_state: bool = True) -> List[Dict]:
        """
        Simulate multiple time steps.
        
        Args:
            steps_data: List of dicts with solar_mw, wind_mw, demand_mw for each step
            update_state: If True, update battery state across steps
        
        Returns:
            List of simulation results for each step
        """
        results = []
        
        for step_num, step_input in enumerate(steps_data, 1):
            try:
                result = self.run_scenario(
                    step_input.get("solar_mw", 0),
                    step_input.get("wind_mw", 0),
                    step_input.get("demand_mw", 0)
                )
                result["step"] = step_num
                
                # Update battery state for next step if requested
                if update_state:
                    self.config.battery_current = result["results"]["battery_after"]
                
                results.append(result)
                logger.debug(f"Step {step_num} completed")
                
            except Exception as e:
                logger.error(f"Error in step {step_num}: {e}")
                raise
        
        self.simulation_history.extend(results)
        return results
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get simulation history"""
        return self.simulation_history[-limit:]
    
    def reset_battery_state(self, battery_current: float = None):
        """Reset battery state to a known value"""
        if battery_current is not None:
            self.config.battery_current = max(0, min(battery_current, self.config.battery_capacity))
        logger.info(f"Battery state reset to {self.config.battery_current} MWh")


# Global instance
simulation_engine = SimulationEngine()


def log_simulation_run(inputs: Dict, outputs: Dict):
    """Log simulation run to file/database"""
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "inputs": inputs,
            "outputs": outputs
        }
        logger.info(f"Simulation logged: {log_entry}")
    except Exception as e:
        logger.error(f"Error logging simulation: {e}")
