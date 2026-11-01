from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("farmwise.weather_service")

_DEFAULT_LATITUDE = 13.0674
_DEFAULT_LONGITUDE = 77.577
_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherService:
    @staticmethod
    def get_weather_for_location(lat: float | None, lon: float | None) -> dict[str, Any]:
        latitude = float(lat) if lat is not None else _DEFAULT_LATITUDE
        longitude = float(lon) if lon is not None else _DEFAULT_LONGITUDE

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,precipitation",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "Asia/Kolkata",
            "forecast_days": 5,
        }

        try:
            with httpx.Client(timeout=float(getattr(settings, "weather_api_timeout_seconds", 10))) as client:
                response = client.get(_OPEN_METEO_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # pragma: no cover - network dependency
            logger.warning("Weather provider failed for lat=%s lon=%s: %s", latitude, longitude, exc)
            return {
                "success": False,
                "provider": "open-meteo",
                "message": "Weather service unavailable. Please try again later.",
                "current": {},
                "forecast": [],
                "warnings": [],
            }

        current = payload.get("current", {})
        daily = payload.get("daily", {})
        forecast = []
        for idx, day in enumerate(daily.get("time", [])):
            forecast.append(
                {
                    "date": day,
                    "temp_min_c": daily.get("temperature_2m_min", [None])[idx],
                    "temp_max_c": daily.get("temperature_2m_max", [None])[idx],
                    "precipitation_mm": daily.get("precipitation_sum", [None])[idx],
                    "weather_code": daily.get("weather_code", [None])[idx],
                }
            )

        warnings = []
        if current.get("precipitation", 0) and current.get("precipitation", 0) > 20:
            warnings.append("Heavy rain risk in the current period")

        return {
            "success": True,
            "provider": "open-meteo",
            "latitude": latitude,
            "longitude": longitude,
            "current": {
                "temperature_c": current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "weather_code": current.get("weather_code"),
                "precipitation_mm": current.get("precipitation"),
            },
            "forecast": forecast,
            "warnings": warnings,
        }
