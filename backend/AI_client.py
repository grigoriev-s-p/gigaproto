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
        }
    )

    return response.json()["choices"][0]["message"]["content"]

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