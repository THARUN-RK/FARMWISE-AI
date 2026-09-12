"""
Weather routes using Open-Meteo (https://open-meteo.com).

Open-Meteo is completely free with no API key required.
It provides hourly and daily weather data globally including India.
Responses are cached in-memory for 30 minutes to avoid unnecessary calls.
"""
import logging
import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import current_user
from app.models.entities import Farmer

log = logging.getLogger("farmwise.weather")
router = APIRouter(prefix="/weather", tags=["weather"])

# Simple in-process cache: key -> (timestamp, data)
_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 1800  # 30 minutes

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather code descriptions (simplified)
_WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < _CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)


def _fetch_weather(lat: float, lon: float) -> dict:
    """Call Open-Meteo API and return structured weather data."""
    cache_key = f"{round(lat, 2)},{round(lon, 2)}"
    cached = _cache_get(cache_key)
    if cached:
        log.debug("weather cache hit lat=%s lon=%s", lat, lon)
        return cached

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code",
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
    }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            raw = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(503, "Weather service timed out — please try again")
    except httpx.HTTPError as exc:
        log.warning("open-meteo error: %s", exc)
        raise HTTPException(503, "Weather service temporarily unavailable")

    current = raw.get("current", {})
    daily = raw.get("daily", {})

    result = {
        "provider": "open-meteo",
        "latitude": lat,
        "longitude": lon,
        "current": {
            "temperature_c": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
            "description": _WMO_CODES.get(current.get("weather_code", 0), "Unknown"),
        },
        "forecast": [
            {
                "date": daily["time"][i],
                "temp_max_c": daily["temperature_2m_max"][i],
                "temp_min_c": daily["temperature_2m_min"][i],
                "precipitation_mm": daily["precipitation_sum"][i],
                "rain_probability_percent": daily["precipitation_probability_max"][i],
                "weather_code": daily["weather_code"][i],
                "description": _WMO_CODES.get(daily["weather_code"][i], "Unknown"),
            }
            for i in range(len(daily.get("time", [])))
        ],
    }

    _cache_set(cache_key, result)
    log.info("weather fetched lat=%s lon=%s", lat, lon)
    return result


# Default coordinates for India (Karnataka) when no profile location is set
_DEFAULT_LAT = 15.3173
_DEFAULT_LON = 75.7139


@router.get("/current")
def current_weather(user: Farmer = Depends(current_user)):
    """
    Return current weather for the farmer's location.

    Uses the latitude/longitude from the farmer's profile.
    Falls back to Karnataka, India if no location is stored.
    """
    lat = user.latitude or _DEFAULT_LAT
    lon = user.longitude or _DEFAULT_LON
    data = _fetch_weather(lat, lon)
    return {"success": True, "data": {**data["current"], "provider": data["provider"]}}


@router.get("/forecast")
def weather_forecast(user: Farmer = Depends(current_user)):
    """
    Return 7-day weather forecast for the farmer's location.

    Uses Open-Meteo daily forecast. Useful for sowing and irrigation planning.
    """
    lat = user.latitude or _DEFAULT_LAT
    lon = user.longitude or _DEFAULT_LON
    data = _fetch_weather(lat, lon)
    return {"success": True, "data": {"forecast": data["forecast"], "provider": data["provider"]}}
