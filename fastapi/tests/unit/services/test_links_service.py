"""
Модульные тесты для LinksService.
"""

from typing import ClassVar
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.links_repository import LinksRepository
from schemas.links import LinkDetailCreate, LinkDetailUpdate
from services.links_service import LinksService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestLinksService:
    """Тесты для LinksService."""

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=LinksRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр LinksService с моком репозитория."""
        return LinksService(repository=mock_repo)

    async def test_get_links_by_alert_success(self, service, mock_repo):
        """Тест успешного получения линков алерта."""
        alert_id = uuid4()
        link_id = uuid4()
        mock_repo.get_links_by_alert.return_value = [
            {
                "id": link_id,
                "link_name": "test_link",
                "link_url": "https://example.com",
            }
        ]

        result = await service.get_links_by_alert(alert_id)

        assert result.total == 1
        assert len(result.links) == 1
        assert result.links[0].link_id == link_id

    async def test_get_link_detail_success(self, service, mock_repo):
        """Тест успешного получения деталей линка."""
        link_id = uuid4()
        alert_id = uuid4()
        mock_repo.get_link_by_id.return_value = {
            "id": link_id,
            "alert": alert_id,
            "alert_name": "test_alert",
            "link_name": "test_link",
            "link_url": "https://example.com",
        }

        result = await service.get_link_detail(link_id)

        assert result.link_id == link_id
        assert result.alert_id == alert_id
        assert result.link_name == "test_link"

    async def test_get_link_detail_not_found(self, service, mock_repo):
        """Тест получения несуществующего линка."""
        link_id = uuid4()
        mock_repo.get_link_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_link_detail(link_id)

        assert exc_info.value.status_code == 404

    async def test_create_link_success(self, service, mock_repo):
        """Тест успешного создания линка."""
        data = LinkDetailCreate(
            alert_id=uuid4(),
            link_name="test_link",
            link_url="https://example.com",
        )

        result = await service.create_link(data)

        assert result is True
        mock_repo.create_link.assert_called_once()

    async def test_update_link_success(self, service, mock_repo):
        """Тест успешного обновления линка."""
        link_id = uuid4()
        mock_repo.check_link_exists.return_value = True

        data = LinkDetailUpdate(
            link_id=link_id,
            link_name="updated_link",
            link_url="https://updated.com",
        )

        result = await service.update_link(data)

        assert result is True
        mock_repo.check_link_exists.assert_called_once_with(link_id)
        mock_repo.update_link.assert_called_once()

    async def test_update_link_not_found(self, service, mock_repo):
        """Тест обновления несуществующего линка."""
        link_id = uuid4()
        mock_repo.check_link_exists.return_value = False

        data = LinkDetailUpdate(link_id=link_id, link_name="updated")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_link(data)

        assert exc_info.value.status_code == 404

    async def test_delete_link_success(self, service, mock_repo):
        """Тест успешного удаления линка."""
        link_id = uuid4()
        mock_repo.check_link_exists.return_value = True

        result = await service.delete_link(link_id)

        assert result is True
        mock_repo.check_link_exists.assert_called_once_with(link_id)
        mock_repo.delete_link.assert_called_once_with(link_id)

    async def test_delete_link_not_found(self, service, mock_repo):
        """Тест удаления несуществующего линка."""
        link_id = uuid4()
        mock_repo.check_link_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_link(link_id)

        assert exc_info.value.status_code == 404

    async def test_get_links_by_alert_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении линков."""
        alert_id = uuid4()
        mock_repo.get_links_by_alert.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_links_by_alert(alert_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении линков алерта" in exc_info.value.detail

    async def test_get_link_detail_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении деталей линка."""
        link_id = uuid4()
        mock_repo.get_link_by_id.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_link_detail(link_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении линка" in exc_info.value.detail

    async def test_create_link_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при создании линка."""
        mock_repo.create_link.side_effect = Exception("Ошибка БД")

        data = LinkDetailCreate(
            alert_id=uuid4(),
            link_name="test_link",
            link_url="https://example.com",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_link(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при создании линка" in exc_info.value.detail

    async def test_update_link_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при обновлении линка."""
        link_id = uuid4()
        mock_repo.check_link_exists.return_value = True
        mock_repo.update_link.side_effect = Exception("Ошибка БД")

        data = LinkDetailUpdate(link_id=link_id, link_name="updated")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_link(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при обновлении линка" in exc_info.value.detail

    async def test_delete_link_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при удалении линка."""
        link_id = uuid4()
        mock_repo.check_link_exists.return_value = True
        mock_repo.delete_link.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_link(link_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при удалении линка" in exc_info.value.detail

    async def test_get_links_by_alert_with_mapping_rows(self, service, mock_repo):
        """Покрыть _as_dict через _mapping."""
        alert_id = uuid4()

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": uuid4(),
                "link_name": "m",
                "link_url": "https://m.local",
            }

        mock_repo.get_links_by_alert.return_value = [RowObj()]
        result = await service.get_links_by_alert(alert_id)
        assert result.total == 1
        assert result.links[0].link_name == "m"

    async def test_get_link_detail_with_keys_row(self, service, mock_repo):
        """Покрыть _as_dict через keys()/index."""
        link_id = uuid4()
        alert_id = uuid4()

        class RowObj:
            def keys(self):
                return ["id", "alert", "alert_name", "link_name", "link_url"]

            def __getitem__(self, idx):
                return [link_id, alert_id, "A", "L", "https://k.local"][idx]

        mock_repo.get_link_by_id.return_value = RowObj()
        result = await service.get_link_detail(link_id)
        assert result.alert_name == "A"

    async def test_get_link_detail_with_bad_keys_row(self, service, mock_repo):
        """Покрыть _as_dict fallback при ошибке keys()."""
        link_id = uuid4()

        class BadRow:
            def keys(self):
                raise RuntimeError("bad")

        mock_repo.get_link_by_id.return_value = BadRow()
        with pytest.raises(HTTPException) as exc_info:
            await service.get_link_detail(link_id)
        assert exc_info.value.status_code == 500

    async def test_as_dict_plain_object_returns_empty(self, service):
        """Покрыть финальную ветку _as_dict -> {}."""
        assert service._as_dict(object()) == {}
