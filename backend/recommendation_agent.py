from typing import Any


def build_recommendations(requirements: dict[str, Any], ui_schema: dict[str, Any]) -> list[dict[str, str]]:
    pages = ui_schema.get("pages", []) if isinstance(ui_schema, dict) else []
    actions = ui_schema.get("actions", []) if isinstance(ui_schema, dict) else []

    def page_has_type(type_name: str) -> bool:
        for page in pages:
            if not isinstance(page, dict):
                continue
            for element in page.get("elements", []) or []:
                if isinstance(element, dict) and str(element.get("type", "")).lower() == type_name:
                    return True
        return False

    recs: list[dict[str, str]] = []

    meta = requirements.get("meta", {}) if isinstance(requirements, dict) else {}
    domain = str(meta.get("domain", "")).lower()

    functional = requirements.get("functional_requirements", {}) if isinstance(requirements, dict) else {}
    basic = functional.get("basic", []) if isinstance(functional, dict) else []

    if domain in {"e-commerce", "marketplace", "retail"} or any("каталог" in str(item).lower() for item in basic):
        if not page_has_type("filters"):
            recs.append({
                "title": "Добавить фильтрацию",
                "description": "Для каталога товаров или сущностей полезно добавить фильтры по категории, цене, статусу или характеристикам.",
            })

    if not any(str(action.get("type", "")) == "navigate" for action in actions if isinstance(action, dict)):
        recs.append({
            "title": "Усилить навигацию",
            "description": "Добавьте явные переходы между ключевыми страницами, чтобы пользователь быстрее проходил сценарий от входа до целевого действия.",
        })

    if not page_has_type("form"):
        recs.append({
            "title": "Добавить форму целевого действия",
            "description": "Если пользователю нужно оставить заявку, оформить заказ или связаться с компанией, лучше вынести это в отдельную форму.",
        })

    if not page_has_type("chart") and any(word in domain for word in ["analytics", "crm", "finance", "dashboard"]):
        recs.append({
            "title": "Показать аналитику визуально",
            "description": "Для данных и метрик лучше добавить график или KPI-блок, чтобы интерфейс был понятнее с первого взгляда.",
        })

    if len(pages) < 2:
        recs.append({
            "title": "Разделить сценарий на несколько экранов",
            "description": "Сейчас прототип очень компактный. Отдельные страницы для каталога, деталей и действия повысят читаемость сценария.",
        })

    if not recs:
        recs.append({
            "title": "Проверить контентные состояния",
            "description": "Добавьте пустые состояния, ошибки загрузки и сообщения успеха, чтобы прототип выглядел зрелее на защите проекта.",
        })

    return recs[:4]
