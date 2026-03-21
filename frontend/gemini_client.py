from google import genai
from google.genai import types
def ask(prompt:str, _temperature=0.2, _top_p=0.9, _top_k=40, _system_prompt="")->str:
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