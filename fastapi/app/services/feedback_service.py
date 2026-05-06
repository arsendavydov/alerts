"""
Сервис для работы с фидбеком.
Содержит асинхронную бизнес-логику для работы с фидбеком.
"""

from uuid import uuid4

from contracts.repository_protocols import FeedbackRepositoryProtocol
from fastapi import HTTPException

from schemas.feedback import FeedbackCreate, FeedbackDelete, FeedbackResponse
from utils import log


class FeedbackService:
    """Сервис для работы с фидбеком."""

    def __init__(self, repository: FeedbackRepositoryProtocol):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с фидбеком
        """
        self.repository = repository

    async def create_feedback(self, data: FeedbackCreate) -> FeedbackResponse:
        """Создать или обновить фидбек."""
        try:
            contact = data.user_fio
            existing = (
                await self.repository.get_feedback_by_status_and_contact(
                    data.status_history, contact
                )
            )

            if existing:
                # Обновляем существующий
                mapping = getattr(existing, "_mapping", None)
                if mapping is not None:
                    feedback_id = dict(mapping).get("id")
                elif isinstance(existing, dict):
                    feedback_id = existing["id"]
                else:
                    feedback_id = existing[0]
                await self.repository.update_feedback(feedback_id, data.score)
                return FeedbackResponse(
                    message="Спасибо! Достаточно одного раза, больше не надо."
                )
            else:
                # Создаем новый
                feedback_id = uuid4()
                await self.repository.create_feedback(
                    feedback_id, data.status_history, contact, data.score
                )
                return FeedbackResponse(message="Спасибо за обратную связь!")
        except Exception as e:
            log.error(
                f"[FeedbackService.create_feedback] Ошибка при создании фидбека: {e}"
            )
            raise HTTPException(
                status_code=500, detail=f"Ошибка при создании фидбека: {e!s}"
            )

    async def delete_feedback(self, data: FeedbackDelete) -> bool:
        """Удалить фидбек."""
        try:
            contact = data.user_fio
            existing = (
                await self.repository.get_feedback_by_status_and_contact(
                    data.status_history, contact
                )
            )

            if not existing:
                raise HTTPException(
                    status_code=404,
                    detail=f"Фидбек не найден для status_history={data.status_history} и contact={contact}",
                )

            await self.repository.delete_feedback(data.status_history, contact)
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(
                f"[FeedbackService.delete_feedback] Ошибка при удалении фидбека: {e}"
            )
            raise HTTPException(
                status_code=500, detail=f"Ошибка при удалении фидбека: {e!s}"
            )
