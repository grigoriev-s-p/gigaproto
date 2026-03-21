API_KEY = "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"

import os
import requests

SESSION = requests.Session()

def ask_openrouter(prompt: str) -> str:
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY не найден в переменных окружения")

    response = SESSION.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "stepfun/step-3.5-flash:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        },
        timeout=90,
    )

    response.raise_for_status()
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
            f"Модель обрезала ответ по лимиту токенов. "
            f"finish_reason=length. "
            f"Начало ответа: {repr((content or '')[:500])}"
        )

    if content:
        return content

    raise ValueError(
        f"Модель не вернула content. finish_reason={finish_reason}, response={data}"
    )