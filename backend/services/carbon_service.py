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

    def get_carbon_intensity(self) -> float:
        if self._cache_valid():
            return float(self._cached_value)

        fallback_value = float(self.settings.carbon_intensity_fallback)
        try:
            fetched = self._fetch_from_electricity_maps()
            value = fallback_value if fetched is None else fetched
            self._cached_value = value
            self._cached_at = datetime.now(timezone.utc)
            return float(value)
        except HTTPError as exc:
            if exc.code in (401, 403):
                logger.warning("Electricity Maps authentication failed; using fallback carbon intensity")
            else:
                logger.warning(f"Electricity Maps HTTP error {exc.code}; using fallback carbon intensity")
            return fallback_value
        except URLError as exc:
            logger.warning(f"Electricity Maps network error; using fallback carbon intensity: {exc.reason}")
            return fallback_value
        except Exception as exc:
            logger.warning(f"Carbon intensity fetch failed; using fallback: {exc}")
            return fallback_value


carbon_service = CarbonService()
