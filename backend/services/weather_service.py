import requests
import asyncio
from datetime import datetime, timedelta
from utils import get_logger

logger = get_logger(__name__)

class WeatherService:
    """Service to fetch real-world weather data for energy simulation"""
    
    # Bhubaneswar, India coordinates
    LATITUDE = 20.27
    LONGITUDE = 85.83
    API_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self):
        self.last_fetch = None
        self.cached_data = {
            "solar_radiation": 800.0, # W/m2 default
            "wind_speed": 15.0,        # km/h default
            "temperature": 28.0,       # C default
            "cloud_cover": 10.0,       # % default
            "location": "Bhubaneswar, IN"
        }
        self.cache_duration = timedelta(minutes=15)

    async def get_current_weather(self):
        """Fetch current weather from Open-Meteo or return cached data"""
        if self.last_fetch and (datetime.now() - self.last_fetch < self.cache_duration):
            return self.cached_data

        try:
            params = {
                "latitude": self.LATITUDE,
                "longitude": self.LONGITUDE,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m,shortwave_radiation",
                "timezone": "auto"
            }
            
            # Since requests is blocking, run it in a thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.get(self.API_URL, params=params, timeout=10))
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                
                self.cached_data = {
                    "solar_radiation": current.get("shortwave_radiation", 0.0),
                    "wind_speed": current.get("wind_speed_10m", 0.0),
                    "temperature": current.get("temperature_2m", 0.0),
                    "cloud_cover": current.get("cloud_cover", 0.0),
                    "is_day": current.get("is_day", 1),
                    "location": "Bhubaneswar, IN",
                    "timestamp": datetime.now().isoformat()
                }
                self.last_fetch = datetime.now()
                logger.info(f"Successfully updated weather data for {self.cached_data['location']}")
                return self.cached_data
            else:
                logger.warning(f"Failed to fetch weather data: HTTP {response.status_code}")
                return self.cached_data
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return self.cached_data

# Singleton instance
weather_service = WeatherService()
