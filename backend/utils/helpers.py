"""Utility functions and helpers"""
import logging
from datetime import datetime
import json

# Configure logging
def setup_logging(log_file: str = "logs/app.log", log_level: str = "INFO"):
    """Setup application logging"""
    import os
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_logger(name: str):
    """Get logger instance"""
    return logging.getLogger(name)

def calculate_soc(current_level: float, capacity: float) -> float:
    """Calculate State of Charge percentage"""
    if capacity == 0:
        return 0
    return (current_level / capacity) * 100

def calculate_imbalance(generation: float, demand: float) -> float:
    """Calculate generation-demand imbalance"""
    return generation - demand

def calculate_load_percentage(demand: float, capacity: float) -> float:
    """Calculate load percentage"""
    if capacity == 0:
        return 0
    return (demand / capacity) * 100

def format_timestamp(dt: datetime = None) -> str:
    """Format datetime to ISO string"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()

def is_frequency_stable(frequency: float, nominal: float = 50.0, tolerance: float = 0.5) -> bool:
    """Check if frequency is within acceptable range"""
    return abs(frequency - nominal) <= tolerance

def is_frequency_critical(frequency: float, nominal: float = 50.0, critical_threshold: float = 1.5) -> bool:
    """Check if frequency is at critical level"""
    return abs(frequency - nominal) > critical_threshold

def save_to_json(data: dict, filepath: str):
    """Save data to JSON file"""
    import os
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_from_json(filepath: str) -> dict:
    """Load data from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)
