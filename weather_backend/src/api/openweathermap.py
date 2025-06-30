"""
Handles communication with the OpenWeatherMap API for current weather and forecast.
Includes error handling and transformation to internal schemas.
"""

import os
import httpx
from typing import Optional

from .schemas import WeatherResponse, ForecastResponse

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHERMAP_ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"


def get_api_key():
    """
    Retrieve OpenWeatherMap API key from environment for security.
    """
    key = OPENWEATHERMAP_API_KEY or os.environ.get(
        "OPENWEATHERMAP_API_KEY"
    )
    if not key:
        raise RuntimeError(
            "OpenWeatherMap API key is not set in the environment variable "
            "'OPENWEATHERMAP_API_KEY'."
        )
    return key


# PUBLIC_INTERFACE
async def get_current_weather(
    city: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    units: str
) -> Optional[WeatherResponse]:
    """
    Fetch current weather from OpenWeatherMap, searching by city name or coordinates.

    Returns WeatherResponse or None if data not found.
    """
    api_key = get_api_key()

    if city:
        # Step 1: Get coordinates for city
        geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
        async with httpx.AsyncClient() as client:
            geo_resp = await client.get(
                geocode_url,
                params={"q": city, "limit": 1, "appid": api_key},
                timeout=10,
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data:
                return None
            coordinates = geo_data[0]
            lat = coordinates.get("lat")
            lon = coordinates.get("lon")

    # Step 2: Get weather by coordinates.
    url = f"{OPENWEATHERMAP_BASE_URL}/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units,
    }
    async with httpx.AsyncClient() as client:
        api_resp = await client.get(url, params=params, timeout=10)
        try:
            api_resp.raise_for_status()
        except httpx.HTTPStatusError:
            return None
        data = api_resp.json()
        if data.get("cod") != 200:
            return None
        return WeatherResponse.from_openweathermap(data)


# PUBLIC_INTERFACE
async def get_weather_forecast(
    city: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    units: str
) -> Optional[ForecastResponse]:
    """
    Fetch 5-day/3-hour forecast from OpenWeatherMap using the OneCall API or /forecast endpoint.

    Returns ForecastResponse or None if data not found.
    """
    api_key = get_api_key()

    if city:
        # Step 1: Get coordinates
        geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
        async with httpx.AsyncClient() as client:
            geo_resp = await client.get(
                geocode_url,
                params={"q": city, "limit": 1, "appid": api_key},
                timeout=10,
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data:
                return None
            coordinates = geo_data[0]
            lat = coordinates.get("lat")
            lon = coordinates.get("lon")

    # Step 2: Get forecast (using both hourly/daily in OneCall if possible)
    forecast_url = f"{OPENWEATHERMAP_ONECALL_URL}"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "exclude": "minutely,alerts",
        "units": units,
    }
    async with httpx.AsyncClient() as client:
        api_resp = await client.get(forecast_url, params=params, timeout=10)
        try:
            api_resp.raise_for_status()
        except httpx.HTTPStatusError:
            return None
        data = api_resp.json()
        if (
            "current" not in data
            or "hourly" not in data
            or "daily" not in data
        ):
            return None
        return ForecastResponse.from_openweathermap(data)
