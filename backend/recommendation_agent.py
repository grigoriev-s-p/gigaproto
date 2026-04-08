from __future__ import annotations

import ast
import json
import re
from typing import Any, Dict, List

from AI_client import ask_openrouter

def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or default
    return str(value)


def _slug(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^a-zа-я0-9]+", "-", (value or "").strip().lower(), flags=re.IGNORECASE)
    normalized = normalized.strip("-")
    return normalized or fallback


def _extract_json_object(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("recommendation JSON не найден")

    payload = raw[start:end + 1]

    try:
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    parsed = ast.literal_eval(payload)
    if isinstance(parsed, dict):
        return parsed

    raise ValueError("recommendation JSON не удалось распарсить")


def _page_has_kind(ui_preview: Dict[str, Any], section_kind: str) -> bool:
    pages = ui_preview.get("pages") if isinstance(ui_preview.get("pages"), list) else []
    for page in pages:
        if not isinstance(page, dict):
            continue
        for section in page.get("sections", []) or []:
            if isinstance(section, dict) and _safe_text(section.get("kind")).lower() == section_kind.lower():
                return True
    return False


def _page_has_schema_type(ui_schema: Dict[str, Any], element_type: str) -> bool:
    pages = ui_schema.get("pages") if isinstance(ui_schema.get("pages"), list) else []
    for page in pages:
        if not isinstance(page, dict):
            continue
        for element in page.get("elements", []) or []:
            if isinstance(element, dict) and _safe_text(element.get("type")).lower() == element_type.lower():
                return True
    return False


def _section_counts(ui_preview: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    pages = ui_preview.get("pages") if isinstance(ui_preview.get("pages"), list) else []
    for page in pages:
        if not isinstance(page, dict):
            continue
        for section in page.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            kind = _safe_text(section.get("kind")).lower()
            if kind:
                counts[kind] = counts.get(kind, 0) + 1
    return counts


def _build_context_summary(requirements: Dict[str, Any], ui_schema: Dict[str, Any], ui_preview: Dict[str, Any]) -> Dict[str, Any]:
    meta = requirements.get("meta") if isinstance(requirements.get("meta"), dict) else {}
    basic = []
    additional = []
    functional = requirements.get("functional_requirements") if isinstance(requirements.get("functional_requirements"), dict) else {}
    if isinstance(functional.get("basic"), list):
        basic = [_safe_text(item) for item in functional.get("basic", []) if _safe_text(item)]
    if isinstance(functional.get("additional"), list):
        additional = [_safe_text(item) for item in functional.get("additional", []) if _safe_text(item)]

    pages = []
    preview_pages = ui_preview.get("pages") if isinstance(ui_preview.get("pages"), list) else []
    for page in preview_pages:
        if not isinstance(page, dict):
            continue
        sections = []
        for section in page.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            sections.append({
                "id": _safe_text(section.get("id")),
                "kind": _safe_text(section.get("kind")),
                "title": _safe_text(section.get("title")),
            })
        pages.append({
            "id": _safe_text(page.get("id")),
            "name": _safe_text(page.get("name")),
            "route": _safe_text(page.get("route")),
            "sections": sections,
        })

    actions = []
    for action in ui_schema.get("actions", []) if isinstance(ui_schema.get("actions"), list) else []:
        if isinstance(action, dict):
            actions.append({
                "label": _safe_text(action.get("label")),
                "type": _safe_text(action.get("type")),
                "target": _safe_text(action.get("target")),
            })

    return {
        "meta": {
            "title": _safe_text(meta.get("title")),
            "domain": _safe_text(meta.get("domain")),
        },
        "product_goal": _safe_text(requirements.get("product_goal")),
        "basic_requirements": basic[:8],
        "additional_requirements": additional[:8],
        "pages": pages[:8],
        "actions": actions[:12],
        "section_counts": _section_counts(ui_preview),
    }


def _normalize_priority(value: Any) -> str:
    normalized = _safe_text(value).lower()
    if normalized in {"high", "medium", "low"}:
        return normalized
    if normalized in {"высокий", "high priority", "critical"}:
        return "high"
    if normalized in {"низкий", "minor"}:
        return "low"
    return "medium"


def _normalize_recommendation(item: Any, index: int) -> Dict[str, str] | None:
    if not isinstance(item, dict):
        return None

    title = _safe_text(item.get("title"), f"Улучшение {index + 1}")
    description = _safe_text(item.get("description"))
    rationale = _safe_text(item.get("rationale"))
    impact = _safe_text(item.get("impact"))
    apply_prompt = _safe_text(item.get("apply_prompt") or item.get("edit_prompt"))

    if not description and rationale:
        description = rationale
    if not rationale and description:
        rationale = description
    if not apply_prompt:
        apply_prompt = description or rationale or title

    return {
        "id": _slug(_safe_text(item.get("id"), title), f"rec-{index + 1}"),
        "priority": _normalize_priority(item.get("priority")),
        "title": title,
        "description": description or title,
        "rationale": rationale or description or title,
        "impact": impact or "Повысит понятность интерфейса и качество сценария.",
        "apply_prompt": apply_prompt,
    }


def _deduplicate_recommendations(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    result: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (
            _safe_text(item.get("title")).lower(),
            _safe_text(item.get("apply_prompt")).lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _fallback_recommendations(requirements: Dict[str, Any], ui_schema: Dict[str, Any], ui_preview: Dict[str, Any]) -> List[Dict[str, str]]:
    recs: List[Dict[str, str]] = []

    meta = requirements.get("meta") if isinstance(requirements.get("meta"), dict) else {}
    domain = _safe_text(meta.get("domain")).lower()
    functional = requirements.get("functional_requirements") if isinstance(requirements.get("functional_requirements"), dict) else {}
    basic = [
        _safe_text(item).lower()
        for item in functional.get("basic", [])
        if isinstance(functional.get("basic"), list) and _safe_text(item)
    ]

    preview_pages = ui_preview.get("pages") if isinstance(ui_preview.get("pages"), list) else []
    first_page = preview_pages[0] if preview_pages and isinstance(preview_pages[0], dict) else {}
    first_page_name = _safe_text(first_page.get("name"), "главном экране")

    has_filters = _page_has_kind(ui_preview, "filters") or _page_has_schema_type(ui_schema, "filters")
    has_form = _page_has_kind(ui_preview, "form") or _page_has_schema_type(ui_schema, "form")
    has_chart = _page_has_kind(ui_preview, "chart") or _page_has_schema_type(ui_schema, "chart")
    has_table = _page_has_kind(ui_preview, "table") or _page_has_schema_type(ui_schema, "table")
    has_actions = bool(ui_schema.get("actions"))

    if (domain in {"e-commerce", "marketplace", "retail"} or any("каталог" in item for item in basic)) and not has_filters:
        recs.append({
            "id": "catalog-filters",
            "priority": "high",
            "title": "Добавить панель фильтров и сортировки",
            "description": f"На экране «{first_page_name}» не хватает явной панели фильтров по категории, статусу, цене или другим ключевым параметрам.",
            "rationale": "Без фильтров пользователь медленнее доходит до нужного объекта и интерфейс выглядит слишком демо-версией.",
            "impact": "Сценарий поиска станет понятнее, а сам прототип будет выглядеть ближе к реальному продукту.",
            "apply_prompt": f"Добавь на странице «{first_page_name}» отдельную секцию filters перед списком или карточками. В ней должны быть минимум 3 поля фильтра и кнопки сортировки/сброса. Обнови и ui_schema, и ui_preview согласованно.",
        })

    if not has_actions:
        recs.append({
            "id": "global-navigation",
            "priority": "high",
            "title": "Сделать навигацию явной",
            "description": "Между экранами не хватает явных CTA и переходов по основному сценарию.",
            "rationale": "Сейчас пользователь видит набор экранов, но путь от первого шага до результата читается слабо.",
            "impact": "На защите проекта будет проще показать пользовательский сценарий и логику экранов.",
            "apply_prompt": "Добавь явные navigation actions между ключевыми страницами: с главного экрана на основной рабочий экран, затем на экран деталей или результата. На каждой важной странице оставь 1-2 понятные CTA-кнопки.",
        })

    if not has_form:
        recs.append({
            "id": "target-form",
            "priority": "medium",
            "title": "Добавить форму целевого действия",
            "description": "В прототипе не видно места, где пользователь завершает ключевое действие: заявку, оформление, обратную связь или подтверждение.",
            "rationale": "Без формы сценарий выглядит незавершённым и продуктовая цель не доведена до результата.",
            "impact": "Прототип станет полноценным: от просмотра данных до выполнения главного действия.",
            "apply_prompt": "Добавь отдельную форму для целевого действия на подходящую страницу: 3-5 полей, понятный CTA, короткое пояснение и состояние успешной отправки. Не заменяй весь экран, а дополни текущий сценарий.",
        })

    if not has_chart and any(word in domain for word in ["analytics", "crm", "finance", "dashboard"]):
        recs.append({
            "id": "visual-analytics",
            "priority": "medium",
            "title": "Показать ключевые метрики визуально",
            "description": "Для аналитического или финансового сценария стоит добавить KPI-блок или график, а не оставлять только текст и таблицы.",
            "rationale": "Визуальная аналитика помогает мгновенно считывать состояние продукта и делает экран убедительнее.",
            "impact": "Интерфейс будет выглядеть профессиональнее, а данные — понятнее с первого взгляда.",
            "apply_prompt": "Добавь на основной аналитический экран секцию chart или KPI-блок с 3-4 ключевыми показателями и коротким пояснением, сохранив существующие таблицы и действия.",
        })

    if len(preview_pages) < 2:
        recs.append({
            "id": "multi-screen-flow",
            "priority": "medium",
            "title": "Разделить сценарий на несколько экранов",
            "description": "Сейчас прототип слишком компактный и не показывает полноценный пользовательский путь.",
            "rationale": "Отдельные экраны для списка, деталей и результата воспринимаются лучше, чем один перегруженный экран.",
            "impact": "Появится более правдоподобный flow, который легче презентовать и дальше редактировать.",
            "apply_prompt": "Добавь минимум ещё один экран и навигацию к нему: например, экран деталей или экран подтверждения результата. Сохрани текущую страницу и дополни сценарий, а не замени его полностью.",
        })

    if has_table and not has_filters:
        recs.append({
            "id": "table-toolbar",
            "priority": "medium",
            "title": "Усилить таблицу панелью управления",
            "description": "Таблица есть, но рядом не хватает панели поиска, фильтрации и быстрых действий.",
            "rationale": "Так таблица выглядит скорее как статический пример, а не рабочий бизнес-инструмент.",
            "impact": "Пользователю будет понятнее, что данные можно исследовать и с ними можно работать.",
            "apply_prompt": "Для страницы с таблицей добавь перед таблицей секцию filters или actions с поиском, 1-2 фильтрами и кнопкой сброса. Если есть место, добавь вторичное действие вроде экспорта или просмотра деталей.",
        })

    if not recs:
        recs.append({
            "id": "states-and-feedback",
            "priority": "medium",
            "title": "Добавить пустые и успешные состояния",
            "description": "Интерфейс уже выглядит цельным, но ему не хватает зрелости на уровне системных состояний.",
            "rationale": "Пустые результаты, подтверждения и статусы делают даже демо-прототип заметно убедительнее.",
            "impact": "Проект будет выглядеть более продуманным и ближе к реальной продуктовой разработке.",
            "apply_prompt": "Добавь в текущий прототип хотя бы одно пустое или успешное состояние: блок с сообщением, пояснением и кнопкой действия. Встрой его в наиболее важный экран, не ломая текущую структуру.",
        })

    return recs[:4]


RECOMMENDATION_PROMPT_TEMPLATE = """
Ты — продуктовый и UX-агент рекомендаций для уже сгенерированного UI-прототипа.

Твоя задача: проанализировать требования и ТЕКУЩИЙ прототип, затем предложить 3-4 КОНКРЕТНЫЕ правки, которые реально можно применить к этому интерфейсу через следующего агента правок.

Верни строго JSON формата:
{
  "recommendations": [
    {
      "id": "short-id",
      "priority": "high|medium|low",
      "title": "Короткое название правки",
      "description": "Что именно улучшить в текущем UI, максимально конкретно",
      "rationale": "Почему это важно именно для данного прототипа",
      "impact": "Какой эффект получит пользователь или защита проекта",
      "apply_prompt": "Точная инструкция агенту правок, как изменить текущий прототип без генерации с нуля"
    }
  ]
}

Жёсткие правила:
- Опирайся только на текущий контекст, страницы и секции из прототипа.
- Не давай абстрактные советы вроде «улучшить UX» или «сделать красиво».
- Каждая рекомендация должна быть применима как правка: добавить/убрать/переставить/уточнить/связать/сделать явным.
- Если в прототипе уже есть хороший элемент, не советуй добавить его ещё раз.
- Не повторяй одно и то же разными словами.
- В apply_prompt всегда пиши инструкцию на русском и через конкретные действия над текущим UI.
- Не проси переписать весь продукт заново.
- Приоритет high ставь только тем правкам, которые заметно улучшают сценарий или бизнес-цель.

КОНТЕКСТ ПРОЕКТА:
__CONTEXT_JSON__
""".strip()


def _llm_recommendations(requirements: Dict[str, Any], ui_schema: Dict[str, Any], ui_preview: Dict[str, Any]) -> List[Dict[str, str]]:
    context = _build_context_summary(requirements, ui_schema, ui_preview)
    prompt = RECOMMENDATION_PROMPT_TEMPLATE.replace(
        "__CONTEXT_JSON__",
        json.dumps(context, ensure_ascii=False, indent=2),
    )

    raw = ask_openrouter(prompt, temperature=0.2)
    parsed = _extract_json_object(raw)
    items = parsed.get("recommendations") if isinstance(parsed.get("recommendations"), list) else []
    normalized = [
        normalized_item
        for index, item in enumerate(items)
        if (normalized_item := _normalize_recommendation(item, index)) is not None
    ]
    normalized = _deduplicate_recommendations(normalized)
    if not normalized:
        raise ValueError("LLM не вернул валидных рекомендаций")
    return normalized[:4]


def build_recommendations(
    requirements: Dict[str, Any],
    ui_schema: Dict[str, Any],
    ui_preview: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    preview = ui_preview if isinstance(ui_preview, dict) else {}

    try:
        return _llm_recommendations(requirements, ui_schema, preview)
    except Exception:
        return _fallback_recommendations(requirements, ui_schema, preview)
