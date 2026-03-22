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

DESIGN_PRESETS: Dict[str, Dict[str, Any]] = {
    "finance": {
        "preset": "banking-green",
        "mood": "Спокойный финансовый интерфейс с акцентом на надёжность и ясность.",
        "theme": "light",
        "background": "#f4fbf7",
        "surface": "#ffffff",
        "surfaceAlt": "#eef7f1",
        "text": "#153528",
        "mutedText": "#60786b",
        "primary": "#1b9b5f",
        "primaryText": "#ffffff",
        "accent": "#0f7f59",
        "border": "rgba(27, 155, 95, 0.16)",
        "shadow": "0 24px 60px rgba(16, 74, 48, 0.12)",
        "radius": 22,
    },
    "medical": {
        "preset": "medical-red",
        "mood": "Чистый медицинский интерфейс с белой базой и аккуратными красными акцентами.",
        "theme": "light",
        "background": "#fff8f8",
        "surface": "#ffffff",
        "surfaceAlt": "#fff0f1",
        "text": "#40282c",
        "mutedText": "#88666b",
        "primary": "#d44c5c",
        "primaryText": "#ffffff",
        "accent": "#a43746",
        "border": "rgba(212, 76, 92, 0.16)",
        "shadow": "0 24px 60px rgba(132, 39, 52, 0.12)",
        "radius": 22,
    },
    "education": {
        "preset": "education-blue",
        "mood": "Дружелюбный учебный интерфейс с мягкими синими акцентами.",
        "theme": "light",
        "background": "#f6f9ff",
        "surface": "#ffffff",
        "surfaceAlt": "#edf4ff",
        "text": "#1a2f52",
        "mutedText": "#64779a",
        "primary": "#4a7cf3",
        "primaryText": "#ffffff",
        "accent": "#335fd4",
        "border": "rgba(74, 124, 243, 0.16)",
        "shadow": "0 24px 60px rgba(51, 95, 212, 0.12)",
        "radius": 22,
    },
    "retail": {
        "preset": "retail-orange",
        "mood": "Тёплый коммерческий интерфейс с насыщенными оранжевыми акцентами.",
        "theme": "light",
        "background": "#fffaf4",
        "surface": "#ffffff",
        "surfaceAlt": "#fff3e5",
        "text": "#402d1f",
        "mutedText": "#866a53",
        "primary": "#ef8f2f",
        "primaryText": "#ffffff",
        "accent": "#d06b11",
        "border": "rgba(239, 143, 47, 0.16)",
        "shadow": "0 24px 60px rgba(208, 107, 17, 0.12)",
        "radius": 22,
    },
    "tech": {
        "preset": "tech-indigo",
        "mood": "Современный технологичный интерфейс с контрастными индиго-акцентами.",
        "theme": "dark",
        "background": "#0f1220",
        "surface": "#171b2e",
        "surfaceAlt": "#1d2238",
        "text": "#f4f6ff",
        "mutedText": "#b4bcde",
        "primary": "#6f7cff",
        "primaryText": "#ffffff",
        "accent": "#31c4ff",
        "border": "rgba(111, 124, 255, 0.18)",
        "shadow": "0 24px 60px rgba(9, 12, 24, 0.45)",
        "radius": 22,
    },
    "generic": {
        "preset": "neutral-teal",
        "mood": "Нейтральный продуктовый интерфейс с мягкими бирюзовыми акцентами.",
        "theme": "light",
        "background": "#f7faf8",
        "surface": "#ffffff",
        "surfaceAlt": "#eef7f4",
        "text": "#1d322d",
        "mutedText": "#677c76",
        "primary": "#259b82",
        "primaryText": "#ffffff",
        "accent": "#1c7d6b",
        "border": "rgba(37, 155, 130, 0.16)",
        "shadow": "0 24px 60px rgba(28, 87, 75, 0.12)",
        "radius": 22,
    },
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
        cleaned = value.strip()
        return cleaned or default
    return str(value)


def _slug(value: str, fallback: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.IGNORECASE)
    value = value.strip("-")
    return value or fallback


def _field_objects(fields: Any) -> List[Dict[str, Any]]:
    if not isinstance(fields, list):
        return []

    result: List[Dict[str, Any]] = []
    for index, field in enumerate(fields):
        if isinstance(field, dict):
            label = _safe_text(field.get("label"), _safe_text(field.get("name"), f"Поле {index + 1}"))
            name = _slug(_safe_text(field.get("name"), label), f"field-{index + 1}")
            field_type = _safe_text(field.get("type"), "text")
            placeholder = _safe_text(field.get("placeholder"), label)
            options = field.get("options") if isinstance(field.get("options"), list) else None
            normalized: Dict[str, Any] = {
                "name": name,
                "label": label,
                "type": field_type,
                "placeholder": placeholder,
            }
            if options:
                normalized["options"] = [_safe_text(option) for option in options if _safe_text(option)]
            result.append(normalized)
            continue

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


def _table_rows(columns: List[str], description: str, page_name: str) -> List[List[str]]:
    if not columns:
        columns = ["Поле 1", "Поле 2", "Поле 3"]

    lowered = " ".join([page_name, description, " ".join(columns)]).lower()

    if any(keyword in lowered for keyword in ["операц", "транзак", "плат", "сч", "card", "банк", "amount", "sum"]):
        source_rows = [
            {"date": "2026-03-18", "name": "Покупка в магазине", "status": "Завершено", "amount": "1 250"},
            {"date": "2026-03-21", "name": "Онлайн-подписка", "status": "В обработке", "amount": "499"},
            {"date": "2026-03-16", "name": "Перевод между счетами", "status": "Завершено", "amount": "3 200"},
            {"date": "2026-03-19", "name": "Пополнение карты", "status": "Черновик", "amount": "900"},
        ]
    elif any(keyword in lowered for keyword in ["заказ", "товар", "каталог", "доставка"]):
        source_rows = [
            {"date": "2026-03-18", "name": "Заказ #1042", "status": "В пути", "amount": "4 800"},
            {"date": "2026-03-15", "name": "Заказ #1039", "status": "Доставлен", "amount": "1 990"},
            {"date": "2026-03-20", "name": "Заказ #1044", "status": "Собирается", "amount": "2 450"},
            {"date": "2026-03-14", "name": "Заказ #1036", "status": "Отменён", "amount": "750"},
        ]
    else:
        source_rows = [
            {"date": "2026-03-18", "name": f"{page_name} — запись 1", "status": "В обработке", "amount": "120"},
            {"date": "2026-03-21", "name": f"{page_name} — запись 2", "status": "Завершено", "amount": "340"},
            {"date": "2026-03-16", "name": description[:36] or f"{page_name} — запись 3", "status": "Черновик", "amount": "210"},
            {"date": "2026-03-19", "name": f"{page_name} — запись 4", "status": "Новый", "amount": "450"},
        ]

    rows: List[List[str]] = []
    for record in source_rows:
        row: List[str] = []
        for column in columns:
            key = column.lower()
            if any(token in key for token in ["дат", "date", "time"]):
                row.append(record["date"])
            elif any(token in key for token in ["сум", "amount", "price", "стоим"]):
                row.append(record["amount"])
            elif any(token in key for token in ["стат", "status"]):
                row.append(record["status"])
            else:
                row.append(record["name"])
        rows.append(row)

    return rows



def _cards_from_description(label: str, description: str, route: str) -> List[Dict[str, Any]]:
    return [
        {
            "title": label or "Карточка",
            "description": description or "Описание элемента интерфейса",
            "meta": ["Демо-данные", route],
        },
        {
            "title": f"{label or 'Блок'} — состояние",
            "description": "Карточка показывает типовой сценарий и основные статусы этого блока.",
            "meta": ["Preview", "Автогенерация"],
        },
    ]


def _page_descriptors(ui_schema: Dict[str, Any], preview: Dict[str, Any] | None = None) -> List[Dict[str, str]]:
    pages: List[Dict[str, str]] = []
    source_pages = ui_schema.get("pages") if isinstance(ui_schema.get("pages"), list) else []
    if not source_pages and preview and isinstance(preview.get("pages"), list):
        source_pages = preview.get("pages")

    for index, page in enumerate(source_pages):
        if not isinstance(page, dict):
            continue
        page_name = _safe_text(page.get("name"), f"Страница {index + 1}")
        page_id = _safe_text(page.get("id"), _slug(page_name, f"page-{index + 1}"))
        route = _safe_text(page.get("route"), f"/{_slug(page_id, f'page-{index + 1}')}")
        if not route.startswith("/"):
            route = f"/{_slug(route, page_id)}"
        pages.append({"id": page_id, "name": page_name, "route": route})
    return pages


def infer_design(requirements: Dict[str, Any], ui_schema: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(
        [
            json.dumps(requirements, ensure_ascii=False),
            json.dumps(ui_schema, ensure_ascii=False),
        ]
    ).lower()

    if any(keyword in text for keyword in ["банк", "банков", "finance", "финанс", "card", "счёт", "счет", "транзак", "платеж"]):
        return DESIGN_PRESETS["finance"].copy()
    if any(keyword in text for keyword in ["мед", "клиник", "health", "doctor", "пациент", "hospital"]):
        return DESIGN_PRESETS["medical"].copy()
    if any(keyword in text for keyword in ["школ", "курс", "education", "студент", "обуч", "lesson"]):
        return DESIGN_PRESETS["education"].copy()
    if any(keyword in text for keyword in ["магаз", "retail", "ecommerce", "товар", "каталог", "заказ"]):
        return DESIGN_PRESETS["retail"].copy()
    if any(keyword in text for keyword in ["saas", "crm", "platform", "панель", "dashboard", "ai", "dev", "tech"]):
        return DESIGN_PRESETS["tech"].copy()
    return DESIGN_PRESETS["generic"].copy()


def _find_target(value: str, pages: List[Dict[str, str]], current_route: str) -> str:
    if not value:
        return current_route

    lowered = value.strip().lower()
    route_part = lowered.split("#")[0]

    for page in pages:
        if page["route"].lower() == route_part:
            return page["route"]
        if page["id"].lower() == route_part:
            return page["route"]
        if page["name"].lower() == route_part:
            return page["route"]
        if page["name"].lower() in lowered or lowered in page["name"].lower():
            return page["route"]
        if _slug(page["name"], page["id"]) == _slug(route_part, page["id"]):
            return page["route"]

    return current_route


def _hero_actions(current_page: Dict[str, str], pages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    other_pages = [page for page in pages if page["route"] != current_page["route"]]
    if not other_pages:
        return [{"label": "Основной сценарий", "type": "primary", "target": current_page["route"]}]

    actions: List[Dict[str, str]] = [
        {
            "label": f"Открыть {other_pages[0]['name']}",
            "type": "primary",
            "target": other_pages[0]["route"],
        }
    ]

    for extra_page in other_pages[1:3]:
        actions.append(
            {
                "label": extra_page["name"],
                "type": "secondary",
                "target": extra_page["route"],
            }
        )

    return actions


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
    "primaryAction": "string",
    "design": {{
      "preset": "string",
      "mood": "string",
      "theme": "light|dark",
      "background": "string",
      "surface": "string",
      "surfaceAlt": "string",
      "text": "string",
      "mutedText": "string",
      "primary": "string",
      "primaryText": "string",
      "accent": "string",
      "border": "string",
      "shadow": "string",
      "radius": "string|number"
    }}
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
- Все навигационные action.target должны ссылаться на существующий route или id страницы.
- Для одного прототипа используй один единый дизайн. Подбирай его ассоциативно по домену: finance -> зелёный/светлый, medical -> бело-красный, education -> синий, retail -> тёплый оранжевый, tech -> тёмный индиго.

REQUIREMENTS:
{json.dumps(requirements, ensure_ascii=False)}

UI_SCHEMA:
{json.dumps(ui_schema, ensure_ascii=False)}
"""


def build_fallback_preview(ui_schema: Dict[str, Any], requirements: Dict[str, Any] | None = None) -> Dict[str, Any]:
    requirements = requirements or {}
    pages = _page_descriptors(ui_schema)
    design = infer_design(requirements, ui_schema)

    app_title = (
        requirements.get("meta", {}).get("title")
        if isinstance(requirements.get("meta"), dict)
        else None
    ) or requirements.get("screen_name") or "Сгенерированный интерфейс"

    preview_pages: List[Dict[str, Any]] = []
    schema_pages = ui_schema.get("pages") if isinstance(ui_schema.get("pages"), list) else []

    for page_index, page in enumerate(schema_pages):
        if not isinstance(page, dict):
            continue

        page_name = _safe_text(page.get("name"), f"Страница {page_index + 1}")
        page_id = _safe_text(page.get("id"), f"page-{page_index + 1}")
        route = _safe_text(page.get("route"), f"/{page_id}")
        if not route.startswith("/"):
            route = f"/{_slug(route, page_id)}"
        elements = page.get("elements") if isinstance(page.get("elements"), list) else []
        descriptor = {"id": page_id, "name": page_name, "route": route}

        sections: List[Dict[str, Any]] = [
            {
                "id": f"{page_id}-hero",
                "kind": "hero",
                "title": page_name,
                "description": f"Демо-предпросмотр экрана «{page_name}», собранный из требований и ui_schema.",
                "actions": _hero_actions(descriptor, pages),
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
            target = _find_target(_safe_text(element.get("action"), label), pages, route)

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
                        "actions": [
                            {"label": "Применить", "type": "primary", "target": route},
                            {"label": "Открыть результат", "type": "secondary", "target": target},
                        ],
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
                        "actions": [
                            {"label": "Сохранить", "type": "primary", "target": route},
                            {"label": "Следующий экран", "type": "secondary", "target": target},
                        ],
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
                        "rows": _table_rows(columns, description, page_name),
                    }
                )
            elif element_type == "list":
                sections.append(
                    {
                        "id": section_id,
                        "kind": "list",
                        "title": label,
                        "description": description or "Список элементов для просмотра.",
                        "bullets": [field["label"] for field in fields] or [
                            f"{label}: первый элемент",
                            f"{label}: второй элемент",
                            f"{label}: третий элемент",
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
                        "cards": _cards_from_description(label, description, route),
                    }
                )
            elif element_type == "chart":
                sections.append(
                    {
                        "id": section_id,
                        "kind": "chart",
                        "title": label,
                        "description": description or "Графический блок для аналитики и трендов.",
                        "bullets": ["Рост показателя", "Ключевые пики", "Сравнение сегментов"],
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
                                "target": target,
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

        if len(pages) > 1:
            navigation_actions = [
                {
                    "label": next_page["name"],
                    "type": "primary" if index == 0 else "secondary",
                    "target": next_page["route"],
                }
                for index, next_page in enumerate(pages)
                if next_page["route"] != route
            ][:4]
            if navigation_actions:
                sections.append(
                    {
                        "id": f"{page_id}-navigation",
                        "kind": "actions",
                        "title": "Навигация по прототипу",
                        "description": "Переходы между основными экранами бизнес-сценария.",
                        "actions": navigation_actions,
                    }
                )

        preview_pages.append(
            {
                "id": page_id,
                "name": page_name,
                "route": route,
                "summary": f"Страница {page_name} с {max(len(sections) - 1, 0)} основными блоками и кликабельной навигацией.",
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
            "subtitle": design["mood"],
            "theme": design["theme"],
            "primaryAction": "Открыть сценарий",
            "design": design,
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


def normalize_preview(preview: Dict[str, Any], ui_schema: Dict[str, Any], requirements: Dict[str, Any] | None = None) -> Dict[str, Any]:
    requirements = requirements or {}
    pages_index = _page_descriptors(ui_schema, preview)
    design = infer_design(requirements, ui_schema)

    app = preview.get("app") if isinstance(preview.get("app"), dict) else {}
    incoming_design = app.get("design") if isinstance(app.get("design"), dict) else {}
    merged_design = {**design, **incoming_design}

    normalized_pages: List[Dict[str, Any]] = []
    preview_pages = preview.get("pages") if isinstance(preview.get("pages"), list) else []

    for page_index, page in enumerate(preview_pages):
        if not isinstance(page, dict):
            continue

        fallback_descriptor = pages_index[page_index] if page_index < len(pages_index) else {
            "id": f"page-{page_index + 1}",
            "name": f"Страница {page_index + 1}",
            "route": f"/page-{page_index + 1}",
        }
        page_id = _safe_text(page.get("id"), fallback_descriptor["id"])
        page_name = _safe_text(page.get("name"), fallback_descriptor["name"])
        route = _find_target(_safe_text(page.get("route"), fallback_descriptor["route"]), pages_index, fallback_descriptor["route"])
        sections_raw = page.get("sections") if isinstance(page.get("sections"), list) else []

        normalized_sections: List[Dict[str, Any]] = []

        for section_index, section in enumerate(sections_raw):
            if not isinstance(section, dict):
                continue

            kind = _safe_text(section.get("kind"), "text")
            if kind not in SECTION_KINDS:
                kind = "text"

            section_id = _safe_text(section.get("id"), f"{page_id}-section-{section_index + 1}")
            title = _safe_text(section.get("title"), f"Блок {section_index + 1}")
            description = _safe_text(section.get("description"), "")

            normalized_section: Dict[str, Any] = {
                "id": section_id,
                "kind": kind,
                "title": title,
            }
            if description:
                normalized_section["description"] = description

            if kind in {"filters", "form"}:
                fields = _field_objects(section.get("fields"))
                if not fields:
                    fields = [
                        {"name": "value", "label": "Значение", "type": "text", "placeholder": "Введите значение"}
                    ]
                normalized_section["fields"] = fields

            if kind == "table":
                columns = [
                    _safe_text(column, f"Колонка {column_index + 1}")
                    for column_index, column in enumerate(section.get("columns", []))
                ] if isinstance(section.get("columns"), list) else []
                if not columns:
                    columns = ["Название", "Статус", "Дата"]
                rows = section.get("rows") if isinstance(section.get("rows"), list) else []
                normalized_rows: List[List[str]] = []
                for row in rows:
                    if isinstance(row, list):
                        normalized_rows.append([_safe_text(cell, "—") for cell in row])
                if not normalized_rows:
                    normalized_rows = _table_rows(columns, description, page_name)
                normalized_section["columns"] = columns
                normalized_section["rows"] = normalized_rows

            if kind in {"text", "list", "chart"}:
                bullets = [_safe_text(item) for item in section.get("bullets", [])] if isinstance(section.get("bullets"), list) else []
                normalized_section["bullets"] = bullets or [description or f"Контент блока {title}"]

            if kind == "cardGrid":
                cards = section.get("cards") if isinstance(section.get("cards"), list) else []
                normalized_cards: List[Dict[str, Any]] = []
                for card in cards:
                    if not isinstance(card, dict):
                        continue
                    normalized_cards.append(
                        {
                            "title": _safe_text(card.get("title"), title),
                            "description": _safe_text(card.get("description"), description or "Описание карточки"),
                            "meta": [_safe_text(item) for item in card.get("meta", [])] if isinstance(card.get("meta"), list) else [],
                        }
                    )
                normalized_section["cards"] = normalized_cards or _cards_from_description(title, description, route)

            if kind in {"hero", "actions", "filters", "form"}:
                actions_raw = section.get("actions") if isinstance(section.get("actions"), list) else []
                actions: List[Dict[str, Any]] = []
                for action_index, action in enumerate(actions_raw):
                    if not isinstance(action, dict):
                        continue
                    label = _safe_text(action.get("label"), f"Действие {action_index + 1}")
                    action_type = _safe_text(action.get("type"), "primary")
                    if action_type not in {"primary", "secondary"}:
                        action_type = "primary"
                    target = _find_target(_safe_text(action.get("target"), label), pages_index, route)
                    actions.append({"label": label, "type": action_type, "target": target})

                if not actions:
                    if kind == "hero":
                        actions = _hero_actions({"id": page_id, "name": page_name, "route": route}, pages_index)
                    elif kind == "actions":
                        actions = [
                            {"label": next_page["name"], "type": "primary" if index == 0 else "secondary", "target": next_page["route"]}
                            for index, next_page in enumerate(pages_index)
                            if next_page["route"] != route
                        ][:4] or [{"label": "Продолжить", "type": "primary", "target": route}]
                    elif kind == "filters":
                        actions = [{"label": "Применить", "type": "primary", "target": route}]
                    else:
                        actions = [{"label": "Сохранить", "type": "primary", "target": route}]

                normalized_section["actions"] = actions

            normalized_sections.append(normalized_section)

        if not normalized_sections or normalized_sections[0].get("kind") != "hero":
            normalized_sections.insert(
                0,
                {
                    "id": f"{page_id}-hero",
                    "kind": "hero",
                    "title": page_name,
                    "description": f"Основной обзор экрана «{page_name}».",
                    "actions": _hero_actions({"id": page_id, "name": page_name, "route": route}, pages_index),
                },
            )

        has_cross_navigation = any(
            action.get("target") != route
            for section in normalized_sections
            for action in section.get("actions", []) if isinstance(section, dict)
        )

        if len(pages_index) > 1 and not has_cross_navigation:
            normalized_sections.append(
                {
                    "id": f"{page_id}-navigation",
                    "kind": "actions",
                    "title": "Переходы между страницами",
                    "description": "Кликабельные кнопки для перехода по основным сценариям.",
                    "actions": [
                        {
                            "label": next_page["name"],
                            "type": "primary" if index == 0 else "secondary",
                            "target": next_page["route"],
                        }
                        for index, next_page in enumerate(pages_index)
                        if next_page["route"] != route
                    ][:4],
                }
            )

        normalized_pages.append(
            {
                "id": page_id,
                "name": page_name,
                "route": route,
                "summary": _safe_text(page.get("summary"), f"Страница {page_name} с рабочими переходами и единым визуальным стилем."),
                "sections": normalized_sections,
            }
        )

    if not normalized_pages:
        return build_fallback_preview(ui_schema, requirements)

    app_title = _safe_text(app.get("title"), requirements.get("screen_name") or "Сгенерированный интерфейс")
    subtitle = _safe_text(app.get("subtitle"), merged_design.get("mood", "Готовый интерактивный прототип"))

    return {
        "app": {
            "title": app_title,
            "subtitle": subtitle,
            "theme": _safe_text(app.get("theme"), merged_design.get("theme", "light")),
            "primaryAction": _safe_text(app.get("primaryAction"), "Открыть сценарий"),
            "design": merged_design,
        },
        "pages": normalized_pages,
    }


def ui_preview_agent(ui_schema: Dict[str, Any], requirements: Dict[str, Any] | None = None) -> Dict[str, Any]:
    prompt = build_ui_preview_prompt(ui_schema, requirements)
    try:
        raw_response = ask_openrouter(prompt, temperature=0.2)
        parsed = extract_json_from_text(raw_response)
        validated = validate_preview(parsed)
        return normalize_preview(validated, ui_schema, requirements)
    except Exception:
        fallback = build_fallback_preview(ui_schema, requirements)
        return normalize_preview(fallback, ui_schema, requirements)
