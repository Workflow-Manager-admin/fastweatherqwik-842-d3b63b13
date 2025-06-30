"""
FastAPI backend for Weather Dashboard: Provides REST endpoints to fetch current weather
and forecast data from OpenWeatherMap with proper error handling and structured responses.

Includes OpenAPI/Swagger documentation with app-level metadata.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional

from .openweathermap import (
    get_current_weather as ow_get_current_weather,
    get_weather_forecast as ow_get_weather_forecast,
)
from .schemas import WeatherResponse, ForecastResponse, ErrorResponse

# Metadata for API docs
tags_metadata = [
    {
        "name": "weather",
        "description": (
            "Endpoints for retrieving current weather and forecasts for locations."
        ),
    }
]

app = FastAPI(
    title="Weather Dashboard Backend API",
    description="REST API for fetching current and forecast weather using OpenWeatherMap.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
def health_check():
    """
    Health check endpoint to verify service operation.
    """
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/api/current-weather",
    response_model=WeatherResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Get Current Weather",
    description=(
        "Returns current weather information for a given city name or geo coordinates."
    ),
    tags=["weather"],
)
async def get_current_weather(
    city: Optional[str] = Query(
        default=None, description="City name (e.g., London)"
    ),
    lat: Optional[float] = Query(
        default=None, description="Latitude for coordinate search"
    ),
    lon: Optional[float] = Query(
        default=None, description="Longitude for coordinate search"
    ),
    units: Optional[str] = Query(
        default="metric",
        description="Units: 'metric', 'imperial', or 'standard'"
    ),
):
    """
    Get current weather for a given city or geographical coordinates.

    Parameters:
    - city: City name as recognized by OpenWeatherMap.
    - lat, lon: Latitude and longitude for geographic search (if city not given).
    - units: Unit system for temperature and wind speed.

    Returns:
    - JSON object with structured weather data (temperature, conditions, etc.)
    """
    if not city and (lat is None or lon is None):
        raise HTTPException(
            status_code=422,
            detail=(
                "Either 'city' or both 'lat' and 'lon' must be provided."
            )
        )

    try:
        weather_data = await ow_get_current_weather(
            city=city, lat=lat, lon=lon, units=units
        )
        if not weather_data:
            raise HTTPException(
                status_code=404,
                detail="Weather data not found for specified location."
            )
        return weather_data
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Error communicating with weather service: {}".format(str(exc))
        )


# PUBLIC_INTERFACE
@app.get(
    "/api/forecast",
    response_model=ForecastResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Get Weather Forecast",
    description=(
        "Returns multi-day forecast (hourly and daily) for a given city name or geo coordinates."
    ),
    tags=["weather"],
)
async def get_forecast(
    city: Optional[str] = Query(
        default=None, description="City name (e.g., Berlin)"
    ),
    lat: Optional[float] = Query(
        default=None, description="Latitude for coordinate search"
    ),
    lon: Optional[float] = Query(
        default=None, description="Longitude for coordinate search"
    ),
    units: Optional[str] = Query(
        default="metric",
        description="Units: 'metric', 'imperial', or 'standard'"
    ),
):
    """
    Get weather forecast (hourly and daily) for a given city or coordinates.

    Parameters:
    - city: City name recognized by OpenWeatherMap.
    - lat, lon: Latitude and longitude (if city not given).
    - units: Unit system.

    Returns:
    - JSON object with structured forecast data.
    """
    if not city and (lat is None or lon is None):
        raise HTTPException(
            status_code=422,
            detail=(
                "Either 'city' or both 'lat' and 'lon' must be provided."
            )
        )

    try:
        forecast_data = await ow_get_weather_forecast(
            city=city, lat=lat, lon=lon, units=units
        )
        if not forecast_data:
            raise HTTPException(
                status_code=404,
                detail="Forecast data not found for specified location."
            )
        return forecast_data
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Error communicating with weather service: {}".format(str(exc))
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Return errors in structured JSON format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
