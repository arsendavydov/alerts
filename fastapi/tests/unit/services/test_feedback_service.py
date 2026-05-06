"""
Модульные тесты для FeedbackService.
"""

from typing import ClassVar
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.feedback_repository import FeedbackRepository
from schemas.feedback import FeedbackCreate, FeedbackDelete
from services.feedback_service import FeedbackService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestFeedbackService:
    """Тесты для FeedbackService."""

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=FeedbackRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр FeedbackService с моком репозитория."""
        return FeedbackService(repository=mock_repo)

    async def test_create_feedback_new(self, service, mock_repo):
        """Тест создания нового фидбека."""
        uuid4()
        mock_repo.get_feedback_by_status_and_contact.return_value = None

        data = FeedbackCreate(
            status_history=uuid4(), user_fio="test_user", score=5
        )

        result = await service.create_feedback(data)

        assert result.message == "Спасибо за обратную связь!"
        mock_repo.create_feedback.assert_called_once()

    async def test_create_feedback_existing(self, service, mock_repo):
        """Тест создания фидбека когда он уже существует."""
        existing_id = uuid4()
        status_id = uuid4()
        mock_repo.get_feedback_by_status_and_contact.return_value = {
            "id": existing_id,
            "status_history": status_id,
            "contact": "test_user",
            "rating": 3,
        }

        data = FeedbackCreate(
            status_history=status_id, user_fio="test_user", score=5
        )

        result = await service.create_feedback(data)

        assert (
            result.message
            == "Спасибо! Достаточно одного раза, больше не надо."
        )
        mock_repo.update_feedback.assert_called_once_with(existing_id, 5)

    async def test_create_feedback_existing_with_mapping_row(
        self, service, mock_repo
    ):
        """Позитивный ORM-style кейс: existing приходит через _mapping."""
        existing_id = uuid4()
        status_id = uuid4()

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": existing_id,
                "status_history": status_id,
                "contact": "test_user",
                "rating": 3,
            }

        mock_repo.get_feedback_by_status_and_contact.return_value = RowObj()

        data = FeedbackCreate(
            status_history=status_id, user_fio="test_user", score=4
        )

        result = await service.create_feedback(data)

        assert (
            result.message
            == "Спасибо! Достаточно одного раза, больше не надо."
        )
        mock_repo.update_feedback.assert_called_once_with(existing_id, 4)

    async def test_delete_feedback_success(self, service, mock_repo):
        """Тест успешного удаления фидбека."""
        feedback_id = uuid4()
        status_id = uuid4()
        mock_repo.get_feedback_by_status_and_contact.return_value = {
            "id": feedback_id,
            "status_history": status_id,
            "contact": "test_user",
            "rating": 5,
        }

        data = FeedbackDelete(status_history=status_id, user_fio="test_user")

        result = await service.delete_feedback(data)

        assert result is True
        mock_repo.delete_feedback.assert_called_once_with(
            status_id, "test_user"
        )

    async def test_delete_feedback_not_found(self, service, mock_repo):
        """Тест удаления несуществующего фидбека."""
        status_id = uuid4()
        mock_repo.get_feedback_by_status_and_contact.return_value = None

        data = FeedbackDelete(status_history=status_id, user_fio="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_feedback(data)

        assert exc_info.value.status_code == 404

    async def test_create_feedback_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при создании фидбека."""
        mock_repo.get_feedback_by_status_and_contact.return_value = None
        mock_repo.create_feedback.side_effect = Exception("Ошибка БД")

        data = FeedbackCreate(
            status_history=uuid4(), user_fio="test_user", score=5
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_feedback(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при создании фидбека" in exc_info.value.detail

    async def test_delete_feedback_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при удалении фидбека."""
        feedback_id = uuid4()
        status_id = uuid4()
        mock_repo.get_feedback_by_status_and_contact.return_value = {
            "id": feedback_id,
            "status_history": status_id,
            "contact": "test_user",
            "rating": 5,
        }
        mock_repo.delete_feedback.side_effect = Exception("Ошибка БД")

        data = FeedbackDelete(status_history=status_id, user_fio="test_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_feedback(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при удалении фидбека" in exc_info.value.detail
