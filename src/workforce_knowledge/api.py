import hmac
import logging
import os
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from workforce_knowledge.answer import answer, ollama_select

app = FastAPI(title="Workforce knowledge assistant")
logger = logging.getLogger("uvicorn.error")


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=3, max_length=500)


@app.get("/health")
def health() -> dict:
    return {"status": "ready"}


@app.post("/v1/answer")
def ask(body: Question, x_support_key: Annotated[str | None, Header()] = None) -> dict:
    key = os.environ.get("SUPPORT_KEY")
    if x_support_key is not None and (not key or not hmac.compare_digest(key.encode(), x_support_key.encode())):
        raise HTTPException(403, "Invalid support credential")
    mode = os.environ.get("ANSWER_MODE", "extractive")
    if mode not in {"extractive", "ollama"}:
        raise HTTPException(503, "Unsupported answer mode")
    result = answer(body.question, support=x_support_key is not None,
                    selector=ollama_select if mode == "ollama" else None)
    logger.info("knowledge_answer status=%s mode=%s elapsed_ms=%s",
                result["status"], mode, result["latency_ms"])
    return result
