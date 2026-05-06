"""
Модульные тесты для валидации схем Links.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.links import (
    LinkByAlertListItem,
    LinkByAlertListResponse,
    LinkDetail,
    LinkDetailCreate,
    LinkDetailUpdate,
)


class TestLinkDetail:
    """Тесты для LinkDetail."""

    def test_valid_detail(self):
        """Тест валидной детальной информации."""
        link_id = uuid4()
        alert_id = uuid4()
        data = LinkDetail(
            link_id=link_id,
            alert_id=alert_id,
            alert_name="Test Alert",
            link_name="Test Link",
            link_url="http://test.com",
        )
        assert data.link_id == link_id
        assert data.alert_id == alert_id
        assert data.link_name == "Test Link"
        assert data.link_url == "http://test.com"


class TestLinkDetailCreate:
    """Тесты для LinkDetailCreate."""

    def test_valid_create(self):
        """Тест валидного создания."""
        alert_id = uuid4()
        data = LinkDetailCreate(
            alert_id=alert_id,
            link_name="Test Link",
            link_url="http://test.com",
        )
        assert data.alert_id == alert_id
        assert data.link_name == "Test Link"
        assert data.link_url == "http://test.com"


class TestLinkDetailUpdate:
    """Тесты для LinkDetailUpdate."""

    def test_all_fields_optional(self):
        """Тест что все поля опциональны."""
        link_id = uuid4()
        data = LinkDetailUpdate(link_id=link_id)
        assert data.link_id == link_id
        assert data.link_name is None
        assert data.link_url is None

    def test_partial_update(self):
        """Тест частичного обновления."""
        link_id = uuid4()
        data = LinkDetailUpdate(link_id=link_id, link_name="Updated Link")
        assert data.link_name == "Updated Link"
        assert data.link_url is None


class TestLinkByAlertListItem:
    """Тесты для LinkByAlertListItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        link_id = uuid4()
        data = LinkByAlertListItem(
            link_id=link_id, link_name="Test Link", link_url="http://test.com"
        )
        assert data.link_id == link_id
        assert data.link_name == "Test Link"
        assert data.link_url == "http://test.com"


class TestLinkByAlertListResponse:
    """Тесты для LinkByAlertListResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        link_id = uuid4()
        item = LinkByAlertListItem(
            link_id=link_id, link_name="Test Link", link_url="http://test.com"
        )
        data = LinkByAlertListResponse(links=[item], total=1)
        assert len(data.links) == 1
        assert data.total == 1

    def test_empty_response(self):
        """Тест пустого ответа."""
        data = LinkByAlertListResponse(links=[], total=0)
        assert len(data.links) == 0
        assert data.total == 0
