"""Carbon intensity integration with graceful fallback."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from urllib import request
from urllib.error import HTTPError, URLError
import json

from config import get_settings
from utils import get_logger

logger = get_logger(__name__)


class CarbonService:
    """Fetches carbon intensity and caches recent values."""

    def __init__(self):
        self.settings = get_settings()
        self.cache_ttl = timedelta(minutes=5)
        self._cached_value: Optional[float] = None
        self._cached_at: Optional[datetime] = None

    def _cache_valid(self) -> bool:
        return (
            self._cached_value is not None
            and self._cached_at is not None
            and (datetime.now(timezone.utc) - self._cached_at) < self.cache_ttl
        )

    def _fetch_from_electricity_maps(self) -> Optional[float]:
        token = self.settings.electricity_maps_token
        zone = self.settings.electricity_maps_zone
        if not token or not zone:
            return None

        url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone}"
        req = request.Request(
            url,
            headers={
                "auth-token": token,
                "User-Agent": "IntelligentEnergyGridBalancer/1.0",
            },
        )
        with request.urlopen(req, timeout=10) as resp:
            payload: Dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        value = payload.get("carbonIntensity")
        return float(value) if value is not None else None

    def get_carbon_intensity(self, solar_mw: float = 150, wind_mw: float = 200, demand_mw: float = 350) -> float:
        """
        Calculate dynamic carbon intensity based on the current energy mix.
        If generation exceeds demand, intensity is purely from renewables (~12g).
        If demand exceeds generation, the deficit is assumed to be met by the thermal grid (~450g).
        """
        try:
            total_gen = solar_mw + wind_mw
            
            # Emission factors (approximate gCO2/kWh)
            I_SOLAR = 12.0
            I_WIND = 11.0
            I_GRID = float(self.settings.carbon_intensity_fallback) # Default 450.0 (Thermal/Mixed)
            
            if total_gen >= demand_mw:
                # Fully renewable (excess goes to battery)
                weighted_sum = (solar_mw * I_SOLAR) + (wind_mw * I_WIND)
                intensity = weighted_sum / total_gen if total_gen > 0 else I_GRID
            else:
                # Renewable + Grid Deficit
                renewable_gen = total_gen
                grid_deficit = demand_mw - renewable_gen
                
                weighted_sum = (solar_mw * I_SOLAR) + (wind_mw * I_WIND) + (grid_deficit * I_GRID)
                intensity = weighted_sum / demand_mw if demand_mw > 0 else I_GRID
            
            return round(float(intensity), 1)
            
        except Exception as e:
            logger.warning(f"Dynamic carbon intensity calculation failed: {e}")
            return float(self.settings.carbon_intensity_fallback)


carbon_service = CarbonService()
