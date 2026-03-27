"""Configuration settings for the application"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings"""
    # Application
    app_name: str = "Intelligent Energy Grid Balancer"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", 8000))
    
    # Grid Configuration
    grid_nominal_frequency: float = 50.0
    frequency_tolerance: float = 0.5  # ±0.5 Hz
    frequency_critical_threshold: float = 1.5  # ±1.5 Hz triggers critical alert
    
    # Battery Configuration
    battery_min_soc_threshold: float = 20.0  # 20% minimum state of charge
    battery_max_soc_threshold: float = 95.0  # 95% maximum state of charge
    
    # Load Shedding
    load_shed_threshold: float = 10.0  # Shed load if imbalance > 10%
    load_shed_priority_levels: list = [1, 2, 3, 4]  # Load shedding priority levels
    
    # Demand Response
    demand_response_threshold: float = 5.0  # 5% imbalance
    
    # Prediction Configuration
    forecast_horizon_hours: int = 24
    historical_data_points: int = 168  # 7 days of hourly data
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Database/Storage
    data_dir: str = "data"
    
    # Monitoring
    monitoring_interval_seconds: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    """Get cached settings instance"""
    return Settings()
