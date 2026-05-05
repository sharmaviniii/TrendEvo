import os
from typing import Dict, Any

import httpx
from dotenv import load_dotenv

from agent.models.schemas import WeatherData


load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "c1e2893d5dbcc2e1d92ac7b5803ff0b1")


def _season_tag_from_weather(temp_c: float, condition: str) -> str:
    condition_lower = condition.lower()
    if "rain" in condition_lower or "storm" in condition_lower:
        return "rainy"
    if temp_c >= 30:
        return "hot_humid"
    if temp_c <= 12:
        return "cold"
    return "pleasant"


async def fetch_weather(city: str) -> WeatherData:
    """
    Call OpenWeatherMap current weather API and normalize response.
    """
    if not OPENWEATHER_API_KEY:
        # Fallback dev stub if key missing
        return WeatherData(
            city=city,
            temp_c=26.0,
            feels_like_c=28.0,
            condition="Clear",
            humidity=60,
            wind_kph=10.0,
            season_tag="pleasant",
        )

    params: Dict[str, Any] = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
        resp.raise_for_status()
        data = resp.json()

    main = data.get("main", {})
    wind = data.get("wind", {})
    weather = (data.get("weather") or [{}])[0]
    temp_c = float(main.get("temp", 0.0))
    feels_like_c = float(main.get("feels_like", temp_c))
    condition = weather.get("description", "Clear")
    humidity = int(main.get("humidity", 0))
    wind_kph = float(wind.get("speed", 0.0)) * 3.6  # m/s to km/h

    season_tag = _season_tag_from_weather(temp_c, condition)

    return WeatherData(
        city=city,
        temp_c=temp_c,
        feels_like_c=feels_like_c,
        condition=condition,
        humidity=humidity,
        wind_kph=wind_kph,
        season_tag=season_tag,
    )


async def get_weather_for_city(city: str) -> WeatherData:
    return await fetch_weather(city)

