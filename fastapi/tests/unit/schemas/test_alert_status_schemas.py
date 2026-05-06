"""
Модульные тесты для валидации схем AlertStatus.
"""

import sys
from pathlib import Path

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.alert_status import (
    AlertStatusCreate,
    AlertStatusListItem,
    AlertStatusListResponse,
    AlertStatusUpdate,
)


class TestAlertStatusListItem:
    """Тесты для AlertStatusListItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        data = AlertStatusListItem(status_id="1", status_name="Test Status")
        assert data.status_id == "1"
        assert data.status_name == "Test Status"

    def test_with_optional_fields(self):
        """Тест с опциональными полями."""
        data = AlertStatusListItem(
            status_id="1",
            status_name="Test Status",
            first_action_text_template="First action",
            continue_action_text_template="Continue action",
        )
        assert data.first_action_text_template == "First action"
        assert data.continue_action_text_template == "Continue action"


class TestAlertStatusListResponse:
    """Тесты для AlertStatusListResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        item = AlertStatusListItem(status_id="1", status_name="Test Status")
        data = AlertStatusListResponse(statuses=[item])
        assert len(data.statuses) == 1

    def test_empty_response(self):
        """Тест пустого ответа."""
        data = AlertStatusListResponse(statuses=[])
        assert len(data.statuses) == 0


class TestAlertStatusCreate:
    """Тесты для AlertStatusCreate."""

    def test_valid_create(self):
        """Тест валидного создания."""
        data = AlertStatusCreate(status_id="1", status_name="Test Status")
        assert data.status_id == "1"
        assert data.status_name == "Test Status"

    def test_with_optional_fields(self):
        """Тест с опциональными полями."""
        data = AlertStatusCreate(
            status_id="1",
            status_name="Test Status",
            first_action_text_template="First action",
            continue_action_text_template="Continue action",
        )
        assert data.first_action_text_template == "First action"


class TestAlertStatusUpdate:
    """Тесты для AlertStatusUpdate."""

    def test_valid_update(self):
        """Тест валидного обновления (наследуется от Create)."""
        data = AlertStatusUpdate(status_id="1", status_name="Updated Status")
        assert data.status_id == "1"
        assert data.status_name == "Updated Status"
