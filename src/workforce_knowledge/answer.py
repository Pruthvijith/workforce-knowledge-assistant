"""Local generation adapter with exact evidence validation and fail-closed output."""

import json
import os
import time
from typing import Protocol

import httpx

from workforce_knowledge.search import retrieve


class Selector(Protocol):
    def __call__(self, query: str, candidates: list[dict]) -> dict: ...


def ollama_select(query: str, candidates: list[dict]) -> dict:
    evidence = [{"source": p["id"], "quote": p["text"]} for p in candidates]
    response = httpx.post("http://127.0.0.1:11434/api/generate", json={
        "model": os.environ.get("OLLAMA_MODEL", "llama3.2:3b"), "stream": False, "format": "json",
        "options": {"temperature": 0},
        "system": "Use only the supplied manual. Select one source and copy its complete quote verbatim. "
                  "Return JSON with source and quote. Return an empty object for insufficient evidence.",
        "prompt": json.dumps(dict(question=query, evidence=evidence))}, timeout=20)
    response.raise_for_status()
    return json.loads(response.json()["response"])


def answer(query: str, support: bool = False, selector: Selector | None = None) -> dict:
    start = time.perf_counter()
    candidates = retrieve(query, support)
    result = dict(status="abstained", reason="insufficient_evidence", citation=None, answer=None,
                  mode="ollama" if selector else "extractive")
    if candidates:
        first = candidates[0]
        try:
            selection = (selector(query, candidates) if selector else
                         {"source": first["id"], "quote": first["text"]})
            match = next((p for p in candidates if isinstance(selection, dict)
                          and p["id"] == selection.get("source")
                          and p["text"] == selection.get("quote")), None)
            if match:
                result.update(status="answered", reason=None,
                              citation=match["id"], answer=match["text"])
            else:
                result["reason"] = "unverified_citation"
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            result["reason"] = "provider_unavailable_or_invalid"
    return dict(**result, latency_ms=round((time.perf_counter()-start)*1000, 3))
