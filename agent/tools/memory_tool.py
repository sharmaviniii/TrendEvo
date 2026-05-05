from typing import List, Dict, Any

from agent.memory.faiss_store import store_interaction, retrieve_relevant


def store_memory_entry(user_id: str, session_id: str, message: str, response: str) -> None:
    store_interaction(user_id=user_id, session_id=session_id, message=message, response=response)


def retrieve_memory_context(user_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    results = retrieve_relevant(user_id=user_id, query=query, top_k=top_k)
    context: List[Dict[str, Any]] = []
    for score, meta in results:
        context.append(
            {
                "score": score,
                "text": meta.get("text", ""),
                "session_id": meta.get("session_id"),
            }
        )
    return context

