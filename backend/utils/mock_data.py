"""Mock data generator for simulation"""
import random
from datetime import datetime, timedelta
from models.energy_source import EnergySource
from models.grid_state import GridState
from models.battery_storage import BatteryStorage
from models.demand_profile import DemandProfile

class MockDataGenerator:
    """Generate mock data for testing and simulation"""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
    
    @staticmethod
    def generate_solar_data(current_hour: int = None, capacity: float = 500.0) -> EnergySource:
        """Generate mock solar generation data"""
        if current_hour is None:
            current_hour = datetime.now().hour
        
        # Solar generation peaks at noon (12:00)
        hour_factor = max(0, -1 * (current_hour - 12) ** 2 + 144) / 144
        base_generation = capacity * hour_factor * random.uniform(0.8, 1.0)
        
        return EnergySource(
            source_id="SOLAR_01",
            type="solar",
            generation_value=max(0, base_generation),
            capacity=capacity,
            location="Northern Farm",
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def generate_wind_data(capacity: float = 400.0) -> EnergySource:
        """Generate mock wind generation data"""
        wind_speed = random.uniform(0, 25)  # m/s
        # Wind generation increases with wind speed (cubic relationship)
        power_coefficient = (wind_speed / 25) ** 3 if wind_speed > 0 else 0
        generation = capacity * power_coefficient * random.uniform(0.7, 1.0)
        
        return EnergySource(
            source_id="WIND_01",
            type="wind",
            generation_value=max(0, generation),
            capacity=capacity,
            location="Coastal Wind Farm",
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def generate_demand_profile(current_hour: int = None, base_demand: float = 1500.0) -> DemandProfile:
        """Generate mock demand profile"""
        if current_hour is None:
            current_hour = datetime.now().hour
        
        # Daily demand pattern: low night, peak morning and evening
        if 6 <= current_hour < 9:
            demand_factor = 0.85  # Morning peak preparation
        elif 9 <= current_hour < 17:
            demand_factor = 0.95  # Day
        elif 17 <= current_hour < 21:
            demand_factor = 1.0  # Evening peak
        else:
            demand_factor = 0.6  # Night
        
        current_demand = base_demand * demand_factor * random.uniform(0.9, 1.1)
        
        hourly_dist = {str(h): base_demand * max(0.6, 1.0 - abs(h - 18) / 24) for h in range(24)}
        
        return DemandProfile(
            profile_id="DEMAND_01",
            current_demand=current_demand,
            peak_demand=base_demand * 1.2,
            minimum_demand=base_demand * 0.5,
            average_demand=base_demand,
            timestamp=datetime.utcnow(),
            hourly_distribution=hourly_dist,
            sector_breakdown={
                "residential": current_demand * 0.5,
                "commercial": current_demand * 0.35,
                "industrial": current_demand * 0.15
            }
        )
    
    @staticmethod
    def generate_battery_status(current_soc: float = 70.0, capacity: float = 500.0) -> BatteryStorage:
        """Generate mock battery status"""
        current_level = (current_soc / 100) * capacity
        
        return BatteryStorage(
            battery_id="BATT_01",
            capacity=capacity,
            current_level=current_level,
            charge_rate=100.0,
            discharge_rate=100.0,
            state_of_charge=current_soc,
            status="idle",
            health=random.uniform(90, 100),
            timestamp=datetime.utcnow(),
            temperature=random.uniform(20, 30),
            cycles=random.randint(1000, 2000)
        )
    
    @staticmethod
    def generate_grid_state(generation: float, demand: float, frequency: float = 50.0) -> GridState:
        """Generate mock grid state"""
        imbalance = generation - demand
        renewable_pct = (generation / (generation + demand)) * 100 if (generation + demand) > 0 else 0
        
        # Calculate stability score
        freq_deviation = abs(frequency - 50.0)
        freq_score = max(0, 100 - freq_deviation * 50)
        balance_score = max(0, 100 - abs(imbalance) / max(1, demand) * 100)
        stability_score = (freq_score + balance_score) / 2
        
        return GridState(
            grid_id="MAIN_GRID_01",
            frequency=frequency,
            total_generation=generation,
            total_demand=demand,
            load_percentage=(demand / max(1, demand + generation)) * 100,
            renewable_percentage=renewable_pct,
            timestamp=datetime.utcnow(),
            grid_stability_score=stability_score,
            is_stable=freq_deviation <= 0.5 and stability_score >= 80,
            imbalance=imbalance
        )

# Singleton instance
mock_generator = MockDataGenerator()
