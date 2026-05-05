import os
import uuid
import asyncio
from pathlib import Path
from typing import List, Tuple, Any, Dict

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain_openai import ChatOpenAI

from agent.models.schemas import (
    ChatRequest,
    ChatResponse,
    AgentMessage,
    OutfitObject,
    TrendItem,
    StyleProfile,
    WeatherData,
)
from agent.tools.weather import get_weather_for_city
from agent.tools.outfit_generator import generate_outfits_with_gpt
from agent.tools.memory_tool import store_memory_entry, retrieve_memory_context
from agent.memory.faiss_store import memory_stats


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


SYSTEM_PROMPT = """
You are TrendÉvo Agent — an elite AI fashion stylist and trend forecaster 
built into the TrendÉvo platform. You are NOT a basic chatbot.

You are an intelligent agent with real tools. ALWAYS follow this process:

1. UNDERSTAND  → Parse intent, mood, occasion, city, constraints
2. GATHER      → Decide which tools to call (weather? trends? memory?)  
3. ANALYZE     → Synthesize all tool outputs together
4. GENERATE    → Create 3 personalized outfit options as valid JSON
5. EXPLAIN     → Tell the user WHY each outfit fits their specific profile

Relevant past context retrieved from memory:
{memory_context}

User's style profile:
{style_profile}

Current weather data:
{weather_data}

Currently trending:
{trend_data}

STRICT RULES:
- Never suggest outfits without first checking weather and current trends
- Always cross-reference user's avoided_styles — never suggest those
- Always output outfits as valid JSON matching the OutfitObject schema
- Show your reasoning chain (Thought/Action/Observation format)
- Reference TrendÉvo catalog categories in trendevo_categories field
- State your confidence score and explain it: "87% because..."
- If you need more info (mood? occasion? city?), ASK before generating
- Remember: you represent TrendÉvo brand — be stylish, specific, confident

TrendÉvo catalog categories available:
denims, jackets, knitwear, upperwear, dresses, thrift
"""


class OrchestratorAgent:
    """
    First version: single LangChain ReAct agent that can call
    weather + memory tools and then generate outfits.
    Later we can delegate to sub-agents, but the interface stays the same.
    """

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = (
            ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.6,
                openai_api_key=api_key,
            )
            if api_key
            else None
        )

    def _build_system_message(
        self,
        memory_context: List[Dict[str, Any]],
        current_profile: StyleProfile | None,
        current_weather: WeatherData | None,
        current_trends: List[TrendItem],
    ) -> str:
        mem_str = "\n".join([m.get("text", "") for m in memory_context]) if memory_context else "None"
        profile_str = current_profile.model_dump_json() if current_profile else "None"
        weather_str = current_weather.model_dump_json() if current_weather else "None"
        trend_str = ", ".join(t.trend_name for t in current_trends) if current_trends else "None"
        return SYSTEM_PROMPT.format(
            memory_context=mem_str,
            style_profile=profile_str,
            weather_data=weather_str,
            trend_data=trend_str,
        )

    def chat(self, req: ChatRequest) -> ChatResponse:
        # Request-scoped state (prevents cross-request contamination).
        current_user_id = req.user_id
        current_session_id = req.session_id or str(uuid.uuid4())
        current_weather: WeatherData | None = None
        current_trends: List[TrendItem] = []
        current_profile: StyleProfile | None = None

        if not self.llm:
            return ChatResponse(
                reply=(
                    "⚠️ TrendÉvo Agent needs OPENAI_API_KEY. "
                    "Add it to agent/.env and restart the API (uvicorn)."
                ),
                reasoning_chain=[],
                outfits=[],
                trends=[],
                tools_used=[],
                session_id=current_session_id,
            )

        def weather_wrapper(city: str) -> str:
            nonlocal current_weather
            weather = asyncio.run(get_weather_for_city(city))
            current_weather = weather
            return weather.model_dump_json()

        def memory_retrieve_wrapper(query: str) -> str:
            context = retrieve_memory_context(current_user_id, query)
            return str(context)

        tools = [
            Tool(
                name="weather_tool",
                func=weather_wrapper,
                description="Get current weather for a given city name.",
            ),
            Tool(
                name="memory_retrieve_tool",
                func=memory_retrieve_wrapper,
                description="Retrieve relevant past interactions for this user.",
            ),
        ]

        agent: AgentExecutor = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        memory_context = retrieve_memory_context(req.user_id, req.message)
        system_message = self._build_system_message(
            memory_context=memory_context,
            current_profile=current_profile,
            current_weather=current_weather,
            current_trends=current_trends,
        )

        # Run the ReAct agent
        result = agent.invoke(
            {
                "input": req.message,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": req.message},
                ],
            }
        )

        final_output: str = result.get("output", "")
        intermediate_steps: List[Tuple[Any, Any]] = result.get("intermediate_steps", [])

        reasoning_chain: List[AgentMessage] = []
        tools_used: List[str] = []
        outfits: List[OutfitObject] = []
        step_idx = 1
        for action, observation in intermediate_steps:
            tools_used.append(getattr(action, "tool", "unknown"))
            reasoning_chain.append(
                AgentMessage(
                    step=step_idx,
                    thought=getattr(action, "log", "") or "",
                    action=getattr(action, "tool", None),
                    observation=str(observation)[:500],
                )
            )
            step_idx += 1


        # Persist interaction to memory
        store_memory_entry(
            user_id=current_user_id,
            session_id=current_session_id,
            message=req.message,
            response=final_output,
        )

        # For now, no external trend data used
        trends: List[TrendItem] = []

        # Append final explanation as last reasoning step
        reasoning_chain.append(
            AgentMessage(
                step=step_idx,
                thought="Synthesizing final answer and outfits for the user.",
                action=None,
                observation=None,
            )
        )

        return ChatResponse(
            reply=final_output,
            reasoning_chain=reasoning_chain,
            outfits=outfits,
            trends=trends,
            tools_used=list(sorted(set(tools_used))),
            session_id=current_session_id,
        )

    @staticmethod
    def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "tools_loaded": ["weather_tool", "memory_retrieve_tool", "outfit_generator"],
            "memory_stats": memory_stats(),
        }

