from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path
import os
import requests

load_dotenv(Path(__file__).resolve().parent / ".env")
API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()


def ask_openrouter(prompt: str) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "stepfun/step-3.5-flash:free",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )

    data = response.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content") or str(data)

def ask_gemini(prompt:str, _temperature=0.2, _top_p=0.9, _top_k=40, _system_prompt="")->str:
    client = genai.Client(api_key="GEMINI_API_KEY")

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
