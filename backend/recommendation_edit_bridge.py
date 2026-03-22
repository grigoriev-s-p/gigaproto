from __future__ import annotations

import re
from typing import Any

PURE_APPROVAL_VALUES = {
    "да",
    "давай",
    "ок",
    "окей",
    "хорошо",
    "сделай так",
    "да сделай так",
    "применяй",
    "согласен",
    "подходит",
    "можно",
    "погнали",
}

PURE_DECLINE_VALUES = {
    "нет",
    "нет спасибо",
    "не надо",
    "не нужно",
    "нет не надо",
    "нет не нужно",
    "не делай",
    "не применяй",
    "не стоит",
    "оставь как есть",
    "пока нет",
    "не хочу",
}

APPROVAL_PREFIX_RE = re.compile(
    r"^(?:ну\s+)?(?:да|давай|ок(?:ей)?|хорошо|согласен|подходит|можно|погнали)(?:\s+сделай\s+так|\s+применяй)?(?:\s*[,:-]\s*|\s+и\s+|\s+но\s+)?",
    re.IGNORECASE,
)

DECLINE_PREFIX_RE = re.compile(
    r"^(?:ну\s+)?(?:нет(?:\s+спасибо)?(?:\s+не\s+надо|\s+не\s+нужно)?|не\s+надо|не\s+нужно|не\s+применяй|не\s+делай|не\s+стоит|пока\s+нет|не\s+хочу|оставь\s+как\s+есть)(?:\s*[,:-]\s*|\s+но\s+|\s+просто\s+)?",
    re.IGNORECASE,
)


def _normalize(value: str) -> str:
    lowered = value.lower().replace("ё", "е")
    lowered = re.sub(r"[!?.,;:]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()



def _strip_prefix(text: str, regex: re.Pattern[str]) -> str:
    stripped = regex.sub("", text.strip(), count=1)
    return stripped.strip(" ,:-")



def _recommendations_to_text(recommendations: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(recommendations, start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or f"Идея {index}").strip()
        description = str(item.get("description") or "").strip()
        if description:
            lines.append(f"{index}. {title}: {description}")
        else:
            lines.append(f"{index}. {title}")
    return "\n".join(lines)



def resolve_edit_request(user_edit: str, pending_recommendations: list[dict[str, Any]] | None) -> dict[str, Any]:
    text = (user_edit or "").strip()
    recommendations = [item for item in (pending_recommendations or []) if isinstance(item, dict)]

    if not text:
        return {
            "mode": "noop",
            "edit_request": "",
            "applied_recommendations": False,
            "dismissed_recommendations": False,
        }

    normalized = _normalize(text)
    has_pending = bool(recommendations)

    if has_pending and normalized in PURE_DECLINE_VALUES:
        return {
            "mode": "decline",
            "edit_request": "",
            "applied_recommendations": False,
            "dismissed_recommendations": True,
            "summary": "Понял, мои рекомендации не применяю. Жду твоих правок к текущему прототипу.",
        }

    if has_pending and normalized in PURE_APPROVAL_VALUES:
        recommendation_block = _recommendations_to_text(recommendations)
        return {
            "mode": "apply_recommendations",
            "edit_request": (
                "Примени к текущему прототипу следующие ранее предложенные рекомендации. "
                "Нужно внести их как реальные правки интерфейса, а не просто описать текстом.\n\n"
                f"РЕКОМЕНДАЦИИ:\n{recommendation_block}"
            ),
            "applied_recommendations": True,
            "dismissed_recommendations": False,
        }

    if has_pending:
        declined_prefix = _strip_prefix(text, DECLINE_PREFIX_RE)
        if declined_prefix != text and declined_prefix:
            return {
                "mode": "user_edit_only",
                "edit_request": declined_prefix,
                "applied_recommendations": False,
                "dismissed_recommendations": True,
            }

        approved_prefix = _strip_prefix(text, APPROVAL_PREFIX_RE)
        if approved_prefix != text and approved_prefix:
            recommendation_block = _recommendations_to_text(recommendations)
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

    return {
        "mode": "user_edit_only",
        "edit_request": text,
        "applied_recommendations": False,
        "dismissed_recommendations": has_pending,
    }
