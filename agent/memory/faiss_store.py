import os
import pickle
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


# agent/.env (works no matter what the process cwd is)
_AGENT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_AGENT_ROOT / ".env")

_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", str(_AGENT_ROOT / "memory" / "faiss_index"))
_INDEX_DIR = Path(_INDEX_PATH)
_INDEX_DIR.mkdir(parents=True, exist_ok=True)

_INDEX_FILE = _INDEX_DIR / "index.faiss"
_META_FILE = _INDEX_DIR / "meta.pkl"

_openai_client: OpenAI | None = None


def _get_openai() -> OpenAI | None:
    """Lazy OpenAI client so import does not crash when OPENAI_API_KEY is unset."""
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    _openai_client = OpenAI(api_key=key)
    return _openai_client


def _embed(texts: List[str]) -> np.ndarray:
    """
    Embed a list of texts using OpenAI text-embedding-3-small.
    """
    client = _get_openai()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set")
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    vectors = [np.array(d.embedding, dtype="float32") for d in resp.data]
    return np.vstack(vectors)


def _load_index(d: int) -> faiss.IndexFlatIP:
    if _INDEX_FILE.exists():
        index = faiss.read_index(str(_INDEX_FILE))
        return index
    index = faiss.IndexFlatIP(d)
    return index


def _save_index(index: faiss.IndexFlatIP) -> None:
    faiss.write_index(index, str(_INDEX_FILE))


def _load_metadata() -> List[dict]:
    if _META_FILE.exists():
        with _META_FILE.open("rb") as f:
            return pickle.load(f)
    return []


def _save_metadata(meta: List[dict]) -> None:
    with _META_FILE.open("wb") as f:
        pickle.dump(meta, f)


def store_interaction(user_id: str, session_id: str, message: str, response: str) -> None:
    """
    Store a single (message, response) pair into FAISS with metadata.
    """
    if _get_openai() is None:
        return
    text = f"USER: {message}\nAGENT: {response}"
    vecs = _embed([text])
    dim = vecs.shape[1]
    index = _load_index(dim)

    # Normalize for cosine similarity
    faiss.normalize_L2(vecs)
    index.add(vecs)
    _save_index(index)

    meta = _load_metadata()
    meta.append(
        {
            "user_id": user_id,
            "session_id": session_id,
            "text": text,
        }
    )
    _save_metadata(meta)


def retrieve_relevant(user_id: str, query: str, top_k: int = 3) -> List[Tuple[float, dict]]:
    """
    Retrieve top_k most similar interactions for a given user and query.
    Returns list of (score, metadata).
    """
    meta = _load_metadata()
    if not meta:
        return []

    if _get_openai() is None:
        return []

    # Reuse pre-computed vectors already stored in FAISS.
    # Only embed the incoming query at retrieval time.
    q_vec = _embed([query])
    dim = q_vec.shape[1]
    index = _load_index(dim)
    if index.ntotal == 0:
        return []

    faiss.normalize_L2(q_vec)

    # Search a wider candidate set, then filter by user_id to preserve isolation.
    search_k = min(max(top_k * 8, top_k), index.ntotal)
    scores, indices = index.search(q_vec, search_k)

    results: List[Tuple[float, dict]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(meta):
            continue
        if meta[idx].get("user_id") != user_id:
            continue
        results.append((float(score), meta[idx]))
        if len(results) >= top_k:
            break

    # If filtering removed too many results, do one full-pass search once.
    if len(results) < top_k and search_k < index.ntotal:
        full_scores, full_indices = index.search(q_vec, index.ntotal)
        for score, idx in zip(full_scores[0], full_indices[0]):
            if idx < 0 or idx >= len(meta):
                continue
            if meta[idx].get("user_id") != user_id:
                continue
            candidate = (float(score), meta[idx])
            if candidate in results:
                continue
            results.append(candidate)
            if len(results) >= top_k:
                break

    return results


def memory_stats() -> dict:
    meta = _load_metadata()
    count = len(meta)
    return {
        "interactions": count,
        "index_exists": _INDEX_FILE.exists(),
    }

