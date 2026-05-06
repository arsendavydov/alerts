"""
Модульные тесты для ScreenshotsService.
Особое внимание к валидации JSON в image_data.
"""

import json
from typing import ClassVar
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.screenshots_repository import ScreenshotsRepository
from schemas.screenshots import ScreenshotCreate, ScreenshotUpdate
from services.screenshots_service import ScreenshotsService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestScreenshotsService:
    """Тесты для ScreenshotsService."""

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=ScreenshotsRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр ScreenshotsService с моком репозитория."""
        return ScreenshotsService(repository=mock_repo)

    async def test_search_screenshots(self, service, mock_repo):
        """Тест поиска скриншотов."""
        screenshot_id = uuid4()
        mock_repo.search_screenshots.return_value = (
            [
                {
                    "id": screenshot_id,
                    "name": "test",
                    "description": "description",
                    "image_data": '{"url": "test"}',
                }
            ],
            1,
        )
        result = await service.search_screenshots(
            query="test", limit=50, offset=0
        )

        assert result.total == 1
        assert result.limit == 50
        assert result.offset == 0
        assert len(result.screenshots) == 1
        assert result.screenshots[0].screenshot_id == screenshot_id

    async def test_search_screenshots_without_query(self, service, mock_repo):
        """Тест поиска скриншотов без query."""
        screenshot_id = uuid4()
        mock_repo.search_screenshots.return_value = (
            [
                {
                    "id": screenshot_id,
                    "name": "test",
                    "description": "description",
                    "image_data": '{"url": "test"}',
                }
            ],
            1,
        )
        result = await service.search_screenshots(limit=50, offset=0)

        assert result.total == 1
        assert len(result.screenshots) == 1

    async def test_search_screenshots_with_sorting(self, service, mock_repo):
        """Тест поиска скриншотов с сортировкой."""
        screenshot_id = uuid4()
        mock_repo.search_screenshots.return_value = (
            [
                {
                    "id": screenshot_id,
                    "name": "test",
                    "description": "description",
                    "image_data": '{"url": "test"}',
                }
            ],
            1,
        )
        result = await service.search_screenshots(
            query="test", order_by="name", order_dir="desc", limit=50, offset=0
        )

        assert result.total == 1
        mock_repo.search_screenshots.assert_called_once_with(
            query="test", order_by="name", order_dir="desc", limit=50, offset=0
        )

    # Тесты валидации order_by/order_dir удалены - валидация теперь происходит в роутерах через Pydantic Literal типы

    async def test_get_screenshot_success(self, service, mock_repo):
        """Тест успешного получения скриншота."""
        screenshot_id = uuid4()
        image_data_json = '{"url": "test.jpg", "width": 1920}'
        mock_repo.get_screenshot_by_id.return_value = {
            "id": screenshot_id,
            "name": "test",
            "description": "description",
            "image_data": image_data_json,
        }

        result = await service.get_screenshot(screenshot_id)

        assert result.screenshot_id == screenshot_id
        assert result.name == "test"
        # Сервис возвращает строку image_data, а не распарсенный JSON
        assert result.image_data == image_data_json

    async def test_get_screenshot_with_array_json(self, service, mock_repo):
        """Тест получения скриншота с JSON массивом."""
        screenshot_id = uuid4()
        image_data_json = '["url1.jpg", "url2.jpg"]'
        mock_repo.get_screenshot_by_id.return_value = {
            "id": screenshot_id,
            "name": "test",
            "description": "desc",
            "image_data": image_data_json,
        }
        result = await service.get_screenshot(screenshot_id)
        assert result.image_data == image_data_json

    async def test_get_screenshot_not_found(self, service, mock_repo):
        """Тест получения несуществующего скриншота."""
        screenshot_id = uuid4()
        mock_repo.get_screenshot_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_screenshot(screenshot_id)

        assert exc_info.value.status_code == 404

    async def test_create_screenshot_success_with_object_json(
        self, service, mock_repo
    ):
        """Тест создания скриншота с JSON объектом."""
        screenshot_id = uuid4()
        mock_repo.create_screenshot.return_value = screenshot_id

        data = ScreenshotCreate(
            name="test", description="desc", image_data='{"url": "test.jpg"}'
        )

        result = await service.create_screenshot(data)

        assert result == screenshot_id
        mock_repo.create_screenshot.assert_called_once()

    async def test_create_screenshot_success_with_array_json(
        self, service, mock_repo
    ):
        """Тест создания скриншота с JSON массивом."""
        screenshot_id = uuid4()
        mock_repo.create_screenshot.return_value = screenshot_id

        data = ScreenshotCreate(
            name="test",
            description="desc",
            image_data='["url1.jpg", "url2.jpg"]',
        )

        result = await service.create_screenshot(data)

        assert result == screenshot_id

    async def test_create_screenshot_invalid_json(self, service, mock_repo):
        """Тест создания скриншота с невалидным JSON."""
        # Валидация происходит на уровне Pydantic схемы, поэтому используем ValidationError
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScreenshotCreate(
                name="test", description="desc", image_data="invalid json"
            )

        mock_repo.create_screenshot.assert_not_called()

    async def test_update_screenshot_success(self, service, mock_repo):
        """Тест успешного обновления скриншота."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = True
        mock_repo.update_screenshot.return_value = True

        data = ScreenshotUpdate(
            name="updated", image_data='{"url": "new.jpg"}'
        )

        result = await service.update_screenshot(screenshot_id, data)

        assert result is True
        mock_repo.check_screenshot_exists.assert_called_once_with(
            screenshot_id
        )
        mock_repo.update_screenshot.assert_called_once()

    async def test_update_screenshot_not_found(self, service, mock_repo):
        """Тест обновления несуществующего скриншота."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = False

        data = ScreenshotUpdate(name="updated")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_screenshot(screenshot_id, data)

        assert exc_info.value.status_code == 404

    async def test_update_screenshot_invalid_json(self, service, mock_repo):
        """Тест обновления скриншота с невалидным JSON."""
        # Валидация происходит на уровне Pydantic схемы, поэтому используем ValidationError
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScreenshotUpdate(image_data="invalid json")

    async def test_update_screenshot_without_image_data(
        self, service, mock_repo
    ):
        """Тест обновления скриншота без image_data."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = True
        mock_repo.update_screenshot.return_value = True

        data = ScreenshotUpdate(name="updated")

        result = await service.update_screenshot(screenshot_id, data)

        assert result is True

    async def test_delete_screenshot_success(self, service, mock_repo):
        """Тест успешного удаления скриншота."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = True
        mock_repo.delete_screenshot.return_value = True

        result = await service.delete_screenshot(screenshot_id)

        assert result is True
        mock_repo.check_screenshot_exists.assert_called_once_with(
            screenshot_id
        )
        mock_repo.delete_screenshot.assert_called_once_with(screenshot_id)

    async def test_delete_screenshot_not_found(self, service, mock_repo):
        """Тест удаления несуществующего скриншота."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_screenshot(screenshot_id)

        assert exc_info.value.status_code == 404

    async def test_search_screenshots_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при поиске."""
        mock_repo.search_screenshots.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.search_screenshots(query="test")

        assert exc_info.value.status_code == 500
        assert "Ошибка при поиске скриншотов" in exc_info.value.detail

    async def test_get_screenshot_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении скриншота."""
        screenshot_id = uuid4()
        mock_repo.get_screenshot_by_id.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_screenshot(screenshot_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении скриншота" in exc_info.value.detail

    async def test_create_screenshot_invalid_json_in_service(
        self, service, mock_repo
    ):
        """Тест создания скриншота с невалидным JSON на уровне сервиса."""
        # Создаем объект с невалидным JSON, обходя валидацию Pydantic
        # Используем прямой вызов с моком, который пропустит валидацию схемы
        from schemas.screenshots import ScreenshotCreate

        # Создаем объект с невалидным JSON (если схема это пропустит)
        # Но обычно Pydantic валидирует, поэтому тестируем обработку ошибки в сервисе
        screenshot_id = uuid4()
        mock_repo.create_screenshot.return_value = screenshot_id

        # Создаем валидный объект, но мокируем json.loads чтобы он упал
        from unittest.mock import patch

        data = ScreenshotCreate(
            name="test", description="desc", image_data='{"url": "test.jpg"}'
        )

        with patch(
            "services.screenshots_service.json.loads",
            side_effect=json.JSONDecodeError("Invalid", "", 0),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_screenshot(data)

            assert exc_info.value.status_code == 400
            assert "валидным JSON" in exc_info.value.detail

    async def test_create_screenshot_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при создании скриншота."""
        mock_repo.create_screenshot.side_effect = Exception("Ошибка БД")

        data = ScreenshotCreate(
            name="test", description="desc", image_data='{"url": "test.jpg"}'
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_screenshot(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при создании скриншота" in exc_info.value.detail

    async def test_update_screenshot_invalid_json_in_service(
        self, service, mock_repo
    ):
        """Тест обновления скриншота с невалидным JSON на уровне сервиса."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = True

        from unittest.mock import patch

        data = ScreenshotUpdate(image_data='{"url": "test.jpg"}')

        with patch(
            "services.screenshots_service.json.loads",
            side_effect=json.JSONDecodeError("Invalid", "", 0),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await service.update_screenshot(screenshot_id, data)

            assert exc_info.value.status_code == 400
            assert "валидным JSON" in exc_info.value.detail

    async def test_update_screenshot_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при обновлении скриншота."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = True
        mock_repo.update_screenshot.side_effect = Exception("Ошибка БД")

        data = ScreenshotUpdate(name="updated")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_screenshot(screenshot_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при обновлении скриншота" in exc_info.value.detail

    async def test_delete_screenshot_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при удалении скриншота."""
        screenshot_id = uuid4()
        mock_repo.check_screenshot_exists.return_value = True
        mock_repo.delete_screenshot.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_screenshot(screenshot_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при удалении скриншота" in exc_info.value.detail

    async def test_search_screenshots_with_mapping_row(self, service, mock_repo):
        """Покрыть _as_dict через _mapping."""
        sid = uuid4()

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": sid,
                "name": "mapped",
                "description": "d",
                "image_data": '{"k":"v"}',
            }

        mock_repo.search_screenshots.return_value = ([RowObj()], 1)
        result = await service.search_screenshots()
        assert result.total == 1
        assert result.screenshots[0].name == "mapped"

    async def test_get_screenshot_with_keys_row(self, service, mock_repo):
        """Покрыть _as_dict через keys()/index."""
        sid = uuid4()

        class RowObj:
            def keys(self):
                return ["id", "name", "description", "image_data"]

            def __getitem__(self, idx):
                return [sid, "n", "d", '{"x":1}'][idx]

        mock_repo.get_screenshot_by_id.return_value = RowObj()
        result = await service.get_screenshot(sid)
        assert result.name == "n"

    async def test_as_dict_plain_object_returns_empty(self, service):
        """Покрыть финальную ветку _as_dict -> {}."""
        assert service._as_dict(object()) == {}

    async def test_as_dict_keys_index_error_returns_empty(self, service):
        """Покрыть ветку except внутри _as_dict."""

        class BadRow:
            def keys(self):
                return ["id"]

            def __getitem__(self, idx):
                raise IndexError("out")

        assert service._as_dict(BadRow()) == {}

    async def test_search_screenshots_http_exception_passthrough(
        self, service, mock_repo
    ):
        """Покрыть except HTTPException: raise."""
        from fastapi import HTTPException as FastAPIHTTPException

        mock_repo.search_screenshots.side_effect = FastAPIHTTPException(
            status_code=400, detail="bad"
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.search_screenshots()
        assert exc_info.value.status_code == 400
