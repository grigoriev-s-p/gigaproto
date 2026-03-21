from google import genai
from google.genai import types
import requests

def ask_openrouter(prompt: str) -> str:
    API_KEY = "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"

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "stepfun/step-3.5-flash:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        timeout=60
    )
    try:
        data = response.json()
    except Exception:
        return f"Ошибка: сервер вернул не JSON.\nОтвет:\n{response.text}"

    if "choices" not in data:
        return f"Ошибка OpenRouter:\n{data}"

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Ошибка чтения ответа OpenRouter: {e}\nПолный ответ:\n{data}"

def ask_gemini(prompt:str, _temperature=0.2, _top_p=0.9, _top_k=40, _system_prompt="")->str:
    client = genai.Client(api_key="AIzaSyD0B9vR7VjQ5shYDossCwwhYv2insdKfT0")

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
        temperature=_temperature,
        top_p=_top_p,
        top_k=_top_k,
        system_instruction=_system_prompt
        )
    )
    return response.text or ""