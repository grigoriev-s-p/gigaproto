import json
import os
import ast
import re
from typing import Any, Dict

from AI_client import ask_openrouter


def get_text(input_data: str) -> str:
    if os.path.exists(input_data):
        ext = os.path.splitext(input_data)[1].lower()

        if ext == ".txt":
            with open(input_data, "r", encoding="utf-8") as f:
                return f.read()

        elif ext == ".docx":
            from docx import Document
            doc = Document(input_data)
            return "\n".join(p.text for p in doc.paragraphs)

        elif ext == ".doc":
            import textract
            return textract.process(input_data).decode("utf-8", errors="ignore")

        else:
            raise ValueError(f"Неподдерживаемый формат файла: {ext}")

    return input_data


def extract_json_from_text(text: str) -> Dict[str, Any]:
    text = text.strip()

    # убрать markdown fences
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # пробуем распарсить как обычный JSON
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # пробуем вытащить первую JSON-подобную структуру
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Не удалось извлечь JSON из ответа модели. Ответ был:\n{text[:500]}")

    chunk = match.group(0)

    # сначала как JSON
    try:
        data = json.loads(chunk)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # потом как python-dict: {'a': 1}
    try:
        data = ast.literal_eval(chunk)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    raise ValueError(f"Ответ похож на JSON, но не парсится. Фрагмент:\n{chunk[:500]}")

def normalize_requirements(text: str) -> Dict[str, Any]:
    prompt = f"""
Ты анализируешь текст бизнес-требований и превращаешь его в нормализованный JSON.

Правила:
- Верни только валидный JSON
- Без пояснений
- Без markdown
- Не выдумывай данные
- Убери явные дубликаты
- Исправь кривые или расплывчатые формулировки, не меняя смысл
- Если данных мало, сохрани только то, что реально есть в тексте

Верни строго JSON такого формата:
{{
  "corrected_json": {{}},
  "questions": []
}}

Текст документа:
{text}
"""

    response_text = ask_openrouter(prompt)
    result = extract_json_from_text(response_text)

    if "corrected_json" not in result or not isinstance(result["corrected_json"], dict):
        result["corrected_json"] = {}

    if "questions" not in result or not isinstance(result["questions"], list):
        result["questions"] = []

    return result


def txt_agent(input_data: str) -> Dict[str, Any]:
    text = get_text(input_data)
    result = normalize_requirements(text)
    
    return result["corrected_json"]