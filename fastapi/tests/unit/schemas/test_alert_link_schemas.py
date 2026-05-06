"""
Модульные тесты для валидации схем AlertLink.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.alert_link import (
    AlertLinkAutocomplete,
    AlertLinkCreate,
    AlertLinkListItem,
    AlertLinkListResponse,
)


class TestAlertLinkListItem:
    """Тесты для AlertLinkListItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        link_id = uuid4()
        alert_id = uuid4()
        data = AlertLinkListItem(
            link_id=link_id,
            alert_id=alert_id,
            link_name="Test Link",
            link_url="http://test.com",
        )
        assert data.link_id == link_id
        assert data.alert_id == alert_id
        assert data.link_name == "Test Link"
        assert data.link_url == "http://test.com"


class TestAlertLinkListResponse:
    """Тесты для AlertLinkListResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        link_id = uuid4()
        alert_id = uuid4()
        item = AlertLinkListItem(
            link_id=link_id,
            alert_id=alert_id,
            link_name="Test Link",
            link_url="http://test.com",
        )
        data = AlertLinkListResponse(links=[item])
        assert len(data.links) == 1

    def test_empty_response(self):
        """Тест пустого ответа."""
        data = AlertLinkListResponse(links=[])
        assert len(data.links) == 0


class TestAlertLinkAutocomplete:
    """Тесты для AlertLinkAutocomplete."""

    def test_valid_autocomplete(self):
        """Тест валидного автодополнения."""
        link_id = uuid4()
        data = AlertLinkAutocomplete(link_id=link_id, link_name="Test Link")
        assert data.link_id == link_id
        assert data.link_name == "Test Link"


class TestAlertLinkCreate:
    """Тесты для AlertLinkCreate."""

    def test_valid_create(self):
        """Тест валидного создания."""
        alert_id = uuid4()
        data = AlertLinkCreate(
            alert_id=alert_id,
            link_name="Test Link",
            link_url="http://test.com",
        )
        assert data.alert_id == alert_id
        assert data.link_name == "Test Link"
        assert data.link_url == "http://test.com"
