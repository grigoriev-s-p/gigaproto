import os
import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "stepfun/step-3.5-flash:free"
SESSION = requests.Session()


def ask_openrouter(prompt: str, model: str | None = None, temperature: float = 0.1) -> str:
    api_key = "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"
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY не найден в переменных окружения")

    response = SESSION.post(
        OPENROUTER_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or DEFAULT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        },
        timeout=90,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        try:
            details = response.json()
        except Exception:
            details = response.text
        raise ValueError(f"Ошибка OpenRouter: {details}") from exc

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError(f"OpenRouter не вернул choices: {data}")

    choice = choices[0]
    message = choice.get("message", {}) or {}
    content = message.get("content")
    finish_reason = choice.get("finish_reason")

    if finish_reason == "length":
        raise ValueError(
            "Модель обрезала ответ по лимиту токенов. "
            f"finish_reason=length. Начало ответа: {repr((content or '')[:500])}"
        )

    if isinstance(content, str) and content.strip():
        return content

    raise ValueError(
        f"Модель не вернула content. finish_reason={finish_reason}, response={data}"
    )
