from __future__ import annotations

import json
from typing import Any

from AI_client import ask_openrouter
from ui_preview_agent import extract_json_from_text


Recommendation = dict[str, str]

RECOMMENDATION_RESPONSE_EXAMPLE = {
    "recommendations": [
        {
            "title": "Добавить явное пустое состояние в таблицу операций",
            "scope": "Страница «История операций» → блок «Таблица операций»",
            "priority": "high",
            "description": "Сейчас экран показывает только заполненную таблицу. На защите сценарий с пустой выборкой будет выглядеть незавершённым.",
            "edit_prompt": "На странице «История операций» в блоке «Таблица операций» добавь пустое состояние с коротким текстом о том, что по текущим фильтрам ничего не найдено, и вторичную кнопку для сброса фильтров.",
            "why_it_matters": "Это делает сценарий более реалистичным и улучшает демонстрацию UX-проработки.",
        }
    ]
}

ALLOWED_PRIORITIES = {"low", "medium", "high"}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_priority(value: Any) -> str:
    normalized = _safe_text(value).lower()
    if normalized in ALLOWED_PRIORITIES:
        return normalized
    if normalized in {"critical", "highest", "top", "urgent", "важно", "срочно"}:
        return "high"
    if normalized in {"normal", "default", "средний"}:
        return "medium"
    if normalized in {"minor", "small", "низкий"}:
        return "low"
    return "medium"


def _normalize_recommendation(item: Any, index: int) -> Recommendation | None:
    if not isinstance(item, dict):
        return None

    title = _safe_text(item.get("title")) or f"Рекомендация {index}"
    description = _safe_text(item.get("description"))
    edit_prompt = _safe_text(item.get("edit_prompt"))
    scope = _safe_text(item.get("scope")) or "Текущий прототип"
    priority = _normalize_priority(item.get("priority"))
    why_it_matters = _safe_text(item.get("why_it_matters"))

    if not description and why_it_matters:
        description = why_it_matters
    elif description and why_it_matters and why_it_matters.lower() not in description.lower():
        description = f"{description} {why_it_matters}".strip()

    if not edit_prompt:
        return None

    return {
        "title": title,
        "description": description,
        "edit_prompt": edit_prompt,
        "scope": scope,
        "priority": priority,
    }


def _normalize_recommendations(payload: Any) -> list[Recommendation]:
    if isinstance(payload, dict):
        raw_items = payload.get("recommendations")
        if not isinstance(raw_items, list):
            raw_items = []
    elif isinstance(payload, list):
        raw_items = payload
    else:
        raw_items = []

    normalized: list[Recommendation] = []
    seen: set[str] = set()

    for index, item in enumerate(raw_items, start=1):
        normalized_item = _normalize_recommendation(item, index)
        if not normalized_item:
            continue

        fingerprint = json.dumps(normalized_item, ensure_ascii=False, sort_keys=True)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        normalized.append(normalized_item)
        if len(normalized) >= 4:
            break

    return normalized


def _build_recommendation_prompt(
    requirements: dict[str, Any],
    ui_schema: dict[str, Any],
    ui_preview: dict[str, Any] | None,
) -> str:
    return f"""
Ты — AI-агент UX/UI-ревью текущего прототипа.

Твоя задача: не по правилам и не по шаблонным эвристикам, а как продуктовый AI-ревьюер проанализировать именно ТЕКУЩИЙ интерфейс и предложить 2-4 самых полезных улучшения.

Критично:
- Анализируй в первую очередь CURRENT_UI_PREVIEW, потому что рекомендации должны опираться на реально собранный интерфейс.
- CURRENT_UI_SCHEMA используй как дополнительный технический контекст.
- Не пиши абстрактные советы вроде «улучшить UX», «сделать современнее», «повысить удобство».
- Каждая рекомендация должна быть настолько конкретной, чтобы другой AI-агент мог сразу применить её к прототипу.
- Всегда указывай конкретную страницу, а если возможно — и конкретный блок/секцию.
- Предлагай только то, что можно выразить в текущем UI-прототипе: добавить/убрать/переставить блоки, состояния, фильтры, CTA, формы, действия, навигацию, карточки, таблицы, KPI, подтверждения, сообщения, визуальные акценты.
- Не предлагай изменения бэкенда, БД, интеграций, аналитики, авторизации, ролей или бизнес-процессов вне UI.
- Если прототип уже выглядит неплохо, всё равно выбери самые сильные точечные улучшения для защиты проекта.
- В description обязательно объясни, почему это улучшение важно именно для этого экрана.
- В edit_prompt пиши прямую инструкцию в императиве: что и где изменить.
- Приоритет только: high, medium или low.
- Верни только JSON без markdown и без пояснений.

Формат ответа:
{json.dumps(RECOMMENDATION_RESPONSE_EXAMPLE, ensure_ascii=False, indent=2)}

CURRENT_REQUIREMENTS:
{json.dumps(requirements, ensure_ascii=False, indent=2)}

CURRENT_UI_SCHEMA:
{json.dumps(ui_schema, ensure_ascii=False, indent=2)}

CURRENT_UI_PREVIEW:
{json.dumps(ui_preview or {}, ensure_ascii=False, indent=2)}
"""


def build_recommendations(
    requirements: dict[str, Any],
    ui_schema: dict[str, Any],
    ui_preview: dict[str, Any] | None = None,
) -> list[Recommendation]:
    prompt = _build_recommendation_prompt(requirements, ui_schema, ui_preview)

    try:
        raw_response = ask_openrouter(prompt, temperature=0.2)
        parsed = extract_json_from_text(raw_response)
        return _normalize_recommendations(parsed)
    except Exception:
        return []
