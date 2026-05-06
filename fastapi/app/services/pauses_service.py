"""
Сервис для работы с паузами алертов.
Содержит асинхронную бизнес-логику для работы с паузами.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from contracts.repository_protocols import PausesRepositoryProtocol
from fastapi import HTTPException
from sqlalchemy_db import async_session_scope

from repositories.pauses_repository import PausesRepository
from schemas.pauses import (
    AlertPauseRemoveRequest,
    AlertPauseScheduleRequest,
    AlertPauseUpdateRequest,
    PauseHistoryItem,
    PauseHistoryResponse,
)
from utils import log


class PausesService:
    """Сервис для работы с паузами алертов."""

    def __init__(self, repository: PausesRepositoryProtocol | None = None):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с паузами
        """
        self.repository = repository or PausesRepository()

    @staticmethod
    def _as_dict(row: object) -> dict[str, Any]:
        if isinstance(row, dict):
            return row
        mapping = getattr(row, "_mapping", None)
        if mapping is not None:
            return dict(mapping)
        if hasattr(row, "keys"):
            try:
                keys = list(row.keys())  # type: ignore[attr-defined]
                result: dict[str, Any] = {}
                for idx, key in enumerate(keys):
                    try:
                        result[key] = row[key]  # type: ignore[index]
                    except Exception:
                        result[key] = row[idx]  # type: ignore[index]
                return result
            except Exception:
                return {}
        return {}

    async def get_alert_pauses(
        self,
        alert_id: UUID,
        filter_type: str = "all",
        order_by: str = "start_time",
        order_dir: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> PauseHistoryResponse:
        """
        Получить историю пауз алерта.

        Args:
            alert_id: ID алерта
            filter_type: Тип фильтрации
            order_by: Поле сортировки
            order_dir: Направление сортировки
            limit: Количество записей
            offset: Смещение

        Returns:
            PauseHistoryResponse: Список пауз

        Raises:
            HTTPException: При ошибке валидации или БД
        """
        try:
            # Валидация
            valid_filters = ["all", "active", "future", "past"]
            if filter_type not in valid_filters:
                raise HTTPException(
                    status_code=400,
                    detail=f"filter_type должен быть одним из: {', '.join(valid_filters)}",
                )

            # Проверка существования алерта
            if not await self.repository.check_alert_exists(alert_id):
                raise HTTPException(status_code=404, detail="Алерт не найден")

            # Получение пауз
            rows, total = await self.repository.get_pauses(
                alert_id=alert_id,
                filter_type=filter_type,
                order_by=order_by,
                order_dir=order_dir,
                limit=limit,
                offset=offset,
            )

            pauses = []
            for row in rows:
                row_dict = self._as_dict(row)
                pauses.append(
                    PauseHistoryItem(
                        pause_id=row_dict.get("id"),
                        start_time=row_dict.get("start_time"),
                        end_time=row_dict.get("end_time"),
                        start_user=row_dict.get("start_user"),
                        end_user=row_dict.get("end_user"),
                        comment=row_dict.get("comment"),
                    )
                )

            return PauseHistoryResponse(pauses=pauses, total=total)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[PausesService.get_alert_pauses] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении истории пауз: {e}",
            )

    async def schedule_alert_pause(
        self, alert_id: UUID, data: AlertPauseScheduleRequest
    ) -> bool:
        """
        Установить условную паузу алерта.

        Args:
            alert_id: ID алерта
            data: Данные для установки паузы

        Returns:
            bool: True при успехе

        Raises:
            HTTPException: При ошибке валидации или БД
        """
        try:
            # Обработка start_time
            start_time = None
            use_now_for_start = False
            if data.start_time is not None:
                if data.start_time == "":
                    # Пустая строка - используем now() в SQL
                    use_now_for_start = True
                else:
                    start_time = data.start_time

            # Обработка end_time
            end_time = None
            if data.end_time is not None:
                if data.end_time == "":
                    # Пустая строка - бессрочная пауза
                    end_time = None
                else:
                    end_time = data.end_time

            await self.repository.create_pause(
                alert_id=alert_id,
                login=data.login,
                start_time=start_time,
                end_time=end_time,
                use_now_for_start=use_now_for_start,
                comment=data.comment,
            )

            return True
        except ValueError as e:
            if "не найден" in str(e):
                raise HTTPException(status_code=404, detail="Алерт не найден")
            raise
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[PausesService.schedule_alert_pause] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при установке паузы: {e}"
            )

    async def stop_alert_pause(
        self, alert_id: UUID, data: AlertPauseRemoveRequest
    ) -> bool:
        """
        Остановить все активные паузы алерта.

        Args:
            alert_id: ID алерта
            data: Данные для остановки

        Returns:
            bool: True при успехе
        """
        try:
            async with async_session_scope() as session:
                if not await self.repository.check_alert_exists(
                    alert_id, session
                ):
                    raise HTTPException(
                        status_code=404, detail="Алерт не найден"
                    )

                stop_kwargs: dict[str, Any] = {}
                if "comment" in data.model_fields_set:
                    stop_kwargs["comment"] = data.comment
                await self.repository.stop_all_active_pauses(
                    alert_id, data.login, session=session, **stop_kwargs
                )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[PausesService.stop_alert_pause] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при остановке пауз: {e}"
            )

    async def update_alert_pause(
        self, alert_id: UUID, pause_id: UUID, data: AlertPauseUpdateRequest
    ) -> bool:
        """
        Обновить паузу алерта.

        Args:
            alert_id: ID алерта
            pause_id: ID паузы
            data: Данные для обновления

        Returns:
            bool: True при успехе
        """
        try:
            # Проверка существования паузы
            pause = await self.repository.get_pause_by_id(pause_id, alert_id)
            if not pause:
                raise HTTPException(status_code=404, detail="Пауза не найдена")

            # Обработка start_time
            start_time = None
            use_now_for_start = False
            if data.start_time is not None:
                if data.start_time == "":
                    # Пустая строка - используем now() в SQL
                    use_now_for_start = True
                else:
                    start_time = data.start_time

            # Обработка end_time
            end_time_set_to_none = False
            if data.end_time is not None:
                if data.end_time == "":
                    # Пустая строка - бессрочная пауза (устанавливаем NULL)
                    end_time_set_to_none = True
                else:
                    # Указана дата - используем её
                    # Но в текущей реализации репозитория это не поддерживается напрямую
                    # Нужно доработать репозиторий
                    pass

            # Валидация login
            if (
                start_time is not None
                or use_now_for_start
                or data.end_time is not None
            ) and not data.login:
                raise HTTPException(
                    status_code=400,
                    detail="login обязателен при указании start_time или end_time",
                )

            # Определяем end_time для передачи в репозиторий
            end_time_value = None
            if data.end_time is not None and data.end_time != "":
                end_time_value = data.end_time

            update_kwargs: dict[str, Any] = {}
            if "comment" in data.model_fields_set:
                update_kwargs["comment"] = data.comment

            await self.repository.update_pause(
                pause_id=pause_id,
                alert_id=alert_id,
                start_time=start_time,
                use_now_for_start=use_now_for_start,
                end_time=end_time_value,
                end_time_set_to_none=end_time_set_to_none,
                login=data.login,
                **update_kwargs,
            )

            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[PausesService.update_alert_pause] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при обновлении паузы: {e}"
            )

    async def stop_specific_alert_pause(
        self, alert_id: UUID, pause_id: UUID, data: AlertPauseRemoveRequest
    ) -> bool:
        """
        Остановить конкретную паузу.

        Args:
            alert_id: ID алерта
            pause_id: ID паузы
            data: Данные для остановки

        Returns:
            bool: True при успехе
        """
        try:
            pause = await self.repository.get_pause_by_id(pause_id, alert_id)
            if not pause:
                raise HTTPException(status_code=404, detail="Пауза не найдена")
            pause_dict = self._as_dict(pause)
            if pause_dict:
                start_time = pause_dict.get("start_time")
                end_time = pause_dict.get("end_time")
            else:
                start_time = pause[1]  # type: ignore[index]
                end_time = pause[2]  # type: ignore[index]

            # Используем timezone-aware datetime для сравнения с данными из БД (timestamptz)
            now = datetime.now(timezone.utc)

            # Если start_time или end_time не имеют таймзоны, добавляем UTC
            if isinstance(start_time, datetime) and start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if (
                end_time is not None
                and isinstance(end_time, datetime)
                and end_time.tzinfo is None
            ):
                end_time = end_time.replace(tzinfo=timezone.utc)

            if end_time is not None and end_time < now:
                raise HTTPException(
                    status_code=400, detail="Пауза уже завершена"
                )

            stop_specific_kwargs: dict[str, Any] = {}
            if "comment" in data.model_fields_set:
                stop_specific_kwargs["comment"] = data.comment
            await self.repository.stop_specific_pause(
                pause_id, alert_id, data.login, **stop_specific_kwargs
            )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[PausesService.stop_specific_alert_pause] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при остановке паузы: {e}"
            )

    async def delete_alert_pause(self, alert_id: UUID, pause_id: UUID) -> bool:
        """
        Удалить паузу.

        Args:
            alert_id: ID алерта
            pause_id: ID паузы

        Returns:
            bool: True при успехе
        """
        try:
            async with async_session_scope() as session:
                pause = await self.repository.get_pause_by_id(
                    pause_id, alert_id, session
                )
                if not pause:
                    raise HTTPException(
                        status_code=404, detail="Пауза не найдена"
                    )

                await self.repository.delete_pause(pause_id, alert_id, session)
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[PausesService.delete_alert_pause] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при удалении паузы: {e}"
            )

    async def toggle_alert_pause(
        self, alert_id: UUID, login: str, comment: str | None = None
    ) -> bool:
        """
        Переключение состояния паузы алерта (безусловная пауза).

        Логика работы:
        - Если алерт НЕ на паузе: создает новую запись в pause_history с start_user = login, end_user = NULL, end_time = NULL
        - Если алерт УЖЕ на паузе: закрывает все активные паузы, устанавливая end_user = login и end_time = now()

        Args:
            alert_id: ID алерта
            login: Логин пользователя

        Returns:
            bool: True при успешном переключении

        Raises:
            HTTPException: При отсутствии алерта или ошибке БД
        """
        try:
            await self.repository.toggle_alert_pause(alert_id, login, comment)
            return True
        except HTTPException:
            raise
        except ValueError as e:
            if "не найден" in str(e):
                raise HTTPException(status_code=404, detail="Алерт не найден")
            raise
        except Exception as e:
            log.error(f"[PausesService.toggle_alert_pause] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при переключении паузы алерта: {e}",
            )
