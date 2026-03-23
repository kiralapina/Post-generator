"""Клиент LLM через OpenAI-совместимый Proxy API."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _normalize_env_str(value: str) -> str:
    """Убирает \\r и BOM из .env (часто после копирования из Windows/браузера)."""
    return value.replace("\r", "").replace("\ufeff", "").strip()


def _timeout_seconds() -> float:
    raw = os.getenv("LLM_TIMEOUT", "120")
    try:
        return max(5.0, float(raw))
    except ValueError:
        return 120.0


class LLMClient:
    """Клиент для запросов к LLM (OpenAI-совместимый API, в т.ч. ProxyAPI).

    ProxyAPI: BASE_URL=https://api.proxyapi.ru/openai/v1, API_KEY из кабинета,
    заголовок Authorization: Bearer задаётся SDK автоматически.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        resolved_base = _normalize_env_str(
            (base_url or os.getenv("BASE_URL") or "").rstrip("/")
        )
        self.api_key = _normalize_env_str(api_key or os.getenv("API_KEY") or "")
        self.model = _normalize_env_str(model or os.getenv("MODEL") or "gpt-4o-mini")
        self.base_url = resolved_base

        if not resolved_base:
            raise ValueError(
                "BASE_URL не задан. Для ProxyAPI (OpenAI): "
                "https://api.proxyapi.ru/openai/v1"
            )
        if not self.api_key:
            raise ValueError("API_KEY не задан (ключ из личного кабинета ProxyAPI).")
        if "proxyapi.ru" in resolved_base and "/openai/v1" not in resolved_base:
            raise ValueError(
                "Для ProxyAPI путь к OpenAI должен заканчиваться на /openai/v1 "
                "(см. https://proxyapi.ru/docs/overview)"
            )
        self.system_prompt: str | None = None
        self.max_tokens: int | None = None

        self._client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=_timeout_seconds(),
        )

    def _completion_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    def _messages_for_chat(self, user_prompt: str) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def chat(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=self._messages_for_chat(prompt),
            **self._completion_kwargs(),
        )
        return (response.choices[0].message.content or "").strip()

    def chat_with_system(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            **self._completion_kwargs(),
        )
        return (response.choices[0].message.content or "").strip()

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_standard: str = "",
    ) -> dict[str, Any]:
        parts = [system_prompt.strip()]
        if json_standard.strip():
            parts.append(
                "Ответ — один JSON-объект, строго соответствующий описанию/схеме:\n"
                + json_standard.strip()
            )
        combined_system = "\n\n".join(parts)
        messages = [
            {"role": "system", "content": combined_system},
            {"role": "user", "content": user_prompt},
        ]
        kwargs = self._completion_kwargs()
        kwargs["response_format"] = {"type": "json_object"}
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)


if __name__ == "__main__":
    base = os.getenv("BASE_URL")
    key = os.getenv("API_KEY")
    if not base or not key:
        print(
            "Задайте в .env переменные BASE_URL и API_KEY, "
            "затем снова: python -m app.services.llm_client"
        )
        raise SystemExit(1)

    client = LLMClient(base_url=base, api_key=key)
    client.max_tokens = 256

    print("--- chat() ---")
    client.system_prompt = "Отвечай одним коротким предложением."
    print(client.chat("Что такое Python?"))

    print("\n--- chat_with_system() ---")
    print(
        client.chat_with_system(
            "Ты лаконичный помощник.",
            "Назови одну встроенную функцию Python для списков.",
        )
    )

    print("\n--- chat_json() ---")
    data = client.chat_json(
        'Ответь только JSON-объектом с ключами "lang" (строка) и "year" (число).',
        "Язык программирования для этого скрипта и текущий год как число.",
        json_standard='{"lang": "string", "year": "number"}',
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
