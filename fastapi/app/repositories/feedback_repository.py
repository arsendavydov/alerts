"""
Репозиторий для работы с фидбеком.
Содержит асинхронные методы доступа к данным для фидбека.
"""

from typing import Any, cast
from uuid import UUID

from models.alerts import FeedbackOrm
from sqlalchemy import delete, insert, select, update
from sqlalchemy_db import async_session_scope


class FeedbackRepository:
    """Репозиторий для работы с фидбеком."""

    async def get_feedback_by_status_and_contact(
        self, status_history: UUID, contact: str
    ) -> Any | None:
        """Получить фидбек по status_history и contact."""
        stmt = select(FeedbackOrm.id, FeedbackOrm.score).where(
            FeedbackOrm.status_history == status_history,
            FeedbackOrm.contact == contact,
        )
        async with async_session_scope() as session:
            return (await session.execute(stmt)).one_or_none()

    async def create_feedback(
        self, feedback_id: UUID, status_history: UUID, contact: str, score: int
    ) -> UUID:
        """Создать фидбек."""
        stmt = (
            insert(FeedbackOrm)
            .values(
                id=feedback_id,
                status_history=status_history,
                contact=contact,
                score=score,
            )
            .returning(FeedbackOrm.id)
        )
        async with async_session_scope() as session:
            res = await session.execute(stmt)
            return cast("UUID", res.scalar_one())

    async def update_feedback(self, feedback_id: UUID, score: int) -> bool:
        """Обновить фидбек."""
        async with async_session_scope() as session:
            await session.execute(
                update(FeedbackOrm)
                .where(FeedbackOrm.id == feedback_id)
                .values(score=score)
            )
        return True

    async def delete_feedback(
        self, status_history: UUID, contact: str
    ) -> bool:
        """Удалить фидбек."""
        async with async_session_scope() as session:
            stmt = select(FeedbackOrm.id).where(
                FeedbackOrm.status_history == status_history,
                FeedbackOrm.contact == contact,
            )
            fid = (await session.execute(stmt)).scalar_one_or_none()
            if fid is None:
                raise ValueError("Фидбек не найден")
            await session.execute(
                delete(FeedbackOrm).where(FeedbackOrm.id == fid)
            )
            return True
