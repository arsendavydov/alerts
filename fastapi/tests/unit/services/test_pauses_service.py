"""
Модульные тесты для PausesService.
"""

from datetime import datetime, timedelta, timezone
from typing import ClassVar
from unittest.mock import ANY, AsyncMock, patch
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.pauses_repository import PausesRepository
from schemas.pauses import (
    AlertPauseRemoveRequest,
    AlertPauseScheduleRequest,
    AlertPauseUpdateRequest,
)
from services.pauses_service import PausesService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestPausesService:
    """Тесты для PausesService."""

    @pytest.fixture(autouse=True)
    def _stub_uow_session(self):
        cm = AsyncMock()
        cm.__aenter__.return_value = None
        cm.__aexit__.return_value = None
        with patch(
            "services.pauses_service.async_session_scope", return_value=cm
        ):
            yield

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=PausesRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр PausesService с моком репозитория."""
        return PausesService(repository=mock_repo)

    async def test_get_alert_pauses_success(self, service, mock_repo):
        """Тест успешного получения пауз алерта."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_pauses.return_value = (
            [
                {
                    "id": pause_id,
                    "start_time": datetime.now(timezone.utc),
                    "end_time": None,
                    "start_user": "user1",
                    "end_user": None,
                    "comment": "pause comment",
                }
            ],
            1,
        )

        result = await service.get_alert_pauses(alert_id)

        assert result.total == 1
        assert len(result.pauses) == 1
        assert result.pauses[0].pause_id == pause_id
        assert result.pauses[0].comment == "pause comment"

    async def test_get_alert_pauses_passes_timestamps_from_repository(
        self, service, mock_repo
    ):
        """Репозиторий отдаёт время уже в таймзоне БД; сервис собирает схему без повторной конвертации."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.check_alert_exists.return_value = True

        db_tz = timezone(timedelta(hours=3))
        utc_dt = datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc)
        localized = utc_dt.astimezone(db_tz)
        mock_repo.get_pauses.return_value = (
            [
                {
                    "id": pause_id,
                    "start_time": localized,
                    "end_time": None,
                    "start_user": "user1",
                    "end_user": None,
                }
            ],
            1,
        )

        result = await service.get_alert_pauses(alert_id)

        pause = result.pauses[0]
        assert pause.start_time == localized
        assert pause.start_time.tzinfo == db_tz
        assert pause.start_time.hour == 15

    async def test_get_alert_pauses_with_mapping_row(self, service, mock_repo):
        """Позитивный ORM-style кейс: пауза приходит через _mapping."""
        alert_id = uuid4()
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc)
        mock_repo.check_alert_exists.return_value = True

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": pause_id,
                "start_time": start_time,
                "end_time": None,
                "start_user": "user1",
                "end_user": None,
                "comment": "mapped comment",
            }

        mock_repo.get_pauses.return_value = ([RowObj()], 1)

        result = await service.get_alert_pauses(alert_id)

        assert result.total == 1
        assert len(result.pauses) == 1
        assert result.pauses[0].pause_id == pause_id
        assert result.pauses[0].comment == "mapped comment"

    async def test_get_alert_pauses_invalid_filter(self, service, mock_repo):
        """Тест получения пауз с невалидным фильтром."""
        alert_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await service.get_alert_pauses(alert_id, filter_type="invalid")

        assert exc_info.value.status_code == 400

    # Тесты валидации order_by/order_dir удалены - валидация теперь происходит в роутерах через Pydantic Literal типы

    async def test_get_alert_pauses_alert_not_found(self, service, mock_repo):
        """Тест получения пауз для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.get_alert_pauses(alert_id)

        assert exc_info.value.status_code == 404

    async def test_schedule_alert_pause_success(self, service, mock_repo):
        """Тест успешной установки паузы."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(
            login="test_user",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-02T00:00:00Z",
            comment="schedule reason",
        )

        result = await service.schedule_alert_pause(alert_id, data)

        assert result is True
        mock_repo.create_pause.assert_called_once()
        assert mock_repo.create_pause.call_args.kwargs["comment"] == "schedule reason"

    async def test_schedule_alert_pause_empty_start_time(
        self, service, mock_repo
    ):
        """Тест установки паузы с пустым start_time."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(
            login="test_user", start_time="", end_time="2024-01-02T00:00:00Z"
        )

        result = await service.schedule_alert_pause(alert_id, data)

        assert result is True
        # Проверяем что use_now_for_start=True
        call_args = mock_repo.create_pause.call_args
        assert call_args[1]["use_now_for_start"] is True

    async def test_stop_alert_pause_success(self, service, mock_repo):
        """Тест успешной остановки всех пауз."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        data = AlertPauseRemoveRequest(
            login="test_user", comment="stop reason"
        )

        result = await service.stop_alert_pause(alert_id, data)

        assert result is True
        mock_repo.check_alert_exists.assert_called_once_with(alert_id, ANY)
        mock_repo.stop_all_active_pauses.assert_called_once_with(
            alert_id, "test_user", session=ANY, comment="stop reason"
        )

    async def test_stop_alert_pause_alert_not_found(self, service, mock_repo):
        """Тест остановки пауз для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = False
        data = AlertPauseRemoveRequest(login="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.stop_alert_pause(alert_id, data)

        assert exc_info.value.status_code == 404

    async def test_stop_specific_alert_pause_success(self, service, mock_repo):
        """Тест успешной остановки конкретной паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        now = datetime.now(timezone.utc)
        # Используем datetime с timezone для совместимости
        from datetime import timedelta

        future = now + timedelta(days=365)
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": now,
            "end_time": future,
            "start_user": "user1",
            "end_user": None,
        }
        data = AlertPauseRemoveRequest(login="test_user")

        result = await service.stop_specific_alert_pause(
            alert_id, pause_id, data
        )

        assert result is True
        mock_repo.stop_specific_pause.assert_called_once()
        assert "comment" not in mock_repo.stop_specific_pause.call_args.kwargs

    async def test_stop_specific_alert_pause_not_found(
        self, service, mock_repo
    ):
        """Тест остановки несуществующей паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = None
        data = AlertPauseRemoveRequest(login="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.stop_specific_alert_pause(alert_id, pause_id, data)

        assert exc_info.value.status_code == 404

    async def test_stop_specific_alert_pause_already_ended(
        self, service, mock_repo
    ):
        """Тест остановки уже завершенной паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        past = datetime.now(timezone.utc).replace(year=2020)
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": past,
            "end_time": past,
            "start_user": "user1",
            "end_user": "user2",
        }
        data = AlertPauseRemoveRequest(login="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.stop_specific_alert_pause(alert_id, pause_id, data)

        assert exc_info.value.status_code == 400

    async def test_delete_alert_pause_success(self, service, mock_repo):
        """Тест успешного удаления паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }

        result = await service.delete_alert_pause(alert_id, pause_id)

        assert result is True
        mock_repo.get_pause_by_id.assert_called_once_with(
            pause_id, alert_id, ANY
        )
        mock_repo.delete_pause.assert_called_once_with(pause_id, alert_id, ANY)

    async def test_delete_alert_pause_not_found(self, service, mock_repo):
        """Тест удаления несуществующей паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_alert_pause(alert_id, pause_id)

        assert exc_info.value.status_code == 404

    async def test_toggle_alert_pause_success(self, service, mock_repo):
        """Тест успешного переключения паузы."""
        alert_id = uuid4()
        mock_repo.toggle_alert_pause.return_value = True

        result = await service.toggle_alert_pause(
            alert_id, "test_user", "toggle reason"
        )

        assert result is True
        mock_repo.toggle_alert_pause.assert_called_once_with(
            alert_id, "test_user", "toggle reason"
        )

    async def test_toggle_alert_pause_alert_not_found(
        self, service, mock_repo
    ):
        """Тест переключения паузы для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.toggle_alert_pause.side_effect = ValueError(
            "Алерт не найден"
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.toggle_alert_pause(alert_id, "test_user")

        assert exc_info.value.status_code == 404

    async def test_toggle_alert_pause_value_error_passthrough(
        self, service, mock_repo
    ):
        """Покрыть re-raise ValueError, если текст другой."""
        alert_id = uuid4()
        mock_repo.toggle_alert_pause.side_effect = ValueError("другая ошибка")
        with pytest.raises(ValueError):
            await service.toggle_alert_pause(alert_id, "test_user")

    async def test_toggle_alert_pause_repository_error(
        self, service, mock_repo
    ):
        """Тест переключения паузы с неожиданной ошибкой репозитория."""
        alert_id = uuid4()
        mock_repo.toggle_alert_pause.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.toggle_alert_pause(alert_id, "test_user")

        assert exc_info.value.status_code == 500

    async def test_update_alert_pause_success(self, service, mock_repo):
        """Тест успешного обновления паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        mock_repo.update_pause.return_value = True

        data = AlertPauseUpdateRequest(
            login="test_user",
            start_time="2024-01-01T00:00:00Z",
            comment="update reason",
        )

        result = await service.update_alert_pause(alert_id, pause_id, data)

        assert result is True
        mock_repo.update_pause.assert_called_once()
        assert mock_repo.update_pause.call_args.kwargs["comment"] == "update reason"

    async def test_update_alert_pause_not_found(self, service, mock_repo):
        """Тест обновления несуществующей паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = None

        data = AlertPauseUpdateRequest(login="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert_pause(alert_id, pause_id, data)

        assert exc_info.value.status_code == 404

    async def test_get_alert_pauses_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении пауз."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_pauses.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_alert_pauses(alert_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении истории пауз" in exc_info.value.detail

    async def test_schedule_alert_pause_empty_end_time(
        self, service, mock_repo
    ):
        """Тест установки паузы с пустым end_time (бессрочная пауза)."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(
            login="test_user", start_time="2024-01-01T00:00:00Z", end_time=""
        )

        result = await service.schedule_alert_pause(alert_id, data)

        assert result is True
        # Проверяем что end_time=None для бессрочной паузы
        call_args = mock_repo.create_pause.call_args
        assert call_args[1]["end_time"] is None

    async def test_schedule_alert_pause_error_handling(
        self, service, mock_repo
    ):
        """Тест обработки ошибки при установке паузы."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(
            login="test_user", start_time="2024-01-01T00:00:00Z"
        )
        mock_repo.create_pause.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.schedule_alert_pause(alert_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при установке паузы" in exc_info.value.detail

    async def test_schedule_alert_pause_http_exception_passthrough(
        self, service, mock_repo
    ):
        """Покрыть except HTTPException: raise."""
        from fastapi import HTTPException as FastAPIHTTPException

        alert_id = uuid4()
        data = AlertPauseScheduleRequest(login="u")
        mock_repo.create_pause.side_effect = FastAPIHTTPException(
            status_code=409, detail="conflict"
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.schedule_alert_pause(alert_id, data)
        assert exc_info.value.status_code == 409

    async def test_schedule_alert_pause_alert_not_found(
        self, service, mock_repo
    ):
        """Тест установки паузы для несуществующего алерта."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(
            login="test_user", start_time="2024-01-01T00:00:00Z"
        )
        mock_repo.create_pause.side_effect = ValueError("Алерт не найден")

        with pytest.raises(HTTPException) as exc_info:
            await service.schedule_alert_pause(alert_id, data)

        assert exc_info.value.status_code == 404

    async def test_schedule_alert_pause_value_error_passthrough(
        self, service, mock_repo
    ):
        """Покрыть re-raise ValueError, если сообщение не 'не найден'."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(login="u")
        mock_repo.create_pause.side_effect = ValueError("другая ошибка")
        with pytest.raises(ValueError):
            await service.schedule_alert_pause(alert_id, data)

    async def test_stop_alert_pause_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при остановке пауз."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.stop_all_active_pauses.side_effect = Exception("Ошибка БД")
        data = AlertPauseRemoveRequest(login="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.stop_alert_pause(alert_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при остановке пауз" in exc_info.value.detail

    async def test_update_alert_pause_empty_start_time(
        self, service, mock_repo
    ):
        """Тест обновления паузы с пустым start_time."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        mock_repo.update_pause.return_value = True

        data = AlertPauseUpdateRequest(login="test_user", start_time="")

        result = await service.update_alert_pause(alert_id, pause_id, data)

        assert result is True
        # Проверяем что use_now_for_start=True
        call_args = mock_repo.update_pause.call_args
        assert call_args[1]["use_now_for_start"] is True

    async def test_update_alert_pause_empty_end_time(self, service, mock_repo):
        """Тест обновления паузы с пустым end_time (бессрочная пауза)."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        mock_repo.update_pause.return_value = True

        data = AlertPauseUpdateRequest(login="test_user", end_time="")

        result = await service.update_alert_pause(alert_id, pause_id, data)

        assert result is True
        # Проверяем что end_time_set_to_none=True
        call_args = mock_repo.update_pause.call_args
        assert call_args[1]["end_time_set_to_none"] is True

    async def test_update_alert_pause_with_end_time(self, service, mock_repo):
        """Тест обновления паузы с указанным end_time."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        mock_repo.update_pause.return_value = True

        data = AlertPauseUpdateRequest(
            login="test_user", end_time="2024-01-02T00:00:00Z"
        )

        result = await service.update_alert_pause(alert_id, pause_id, data)

        assert result is True
        # end_time должен быть передан, но в текущей реализации репозитория это не поддерживается
        # Проверяем что метод вызван
        mock_repo.update_pause.assert_called_once()

    async def test_update_alert_pause_login_required_for_end_time(
        self, service, mock_repo
    ):
        """Покрыть 400 ветку login обязателен."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {"id": pause_id}
        data = AlertPauseUpdateRequest.model_construct(
            login=None, start_time=None, end_time="2026-01-01T00:00:00+00:00"
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert_pause(alert_id, pause_id, data)
        assert exc_info.value.status_code == 400

    async def test_update_alert_pause_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при обновлении паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        mock_repo.update_pause.side_effect = Exception("Ошибка БД")

        data = AlertPauseUpdateRequest(login="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert_pause(alert_id, pause_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при обновлении паузы" in exc_info.value.detail

    async def test_stop_specific_alert_pause_error_handling(
        self, service, mock_repo
    ):
        """Тест обработки ошибки при остановке конкретной паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        now = datetime.now(timezone.utc)
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": now,
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        mock_repo.stop_specific_pause.side_effect = Exception("Ошибка БД")
        data = AlertPauseRemoveRequest(login="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.stop_specific_alert_pause(alert_id, pause_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при остановке паузы" in exc_info.value.detail

    async def test_stop_specific_alert_pause_naive_times(
        self, service, mock_repo
    ):
        """Покрыть ветки tzinfo None для start_time и end_time."""
        alert_id = uuid4()
        pause_id = uuid4()
        now_naive = datetime.now().replace(microsecond=0)
        future_naive = now_naive + timedelta(days=1)
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": now_naive,
            "end_time": future_naive,
            "start_user": "user1",
            "end_user": None,
        }
        data = AlertPauseRemoveRequest(login="test_user")
        result = await service.stop_specific_alert_pause(alert_id, pause_id, data)
        assert result is True

    async def test_stop_specific_alert_pause_with_mapping_row(
        self, service, mock_repo
    ):
        """Позитивный ORM-style кейс: get_pause_by_id возвращает _mapping."""
        alert_id = uuid4()
        pause_id = uuid4()
        now = datetime.now(timezone.utc)
        future = now.replace(year=now.year + 1)

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": pause_id,
                "start_time": now,
                "end_time": future,
                "start_user": "user1",
                "end_user": None,
            }

        mock_repo.get_pause_by_id.return_value = RowObj()
        data = AlertPauseRemoveRequest(login="test_user")

        result = await service.stop_specific_alert_pause(alert_id, pause_id, data)

        assert result is True
        mock_repo.stop_specific_pause.assert_called_once()

    async def test_delete_alert_pause_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при удалении паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_repo.get_pause_by_id.return_value = {
            "id": pause_id,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        mock_repo.delete_pause.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_alert_pause(alert_id, pause_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при удалении паузы" in exc_info.value.detail

    async def test_toggle_alert_pause_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при переключении паузы."""
        alert_id = uuid4()
        mock_repo.toggle_alert_pause.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.toggle_alert_pause(alert_id, "test_user")

        assert exc_info.value.status_code == 500
        assert "Ошибка при переключении паузы" in exc_info.value.detail

    async def test_toggle_alert_pause_http_exception_passthrough(
        self, service, mock_repo
    ):
        """Покрыть except HTTPException: raise."""
        from fastapi import HTTPException as FastAPIHTTPException

        alert_id = uuid4()
        mock_repo.toggle_alert_pause.side_effect = FastAPIHTTPException(
            status_code=403, detail="forbidden"
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.toggle_alert_pause(alert_id, "u")
        assert exc_info.value.status_code == 403
