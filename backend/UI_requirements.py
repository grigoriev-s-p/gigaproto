import json
import re
from typing import Any, Dict

from AI_client import ask_openrouter


def extract_json_from_text(text: str):
    import re
    text = text.strip()

    # убрать markdown
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    # найти JSON
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("JSON не найден")

    json_text = text[start:end + 1]

    try:
        return json.loads(json_text)
    except:
        # fallback
        json_text = json_text.replace("'", '"')
        return json.loads(json_text)


def build_ui_schema_prompt(requirements: Dict[str, Any]) -> str:
    return f"""
Ты — UI-дизайнер и системный аналитик.

Твоя задача: по requirements JSON создать простой и понятный ui_schema JSON, который описывает структуру сайта.

ВАЖНО:
- Верни ТОЛЬКО JSON
- Без пояснений
- Без markdown
- Без ```json
- Ответ должен начинаться с {{ и заканчиваться }}
ЦЕЛЬ:
Создать структуру сайта в виде:
- страницы
- элементы на страницах (кнопки, таблицы, формы и т.д.)
- действия пользователя
ФОРМАТ ОТВЕТА:

{{
  "pages": [
    {{
      "id": "string",
      "name": "string",
      "route": "string",
      "elements": [
        {{
          "type": "string",
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
      "type": "navigate | submit | download | toggle | filter",
      "target": "string"
    }}
  ]
}}
ПРАВИЛА:

1. Каждая важная функция из requirements должна появиться:
   → либо как элемент
   → либо как action

2. Используй типы элементов:
- "button"
- "input"
- "form"
- "table"
- "list"
- "card"
- "filters"
- "text"
- "chart"

3. ЛОГИКА:
- если есть "история", "операции", "список" → table или list
- если есть "фильтр" → filters
- если есть "создать / изменить" → form + input
- если есть "детали" → отдельная страница
- если есть "экспорт / отчет" → button + action download
- если есть "переключение / лимиты / блокировка" → toggle или button

4. СТРАНИЦЫ:
- создавай страницы только если это нужно
- обычно:
  - главная (dashboard)
  - страницы под ключевые функции

5. ACTIONS:
- связывай кнопки с действиями через поле "action"
- не дублируй одинаковые actions

6. НЕ ДЕЛАЙ:
- не добавляй лишние поля
- не пиши текст вне JSON
- не оставляй пустые массивы без смысла

REQUIREMENTS:
{json.dumps(requirements, ensure_ascii=False, indent=2)}

ОТВЕТ:
Верни только JSON.
"""


def ui_schema_agent(requirements: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_ui_schema_prompt(requirements)
    raw_response = ask_openrouter(prompt)

    return extract_json_from_text(raw_response)
