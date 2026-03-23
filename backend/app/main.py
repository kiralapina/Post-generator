from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import APIStatusError, APITimeoutError, OpenAIError

from app.routers import llm

app = FastAPI(title="LLM API", version="1.0.0")
# Только для /openapi.json и Swagger; на запросы к ProxyAPI не влияет
app.openapi_version = "3.0.2"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llm.router)


def _proxyapi_hint_for_status(status_code: int) -> str:
    if status_code == 401:
        return "Проверьте API_KEY (ключ ProxyAPI, без лишних пробелов)."
    if status_code == 402:
        return "Проверьте баланс в личном кабинете ProxyAPI."
    if status_code == 429:
        return "Лимит запросов; подождите или проверьте тариф ProxyAPI."
    return "См. документацию ProxyAPI и раздел про ошибки в кабинете."


@app.exception_handler(APIStatusError)
async def openai_http_error_handler(_: Request, exc: APIStatusError) -> JSONResponse:
    """Ответы 4xx/5xx от ProxyAPI с тем же смыслом кода (кроме 5xx апстрима → 502)."""
    out_status = exc.status_code
    if out_status >= 500:
        out_status = 502
    return JSONResponse(
        status_code=out_status,
        content={
            "detail": exc.message,
            "error_type": exc.__class__.__name__,
            "upstream_status": exc.status_code,
            "hint": _proxyapi_hint_for_status(exc.status_code),
        },
    )


@app.exception_handler(OpenAIError)
async def openai_error_handler(_: Request, exc: OpenAIError) -> JSONResponse:
    """Сеть, таймаут и прочие ошибки SDK до HTTP-ответа апстрима."""
    hint = "Проверьте BASE_URL, API_KEY, доступность api.proxyapi.ru и квоту."
    if isinstance(exc, APITimeoutError):
        hint += " Увеличьте LLM_TIMEOUT в .env и перезапустите процесс."
    return JSONResponse(
        status_code=502,
        content={
            "detail": str(exc),
            "error_type": exc.__class__.__name__,
            "hint": hint,
        },
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "LLM API",
        "docs": "/docs",
        "endpoints": (
            "POST /chat, POST /chat-with-system, POST /chat-json, POST /analyze-site"
        ),
    }
