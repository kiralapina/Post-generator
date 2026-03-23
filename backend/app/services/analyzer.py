"""Анализ сайта: загрузка HTML, извлечение текста, многошаговый опрос LLM."""

from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import contextmanager
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.llm_client import LLMClient


class AnalyzerError(Exception):
    """Ошибка загрузки/парсинга — превращается в HTTP 400."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def _max_text_chars() -> int:
    raw = os.getenv("ANALYZE_MAX_TEXT_CHARS", "80000")
    try:
        return max(5000, int(raw))
    except ValueError:
        return 80000


def _validate_http_url(url: str) -> str:
    u = url.strip()
    if not u:
        raise AnalyzerError("Пустой URL.")
    parsed = urlparse(u)
    if parsed.scheme not in ("http", "https"):
        raise AnalyzerError("Разрешены только URL с протоколом http или https.")
    if not parsed.netloc:
        raise AnalyzerError("Некорректный URL: не указан хост.")
    return u


async def _download_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; PostGeneratorAnalyzer/1.0; +https://example.com)"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    timeout = float(os.getenv("ANALYZE_FETCH_TIMEOUT", "30"))
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPStatusError as e:
        raise AnalyzerError(
            f"Сайт вернул ошибку HTTP {e.response.status_code}."
        ) from e
    except httpx.RequestError as e:
        raise AnalyzerError(f"Не удалось скачать страницу: {e!s}") from e


def _html_to_text(html: str) -> str:
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "template"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
    except Exception as e:
        raise AnalyzerError(f"Не удалось разобрать HTML: {e!s}") from e

    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    if not out:
        raise AnalyzerError("После очистки HTML не осталось текста.")
    limit = _max_text_chars()
    if len(out) > limit:
        out = out[:limit] + "\n\n[…текст обрезан по лимиту ANALYZE_MAX_TEXT_CHARS…]"
    return out


def _steps_from_json(data: dict[str, Any]) -> list[str]:
    for key in ("steps", "prompts", "analysis_steps", "шаги"):
        v = data.get(key)
        if isinstance(v, list):
            out = [str(x).strip() for x in v if str(x).strip()]
            if out:
                return out
    return []


@contextmanager
def _temp_max_tokens(client: LLMClient, value: int | None) -> Any:
    prev = client.max_tokens
    client.max_tokens = value
    try:
        yield
    finally:
        client.max_tokens = prev


STEPS_JSON_STANDARD = (
    '{"steps": ["краткая формулировка шага 1 для аналитика", "…"], '
    '"count": "number — сколько шагов (5-6)"}'
)

FINAL_JSON_STANDARD = (
    '{"introduction": "строка — введение", '
    '"page_interpretation": "строка — интерпретация страницы", '
    '"posts": ["вариант поста 1", "вариант 2", "вариант 3"]}'
)


async def analyze_site(url: str, client: LLMClient) -> dict[str, Any]:
    """Полный пайплайн анализа сайта. Результат — dict для ответа API."""
    url = _validate_http_url(url)
    html = await _download_html(url)
    site_text = await asyncio.to_thread(_html_to_text, html)

    system_plan = (
        "Ты бот-анализатор сайтов. Вот текст сайта:\n\n"
        f"{site_text}\n\n"
        "В ответе в формате JSON выдай список из 5-6 шагов (промптов), которые нужно "
        "выполнить для анализа этого сайта и выявления идей для постов."
    )
    user_plan = (
        "Сформируй ровно один JSON-объект по схеме. Шаги — отдельные короткие "
        "инструкции для последующего анализа того же текста."
    )

    def _plan() -> dict[str, Any]:
        with _temp_max_tokens(client, 4096):
            return client.chat_json(
                system_plan,
                user_plan,
                json_standard=STEPS_JSON_STANDARD,
            )

    plan_raw = await asyncio.to_thread(_plan)
    steps = _steps_from_json(plan_raw)
    if not steps:
        raise AnalyzerError(
            "Не удалось получить список шагов из ответа LLM (ожидался ключ steps и т.п.)."
        )
    if len(steps) > 8:
        steps = steps[:8]

    intermediate: list[str] = []

    def _run_step(step: str) -> str:
        with _temp_max_tokens(client, 4096):
            return client.chat_with_system(step, site_text)

    for step in steps:
        ans = await asyncio.to_thread(_run_step, step)
        intermediate.append(ans)

    combined = json.dumps(intermediate, ensure_ascii=False, indent=2)
    final_system = (
        "У тебя есть результаты промежуточного анализа:\n\n"
        f"{combined}\n\n"
        "Объедини их и выдай три варианта постов для соцсетей. "
        "Обязательно включи в анализ оригинальный текст сайта (он будет в user-сообщении)."
    )
    final_user = (
        "Оригинальный текст сайта для контекста:\n\n"
        f"{site_text}\n\n"
        "Верни один JSON: введение, интерпретация страницы, три примера постов."
    )

    def _final() -> dict[str, Any]:
        with _temp_max_tokens(client, 8192):
            return client.chat_json(
                final_system,
                final_user,
                json_standard=FINAL_JSON_STANDARD,
            )

    final_obj = await asyncio.to_thread(_final)

    return {
        "url": url,
        "steps": steps,
        "intermediate_results": intermediate,
        "final": final_obj,
    }
