import json
from copy import deepcopy
from typing import Any, Dict, List, Optional

from AI_client import ask_openrouter
from UI_requirements import normalize_ui_schema
from ui_preview_agent import extract_json_from_text, normalize_preview, validate_preview


EDIT_RESPONSE_EXAMPLE = {
    "ui_schema": {
        "pages": [
            {
                "id": "history",
                "name": "История операций",
                "route": "/history",
                "elements_mode": "replace",
                "disableAutoNavigation": True,
                "elements": [
                    {
                        "type": "filters",
                        "label": "Фильтры операций",
                        "description": "Фильтрация списка",
                        "fields": ["Период", "Статус"],
                        "action": "/history",
                    },
                    {
                        "type": "button",
                        "label": "Удалить кнопку",
                        "_delete": True,
                    },
                ],
            }
        ],
        "actions": [
            {
                "id": "go-history",
                "label": "История операций",
                "type": "navigate",
                "target": "/history",
            }
        ],
    },
    "ui_preview": {
        "app": {
            "title": "Банк «История операций»",
            "subtitle": "Интерактивный прототип",
            "theme": "light",
            "primaryAction": "Открыть сценарий",
            "design": {
                "preset": "banking-green",
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
        },
        "pages": [
            {
                "id": "history",
                "name": "История операций",
                "route": "/history",
                "disableAutoNavigation": True,
                "sections_mode": "replace",
                "sections_order": ["history-hero", "history-table"],
                "sections": [
                    {
                        "id": "history-hero",
                        "kind": "hero",
                        "title": "История операций",
                        "description": "Главный экран со списком операций",
                        "actions_mode": "replace",
                        "actions": [],
                    },
                    {
                        "id": "history-filters",
                        "_delete": True,
                    },
                ],
            }
        ],
    },
    "summary": "Кратко перечисли внесённые правки.",
}


REPLACE_MODES = {"replace", "set"}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()



def _normalized_name(value: Any) -> str:
    return _safe_text(value).lower()



def _normalized_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    return None



def _replace_mode(value: Any) -> bool:
    return _normalized_name(value) in REPLACE_MODES



def _is_delete_patch(item: Any) -> bool:
    return isinstance(item, dict) and bool(item.get("_delete"))



def _page_matches(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_id = _normalized_name(left.get("id"))
    right_id = _normalized_name(right.get("id"))
    if left_id and right_id and left_id == right_id:
        return True

    left_route = _normalized_name(left.get("route"))
    right_route = _normalized_name(right.get("route"))
    if left_route and right_route and left_route == right_route:
        return True

    left_name = _normalized_name(left.get("name"))
    right_name = _normalized_name(right.get("name"))
    return bool(left_name and right_name and left_name == right_name)



def _schema_element_matches(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_type = _normalized_name(left.get("type"))
    right_type = _normalized_name(right.get("type"))
    left_label = _normalized_name(left.get("label"))
    right_label = _normalized_name(right.get("label"))

    if left_type and right_type and left_label and right_label:
        return left_type == right_type and left_label == right_label

    return False



def _schema_action_matches(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_id = _normalized_name(left.get("id"))
    right_id = _normalized_name(right.get("id"))
    if left_id and right_id and left_id == right_id:
        return True

    left_label = _normalized_name(left.get("label"))
    right_label = _normalized_name(right.get("label"))
    left_target = _normalized_name(left.get("target"))
    right_target = _normalized_name(right.get("target"))
    return bool(left_label and right_label and left_label == right_label and left_target == right_target)



def _preview_section_matches(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_id = _normalized_name(left.get("id"))
    right_id = _normalized_name(right.get("id"))
    if left_id and right_id and left_id == right_id:
        return True

    left_kind = _normalized_name(left.get("kind"))
    right_kind = _normalized_name(right.get("kind"))
    left_title = _normalized_name(left.get("title"))
    right_title = _normalized_name(right.get("title"))
    return bool(left_kind and right_kind and left_title and right_title and left_kind == right_kind and left_title == right_title)



def _preview_action_matches(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_label = _normalized_name(left.get("label"))
    right_label = _normalized_name(right.get("label"))
    left_target = _normalized_name(left.get("target"))
    right_target = _normalized_name(right.get("target"))

    if left_label and right_label and left_target and right_target:
        return left_label == right_label and left_target == right_target

    return bool(left_label and right_label and left_label == right_label)



def _field_matches(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_name = _normalized_name(left.get("name"))
    right_name = _normalized_name(right.get("name"))
    if left_name and right_name and left_name == right_name:
        return True

    left_label = _normalized_name(left.get("label"))
    right_label = _normalized_name(right.get("label"))
    return bool(left_label and right_label and left_label == right_label)



def _card_matches(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_title = _normalized_name(left.get("title"))
    right_title = _normalized_name(right.get("title"))
    return bool(left_title and right_title and left_title == right_title)



def _find_match_index(current_items: List[Dict[str, Any]], incoming_item: Dict[str, Any], matcher) -> Optional[int]:
    for index, current_item in enumerate(current_items):
        if isinstance(current_item, dict) and matcher(current_item, incoming_item):
            return index
    return None



def _merge_unique_string_lists(current_items: Any, incoming_items: Any) -> List[str]:
    result: List[str] = []
    for source in [current_items, incoming_items]:
        if not isinstance(source, list):
            continue
        for item in source:
            text = _safe_text(item)
            if text and text not in result:
                result.append(text)
    return result



def _ref_matches_page(ref: Any, page: Dict[str, Any]) -> bool:
    target = _normalized_name(ref)
    return bool(target and target in {
        _normalized_name(page.get("id")),
        _normalized_name(page.get("route")),
        _normalized_name(page.get("name")),
    })



def _ref_matches_schema_element(ref: Any, element: Dict[str, Any]) -> bool:
    target = _normalized_name(ref)
    label = _normalized_name(element.get("label"))
    element_type = _normalized_name(element.get("type"))
    return bool(target and (target == label or target == f"{element_type}:{label}"))



def _ref_matches_preview_section(ref: Any, section: Dict[str, Any]) -> bool:
    target = _normalized_name(ref)
    section_id = _normalized_name(section.get("id"))
    title = _normalized_name(section.get("title"))
    kind = _normalized_name(section.get("kind"))
    return bool(target and (target == section_id or target == title or target == f"{kind}:{title}"))



def _ref_matches_preview_action(ref: Any, action: Dict[str, Any]) -> bool:
    target = _normalized_name(ref)
    label = _normalized_name(action.get("label"))
    action_target = _normalized_name(action.get("target"))
    return bool(target and (target == label or target == action_target or target == f"{label}->{action_target}"))



def _reorder_by_refs(items: List[Dict[str, Any]], refs: Any, ref_matcher) -> List[Dict[str, Any]]:
    if not isinstance(refs, list) or not items:
        return items

    remaining = list(items)
    ordered: List[Dict[str, Any]] = []

    for ref in refs:
        match_index = None
        for index, item in enumerate(remaining):
            if isinstance(item, dict) and ref_matcher(ref, item):
                match_index = index
                break
        if match_index is not None:
            ordered.append(remaining.pop(match_index))

    ordered.extend(remaining)
    return ordered



def _merge_schema_element(current_element: Dict[str, Any], patch_element: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_element)

    for key in ["type", "label", "description", "action"]:
        if key in patch_element and patch_element.get(key) not in (None, ""):
            merged[key] = patch_element[key]

    if "fields" in patch_element and isinstance(patch_element.get("fields"), list):
        if _replace_mode(patch_element.get("fields_mode")):
            merged["fields"] = [_safe_text(item) for item in patch_element.get("fields", []) if _safe_text(item)]
        else:
            merged["fields"] = _merge_unique_string_lists(current_element.get("fields"), patch_element.get("fields"))

    return merged



def _merge_schema_page(current_page: Dict[str, Any], patch_page: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_page)

    for key in ["id", "name", "route"]:
        if key in patch_page and patch_page.get(key) not in (None, ""):
            merged[key] = patch_page[key]

    disable_auto_navigation = _normalized_bool(patch_page.get("disableAutoNavigation"))
    if disable_auto_navigation is not None:
        merged["disableAutoNavigation"] = disable_auto_navigation

    if ("elements" in patch_page and isinstance(patch_page.get("elements"), list)) or "elements_order" in patch_page:
        if _replace_mode(patch_page.get("elements_mode")):
            current_elements = []
        else:
            current_elements = deepcopy(current_page.get("elements", [])) if isinstance(current_page.get("elements"), list) else []

        for patch_element in patch_page.get("elements", []):
            if not isinstance(patch_element, dict):
                continue

            match_index = _find_match_index(current_elements, patch_element, _schema_element_matches)
            if _is_delete_patch(patch_element):
                if match_index is not None:
                    current_elements.pop(match_index)
                continue

            if match_index is None:
                clean_item = {key: deepcopy(value) for key, value in patch_element.items() if key not in {"_delete", "fields_mode"}}
                current_elements.append(clean_item)
            else:
                current_elements[match_index] = _merge_schema_element(current_elements[match_index], patch_element)

        current_elements = _reorder_by_refs(current_elements, patch_page.get("elements_order"), _ref_matches_schema_element)
        merged["elements"] = current_elements

    return merged



def _merge_schema_action(current_action: Dict[str, Any], patch_action: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_action)
    for key in ["id", "label", "type", "target"]:
        if key in patch_action and patch_action.get(key) not in (None, ""):
            merged[key] = patch_action[key]
    return merged



def merge_ui_schema(current_ui_schema: Dict[str, Any], ui_schema_patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_ui_schema) if isinstance(current_ui_schema, dict) else {}

    current_pages = deepcopy(current_ui_schema.get("pages", [])) if isinstance(current_ui_schema.get("pages"), list) else []
    patch_pages = ui_schema_patch.get("pages") if isinstance(ui_schema_patch.get("pages"), list) else []

    for patch_page in patch_pages:
        if not isinstance(patch_page, dict):
            continue

        match_index = _find_match_index(current_pages, patch_page, _page_matches)
        if _is_delete_patch(patch_page):
            if match_index is not None:
                current_pages.pop(match_index)
            continue

        if match_index is None:
            clean_page = {key: deepcopy(value) for key, value in patch_page.items() if key not in {"_delete"}}
            current_pages.append(clean_page)
        else:
            current_pages[match_index] = _merge_schema_page(current_pages[match_index], patch_page)

    current_pages = _reorder_by_refs(current_pages, ui_schema_patch.get("pages_order"), _ref_matches_page)
    merged["pages"] = current_pages

    current_actions = deepcopy(current_ui_schema.get("actions", [])) if isinstance(current_ui_schema.get("actions"), list) else []
    patch_actions = ui_schema_patch.get("actions") if isinstance(ui_schema_patch.get("actions"), list) else []
    actions_replace = _replace_mode(ui_schema_patch.get("actions_mode"))
    if actions_replace:
        current_actions = []

    for patch_action in patch_actions:
        if not isinstance(patch_action, dict):
            continue

        match_index = _find_match_index(current_actions, patch_action, _schema_action_matches)
        if _is_delete_patch(patch_action):
            if match_index is not None:
                current_actions.pop(match_index)
            continue

        if match_index is None:
            clean_action = {key: deepcopy(value) for key, value in patch_action.items() if key != "_delete"}
            current_actions.append(clean_action)
        else:
            current_actions[match_index] = _merge_schema_action(current_actions[match_index], patch_action)

    if current_actions or actions_replace:
        merged["actions"] = current_actions

    return merged



def _merge_preview_action(current_action: Dict[str, Any], patch_action: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_action)
    for key in ["label", "type", "target"]:
        if key in patch_action and patch_action.get(key) not in (None, ""):
            merged[key] = patch_action[key]
    return merged



def _merge_preview_field(current_field: Dict[str, Any], patch_field: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_field)
    for key in ["name", "label", "type", "placeholder"]:
        if key in patch_field and patch_field.get(key) not in (None, ""):
            merged[key] = patch_field[key]

    if "options" in patch_field and isinstance(patch_field.get("options"), list):
        if _replace_mode(patch_field.get("options_mode")):
            merged["options"] = _merge_unique_string_lists([], patch_field.get("options"))
        else:
            merged["options"] = _merge_unique_string_lists(current_field.get("options"), patch_field.get("options"))

    return merged



def _merge_preview_card(current_card: Dict[str, Any], patch_card: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_card)
    for key in ["title", "description"]:
        if key in patch_card and patch_card.get(key) not in (None, ""):
            merged[key] = patch_card[key]

    if "meta" in patch_card and isinstance(patch_card.get("meta"), list):
        if _replace_mode(patch_card.get("meta_mode")):
            merged["meta"] = _merge_unique_string_lists([], patch_card.get("meta"))
        else:
            merged["meta"] = _merge_unique_string_lists(current_card.get("meta"), patch_card.get("meta"))

    return merged



def _merge_named_object_list(
    current_items: Any,
    patch_items: Any,
    matcher,
    merger,
    replace_mode: bool = False,
    order_refs: Any = None,
    ref_matcher=None,
) -> List[Dict[str, Any]]:
    items = [] if replace_mode else (deepcopy(current_items) if isinstance(current_items, list) else [])
    patch_list = patch_items if isinstance(patch_items, list) else []

    for patch_item in patch_list:
        if not isinstance(patch_item, dict):
            continue

        match_index = _find_match_index(items, patch_item, matcher)
        if _is_delete_patch(patch_item):
            if match_index is not None:
                items.pop(match_index)
            continue

        if match_index is None:
            clean_item = {key: deepcopy(value) for key, value in patch_item.items() if key != "_delete" and not key.endswith("_mode")}
            items.append(clean_item)
        else:
            items[match_index] = merger(items[match_index], patch_item)

    if ref_matcher is not None:
        items = _reorder_by_refs(items, order_refs, ref_matcher)
    return items



def _merge_preview_section(current_section: Dict[str, Any], patch_section: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_section)

    for key in ["id", "kind", "title", "description"]:
        if key in patch_section and patch_section.get(key) not in (None, ""):
            merged[key] = patch_section[key]

    for key in ["disableAutoActions"]:
        incoming_bool = _normalized_bool(patch_section.get(key))
        if incoming_bool is not None:
            merged[key] = incoming_bool

    if "fields" in patch_section:
        merged["fields"] = _merge_named_object_list(
            current_section.get("fields"),
            patch_section.get("fields"),
            _field_matches,
            _merge_preview_field,
            replace_mode=_replace_mode(patch_section.get("fields_mode")),
        )

    if "cards" in patch_section:
        merged["cards"] = _merge_named_object_list(
            current_section.get("cards"),
            patch_section.get("cards"),
            _card_matches,
            _merge_preview_card,
            replace_mode=_replace_mode(patch_section.get("cards_mode")),
        )

    if "actions" in patch_section or "actions_order" in patch_section:
        merged["actions"] = _merge_named_object_list(
            current_section.get("actions"),
            patch_section.get("actions"),
            _preview_action_matches,
            _merge_preview_action,
            replace_mode=_replace_mode(patch_section.get("actions_mode")),
            order_refs=patch_section.get("actions_order"),
            ref_matcher=_ref_matches_preview_action,
        )

    for replace_key in ["columns", "rows", "bullets"]:
        if replace_key in patch_section and isinstance(patch_section.get(replace_key), list):
            merged[replace_key] = deepcopy(patch_section[replace_key])

    return merged



def _merge_preview_page(current_page: Dict[str, Any], patch_page: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_page)

    for key in ["id", "name", "route", "summary"]:
        if key in patch_page and patch_page.get(key) not in (None, ""):
            merged[key] = patch_page[key]

    for key in ["disableAutoNavigation", "disableAutoHero"]:
        incoming_bool = _normalized_bool(patch_page.get(key))
        if incoming_bool is not None:
            merged[key] = incoming_bool

    if ("sections" in patch_page and isinstance(patch_page.get("sections"), list)) or "sections_order" in patch_page:
        merged["sections"] = _merge_named_object_list(
            current_page.get("sections"),
            patch_page.get("sections"),
            _preview_section_matches,
            _merge_preview_section,
            replace_mode=_replace_mode(patch_page.get("sections_mode")),
            order_refs=patch_page.get("sections_order"),
            ref_matcher=_ref_matches_preview_section,
        )

    return merged



def merge_ui_preview(current_ui_preview: Dict[str, Any], ui_preview_patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(current_ui_preview) if isinstance(current_ui_preview, dict) else {}

    current_app = deepcopy(current_ui_preview.get("app", {})) if isinstance(current_ui_preview.get("app"), dict) else {}
    patch_app = ui_preview_patch.get("app") if isinstance(ui_preview_patch.get("app"), dict) else {}
    if patch_app:
        merged_app = deepcopy(current_app)
        for key, value in patch_app.items():
            if key == "design" and isinstance(value, dict):
                base_design = merged_app.get("design") if isinstance(merged_app.get("design"), dict) else {}
                merged_app["design"] = {**deepcopy(base_design), **deepcopy(value)}
            elif value not in (None, ""):
                merged_app[key] = deepcopy(value)
        merged["app"] = merged_app
    elif current_app:
        merged["app"] = current_app

    current_pages = deepcopy(current_ui_preview.get("pages", [])) if isinstance(current_ui_preview.get("pages"), list) else []
    patch_pages = ui_preview_patch.get("pages") if isinstance(ui_preview_patch.get("pages"), list) else []

    for patch_page in patch_pages:
        if not isinstance(patch_page, dict):
            continue

        match_index = _find_match_index(current_pages, patch_page, _page_matches)
        if _is_delete_patch(patch_page):
            if match_index is not None:
                current_pages.pop(match_index)
            continue

        if match_index is None:
            clean_page = {key: deepcopy(value) for key, value in patch_page.items() if key != "_delete"}
            current_pages.append(clean_page)
        else:
            current_pages[match_index] = _merge_preview_page(current_pages[match_index], patch_page)

    current_pages = _reorder_by_refs(current_pages, ui_preview_patch.get("pages_order"), _ref_matches_page)
    merged["pages"] = current_pages
    return merged



def build_ui_edit_prompt(
    edit_request: str,
    current_requirements: Dict[str, Any],
    current_ui_schema: Dict[str, Any],
    current_ui_preview: Dict[str, Any],
) -> str:
    return f"""
Ты — агент точечных правок UI-прототипа.

Твоя задача: взять ТЕКУЩИЙ прототип и изменить именно его по запросу пользователя.
Нельзя генерировать новый продукт с нуля.
По умолчанию сервер делает merge, поэтому для удаления и перестановки нужно использовать специальные поля ниже.

Верни строго только JSON без markdown и пояснений. Формат ответа:
{json.dumps(EDIT_RESPONSE_EXAMPLE, ensure_ascii=False, indent=2)}

Правила ответа:
- Основа для изменений — CURRENT_UI_PREVIEW и CURRENT_UI_SCHEMA.
- Меняй только то, что следует из EDIT_REQUEST.
- Если изменения локальные, возвращай только изменённые страницы/секции/элементы.
- Если надо УДАЛИТЬ страницу, секцию, кнопку, action, поле, карточку или элемент ui_schema — верни соответствующий объект с "_delete": true.
- Если надо УДАЛИТЬ ВСЕ кнопки в секции hero/actions/filters/form — верни для этой секции "actions_mode": "replace" и "actions": [].
- Если надо ПЕРЕСТАВИТЬ секции на странице — укажи "sections_order": [..] и при необходимости "sections_mode": "replace".
- Если надо ПЕРЕСТАВИТЬ элементы в ui_schema page — укажи "elements_order": [..] и при необходимости "elements_mode": "replace".
- Если надо ЗАМЕНИТЬ полный список sections или elements на странице — используй "sections_mode": "replace" или "elements_mode": "replace".
- Если пользователь просит убрать все навигационные кнопки на странице и не добавлять их автоматически — поставь на странице "disableAutoNavigation": true.
- Если пользователь просит убрать hero-секцию и не возвращать её автоматически — поставь "disableAutoHero": true.
- Для удаления конкретной секции/кнопки старайся указывать id. Если id неизвестен, используй точные текущие title/label.
- Сохраняй существующие страницы, если пользователь явно не просил их удалить.
- Сохраняй page.id и route, если пользователь явно не попросил их изменить.
- Если добавляешь новый экран, добавь его и в ui_schema, и в ui_preview, и в навигацию.
- Если меняешь тексты, цвета, кнопки, таблицы, формы или порядок блоков — обнови и ui_schema, и ui_preview согласованно.
- Таблицы должны оставаться интерактивными: columns и rows должны быть корректными.
- action.target в ui_preview и target в ui_schema.actions должны ссылаться на существующий route или id.
- Весь видимый пользователю текст должен быть только на русском языке, без мусора вроде "/", "/home", "Main Page", "Dashboard" и других технических строк.
- route можно сохранять как техническое поле, но пользовательские title/name/summary/description/label должны быть чистыми и понятными.
- Если пользователь просит добавить кнопку, CTA, переход, подтверждение, выбор, оформление, сортировку или фильтрацию — не прячь это в описании: добавляй явные actions и при необходимости отдельные секции actions/filters рядом с нужным контентом.
- Если правка касается списка, каталога, таблицы или аналитики, фильтры обычно должны идти перед table/cardGrid, а сортировки лучше оформлять отдельными action-кнопками.
- Если пользователь просит изменить основной цвет, акцент, тему или сделать интерфейс «весь синий/зелёный/фиолетовый» — обновляй согласованно app.design и связанные акцентные поля, а не только один частный элемент.
- Если запрос пользователя неоднозначный, внеси наиболее безопасные и минимально достаточные правки.
- Дизайн меняй только если пользователь явно просит изменить стиль, тему, цвета или визуальную подачу.
- summary должен быть коротким, 1-2 предложения, без слова "JSON".

CURRENT_REQUIREMENTS:
{json.dumps(current_requirements, ensure_ascii=False, indent=2)}

CURRENT_UI_SCHEMA:
{json.dumps(current_ui_schema, ensure_ascii=False, indent=2)}

CURRENT_UI_PREVIEW:
{json.dumps(current_ui_preview, ensure_ascii=False, indent=2)}

EDIT_REQUEST:
{edit_request}
"""



def apply_ui_edit(
    edit_request: str,
    current_requirements: Dict[str, Any],
    current_ui_schema: Dict[str, Any],
    current_ui_preview: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = build_ui_edit_prompt(
        edit_request=edit_request,
        current_requirements=current_requirements,
        current_ui_schema=current_ui_schema,
        current_ui_preview=current_ui_preview,
    )

    raw_response = ask_openrouter(prompt, temperature=0.15)
    parsed = extract_json_from_text(raw_response)

    ui_schema_patch = parsed.get("ui_schema") if isinstance(parsed.get("ui_schema"), dict) else {}
    ui_preview_patch = parsed.get("ui_preview") if isinstance(parsed.get("ui_preview"), dict) else {}

    merged_ui_schema = merge_ui_schema(current_ui_schema, ui_schema_patch)
    normalized_ui_schema = normalize_ui_schema(merged_ui_schema)

    merged_ui_preview = merge_ui_preview(current_ui_preview, ui_preview_patch)
    validated_preview = validate_preview(merged_ui_preview)
    normalized_ui_preview = normalize_preview(validated_preview, normalized_ui_schema, current_requirements)

    summary = parsed.get("summary") if isinstance(parsed.get("summary"), str) else "Готово: внёс правки в текущий прототип без потери остальных страниц."

    return {
        "requirements": current_requirements,
        "ui_schema": normalized_ui_schema,
        "ui_preview": normalized_ui_preview,
        "summary": summary.strip() or "Готово: внёс правки в текущий прототип без потери остальных страниц.",
    }
