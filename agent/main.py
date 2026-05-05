import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.agents import OrchestratorAgent
from agent.db.mongo import get_db
from agent.models.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    TrendOverviewResponse,
    StyleProfile,
    StyleProfileUpdate,
    OutfitFeedback,
    WeatherData,
)
from agent.tools.weather import get_weather_for_city
from agent.memory.faiss_store import memory_stats


# Load agent/.env regardless of current working directory.
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="TrendÉvo Agent API", version="0.1.0")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    os.getenv("FLASK_ORIGIN", "http://127.0.0.1:5000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()


@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(body: ChatRequest):
    try:
        # Run sync chat logic in a worker thread to avoid blocking event loop.
        result = await run_in_threadpool(orchestrator.chat, body)
        return result
    except Exception as e:
        # Match Flask-style error envelope
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(success=False, message=str(e)).model_dump(),
        )


@app.get("/agent/trends", response_model=TrendOverviewResponse)
async def get_trends():
    # Placeholder until trend tools are wired
    return TrendOverviewResponse(success=True, scraped_at=None, trends=[], predicted_next_season=[])


@app.post("/agent/trends/scrape")
async def scrape_trends():
    # Placeholder background job stub
    return JSONResponse({"success": True, "job_id": "stub", "status": "queued"})


@app.get("/agent/profile/{user_id}", response_model=StyleProfile | ErrorResponse)
async def get_profile(user_id: str):
    db = get_db()
    doc = db.style_profiles.find_one({"user_id": user_id})
    if not doc:
        profile = StyleProfile(user_id=user_id)
        return profile
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    return StyleProfile.model_validate(doc)


@app.post("/agent/profile/{user_id}", response_model=StyleProfile | ErrorResponse)
async def update_profile(user_id: str, update: StyleProfileUpdate):
    db = get_db()
    payload: Dict[str, Any] = {k: v for k, v in update.model_dump(exclude_none=True).items()}
    payload["updated_at"] = datetime.now(timezone.utc)
    db.style_profiles.update_one(
        {"user_id": user_id},
        {
            "$set": payload,
            "$setOnInsert": {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )
    doc = db.style_profiles.find_one({"user_id": user_id})
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    return StyleProfile.model_validate(doc)


@app.post("/agent/profile/{user_id}/feedback")
async def profile_feedback(user_id: str, body: OutfitFeedback):
    # Simple stub: append feedback and lightly tweak style_dna later
    db = get_db()
    db.style_profiles.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "outfit_history": {
                    "outfit_id": body.outfit_id,
                    "rating": body.rating,
                    "notes": body.notes,
                }
            }
        },
        upsert=True,
    )
    # In a full version we would read, adjust style_dna, and return updated scores
    return {"success": True, "updated_style_dna": {}}


@app.get("/agent/weather/{city}", response_model=WeatherData | ErrorResponse)
async def weather(city: str):
    try:
        data = await get_weather_for_city(city)
        return data
    except Exception as e:
        return ErrorResponse(success=False, message=str(e))


@app.get("/agent/health")
async def health():
    db_ok = True
    try:
        db = get_db()
        # ping as a simple check
        db.command("ping")
    except Exception:
        db_ok = False

    info = orchestrator.health()
    info["db_connected"] = db_ok
    info["memory_stats"] = memory_stats()
    return info


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "success" in detail and "message" in detail:
        # Already in our envelope
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(detail)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agent.main:app", host="127.0.0.1", port=8000, reload=True)

