from __future__ import annotations

import json
from typing import Any

from AI_client import ask_openrouter
from ui_preview_agent import extract_json_from_text


BRIDGE_RESPONSE_EXAMPLE = {
    "decision": "apply_recommendations_with_user_edit",
    "selected_indexes": [1, 3],
    "user_edit": "Сделай кнопки компактнее и перенеси фильтры выше таблицы.",
    "summary": "Пользователь согласился применить выбранные рекомендации и добавил свои уточнения.",
}

ALLOWED_DECISIONS = {
    "noop",
    "decline_recommendations",
    "apply_recommendations",
    "apply_selected_recommendations",
    "apply_recommendations_with_user_edit",
    "user_edit_only",
}

<<<<<<< HEAD
=======
APPROVAL_PREFIX_RE = re.compile(
    r"^(?:ну\s+)?(?:да|давай|ок(?:ей)?|хорошо|согласен|подходит|можно|погнали)(?:\s*[,:-]?\s*сделай\s+так|\s*[,:-]?\s*применяй)?(?:\s*[,:-]\s*|\s+и\s+|\s+но\s+)?",
    re.IGNORECASE,
)
>>>>>>> 4568051 (Финальная версия для хакатона)

def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _recommendation_instruction(item: dict[str, Any], index: int) -> str:
    title = _safe_text(item.get("title")) or f"Рекомендация {index}"
    edit_prompt = _safe_text(item.get("edit_prompt"))
    description = _safe_text(item.get("description"))
    scope = _safe_text(item.get("scope"))

    details = [f"{index}. {title}"]
    if scope:
        details.append(f"Где: {scope}")
    if description:
        details.append(f"Почему: {description}")
    if edit_prompt:
        details.append(f"Что сделать: {edit_prompt}")
    return "\n".join(details)


def _recommendations_to_text(recommendations: list[dict[str, Any]]) -> str:
<<<<<<< HEAD
    return "\n\n".join(
        _recommendation_instruction(item, index)
        for index, item in enumerate(recommendations, start=1)
        if isinstance(item, dict)
    )
=======
    lines: list[str] = []
    for index, item in enumerate(recommendations, start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or f"Идея {index}").strip()
        description = str(item.get("description") or "").strip()
        rationale = str(item.get("rationale") or "").strip()
        apply_prompt = str(item.get("apply_prompt") or item.get("edit_prompt") or "").strip()

        parts = [f"{index}. {title}"]
        if description:
            parts.append(f"Что улучшить: {description}")
        if rationale:
            parts.append(f"Почему: {rationale}")
        if apply_prompt:
            parts.append(f"Как изменить: {apply_prompt}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)



def _recommendations_to_apply_instructions(recommendations: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(recommendations, start=1):
        if not isinstance(item, dict):
            continue
        apply_prompt = str(item.get("apply_prompt") or item.get("edit_prompt") or "").strip()
        if apply_prompt:
            lines.append(f"{index}. {apply_prompt}")
            continue

        title = str(item.get("title") or f"Идея {index}").strip()
        description = str(item.get("description") or "").strip()
        combined = ": ".join(part for part in [title, description] if part)
        if combined:
            lines.append(f"{index}. {combined}")
    return "\n".join(lines)
>>>>>>> 4568051 (Финальная версия для хакатона)


def _normalize_indexes(indexes: Any, total: int) -> list[int]:
    if not isinstance(indexes, list) or total <= 0:
        return []

    normalized: list[int] = []
    for raw_value in indexes:
        try:
            value = int(raw_value)
        except Exception:
            continue
        if 1 <= value <= total and value not in normalized:
            normalized.append(value)
    return normalized


def _select_recommendations(recommendations: list[dict[str, Any]], indexes: list[int]) -> list[dict[str, Any]]:
    if not indexes:
        return recommendations
    return [recommendations[index - 1] for index in indexes if 1 <= index <= len(recommendations)]


def _build_bridge_prompt(user_edit: str, recommendations: list[dict[str, Any]]) -> str:
    return f"""
Ты — AI-агент, который интерпретирует ответ пользователя на рекомендации по UI-прототипу.

Тебе нужно понять, что пользователь имел в виду:
- он отклоняет рекомендации;
- он хочет применить все рекомендации;
- он хочет применить только часть рекомендаций;
- он хочет применить рекомендации и дополнительно внести свои правки;
- он хочет проигнорировать рекомендации и выполнить только свои правки.

Важно:
- Ориентируйся на смысл, а не на ключевые слова и не на шаблонные регулярки.
- Если пользователь явно пишет, что рекомендации не нужны, выбери decline_recommendations или user_edit_only.
- Если пользователь соглашается и одновременно добавляет свои уточнения, выбери apply_recommendations_with_user_edit.
- Если пользователь ссылается на конкретные номера рекомендаций, заполни selected_indexes.
- Если пользователь просто пишет свою новую правку и не подтверждает рекомендации, выбери user_edit_only.
- Если pending recommendations пусты, верни user_edit_only или noop.
- Возвращай только JSON без markdown.

Формат ответа:
{json.dumps(BRIDGE_RESPONSE_EXAMPLE, ensure_ascii=False, indent=2)}

Допустимые decision:
- noop
- decline_recommendations
- apply_recommendations
- apply_selected_recommendations
- apply_recommendations_with_user_edit
- user_edit_only

PENDING_RECOMMENDATIONS:
{_recommendations_to_text(recommendations) or 'Нет рекомендаций.'}

USER_MESSAGE:
{user_edit}
"""


def resolve_edit_request(user_edit: str, pending_recommendations: list[dict[str, Any]] | None) -> dict[str, Any]:
    text = _safe_text(user_edit)
    recommendations = [item for item in (pending_recommendations or []) if isinstance(item, dict)]

    if not text:
        return {
            "mode": "noop",
            "edit_request": "",
            "applied_recommendations": False,
            "dismissed_recommendations": False,
        }

    if not recommendations:
        return {
            "mode": "user_edit_only",
            "edit_request": text,
            "applied_recommendations": False,
            "dismissed_recommendations": False,
        }

    try:
        raw_response = ask_openrouter(_build_bridge_prompt(text, recommendations), temperature=0.0)
        parsed = extract_json_from_text(raw_response)
    except Exception:
        return {
            "mode": "user_edit_only",
            "edit_request": text,
            "applied_recommendations": False,
            "dismissed_recommendations": False,
        }

    decision = _safe_text(parsed.get("decision"))
    if decision not in ALLOWED_DECISIONS:
        decision = "user_edit_only"

    selected_indexes = _normalize_indexes(parsed.get("selected_indexes"), len(recommendations))
    selected_recommendations = _select_recommendations(recommendations, selected_indexes)
    recommendation_block = _recommendations_to_text(selected_recommendations)
    user_edit_only_text = _safe_text(parsed.get("user_edit")) or text
    summary = _safe_text(parsed.get("summary"))

    if decision == "noop":
        return {
            "mode": "noop",
            "edit_request": "",
            "applied_recommendations": False,
            "dismissed_recommendations": False,
        }

    if decision == "decline_recommendations":
        return {
            "mode": "decline",
            "edit_request": "",
            "applied_recommendations": False,
            "dismissed_recommendations": True,
            "summary": summary or "Понял, рекомендации не применяю. Жду твоих точечных правок к текущему прототипу.",
        }

<<<<<<< HEAD
    if decision == "apply_recommendations":
=======
    if has_pending and normalized in PURE_APPROVAL_VALUES:
        recommendation_block = _recommendations_to_apply_instructions(recommendations)
>>>>>>> 4568051 (Финальная версия для хакатона)
        return {
            "mode": "apply_recommendations",
            "edit_request": (
                "Примени к текущему прототипу следующие рекомендации от AI-агента. "
                "Нужно внести их как реальные изменения интерфейса, а не описывать словами.\n\n"
                f"РЕКОМЕНДАЦИИ:\n{recommendation_block}"
            ),
            "applied_recommendations": True,
            "dismissed_recommendations": False,
        }

    if decision == "apply_selected_recommendations":
        return {
            "mode": "apply_selected_recommendations",
            "edit_request": (
                "Примени только выбранные рекомендации от AI-агента к текущему прототипу. "
                "Нужно внести их как реальные изменения интерфейса.\n\n"
                f"ВЫБРАННЫЕ РЕКОМЕНДАЦИИ:\n{recommendation_block}"
            ),
            "applied_recommendations": True,
            "dismissed_recommendations": False,
        }

<<<<<<< HEAD
    if decision == "apply_recommendations_with_user_edit":
        return {
            "mode": "apply_recommendations_with_user_edit",
            "edit_request": (
                "Сначала учти следующие рекомендации от AI-агента, а затем дополнительно выполни явные указания пользователя. "
                "Если есть конфликт, приоритет всегда у явных указаний пользователя.\n\n"
                f"РЕКОМЕНДАЦИИ:\n{recommendation_block}\n\n"
                f"УКАЗАНИЯ ПОЛЬЗОВАТЕЛЯ:\n{user_edit_only_text}"
            ),
            "applied_recommendations": True,
            "dismissed_recommendations": False,
        }
=======
        approved_prefix = _strip_prefix(text, APPROVAL_PREFIX_RE)
        if approved_prefix != text and approved_prefix:
            recommendation_block = _recommendations_to_apply_instructions(recommendations)
            return {
                "mode": "apply_recommendations_with_user_edit",
                "edit_request": (
                    "Сначала учти следующие ранее предложенные рекомендации, "
                    "а затем дополнительно выполни явные указания пользователя. "
                    "Если есть конфликт, приоритет всегда у явных указаний пользователя.\n\n"
                    f"РЕКОМЕНДАЦИИ:\n{recommendation_block}\n\n"
                    f"УКАЗАНИЯ ПОЛЬЗОВАТЕЛЯ:\n{approved_prefix}"
                ),
                "applied_recommendations": True,
                "dismissed_recommendations": False,
            }
>>>>>>> 4568051 (Финальная версия для хакатона)

    return {
        "mode": "user_edit_only",
        "edit_request": user_edit_only_text,
        "applied_recommendations": False,
        "dismissed_recommendations": True,
    }
