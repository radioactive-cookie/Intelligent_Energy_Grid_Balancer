"""Real weather data integration with caching and simulation fallback."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any
from urllib import request, parse
import json

from config import get_settings
from utils import get_logger

logger = get_logger(__name__)


class RealDataFetcher:
    """Fetches weather data and converts it into solar/wind generation estimates."""

    def __init__(self):
        self.settings = get_settings()
        self.cache_ttl = timedelta(minutes=5)
        self._cache: Dict[str, Any] | None = None
        self._cached_at: datetime | None = None

    def _cache_valid(self) -> bool:
        return (
            self._cache is not None
            and self._cached_at is not None
            and (datetime.utcnow() - self._cached_at) < self.cache_ttl
        )

    def _simulate_fallback(self, simulated_inputs: Dict[str, float]) -> Dict[str, Any]:
        # Fallback keeps existing simulation behavior so the system remains operational.
        return {
            "solar_mw": float(simulated_inputs.get("solar_mw", 0.0)),
            "wind_mw": float(simulated_inputs.get("wind_mw", 0.0)),
            "dataSource": "simulated",
            "rawWeather": {},
        }

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _convert_weather_to_generation(self, weather: Dict[str, Any]) -> Dict[str, float]:
        # direct_radiation is W/m², so normalize by 1000 W/m² peak and reduce by cloud cover.
        direct_radiation = float(weather.get("direct_radiation") or 0.0)
        cloud_cover = float(weather.get("cloud_cover") or 0.0)
        wind_speed_10m = float(weather.get("wind_speed_10m") or 0.0)

        solar_capacity_kw = float(self.settings.solar_peak_capacity_kw)
        wind_capacity_kw = float(self.settings.wind_peak_capacity_kw)

        solar_factor = self._clamp(direct_radiation / 1000.0, 0.0, 1.0) * (1.0 - self._clamp(cloud_cover, 0.0, 100.0) / 100.0)
        solar_kw = solar_capacity_kw * solar_factor

        # Simple turbine curve approximation between cut-in and rated speed.
        cut_in = float(self.settings.wind_cut_in_speed_ms)
        rated = float(self.settings.wind_rated_speed_ms)
        wind_factor = self._clamp((wind_speed_10m - cut_in) / (rated - cut_in), 0.0, 1.0)
        wind_kw = wind_capacity_kw * wind_factor

        # Convert kW -> MW because the current backend metrics are MW-based.
        return {
            "solar_mw": round(solar_kw / 1000.0, 2),
            "wind_mw": round(wind_kw / 1000.0, 2),
        }

    def _fetch_open_meteo(self) -> Dict[str, Any]:
        query = parse.urlencode(
            {
                "latitude": self.settings.weather_latitude,
                "longitude": self.settings.weather_longitude,
                "current": "direct_radiation,wind_speed_10m,cloud_cover,temperature_2m",
            }
        )
        url = f"https://api.open-meteo.com/v1/forecast?{query}"
        req = request.Request(url, headers={"User-Agent": "IntelligentEnergyGridBalancer/1.0"})
        with request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload.get("current", {}) or {}

    def get_generation(self, simulated_inputs: Dict[str, float]) -> Dict[str, Any]:
        # Use fresh cache first to avoid unnecessary external calls and keep updates stable.
        if self._cache_valid():
            return self._cache

        try:
            raw_weather = self._fetch_open_meteo()
            generation = self._convert_weather_to_generation(raw_weather)
            result = {
                **generation,
                "dataSource": "real",
                "rawWeather": {
                    "direct_radiation": raw_weather.get("direct_radiation"),
                    "wind_speed_10m": raw_weather.get("wind_speed_10m"),
                    "cloud_cover": raw_weather.get("cloud_cover"),
                    "temperature_2m": raw_weather.get("temperature_2m"),
                },
            }
            self._cache = result
            self._cached_at = datetime.utcnow()
            return result
        except Exception as exc:
            logger.warning(f"Open-Meteo fetch failed; using simulation fallback: {exc}")
            return self._simulate_fallback(simulated_inputs)


real_data_fetcher = RealDataFetcher()
