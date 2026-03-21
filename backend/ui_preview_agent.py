import ast
import json
import re
from typing import Any, Dict, List

from AI_client import ask_openrouter


SECTION_KINDS = {
    "hero",
    "text",
    "filters",
    "form",
    "table",
    "list",
    "cardGrid",
    "actions",
    "chart",
}


def extract_json_from_text(text: str) -> Dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"ui_preview JSON не найден. Ответ модели:\n{text[:500]}")

    payload = text[start:end + 1]

    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    try:
        data = ast.literal_eval(payload)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    raise ValueError(f"Не удалось распарсить ui_preview JSON. Фрагмент:\n{payload[:500]}")


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    return str(value)


def _slug(value: str, fallback: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.IGNORECASE)
    value = value.strip("-")
    return value or fallback


def _field_objects(fields: Any) -> List[Dict[str, str]]:
    if not isinstance(fields, list):
        return []

    result: List[Dict[str, str]] = []
    for index, field in enumerate(fields):
        label = _safe_text(field, f"Поле {index + 1}")
        result.append(
            {
                "name": _slug(label, f"field-{index + 1}"),
                "label": label,
                "type": "text",
                "placeholder": label,
            }
        )
    return result


def _table_rows(columns: List[str], description: str) -> List[List[str]]:
    if not columns:
        columns = ["Поле 1", "Поле 2", "Поле 3"]
    rows: List[List[str]] = []
    for row_index in range(3):
        row: List[str] = []
        for col in columns:
            if row_index == 0:
                row.append(f"Пример {col.lower()}")
            elif row_index == 1:
                row.append(f"Тестовое значение {row_index + 1}")
            else:
                row.append(description[:36] or f"Значение {row_index + 1}")
        rows.append(row)
    return rows


def _cards_from_description(label: str, description: str) -> List[Dict[str, Any]]:
    return [
        {
            "title": label or "Карточка",
            "description": description or "Описание элемента интерфейса",
            "meta": ["Автогенерация", "По ui_schema"],
        },
        {
            "title": f"{label or 'Блок'} — состояние",
            "description": "Эта карточка показывает, как будет выглядеть типовой контент.",
            "meta": ["Preview", "Demo"],
        },
    ]


def build_ui_preview_prompt(ui_schema: Dict[str, Any], requirements: Dict[str, Any] | None = None) -> str:
    requirements = requirements or {}
    return f"""
Сделай renderable ui_preview JSON по ui_schema JSON.

Верни только JSON без пояснений и без markdown.

Строгий формат ответа:
{{
  "app": {{
    "title": "string",
    "subtitle": "string",
    "theme": "light|dark",
    "primaryAction": "string"
  }},
  "pages": [
    {{
      "id": "string",
      "name": "string",
      "route": "string",
      "summary": "string",
      "sections": [
        {{
          "id": "string",
          "kind": "hero|text|filters|form|table|list|cardGrid|actions|chart",
          "title": "string",
          "description": "string",
          "fields": [
            {{
              "name": "string",
              "label": "string",
              "type": "text|number|date|select|textarea",
              "placeholder": "string",
              "options": ["string"]
            }}
          ],
          "columns": ["string"],
          "rows": [["string"]],
          "cards": [
            {{
              "title": "string",
              "description": "string",
              "meta": ["string"]
            }}
          ],
          "bullets": ["string"],
          "actions": [
            {{
              "label": "string",
              "type": "primary|secondary",
              "target": "string"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Правила:
- Не генерируй код React/HTML.
- Это именно JSON для дальнейшего рендера во frontend.
- Для каждой страницы добавь hero секцию первой.
- Для table добавляй columns и rows.
- Для filters/form добавляй fields.
- Для list/text добавляй bullets.
- Для card добавляй kind=cardGrid.
- Для button и action-блоков добавляй kind=actions.
- Данные в rows/cards должны быть демонстрационными, но близкими по смыслу.
- Не оставляй пустых sections.

REQUIREMENTS:
{json.dumps(requirements, ensure_ascii=False)}

UI_SCHEMA:
{json.dumps(ui_schema, ensure_ascii=False)}
"""


def build_fallback_preview(ui_schema: Dict[str, Any], requirements: Dict[str, Any] | None = None) -> Dict[str, Any]:
    requirements = requirements or {}
    pages = ui_schema.get("pages") if isinstance(ui_schema, dict) else None
    if not isinstance(pages, list):
        pages = []

    app_title = (
        requirements.get("meta", {}).get("title")
        if isinstance(requirements.get("meta"), dict)
        else None
    ) or requirements.get("screen_name") or "Сгенерированный интерфейс"

    preview_pages: List[Dict[str, Any]] = []

    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue

        page_name = _safe_text(page.get("name"), f"Страница {page_index + 1}")
        page_id = _safe_text(page.get("id"), f"page-{page_index + 1}")
        route = _safe_text(page.get("route"), f"/{page_id}")
        elements = page.get("elements") if isinstance(page.get("elements"), list) else []

        sections: List[Dict[str, Any]] = [
            {
                "id": f"{page_id}-hero",
                "kind": "hero",
                "title": page_name,
                "description": f"Демо-предпросмотр страницы {page_name} на основе ui_schema.",
                "actions": [{"label": "Основной сценарий", "type": "primary", "target": route}],
            }
        ]

        for element_index, element in enumerate(elements):
            if not isinstance(element, dict):
                continue

            element_type = _safe_text(element.get("type"), "text")
            label = _safe_text(element.get("label"), f"Элемент {element_index + 1}")
            description = _safe_text(element.get("description"), "")
            fields = _field_objects(element.get("fields"))
            section_id = f"{page_id}-section-{element_index + 1}"

            if element_type == "filters":
                sections.append(
                    {
                        "id": section_id,
                        "kind": "filters",
                        "title": label,
                        "description": description or "Блок фильтров для быстрого отбора данных.",
                        "fields": fields or [
                            {"name": "search", "label": "Поиск", "type": "text", "placeholder": "Введите запрос"},
                            {"name": "period", "label": "Период", "type": "date", "placeholder": "Выберите дату"},
                        ],
                        "actions": [{"label": "Применить", "type": "primary", "target": route}],
                    }
                )
            elif element_type in {"form", "input"}:
                sections.append(
                    {
                        "id": section_id,
                        "kind": "form",
                        "title": label,
                        "description": description or "Форма ввода пользовательских данных.",
                        "fields": fields or [
                            {"name": "title", "label": "Название", "type": "text", "placeholder": "Введите значение"},
                            {"name": "comment", "label": "Комментарий", "type": "textarea", "placeholder": "Опишите детали"},
                        ],
                        "actions": [{"label": element.get("action") or "Отправить", "type": "primary", "target": route}],
                    }
                )
            elif element_type == "table":
                columns = [field.get("label", "Колонка") for field in fields] or ["Название", "Статус", "Дата"]
                sections.append(
                    {
                        "id": section_id,
                        "kind": "table",
                        "title": label,
                        "description": description or "Табличное представление данных.",
                        "columns": columns,
                        "rows": _table_rows(columns, description),
                    }
                )
            elif element_type == "list":
                sections.append(
                    {
                        "id": section_id,
                        "kind": "list",
                        "title": label,
                        "description": description or "Список элементов для просмотра.",
                        "bullets": fields and [field["label"] for field in fields] or [
                            "Первый элемент списка",
                            "Второй элемент списка",
                            "Третий элемент списка",
                        ],
                    }
                )
            elif element_type == "card":
                sections.append(
                    {
                        "id": section_id,
                        "kind": "cardGrid",
                        "title": label,
                        "description": description or "Карточки с краткими сущностями и метаданными.",
                        "cards": _cards_from_description(label, description),
                    }
                )
            elif element_type == "chart":
                sections.append(
                    {
                        "id": section_id,
                        "kind": "chart",
                        "title": label,
                        "description": description or "Графический блок для аналитики и трендов.",
                        "bullets": ["Тренд за период", "Пиковые значения", "Сравнение сегментов"],
                    }
                )
            elif element_type == "button":
                sections.append(
                    {
                        "id": section_id,
                        "kind": "actions",
                        "title": label,
                        "description": description or "Набор действий пользователя.",
                        "actions": [
                            {
                                "label": label,
                                "type": "primary",
                                "target": _safe_text(element.get("action"), route),
                            }
                        ],
                    }
                )
            else:
                sections.append(
                    {
                        "id": section_id,
                        "kind": "text",
                        "title": label,
                        "description": description or "Текстовое описание блока.",
                        "bullets": [
                            description or "Описание блока",
                            f"Тип элемента: {element_type}",
                            f"Маршрут: {route}",
                        ],
                    }
                )

        preview_pages.append(
            {
                "id": page_id,
                "name": page_name,
                "route": route,
                "summary": f"Страница {page_name} с {max(len(sections) - 1, 0)} основными блоками.",
                "sections": sections,
            }
        )

    if not preview_pages:
        preview_pages = [
            {
                "id": "main",
                "name": "Главная",
                "route": "/",
                "summary": "Предпросмотр недоступен: ui_schema пустая или не распознана.",
                "sections": [
                    {
                        "id": "main-hero",
                        "kind": "hero",
                        "title": app_title,
                        "description": "Нужно сгенерировать хотя бы одну страницу в ui_schema.",
                        "actions": [{"label": "Попробовать снова", "type": "primary", "target": "/"}],
                    }
                ],
            }
        ]

    return {
        "app": {
            "title": _safe_text(app_title, "Сгенерированный интерфейс"),
            "subtitle": "Визуализация, собранная из ui_schema",
            "theme": "light",
            "primaryAction": "Открыть сценарий",
        },
        "pages": preview_pages,
    }


def validate_preview(preview: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(preview, dict):
        raise ValueError("ui_preview должен быть объектом")

    app = preview.get("app")
    pages = preview.get("pages")
    if not isinstance(app, dict) or not isinstance(pages, list) or not pages:
        raise ValueError("ui_preview должен содержать app и непустой pages")

    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("Каждая страница ui_preview должна быть объектом")
        sections = page.get("sections")
        if not isinstance(sections, list) or not sections:
            raise ValueError("У каждой страницы должны быть sections")
        for section in sections:
            if not isinstance(section, dict):
                raise ValueError("Каждая section должна быть объектом")
            kind = section.get("kind")
            if kind not in SECTION_KINDS:
                raise ValueError(f"Некорректный kind секции: {kind}")

    return preview


def ui_preview_agent(ui_schema: Dict[str, Any], requirements: Dict[str, Any] | None = None) -> Dict[str, Any]:
    prompt = build_ui_preview_prompt(ui_schema, requirements)
    try:
        raw_response = ask_openrouter(prompt, temperature=0.2)
        parsed = extract_json_from_text(raw_response)
        return validate_preview(parsed)
    except Exception:
        return build_fallback_preview(ui_schema, requirements)
