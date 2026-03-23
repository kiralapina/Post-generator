from functools import lru_cache

from fastapi import HTTPException

from app.services.llm_client import LLMClient


@lru_cache
def get_llm_client() -> LLMClient:
    try:
        return LLMClient()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
