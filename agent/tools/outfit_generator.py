import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

from agent.models.schemas import OutfitObject, StyleProfile, WeatherData, TrendItem


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_openai_client: OpenAI | None = None


def _get_openai() -> OpenAI | None:
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    _openai_client = OpenAI(api_key=key)
    return _openai_client


def _build_outfit_prompt(
    mood: str,
    weather: Optional[WeatherData],
    trends: List[TrendItem],
    profile: Optional[StyleProfile],
    occasion: Optional[str],
) -> str:
    trend_str = ", ".join([t.trend_name for t in trends]) or "general contemporary fashion"
    avoided = ", ".join(profile.avoided_styles) if profile else ""
    vibe_tags = ", ".join(profile.vibe_tags) if profile else ""
    budget = ""
    if profile and profile.budget_range:
        budget = f"Budget range approx {profile.budget_range.min}-{profile.budget_range.max}."

    weather_str = ""
    if weather:
        weather_str = (
            f"Weather in {weather.city}: {weather.temp_c}C, feels like {weather.feels_like_c}C, "
            f"condition {weather.condition}, season_tag={weather.season_tag}."
        )

    return f"""
You are TrendÉvo Agent, an elite AI stylist.
User mood: {mood}
Occasion: {occasion or "unspecified"}
Weather: {weather_str}
Current trends: {trend_str}
User vibe tags: {vibe_tags}
Avoided styles: {avoided}
{budget}

Generate exactly 3 outfit options as a JSON array of objects.
Each object MUST match this schema strictly:
{{
  "outfit_id": "string",
  "name": "string",
  "vibe_tag": "string",
  "items": {{
    "top": {{"name": "string", "category": "string", "color": "string", "price_range": "string"}},
    "bottom": {{"name": "string", "category": "string", "color": "string", "price_range": "string"}},
    "layer": {{"name": "string", "category": "string", "color": "string", "price_range": "string"}},
    "shoes": {{"name": "string", "style": "string", "color": "string"}},
    "accessory": {{"name": "string", "type": "string"}}
  }},
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "trendevo_categories": ["denims", "jackets", "knitwear", "upperwear", "dresses", "thrift"],
  "reasoning": "Why this works for the user specifically.",
  "confidence": 0-100
}}

Rules:
- Respect weather (no heavy knitwear for hot_humid).
- Never use avoided styles.
- Reference TrendÉvo categories only from the allowed list.
Return ONLY the JSON array, no extra text.
"""


def generate_outfits_with_gpt(
    mood: str,
    weather: Optional[WeatherData],
    trends: List[TrendItem],
    profile: Optional[StyleProfile],
    occasion: Optional[str],
) -> List[OutfitObject]:
    client = _get_openai()
    if client is None:
        return []

    prompt = _build_outfit_prompt(mood, weather, trends, profile, occasion)

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a JSON-only fashion outfit generator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )
    content = resp.choices[0].message.content or "[]"

    # Best-effort JSON parse
    import json

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Try to recover JSON between first [ and last ]
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1 and end > start:
            data = json.loads(content[start : end + 1])
        else:
            data = []

    outfits: List[OutfitObject] = []
    if isinstance(data, list):
        for raw in data:
            try:
                outfits.append(OutfitObject.model_validate(raw))
            except Exception:
                continue

    return outfits

