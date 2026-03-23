from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.deps import get_llm_client
from app.services.analyzer import AnalyzerError, analyze_site as run_analyze_site
from app.services.llm_client import LLMClient

router = APIRouter(tags=["llm"])


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "Привет! Ответь одним коротким предложением: что такое FastAPI?"
            }
        }
    )

    prompt: str


class ChatWithSystemRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "system_prompt": "Отвечай только на русском, максимум два предложения.",
                "user_prompt": "Чем полезен Docker для разработки?",
            }
        }
    )

    system_prompt: str
    user_prompt: str


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"url": "https://example.com"}},
    )

    url: str


class ChatJsonRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "system_prompt": "Верни только JSON без пояснений.",
                "user_prompt": "Назови один язык программирования и год.",
                "jsonStandard": '{"language": "string", "year": "number"}',
            }
        },
    )

    system_prompt: str
    user_prompt: str
    json_standard: str = Field(..., alias="jsonStandard")


@router.post("/chat")
def post_chat(
    body: ChatRequest,
    client: LLMClient = Depends(get_llm_client),
) -> dict[str, str]:
    return {"result": client.chat(body.prompt)}


@router.post("/chat-with-system")
def post_chat_with_system(
    body: ChatWithSystemRequest,
    client: LLMClient = Depends(get_llm_client),
) -> dict[str, str]:
    return {
        "result": client.chat_with_system(body.system_prompt, body.user_prompt),
    }


@router.post("/chat-json")
def post_chat_json(
    body: ChatJsonRequest,
    client: LLMClient = Depends(get_llm_client),
) -> dict[str, Any]:
    return client.chat_json(
        body.system_prompt,
        body.user_prompt,
        json_standard=body.json_standard,
    )


@router.post("/analyze-site")
async def analyze_site(
    request: AnalyzeRequest,
    client: LLMClient = Depends(get_llm_client),
) -> dict[str, Any]:
    try:
        return await run_analyze_site(request.url, client)
    except AnalyzerError as e:
        raise HTTPException(status_code=400, detail=e.detail) from e
