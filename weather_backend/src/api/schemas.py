"""
Pydantic schemas for FastAPI - defines current weather and forecast models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class WeatherMain(BaseModel):
    temp: float = Field(..., description="Current temperature")
    feels_like: float = Field(..., description="What temperature feels like")
    temp_min: Optional[float] = Field(
        None, description="Minimum temperature at the moment"
    )
    temp_max: Optional[float] = Field(
        None, description="Maximum temperature at the moment"
    )
    pressure: Optional[float] = Field(
        None, description="Atmospheric pressure (hPa)"
    )
    humidity: Optional[float] = Field(None, description="Humidity (%)")


# PUBLIC_INTERFACE
class WeatherCondition(BaseModel):
    main: str = Field(
        ..., description="Group of weather parameters (Rain, Snow, Clear, etc.)"
    )
    description: str = Field(..., description="Description of the weather")
    icon: str = Field(..., description="Icon code for weather condition")


# PUBLIC_INTERFACE
class WeatherWind(BaseModel):
    speed: float = Field(..., description="Wind speed (m/s or miles/hour)")
    deg: Optional[float] = Field(None, description="Wind direction (degrees)")
    gust: Optional[float] = Field(None, description="Wind gust")


# PUBLIC_INTERFACE
class WeatherResponse(BaseModel):
    city: str = Field(..., description="City name")
    country: Optional[str] = Field(None, description="Country code")
    coord: dict = Field(
        ..., description="Coordinates dict {'lat': ...,'lon': ...}"
    )
    weather: List[WeatherCondition] = Field(
        ..., description="Weather conditions"
    )
    main: WeatherMain = Field(..., description="Main weather data")
    wind: WeatherWind = Field(..., description="Wind data")
    dt: int = Field(
        ..., description="UTC time of data calculation (unix UTC)"
    )
    timezone: int = Field(..., description="Seconds shift from UTC")
    name: str = Field(..., description="City name (again)")

    # Method: From OWM dict
    @classmethod
    def from_openweathermap(cls, data: dict):
        return cls(
            city=data.get("name"),
            country=data.get("sys", {}).get("country"),
            coord=data.get("coord", {}),
            weather=[
                WeatherCondition(
                    main=w.get("main", ""),
                    description=w.get("description", ""),
                    icon=w.get("icon", ""),
                )
                for w in data.get("weather", [])
            ],
            main=WeatherMain(**data["main"]),
            wind=WeatherWind(**data.get("wind", {})),
            dt=data.get("dt"),
            timezone=data.get("timezone"),
            name=data.get("name"),
        )


# PUBLIC_INTERFACE
class ForecastHourly(BaseModel):
    dt: int = Field(..., description="Timestamp")
    temp: float = Field(..., description="Temperature")
    weather: List[WeatherCondition] = Field(
        ..., description="Weather conditions"
    )
    wind_speed: float = Field(..., description="Wind speed")
    wind_deg: Optional[float] = Field(None, description="Wind angle")
    pop: Optional[float] = Field(None, description="Probability of precipitation")


# PUBLIC_INTERFACE
class ForecastDailyTemp(BaseModel):
    day: float
    min: float
    max: float


# PUBLIC_INTERFACE
class ForecastDaily(BaseModel):
    dt: int = Field(..., description="Timestamp")
    temp: ForecastDailyTemp
    weather: List[WeatherCondition]
    wind_speed: float = Field(..., description="Wind speed")
    wind_deg: Optional[float] = Field(None, description="Wind angle")
    pop: Optional[float] = Field(None, description="Probability of precipitation")


# PUBLIC_INTERFACE
class ForecastResponse(BaseModel):
    city: Optional[str] = Field(None, description="Name of city")
    country: Optional[str] = Field(None, description="Country code")
    coord: dict = Field(
        ..., description="Coord {'lat': ...,'lon': ...}"
    )
    current: WeatherResponse = Field(
        ..., description="Current weather at forecast location"
    )
    hourly: List[ForecastHourly] = Field(
        ..., description="List of hourly forecast data"
    )
    daily: List[ForecastDaily] = Field(
        ..., description="List of daily forecast data"
    )
    timezone: int = Field(..., description="Timezone shift in seconds")

    # Method to parse OpenWeatherMap OneCall API response
    @classmethod
    def from_openweathermap(cls, data: dict):
        def wc_list(list_in):
            return [
                WeatherCondition(
                    main=w.get("main", ""),
                    description=w.get("description", ""),
                    icon=w.get("icon", ""),
                )
                for w in list_in
            ]

        hourly_data = []
        for h in data.get("hourly", [])[:24]:
            hourly_data.append(
                ForecastHourly(
                    dt=h.get("dt"),
                    temp=h.get("temp"),
                    weather=wc_list(h.get("weather", [])),
                    wind_speed=h.get("wind_speed"),
                    wind_deg=h.get("wind_deg"),
                    pop=h.get("pop"),
                )
            )
        daily_data = []
        for d in data.get("daily", [])[:7]:
            daily_data.append(
                ForecastDaily(
                    dt=d.get("dt"),
                    temp=ForecastDailyTemp(
                        day=d["temp"]["day"],
                        min=d["temp"]["min"],
                        max=d["temp"]["max"],
                    ),
                    weather=wc_list(d.get("weather", [])),
                    wind_speed=d.get("wind_speed"),
                    wind_deg=d.get("wind_deg"),
                    pop=d.get("pop"),
                )
            )
        current = WeatherResponse(
            city=None,
            country=None,
            coord={"lat": data.get("lat"), "lon": data.get("lon")},
            weather=wc_list(data["current"].get("weather", [])),
            main=WeatherMain(
                temp=data["current"]["temp"],
                feels_like=data["current"]["feels_like"],
                temp_min=None,
                temp_max=None,
                pressure=data["current"].get("pressure"),
                humidity=data["current"].get("humidity"),
            ),
            wind=WeatherWind(
                speed=data["current"].get("wind_speed"),
                deg=data["current"].get("wind_deg"),
                gust=data["current"].get("wind_gust"),
            ),
            dt=data["current"]["dt"],
            timezone=data.get("timezone_offset", 0),
            name="",
        )
        return cls(
            city=None,
            country=None,
            coord={"lat": data.get("lat"), "lon": data.get("lon")},
            current=current,
            hourly=hourly_data,
            daily=daily_data,
            timezone=data.get("timezone_offset", 0),
        )


# PUBLIC_INTERFACE
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error detail message")
