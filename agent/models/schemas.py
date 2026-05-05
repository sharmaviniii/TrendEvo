from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    city: str
    temp_c: float
    feels_like_c: float
    condition: str
    humidity: int
    wind_kph: float
    season_tag: str


class TrendItem(BaseModel):
    trend_name: str
    aesthetic_tags: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)


class TrendPrediction(BaseModel):
    trend_name: str
    confidence: int
    reasoning: str
    trendevo_categories: List[str] = Field(default_factory=list)
    expected_peak: str


class TrendOverviewResponse(BaseModel):
    success: bool = True
    scraped_at: Optional[datetime] = None
    trends: List[TrendItem] = Field(default_factory=list)
    predicted_next_season: List[TrendPrediction] = Field(default_factory=list)


class ItemBase(BaseModel):
    name: str
    category: str
    color: Optional[str] = None
    price_range: Optional[str] = None


class OutfitItems(BaseModel):
    top: Optional[ItemBase] = None
    bottom: Optional[ItemBase] = None
    layer: Optional[ItemBase] = None
    shoes: Optional[Dict[str, Any]] = None
    accessory: Optional[Dict[str, Any]] = None


class OutfitObject(BaseModel):
    outfit_id: str
    name: str
    vibe_tag: str
    items: OutfitItems
    color_palette: List[str] = Field(default_factory=list)
    trendevo_categories: List[str] = Field(default_factory=list)
    reasoning: str
    confidence: int


class StyleDNA(BaseModel):
    streetwear: int = 0
    formal: int = 0
    bohemian: int = 0
    minimalist: int = 0
    maximalist: int = 0
    sporty: int = 0


class BudgetRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class OutfitFeedback(BaseModel):
    outfit_id: str
    rating: str  # "like" | "dislike"
    notes: Optional[str] = None


class StyleProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    favorite_colors: List[str] = Field(default_factory=list)
    avoided_styles: List[str] = Field(default_factory=list)
    budget_range: BudgetRange = BudgetRange()
    preferred_fit: Optional[str] = None
    vibe_tags: List[str] = Field(default_factory=list)
    body_type: Optional[str] = None
    occasion_preferences: List[str] = Field(default_factory=list)
    style_dna: StyleDNA = StyleDNA()
    outfit_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StyleProfileUpdate(BaseModel):
    name: Optional[str] = None
    favorite_colors: Optional[List[str]] = None
    avoided_styles: Optional[List[str]] = None
    budget_range: Optional[BudgetRange] = None
    preferred_fit: Optional[str] = None
    vibe_tags: Optional[List[str]] = None
    body_type: Optional[str] = None
    occasion_preferences: Optional[List[str]] = None
    style_dna: Optional[StyleDNA] = None


class AgentMessage(BaseModel):
    step: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None


class ChatRequest(BaseModel):
    user_id: str
    message: str
    city: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool = True
    reply: str
    reasoning_chain: List[AgentMessage]
    outfits: List[OutfitObject] = Field(default_factory=list)
    trends: List[TrendItem] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    session_id: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str


class HealthResponse(BaseModel):
    status: str
    tools_loaded: List[str]
    memory_stats: Dict[str, Any]
    db_connected: bool
