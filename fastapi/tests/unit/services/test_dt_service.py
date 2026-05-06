"""
Модульные тесты для DTService.
"""

from typing import ClassVar
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.dt_repository import DTRepository
from schemas.dt import DTDetailCreate, DTDetailUpdate
from services.dt_service import DTService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestDTService:
    """Тесты для DTService."""

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=DTRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр DTService с моком репозитория."""
        return DTService(repository=mock_repo)

    async def test_get_dt_success(self, service, mock_repo):
        """Тест успешного получения DT."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_dt_by_alert_id.return_value = {
            "id": dt_id,
            "alert": alert_id,
            "content": '{"key": "value"}',
            "auto_create": True,
            "silence_time": '{"silence": "time"}',
        }

        result = await service.get_dt(alert_id)

        assert result.dt_id == dt_id
        assert result.alert_id == alert_id
        assert result.content == {"key": "value"}
        assert result.auto_create is True
        assert result.silence_time == {"silence": "time"}

    async def test_get_dt_alert_not_found(self, service, mock_repo):
        """Тест получения DT для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.get_dt(alert_id)

        assert exc_info.value.status_code == 404

    async def test_get_dt_not_found(self, service, mock_repo):
        """Тест получения несуществующего DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_dt_by_alert_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_dt(alert_id)

        assert exc_info.value.status_code == 404

    async def test_create_dt_success(self, service, mock_repo):
        """Тест успешного создания DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = False

        data = DTDetailCreate(content='{"key": "value"}', auto_create=True)

        result = await service.create_dt(alert_id, data)

        assert result is True
        mock_repo.create_dt.assert_called_once()

    async def test_create_dt_alert_not_found(self, service, mock_repo):
        """Тест создания DT для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = False

        data = DTDetailCreate(content='{"key": "value"}', auto_create=True)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_dt(alert_id, data)

        assert exc_info.value.status_code == 404

    async def test_create_dt_already_exists(self, service, mock_repo):
        """Тест создания DT когда он уже существует."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = True

        data = DTDetailCreate(content='{"key": "value"}', auto_create=True)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_dt(alert_id, data)

        assert exc_info.value.status_code == 409

    async def test_create_dt_invalid_content_json(self, service, mock_repo):
        """Тест создания DT с невалидным JSON в content - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        with pytest.raises(ValidationError) as exc_info:
            DTDetailCreate(content="invalid json", auto_create=True)

        # Проверяем что ошибка связана с content
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("content",) for err in errors)

    async def test_create_dt_content_too_long(self, service, mock_repo):
        """Тест создания DT с content превышающим лимит - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        long_content = '{"key": "' + "x" * 3001 + '"}'
        with pytest.raises(ValidationError) as exc_info:
            DTDetailCreate(content=long_content, auto_create=True)

        # Проверяем что ошибка связана с длиной content
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("content",) and "3000" in str(err.get("ctx", {}))
            for err in errors
        )

    async def test_update_dt_success(self, service, mock_repo):
        """Тест успешного обновления DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = True

        data = DTDetailUpdate(content='{"key": "updated"}', auto_create=False)

        result = await service.update_dt(alert_id, data)

        assert result is True
        mock_repo.update_dt.assert_called_once()

    async def test_update_dt_alert_not_found(self, service, mock_repo):
        """Тест обновления DT для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = False

        data = DTDetailUpdate(content='{"key": "updated"}')

        with pytest.raises(HTTPException) as exc_info:
            await service.update_dt(alert_id, data)

        assert exc_info.value.status_code == 404

    async def test_update_dt_not_found(self, service, mock_repo):
        """Тест обновления несуществующего DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = False

        data = DTDetailUpdate(content='{"key": "updated"}')

        with pytest.raises(HTTPException) as exc_info:
            await service.update_dt(alert_id, data)

        assert exc_info.value.status_code == 404

    async def test_delete_dt_success(self, service, mock_repo):
        """Тест успешного удаления DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = True

        result = await service.delete_dt(alert_id)

        assert result is True
        mock_repo.delete_dt.assert_called_once_with(alert_id)

    async def test_delete_dt_alert_not_found(self, service, mock_repo):
        """Тест удаления DT для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_dt(alert_id)

        assert exc_info.value.status_code == 404

    async def test_delete_dt_not_found(self, service, mock_repo):
        """Тест удаления несуществующего DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_dt(alert_id)

        assert exc_info.value.status_code == 404

    async def test_get_dt_invalid_content_json(self, service, mock_repo):
        """Тест получения DT с невалидным JSON в content."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_dt_by_alert_id.return_value = {
            "id": dt_id,
            "alert": alert_id,
            "content": "invalid json",
            "auto_create": True,
            "silence_time": None,
        }

        result = await service.get_dt(alert_id)

        # Должен обработать ошибку и использовать строку как есть
        assert result.content == "invalid json"

    async def test_get_dt_invalid_silence_time_json(self, service, mock_repo):
        """Тест получения DT с невалидным JSON в silence_time."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_dt_by_alert_id.return_value = {
            "id": dt_id,
            "alert": alert_id,
            "content": "{}",
            "auto_create": True,
            "silence_time": "invalid json",
        }

        result = await service.get_dt(alert_id)

        # Должен обработать ошибку и использовать строку как есть
        assert result.silence_time == "invalid json"

    async def test_get_dt_empty_content(self, service, mock_repo):
        """Тест получения DT с пустым content."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_dt_by_alert_id.return_value = {
            "id": dt_id,
            "alert": alert_id,
            "content": "   ",
            "auto_create": True,
            "silence_time": None,
        }

        result = await service.get_dt(alert_id)

        # Пустая строка должна стать пустым словарем
        assert result.content == {}

    async def test_get_dt_empty_silence_time(self, service, mock_repo):
        """Тест получения DT с пустым silence_time."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_dt_by_alert_id.return_value = {
            "id": dt_id,
            "alert": alert_id,
            "content": "{}",
            "auto_create": True,
            "silence_time": "   ",
        }

        result = await service.get_dt(alert_id)

        # Пустая строка должна стать пустым словарем
        assert result.silence_time == {}

    async def test_get_dt_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_dt_by_alert_id.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_dt(alert_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении DT" in exc_info.value.detail

    async def test_create_dt_silence_time_too_long(self, service, mock_repo):
        """Тест создания DT с silence_time превышающим лимит - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        long_silence_time = '{"key": "' + "x" * 1001 + '"}'
        with pytest.raises(ValidationError) as exc_info:
            DTDetailCreate(
                content="{}", auto_create=True, silence_time=long_silence_time
            )

        # Проверяем что ошибка связана с длиной silence_time
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("silence_time",)
            and "1000" in str(err.get("ctx", {}))
            for err in errors
        )

    async def test_create_dt_invalid_silence_time_json(
        self, service, mock_repo
    ):
        """Тест создания DT с невалидным JSON в silence_time - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        with pytest.raises(ValidationError) as exc_info:
            DTDetailCreate(
                content="{}", auto_create=True, silence_time="invalid json"
            )

        # Проверяем что ошибка связана с silence_time
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("silence_time",) for err in errors)

    async def test_create_dt_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при создании DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = False
        mock_repo.create_dt.side_effect = Exception("Ошибка БД")

        data = DTDetailCreate(content="{}", auto_create=True)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_dt(alert_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при создании DT" in exc_info.value.detail

    async def test_update_dt_content_too_long(self, service, mock_repo):
        """Тест обновления DT с content превышающим лимит - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        long_content = '{"key": "' + "x" * 3001 + '"}'
        with pytest.raises(ValidationError) as exc_info:
            DTDetailUpdate(content=long_content)

        # Проверяем что ошибка связана с длиной content
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("content",) and "3000" in str(err.get("ctx", {}))
            for err in errors
        )

    async def test_update_dt_invalid_content_json(self, service, mock_repo):
        """Тест обновления DT с невалидным JSON в content - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        with pytest.raises(ValidationError) as exc_info:
            DTDetailUpdate(content="invalid json")

        # Проверяем что ошибка связана с content
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("content",) for err in errors)

    async def test_update_dt_silence_time_too_long(self, service, mock_repo):
        """Тест обновления DT с silence_time превышающим лимит - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        long_silence_time = '{"key": "' + "x" * 1001 + '"}'
        with pytest.raises(ValidationError) as exc_info:
            DTDetailUpdate(silence_time=long_silence_time)

        # Проверяем что ошибка связана с длиной silence_time
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("silence_time",)
            and "1000" in str(err.get("ctx", {}))
            for err in errors
        )

    async def test_update_dt_invalid_silence_time_json(
        self, service, mock_repo
    ):
        """Тест обновления DT с невалидным JSON в silence_time - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        with pytest.raises(ValidationError) as exc_info:
            DTDetailUpdate(silence_time="invalid json")

        # Проверяем что ошибка связана с silence_time
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("silence_time",) for err in errors)

    async def test_update_dt_empty_silence_time(self, service, mock_repo):
        """Тест обновления DT с пустым silence_time."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = True
        mock_repo.update_dt.return_value = True

        data = DTDetailUpdate(silence_time="   ")

        result = await service.update_dt(alert_id, data)

        assert result is True
        # Проверяем, что пустая строка передается в репозиторий
        # update_dt(alert_id, content, auto_create, silence_time)
        call_args = mock_repo.update_dt.call_args
        assert call_args[0][3] == ""  # silence_time должен быть пустой строкой

    async def test_update_dt_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при обновлении DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = True
        mock_repo.update_dt.side_effect = Exception("Ошибка БД")

        data = DTDetailUpdate(content="{}")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_dt(alert_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при обновлении DT" in exc_info.value.detail

    async def test_delete_dt_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при удалении DT."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_dt_exists.return_value = True
        mock_repo.delete_dt.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_dt(alert_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при удалении DT" in exc_info.value.detail

    async def test_get_dt_with_mapping_row(self, service, mock_repo):
        """Покрыть _as_dict через _mapping."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_repo.check_alert_exists.return_value = True

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": dt_id,
                "alert": alert_id,
                "content": '{"m":1}',
                "auto_create": False,
                "silence_time": None,
            }

        mock_repo.get_dt_by_alert_id.return_value = RowObj()
        result = await service.get_dt(alert_id)
        assert result.dt_id == dt_id
        assert result.content == {"m": 1}

    async def test_get_dt_with_keys_row(self, service, mock_repo):
        """Покрыть _as_dict через keys()/index."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_repo.check_alert_exists.return_value = True

        class RowObj:
            def keys(self):
                return ["id", "alert", "content", "auto_create", "silence_time"]

            def __getitem__(self, idx):
                return [dt_id, alert_id, '{"k":"v"}', True, ""][idx]

        mock_repo.get_dt_by_alert_id.return_value = RowObj()
        result = await service.get_dt(alert_id)
        assert result.content == {"k": "v"}

    async def test_as_dict_plain_object_returns_empty(self, service):
        """Покрыть финальную ветку _as_dict -> {}."""
        assert service._as_dict(object()) == {}

    async def test_as_dict_keys_index_error_returns_empty(self, service):
        """Покрыть except внутри _as_dict."""

        class BadRow:
            def keys(self):
                return ["id"]

            def __getitem__(self, idx):
                raise IndexError("out")

        assert service._as_dict(BadRow()) == {}
