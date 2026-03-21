import json
import re
import ast
from typing import Any, Dict

from AI_client import ask_openrouter


def extract_json_from_text(text: str) -> Dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"JSON не найден. Ответ модели:\n{text[:500]}")

    json_text = text[start:end + 1]

    try:
        data = json.loads(json_text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    try:
        data = ast.literal_eval(json_text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    raise ValueError(f"Не удалось распарсить ui_schema. Фрагмент:\n{json_text[:500]}")


def build_ui_schema_prompt(requirements: Dict[str, Any]) -> str:
    return f"""
Сделай ui_schema JSON по requirements JSON.

Верни только JSON без пояснений.

Формат:
{{
  "pages": [
    {{
      "id": "string",
      "name": "string",
      "route": "string",
      "elements": [
        {{
          "type": "button|input|form|table|list|card|filters|text|chart",
          "label": "string",
          "description": "string",
          "fields": ["string"],
          "action": "string"
        }}
      ]
    }}
  ],
  "actions": [
    {{
      "id": "string",
      "label": "string",
      "type": "navigate|submit|download|toggle|filter",
      "target": "string"
    }}
  ]
}}

Правила:
- каждая важная функция должна попасть либо в pages.elements, либо в actions
- если есть список/история -> table или list
- если есть фильтры -> filters
- если есть детали -> отдельная страница
- если есть экспорт -> button + download
- не добавляй лишнего

REQUIREMENTS:
{json.dumps(requirements, ensure_ascii=False, separators=(",", ":"))}
"""


def ui_schema_agent(requirements: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_ui_schema_prompt(requirements)
    raw_response = ask_openrouter(prompt)
    return extract_json_from_text(raw_response)