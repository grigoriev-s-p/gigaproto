import json
import os
import re
from typing import Any, Dict, Union

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

    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Не удалось извлечь JSON из ответа модели")


def document_to_json(text: str) -> Dict[str, Any]:
    prompt = f"""
Ты анализируешь текст документа и превращаешь его в структурированный JSON.

Правила:
- Верни только валидный JSON
- Без пояснений
- Без markdown
- Не пиши текст до или после JSON
- Не выдумывай данные
- Если структура документа неровная, всё равно собери максимально логичный JSON

Текст документа:
{text}
"""

    response_text = ask_openrouter(prompt)
    return extract_json_from_text(response_text)


def improve_json_and_make_questions(data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    raw_json = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)

    prompt = f"""
Ты редактор JSON бизнес-требований.

Тебе дан JSON, полученный из документа.
Нужно:
1. Исправить кривые или расплывчатые формулировки.
2. Убрать или объединить явные дубликаты.
3. Сохранить только то, что действительно есть во входных данных.
4. Ничего не выдумывать.

Верни строго JSON такого формата:

{{
  "corrected_json": {{
    "key": "value"
  }}
}}

Только JSON. Без markdown. Без пояснений.

Входной JSON:
{raw_json}
"""

    response_text = ask_openrouter(prompt)
    result = extract_json_from_text(response_text)

    if "questions" not in result:
        result["questions"] = []

    if "corrected_json" not in result:
        result["corrected_json"] = {}

    if not isinstance(result["questions"], list):
        result["questions"] = []

    if not isinstance(result["corrected_json"], dict):
        result["corrected_json"] = {}

    return result


def process_input(input_data: str, output_json_path: str = "corrected_json.json") -> Dict[str, Any]:
    text = get_text(input_data)
    raw_json = document_to_json(text)
    result = improve_json_and_make_questions(raw_json)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result["corrected_json"], f, ensure_ascii=False, indent=2)

    return result


def txt_agent(input_data: str):

    result = process_input(input_data)

    # print("Уточняющие вопросы:")
    # for q in result["questions"]:
    #     print("-", q)

    return json.dumps(result["corrected_json"], ensure_ascii=False, indent=2)
