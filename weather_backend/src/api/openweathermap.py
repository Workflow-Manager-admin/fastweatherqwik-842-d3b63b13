"""
Handles communication with the OpenWeatherMap API for current weather and forecast.
Includes error handling and transformation to internal schemas.
"""

import os
import httpx
from typing import Optional, Tuple
from dotenv import load_dotenv

from .schemas import WeatherResponse, ForecastResponse

load_dotenv()

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHERMAP_ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"


def get_api_key():
    """
    PUBLIC_INTERFACE

    Retrieve the OpenWeatherMap API key from environment variables—never hardcoded.

    - On local development: Loads from `.env` if present (auto via `python-dotenv`).
      - Example: .env contains OPENWEATHERMAP_API_KEY=your_api_key
    - On production: Should be provided as an environment variable.
    - Raises:
        RuntimeError: If the API key is missing or unset.

    Returns:
        str: The OpenWeatherMap API key for all requests.
    """
    key = OPENWEATHERMAP_API_KEY or os.environ.get("OPENWEATHERMAP_API_KEY")
    if not key:
        raise RuntimeError(
            "OpenWeatherMap API key is not set in environment variable 'OPENWEATHERMAP_API_KEY'. "
            "Set this variable in your deployment environment or add an entry to a local .env file "
            "for development."
        )
    return key


async def _fetch_city_coordinates(
    city: str, api_key: str
) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Resolves a city name to latitude, longitude, and country using OpenWeatherMap's geocoding
    endpoint. Returns a tuple of (lat, lon, country), or (None, None, None) if not found.
    Raises httpx.HTTPStatusError if the geocode API call fails.
    """
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
    async with httpx.AsyncClient() as client:
        try:
            geo_resp = await client.get(
                geocode_url,
                params={"q": city, "limit": 1, "appid": api_key},
                timeout=10,
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data:
                return None, None, None
            coordinates = geo_data[0]
            lat = coordinates.get("lat")
            lon = coordinates.get("lon")
            country = coordinates.get("country")
            return lat, lon, country
        except httpx.HTTPStatusError as exc:
            # Handle invalid API key (401), or bad request (400), or not found (404)
            if exc.response.status_code == 401:
                raise RuntimeError("Invalid API key for OpenWeatherMap.")
            elif exc.response.status_code == 429:
                raise RuntimeError("API rate limit exceeded for OpenWeatherMap.")
            return None, None, None
        except Exception:
            # For network issues or others
            return None, None, None


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
    Raises RuntimeError for API key problems or upstream API limit errors.
    """
    api_key = get_api_key()
    resolved_country = None

    if city:
        lat, lon, resolved_country = await _fetch_city_coordinates(city, api_key)
        if lat is None or lon is None:
            raise ValueError(f"City '{city}' not found.")

    # Step 2: Get weather by coordinates.
    url = f"{OPENWEATHERMAP_BASE_URL}/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units,
    }
    async with httpx.AsyncClient() as client:
        try:
            api_resp = await client.get(url, params=params, timeout=10)
            api_resp.raise_for_status()
            data = api_resp.json()
            if data.get("cod") != 200:
                cod = data.get("cod", "")
                if cod == "401":
                    raise RuntimeError("Invalid OpenWeatherMap API key.")
                if cod == "404":
                    raise ValueError("Weather data not found for these coordinates.")
                raise ValueError(data.get("message", "Unknown error from API."))
            result = WeatherResponse.from_openweathermap(data)
            # Patch country field on WeatherResponse if city-resolved
            if city and resolved_country and hasattr(result, "country"):
                result.country = resolved_country
            return result
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                raise RuntimeError("Invalid OpenWeatherMap API key.")
            elif status == 429:
                raise RuntimeError("API rate limit exceeded for OpenWeatherMap.")
            elif status == 404:
                raise ValueError("Weather data not found for specified location.")
            else:
                raise RuntimeError(f"Network error: {exc.response.text}")
        except httpx.RequestError as exc:
            raise RuntimeError(
                "Failed to reach OpenWeatherMap service. Please try again later."
            ) from exc


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
    Raises RuntimeError for API key problems or upstream API limit errors.
    """
    api_key = get_api_key()
    resolved_country = None

    if city:
        lat, lon, resolved_country = await _fetch_city_coordinates(city, api_key)
        if lat is None or lon is None:
            raise ValueError(f"City '{city}' not found.")

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
        try:
            api_resp = await client.get(forecast_url, params=params, timeout=10)
            api_resp.raise_for_status()
            data = api_resp.json()
            if (
                "current" not in data
                or "hourly" not in data
                or "daily" not in data
            ):
                raise ValueError("Forecast data not found for specified location.")
            result = ForecastResponse.from_openweathermap(data)
            # Patch country field on ForecastResponse if city
            if city and resolved_country and hasattr(result, "country"):
                result.country = resolved_country
            return result
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                raise RuntimeError("Invalid OpenWeatherMap API key.")
            elif status == 429:
                raise RuntimeError("API rate limit exceeded for OpenWeatherMap.")
            elif status == 404:
                raise ValueError("Forecast data not found for specified location.")
            else:
                raise RuntimeError(f"Network error: {exc.response.text}")
        except httpx.RequestError as exc:
            raise RuntimeError(
                "Failed to reach OpenWeatherMap service. Please try again later."
            ) from exc
