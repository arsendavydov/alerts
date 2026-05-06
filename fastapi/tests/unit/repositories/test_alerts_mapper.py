"""Тесты для `AlertsMapper`."""

from typing import ClassVar

import pytest
from pydantic import ValidationError

from repositories.mappers import AlertsMapper


def test_alert_detail_from_row_with_mapping_raises_validation_error():
    """При row с `_mapping` метод доходит до конструирования схемы и валидирует поля."""

    class FakeRow:
        _mapping: ClassVar[dict[str, object]] = {
            "id": "a1",
            "alert_name": "Alert A",
            "event": "e1",
            "event_name": "event name",
            "description": "desc",
            "image": "img",
            "tags": '["x"]',
            "group_rules": "g1",
            "group_rule_description": "rule desc",
            "group_rule_image": "rule img",
            "silence_time": "{}",
            "paused": 1,
        }

    with pytest.raises(ValidationError):
        AlertsMapper.alert_detail_from_row(FakeRow())


def test_alert_detail_from_row_with_tuple_fallback_raises_validation_error():
    """Intentional legacy edge: tuple-строка использует индексные fallback-ветки и доходит до валидации."""
    row = (
        "a2",
        "Alert B",
        "e2",
        "event two",
        "desc2",
        "img2",
        None,
        None,
        None,
        None,
        None,
        0,
    )
    with pytest.raises(ValidationError):
        AlertsMapper.alert_detail_from_row(row)


def test_alert_detail_from_row_with_dict_raises_validation_error():
    """При dict метод берет значения по ключам и доходит до валидации схемы."""
    row = {"id": "a3", "alert_name": "Alert C", "paused": True}
    with pytest.raises(ValidationError):
        AlertsMapper.alert_detail_from_row(row)


def test_alert_detail_from_row_with_object_attrs_raises_validation_error():
    """При объекте без `_mapping` используются атрибуты (ветка `getattr`)."""

    class AttrRow:
        id = "a4"
        alert_name = "Alert D"
        event = "e4"

    with pytest.raises(ValidationError):
        AlertsMapper.alert_detail_from_row(AttrRow())


def test_alert_detail_from_short_tuple_hits_none_fallback():
    """Intentional legacy edge: короткий tuple вызывает fallback `return None` для отсутствующих полей."""
    with pytest.raises(ValidationError):
        AlertsMapper.alert_detail_from_row(("only-id",))


def test_alert_detail_from_row_requires_value():
    """`None` во входе приводит к ValueError."""
    with pytest.raises(ValueError, match="row is required"):
        AlertsMapper.alert_detail_from_row(None)
