import ast
import json
import re
from typing import Any, Dict, List

from AI_client import ask_openrouter


ALLOWED_ELEMENT_TYPES = {
    "button",
    "input",
    "form",
    "table",
    "list",
    "card",
    "filters",
    "text",
    "chart",
}

ALLOWED_ACTION_TYPES = {"navigate", "submit", "download", "toggle", "filter"}


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


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or default
    return str(value)


def _slug(value: str, fallback: str) -> str:
    value = re.sub(r"[^a-zа-я0-9]+", "-", value.lower(), flags=re.IGNORECASE).strip("-")
    return value or fallback


def _ensure_unique(candidate: str, used: set[str], fallback: str) -> str:
    base = candidate or fallback
    current = base
    index = 2
    while current in used:
        current = f"{base}-{index}"
        index += 1
    used.add(current)
    return current


def _normalize_route(value: str, fallback_slug: str, used: set[str]) -> str:
    raw = value.strip() if value else ""
    if not raw.startswith("/"):
        raw = f"/{_slug(raw, fallback_slug)}" if raw else f"/{fallback_slug}"
    raw = re.sub(r"/+", "/", raw)
    return _ensure_unique(raw, used, f"/{fallback_slug}")


def _normalize_fields(fields: Any) -> List[str]:
    if not isinstance(fields, list):
        return []
    normalized: List[str] = []
    for index, field in enumerate(fields):
        label = _safe_text(field, f"Поле {index + 1}")
        if label and label not in normalized:
            normalized.append(label)
    return normalized


def _resolve_route_target(value: str, pages: List[Dict[str, Any]], current_route: str) -> str:
    if not value:
        return current_route

    lowered = value.strip().lower()
    route_part = lowered if lowered.startswith("/") else ""

    for page in pages:
        if page["route"].lower() == route_part:
            return page["route"]
        if page["id"].lower() == lowered:
            return page["route"]
        if page["name"].lower() == lowered:
            return page["route"]
        if page["name"].lower() in lowered or lowered in page["name"].lower():
            return page["route"]

    return current_route


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
- route у каждой страницы должен быть уникальным и начинаться с /
- если есть несколько страниц, добавляй навигационные button/action элементы с target на route другой страницы
- если есть список/история -> table или list
- если есть фильтры -> filters
- если есть детали -> отдельная страница
- если есть экспорт -> button + download
- не добавляй лишнего
- action для button должен быть либо route другой страницы, либо явным названием действия

REQUIREMENTS:
{json.dumps(requirements, ensure_ascii=False, separators=(",", ":"))}
"""


def normalize_ui_schema(raw_schema: Dict[str, Any]) -> Dict[str, Any]:
    pages_raw = raw_schema.get("pages") if isinstance(raw_schema.get("pages"), list) else []
    normalized_pages: List[Dict[str, Any]] = []
    used_ids: set[str] = set()
    used_routes: set[str] = set()

    for page_index, page in enumerate(pages_raw):
        if not isinstance(page, dict):
            continue

        page_name = _safe_text(page.get("name"), f"Страница {page_index + 1}")
        page_id = _ensure_unique(_slug(_safe_text(page.get("id"), page_name), f"page-{page_index + 1}"), used_ids, f"page-{page_index + 1}")
        page_route = _normalize_route(_safe_text(page.get("route"), f"/{page_id}"), page_id, used_routes)

        elements_raw = page.get("elements") if isinstance(page.get("elements"), list) else []
        elements: List[Dict[str, Any]] = []

        for element_index, element in enumerate(elements_raw):
            if not isinstance(element, dict):
                continue

            element_type = _safe_text(element.get("type"), "text")
            if element_type not in ALLOWED_ELEMENT_TYPES:
                element_type = "text"

            label = _safe_text(element.get("label"), f"Блок {element_index + 1}")
            normalized_element = {
                "type": element_type,
                "label": label,
                "description": _safe_text(element.get("description"), ""),
                "fields": _normalize_fields(element.get("fields")),
            }

            action = _safe_text(element.get("action"), "")
            if action:
                normalized_element["action"] = action

            elements.append(normalized_element)

        normalized_pages.append(
            {
                "id": page_id,
                "name": page_name,
                "route": page_route,
                "elements": elements,
            }
        )

    if not normalized_pages:
        normalized_pages = [
            {
                "id": "main",
                "name": "Главная",
                "route": "/",
                "elements": [
                    {
                        "type": "text",
                        "label": "Описание",
                        "description": "Не удалось извлечь ui_schema, нужна повторная генерация.",
                        "fields": [],
                    }
                ],
            }
        ]

    for page_index, page in enumerate(normalized_pages):
        page["elements"] = page.get("elements", [])

        for element in page["elements"]:
            if element["type"] == "button":
                element["action"] = _resolve_route_target(_safe_text(element.get("action"), element["label"]), normalized_pages, page["route"])

        has_navigation = any(
            element.get("type") == "button" and _resolve_route_target(_safe_text(element.get("action"), ""), normalized_pages, page["route"]) != page["route"]
            for element in page["elements"]
        )

        if len(normalized_pages) > 1 and not has_navigation:
            next_page = normalized_pages[(page_index + 1) % len(normalized_pages)]
            if next_page["route"] != page["route"]:
                page["elements"].append(
                    {
                        "type": "button",
                        "label": f"Перейти: {next_page['name']}",
                        "description": "Переход к следующему ключевому экрану сценария.",
                        "fields": [],
                        "action": next_page["route"],
                    }
                )

    actions_raw = raw_schema.get("actions") if isinstance(raw_schema.get("actions"), list) else []
    normalized_actions: List[Dict[str, Any]] = []
    used_action_ids: set[str] = set()

    for action_index, action in enumerate(actions_raw):
        if not isinstance(action, dict):
            continue

        action_type = _safe_text(action.get("type"), "navigate")
        if action_type not in ALLOWED_ACTION_TYPES:
            action_type = "navigate"

        action_id = _ensure_unique(_slug(_safe_text(action.get("id"), _safe_text(action.get("label"), f"action-{action_index + 1}")), f"action-{action_index + 1}"), used_action_ids, f"action-{action_index + 1}")
        label = _safe_text(action.get("label"), f"Действие {action_index + 1}")
        target = _resolve_route_target(_safe_text(action.get("target"), label), normalized_pages, normalized_pages[0]["route"])

        normalized_actions.append(
            {
                "id": action_id,
                "label": label,
                "type": action_type,
                "target": target,
            }
        )

    if not normalized_actions:
        normalized_actions = [
            {
                "id": f"navigate-{page['id']}",
                "label": page["name"],
                "type": "navigate",
                "target": page["route"],
            }
            for page in normalized_pages
        ]

    return {
        "pages": normalized_pages,
        "actions": normalized_actions,
    }


def ui_schema_agent(requirements: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_ui_schema_prompt(requirements)
    raw_response = ask_openrouter(prompt)
    parsed = extract_json_from_text(raw_response)
    return normalize_ui_schema(parsed)
