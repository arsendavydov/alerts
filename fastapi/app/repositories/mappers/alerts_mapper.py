"""Мапперы для преобразования ORM-объектов alerts."""

from typing import Any

from schemas.alerts import AlertDetail


class AlertsMapper:
    """Преобразования между ORM/row-данными и схемами домена alerts."""

    @staticmethod
    def alert_detail_from_row(row: Any) -> AlertDetail:
        """
        Собирает `AlertDetail` из row/tuple совместимого формата.

        Метод сохраняет совместимость со старым сервисным слоем:
        часть полей может приходить как именованные атрибуты, часть как индексы.
        """
        if row is None:
            raise ValueError("row is required")

        def _get_value(key: str, idx: int) -> Any:
            if hasattr(row, "_mapping"):
                value = row._mapping.get(key)
                if value is not None:
                    return value
            if isinstance(row, dict):
                return row.get(key)
            if hasattr(row, key):
                return getattr(row, key)
            if isinstance(row, (list, tuple)) and len(row) > idx:
                return row[idx]
            return None

        return AlertDetail(
            id=_get_value("id", 0),
            alert_name=_get_value("alert_name", 1),
            indicator_id=_get_value("event", 2),
            indicator_name=_get_value("event_name", 3),
            description=_get_value("description", 4),
            image=_get_value("image", 5),
            tags=_get_value("tags", 6),
            group_rule_id=_get_value("group_rules", 7),
            group_rule_description=_get_value("group_rule_description", 8),
            group_rule_image=_get_value("group_rule_image", 9),
            silence_time=_get_value("silence_time", 10),
            paused=bool(_get_value("paused", 11)),
        )
