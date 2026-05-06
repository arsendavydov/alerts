"""
Модульные тесты для валидации схем Alerts.
"""

import sys
from pathlib import Path
from uuid import uuid4

import pytest

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.alerts import (
    AlertAutocomplete,
    AlertAutocompleteResponse,
    AlertDetail,
    AlertDetailCreate,
    AlertDetailUpdate,
    AlertListItem,
    AlertListResponse,
    GroupRuleInfo,
    IndicatorInfo,
    TagCloudResponse,
)


class TestAlertListItem:
    """Тесты для AlertListItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        alert_id = uuid4()
        data = AlertListItem(
            alert_id=alert_id,
            alert_name="Test Alert",
            indicator_name="Test Indicator",
            paused=False,
        )
        assert data.alert_id == alert_id
        assert data.alert_name == "Test Alert"
        assert data.paused is False

    def test_with_optional_fields(self):
        """Тест с опциональными полями."""
        alert_id = uuid4()
        data = AlertListItem(
            alert_id=alert_id,
            alert_name="Test Alert",
            indicator_name="Test Indicator",
            alert_description="Description",
            indicator_description="Indicator Description",
            status_id="1",
            paused=True,
            tags=["tag1", "tag2"],
        )
        assert data.alert_description == "Description"
        assert data.tags == ["tag1", "tag2"]


class TestAlertListResponse:
    """Тесты для AlertListResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        alert_id = uuid4()
        item = AlertListItem(
            alert_id=alert_id,
            alert_name="Test Alert",
            indicator_name="Test Indicator",
        )
        data = AlertListResponse(alerts=[item], total=1)
        assert len(data.alerts) == 1
        assert data.total == 1

    def test_empty_response(self):
        """Тест пустого ответа."""
        data = AlertListResponse(alerts=[], total=0)
        assert len(data.alerts) == 0
        assert data.total == 0


class TestIndicatorInfo:
    """Тесты для IndicatorInfo."""

    def test_valid_info(self):
        """Тест валидной информации об индикаторе."""
        indicator_id = uuid4()
        data = IndicatorInfo(
            indicator_id=indicator_id, indicator_name="Test Indicator"
        )
        assert data.indicator_id == indicator_id
        assert data.indicator_name == "Test Indicator"


class TestGroupRuleInfo:
    """Тесты для GroupRuleInfo."""

    def test_valid_info(self):
        """Тест валидной информации о группе правил."""
        group_rule_id = uuid4()
        data = GroupRuleInfo(
            group_rule_id=group_rule_id,
            description="Test Description",
            image="test.jpg",
        )
        assert data.group_rule_id == group_rule_id
        assert data.description == "Test Description"
        assert data.image == "test.jpg"

    def test_without_optional_fields(self):
        """Тест без опциональных полей."""
        group_rule_id = uuid4()
        data = GroupRuleInfo(group_rule_id=group_rule_id)
        assert data.description is None
        assert data.image is None


class TestAlertDetail:
    """Тесты для AlertDetail."""

    def test_valid_detail(self):
        """Тест валидной детальной информации."""
        alert_id = uuid4()
        indicator_id = uuid4()
        data = AlertDetail(
            alert_id=alert_id,
            alert_name="Test Alert",
            indicator=IndicatorInfo(
                indicator_id=indicator_id, indicator_name="Test Indicator"
            ),
        )
        assert data.alert_id == alert_id
        assert data.alert_name == "Test Alert"
        assert data.indicator.indicator_id == indicator_id


class TestAlertDetailCreate:
    """Тесты для AlertDetailCreate."""

    def test_valid_create(self):
        """Тест валидного создания."""
        indicator_id = uuid4()
        group_rule_id = uuid4()
        data = AlertDetailCreate(
            alert_name="Test Alert",
            indicator_id=indicator_id,
            description="Description",
            image="test.jpg",
            group_rule_id=group_rule_id,
        )
        assert data.alert_name == "Test Alert"
        assert data.indicator_id == indicator_id
        assert data.group_rule_id == group_rule_id

    def test_with_tags(self):
        """Тест с тегами."""
        indicator_id = uuid4()
        group_rule_id = uuid4()
        data = AlertDetailCreate(
            alert_name="Test Alert",
            indicator_id=indicator_id,
            description="Description",
            image="test.jpg",
            group_rule_id=group_rule_id,
            tags=["tag1", "tag2"],
        )
        assert data.tags == ["tag1", "tag2"]

    def test_silence_time_empty_string_becomes_none(self):
        """Покрыть validator silence_time: пустая строка -> None."""
        data = AlertDetailCreate(
            alert_name="A",
            indicator_id=uuid4(),
            description="D",
            image="I",
            group_rule_id=uuid4(),
            silence_time="   ",
        )
        assert data.silence_time is None


class TestAlertDetailUpdate:
    """Тесты для AlertDetailUpdate."""

    def test_valid_update(self):
        """Тест валидного обновления."""
        alert_id = uuid4()
        data = AlertDetailUpdate(alert_id=alert_id)
        assert data.alert_id == alert_id

    def test_partial_update(self):
        """Тест частичного обновления."""
        alert_id = uuid4()
        data = AlertDetailUpdate(alert_id=alert_id, alert_name="Updated Name")
        assert data.alert_name == "Updated Name"
        assert data.indicator_id is None

    def test_silence_time_empty_string_kept_for_nulling(self):
        """Покрыть validator silence_time: пустая строка -> ''."""
        data = AlertDetailUpdate(alert_id=uuid4(), silence_time=" ")
        assert data.silence_time == ""

    def test_silence_time_invalid_json_raises(self):
        """Покрыть validator silence_time: invalid JSON."""
        with pytest.raises(Exception):
            AlertDetailUpdate(alert_id=uuid4(), silence_time="{bad")

    def test_create_validator_direct_paths(self):
        """Покрыть оставшиеся ветки validate_silence_time_json в Create."""
        assert AlertDetailCreate.validate_silence_time_json(None) is None
        with pytest.raises(ValueError):
            AlertDetailCreate.validate_silence_time_json("x" * 1001)
        assert AlertDetailCreate.validate_silence_time_json('{"ok":1}') == '{"ok":1}'

    def test_update_validator_direct_paths(self):
        """Покрыть оставшиеся ветки validate_silence_time_json в Update."""
        assert AlertDetailUpdate.validate_silence_time_json(None) is None
        with pytest.raises(ValueError):
            AlertDetailUpdate.validate_silence_time_json("x" * 1001)
        assert AlertDetailUpdate.validate_silence_time_json('{"ok":1}') == '{"ok":1}'


class TestTagCloudResponse:
    """Тесты для TagCloudResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        data = TagCloudResponse(tags=["tag1", "tag2"], total=2)
        assert len(data.tags) == 2
        assert data.total == 2

    def test_empty_response(self):
        """Тест пустого ответа."""
        data = TagCloudResponse(tags=[], total=0)
        assert len(data.tags) == 0
        assert data.total == 0


class TestAlertAutocomplete:
    """Тесты для AlertAutocomplete."""

    def test_valid_autocomplete(self):
        """Тест валидного автодополнения."""
        alert_id = uuid4()
        data = AlertAutocomplete(alert_id=alert_id, alert_name="Test Alert")
        assert data.alert_id == alert_id
        assert data.alert_name == "Test Alert"


class TestAlertAutocompleteResponse:
    """Тесты для AlertAutocompleteResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        alert_id = uuid4()
        item = AlertAutocomplete(alert_id=alert_id, alert_name="Test Alert")
        data = AlertAutocompleteResponse(alerts=[item], total=1)
        assert len(data.alerts) == 1
        assert data.total == 1
