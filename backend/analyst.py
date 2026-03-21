import json
import os
import re
from typing import Any, Dict, Union
import textract
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


def ask_llm(prompt: str, retries: int = 3) -> str:
    for _ in range(retries):
        try:
            result = ask_openrouter(prompt)
            if isinstance(result, str) and result.strip():
                return result
        except Exception:
            pass
    raise RuntimeError("OpenRouter не вернул корректный ответ")


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

Текст:
{text}
"""

    response_text = ask_llm(prompt)
    return extract_json_from_text(response_text)


def improve_json_and_make_questions(data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    if isinstance(data, dict):
        raw_json = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        raw_json = str(data)

    prompt = f"""
Ты редактор JSON бизнес-требований.

Нужно:
1. Исправить кривые формулировки.
2. Объединить явные дубликаты.
3. Найти неясности, противоречия и пропуски.
4. Не выдумывать факты.
5. Если данных не хватает, не дописывать их от себя, а сформулировать уточняющие вопросы.

Верни строго JSON такого вида:

{{
  "questions": [
    "вопрос 1",
    "вопрос 2"
  ],
  "corrected_json": {{
    "key": "value"
  }}
}}

Только JSON. Без markdown. Без пояснений.

JSON:
{raw_json}
"""

    response_text = ask_llm(prompt)
    result = extract_json_from_text(response_text)

    if "questions" not in result or "corrected_json" not in result:
        raise ValueError("Модель вернула неверный формат ответа")

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


if __name__ == "__main__":
    input_data = """
    Нужно сделать сайт для бронирования столиков.
    Пользователи: студенты и семьи.
    Нужны регистрация, авторизация и бронирование.
    Также желательно добавить аналитику, но пока неясно какую именно.
    """

    try:
        result = process_input(input_data)

        for q in result["questions"]:
            print(q)

    except Exception:
        with open("corrected_json.json", "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)