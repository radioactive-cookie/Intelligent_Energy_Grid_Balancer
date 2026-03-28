"""Dashboard Calculator Service - Computes real dashboard values from simulation inputs"""
from typing import Dict, Optional
from dataclasses import dataclass
from utils import get_logger

logger = get_logger(__name__)


@dataclass
class DashboardInputs:
    """Input parameters for dashboard calculations"""
    solar_mw: float  # Solar generation in MW
    wind_mw: float   # Wind generation in MW
    demand_mw: float  # Demand in MW
    battery_current: float  # Current battery charge in MWh
    battery_current: float  # Current battery charge in MWh
    battery_capacity: float  # Battery capacity in MWh
    weather_data: Optional[Dict] = None  # Live weather metadata


class DashboardCalculator:
    """Calculates all dashboard values based on real inputs and system logic"""
    
    @staticmethod
    def calculate_dashboard(inputs: DashboardInputs) -> Dict:
        """
        Calculate all dashboard values from inputs using the specified formulas.
        
        Calculations:
        1. TOTAL GENERATION: solar_mw + wind_mw
        2. SURPLUS / DEFICIT: difference = total_generation - demand_mw
        3. BATTERY UPDATE: Update based on surplus/deficit
        4. BATTERY PERCENT: (battery_current / battery_capacity) * 100
        5. GRID FREQUENCY: 50 + (0.01 * (total_generation - demand_mw)), clamped 49.5-50.5
        6. EFFICIENCY: (demand_mw / total_generation) * 100
        7. GRID STATUS: Based on frequency ranges
        8. API RESPONSE: Return calculated values
        """
        
        try:
            # 1. TOTAL GENERATION
            total_generation = inputs.solar_mw + inputs.wind_mw
            logger.debug(f"Total generation: {total_generation} MW (Solar: {inputs.solar_mw}, Wind: {inputs.wind_mw})")
            
            # 2. SURPLUS / DEFICIT
            difference = total_generation - inputs.demand_mw
            if difference > 0:
                surplus = difference
                deficit = 0.0
            else:
                surplus = 0.0
                deficit = abs(difference)
            logger.debug(f"Surplus: {surplus} MW, Deficit: {deficit} MW")
            
            # 3. BATTERY UPDATE
            battery_current = inputs.battery_current
            
            if surplus > 0:
                battery_current += surplus
                logger.debug(f"Battery charging with surplus: +{surplus} MWh")
            
            if deficit > 0:
                battery_current -= deficit
                logger.debug(f"Battery discharging to cover deficit: -{deficit} MWh")
            
            # Clamp battery between 0 and capacity
            battery_current = max(0.0, min(float(battery_current), float(inputs.battery_capacity)))
            logger.debug(f"Battery after update: {battery_current} MWh / {inputs.battery_capacity} MWh")
            
            # 4. BATTERY PERCENT
            battery_percent = (battery_current / inputs.battery_capacity) * 100 if inputs.battery_capacity > 0 else 0
            logger.debug(f"Battery percent: {battery_percent:.2f}%")
            
            # 5. GRID FREQUENCY
            k = 0.01
            frequency = 50.0 + (k * (total_generation - inputs.demand_mw))
            # Clamp frequency between 49.5 and 50.5
            frequency = max(49.5, min(50.5, frequency))
            logger.debug(f"Grid frequency: {frequency:.4f} Hz")
            
            # 6. EFFICIENCY
            efficiency = (inputs.demand_mw / total_generation) * 100 if total_generation > 0 else 0
            logger.debug(f"Efficiency: {efficiency:.2f}%")
            
            # 7. GRID STATUS
            if 49.8 <= frequency <= 50.2:
                status = "stable"
            elif (49.5 <= frequency < 49.8) or (50.2 < frequency <= 50.5):
                status = "warning"
            else:
                status = "critical"
            logger.debug(f"Grid status: {status}")
            
            # 8. API RESPONSE
            return {
                "total_generation": float(round(total_generation, 2)),
                "demand": float(round(inputs.demand_mw, 2)),
                "frequency": float(round(frequency, 4)),
                "efficiency": float(round(efficiency, 2)),
                "battery_percent": float(round(battery_percent, 2)),
                "battery_current": float(round(battery_current, 2)),
                "battery_capacity": float(round(inputs.battery_capacity, 2)),
                "status": status,
                "surplus": float(round(surplus, 2)),
                "deficit": float(round(deficit, 2)),
                "imbalance": float(round(total_generation - inputs.demand_mw, 2)),
                "solar_generation": float(round(inputs.solar_mw, 2)),
                "wind_generation": float(round(inputs.wind_mw, 2)),
                "weather": inputs.weather_data or {"location": "Bhubaneswar, IN", "solar_radiation": 0, "wind_speed": 0}
            }
            
        except Exception as e:
            logger.error(f"Error calculating dashboard values: {e}")
            raise


# Global state to hold current inputs
class SimulationState:
    """Manages the current simulation state"""
    
    def __init__(self):
        # Default state
        self.inputs = DashboardInputs(
            solar_mw=150.0,
            wind_mw=200.0,
            demand_mw=350.0,
            battery_current=350.0,
            battery_capacity=500.0,
            weather_data={"location": "Bhubaneswar, IN", "solar_radiation": 800, "wind_speed": 15}
        )
        self.last_dashboard = {}
        self._update_dashboard()

    def update_from_weather(self, weather: Dict):
        """Scale generation based on real world radiation and wind speed"""
        # Solar scaling: 1000 W/m2 = 100% of 250MW capacity
        irradiance = weather.get("solar_radiation", 0)
        solar_capacity = 250.0 
        new_solar = (irradiance / 1000.0) * solar_capacity
        
        # Wind scaling: 45 km/h = 100% of 300MW capacity
        wind_speed = weather.get("wind_speed", 0)
        wind_capacity = 300.0
        new_wind = (wind_speed / 45.0) * wind_capacity
        
        # Clamp values
        new_solar = max(5.0, min(new_solar, solar_capacity)) # Always at least 5MW during day
        new_wind = max(10.0, min(new_wind, wind_capacity))
        
        self.inputs.weather_data = weather
        return self.update_inputs(solar_mw=new_solar, wind_mw=new_wind)
    
    def update_inputs(self, solar_mw: Optional[float] = None, wind_mw: Optional[float] = None, 
                     demand_mw: Optional[float] = None, battery_current: Optional[float] = None, 
                     battery_capacity: Optional[float] = None) -> Dict:
        """
        Update simulation inputs and recalculate dashboard.
        Only provided parameters are updated.
        """
        if solar_mw is not None:
            self.inputs.solar_mw = max(0.0, float(solar_mw))
        if wind_mw is not None:
            self.inputs.wind_mw = max(0.0, float(wind_mw))
        if demand_mw is not None:
            self.inputs.demand_mw = max(0.0, float(demand_mw))
        if battery_current is not None:
            self.inputs.battery_current = max(0.0, float(battery_current))
        if battery_capacity is not None:
            self.inputs.battery_capacity = max(0.1, float(battery_capacity))  # Prevent division by zero
        
        self._update_dashboard()
        logger.info(f"Simulation inputs updated: Solar={self.inputs.solar_mw}, Wind={self.inputs.wind_mw}, "
                   f"Demand={self.inputs.demand_mw}, Battery={self.inputs.battery_current}/{self.inputs.battery_capacity}")
        return self.last_dashboard
    
    def _update_dashboard(self):
        """Calculate dashboard values for current inputs and persist state changes"""
        self.last_dashboard = DashboardCalculator.calculate_dashboard(self.inputs)
        # Persist the calculated battery level back into our state for the next cycle
        if "battery_current" in self.last_dashboard:
            self.inputs.battery_current = self.last_dashboard["battery_current"]
    
    def get_dashboard(self) -> Dict:
        """Get current dashboard values"""
        return self.last_dashboard
    
    def get_inputs(self) -> Dict:
        """Get current input values"""
        return {
            "solar_mw": self.inputs.solar_mw,
            "wind_mw": self.inputs.wind_mw,
            "demand_mw": self.inputs.demand_mw,
            "battery_current": self.inputs.battery_current,
            "battery_capacity": self.inputs.battery_capacity
        }
    
    def simulate_step(self, solar_mw: float, wind_mw: float, demand_mw: float) -> Dict:
        """
        Simulate one time step with new generation and demand values.
        Battery automatically adjusts based on surplus/deficit.
        """
        return self.update_inputs(solar_mw=solar_mw, wind_mw=wind_mw, demand_mw=demand_mw)


# Global instance
simulation_state = SimulationState()
