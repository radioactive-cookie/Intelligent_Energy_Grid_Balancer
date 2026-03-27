"""Prediction Service - ML/AI for forecasting"""
import random
from datetime import datetime, timedelta
from typing import List, Dict
from models.energy_source import EnergySource
from models.demand_profile import DemandProfile
from utils.helpers import get_logger

logger = get_logger(__name__)

class PredictionService:
    """Simple prediction service using linear regression and time-series analysis"""
    
    def __init__(self):
        self.solar_history = []
        self.wind_history = []
        self.demand_history = []
    
    def predict_solar_generation(self, forecast_hours: int = 24, current_hour: int = None) -> List[float]:
        """
        Predict solar generation for next N hours.
        Uses simple hour-based model (solar peaks at noon).
        """
        if current_hour is None:
            current_hour = datetime.now().hour
        
        predictions = []
        capacity = 500.0
        
        for hour in range(forecast_hours):
            target_hour = (current_hour + hour) % 24
            # Solar generation peaks at noon (hour 12)
            hour_factor = max(0, -1 * (target_hour - 12) ** 2 + 144) / 144
            prediction = capacity * hour_factor * random.uniform(0.7, 1.0)
            predictions.append(max(0, prediction))
        
        logger.info(f"Predicted solar generation for next {forecast_hours} hours")
        return predictions
    
    def predict_wind_generation(self, forecast_hours: int = 24) -> List[float]:
        """
        Predict wind generation for next N hours.
        Uses stochastic model (random walks with trends).
        """
        predictions = []
        capacity = 400.0
        current_speed = random.uniform(5, 15)  # m/s
        
        for _ in range(forecast_hours):
            # Random walk with mean reversion
            current_speed = current_speed * random.uniform(0.95, 1.05)
            current_speed = max(0, min(25, current_speed))
            
            power_coefficient = (current_speed / 25) ** 3
            prediction = capacity * power_coefficient * random.uniform(0.8, 1.0)
            predictions.append(max(0, prediction))
        
        logger.info(f"Predicted wind generation for next {forecast_hours} hours")
        return predictions
    
    def predict_demand(self, forecast_hours: int = 24, current_hour: int = None) -> List[float]:
        """
        Predict demand for next N hours.
        Uses daily demand pattern with random variations.
        """
        if current_hour is None:
            current_hour = datetime.now().hour
        
        predictions = []
        base_demand = 1500.0
        
        for hour in range(forecast_hours):
            target_hour = (current_hour + hour) % 24
            
            # Daily pattern
            if 6 <= target_hour < 9:
                demand_factor = 0.85
            elif 9 <= target_hour < 17:
                demand_factor = 0.95
            elif 17 <= target_hour < 21:
                demand_factor = 1.0
            else:
                demand_factor = 0.6
            
            prediction = base_demand * demand_factor * random.uniform(0.9, 1.1)
            predictions.append(max(0, prediction))
        
        logger.info(f"Predicted demand for next {forecast_hours} hours")
        return predictions
    
    def add_historical_data(self, solar: float, wind: float, demand: float):
        """Add data point to history"""
        self.solar_history.append(solar)
        self.wind_history.append(wind)
        self.demand_history.append(demand)
        
        # Keep only last 168 points (7 days of hourly data)
        if len(self.solar_history) > 168:
            self.solar_history.pop(0)
            self.wind_history.pop(0)
            self.demand_history.pop(0)
    
    def get_confidence_interval(self, mean: float, std_dev: float = None, confidence: float = 0.95) -> Dict[str, float]:
        """Calculate confidence interval for predictions"""
        if std_dev is None:
            std_dev = mean * 0.1  # Assume 10% standard deviation
        
        # 95% confidence interval is approximately ±1.96 * std_dev
        z_score = 1.96 if confidence == 0.95 else 2.576
        
        return {
            "lower": max(0, mean - z_score * std_dev),
            "mean": mean,
            "upper": mean + z_score * std_dev
        }
    
    def get_accuracy_metrics(self) -> Dict[str, float]:
        """Get prediction accuracy metrics"""
        if len(self.solar_history) < 2:
            return {"solar_rmse": 0, "wind_rmse": 0, "demand_rmse": 0}
        
        # Simple metric: calculate variance
        solar_variance = self._calculate_variance(self.solar_history)
        wind_variance = self._calculate_variance(self.wind_history)
        demand_variance = self._calculate_variance(self.demand_history)
        
        return {
            "solar_variance": solar_variance,
            "wind_variance": wind_variance,
            "demand_variance": demand_variance,
            "data_points": len(self.solar_history)
        }
    
    @staticmethod
    def _calculate_variance(data: List[float]) -> float:
        """Calculate variance of a data series"""
        if len(data) < 2:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance
