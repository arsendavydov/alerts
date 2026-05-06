"""
Модульные тесты для валидации схем Feedback.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.feedback import FeedbackCreate, FeedbackDelete, FeedbackResponse


class TestFeedbackCreate:
    """Тесты для FeedbackCreate."""

    def test_valid_create(self):
        """Тест валидного создания."""
        status_history_id = uuid4()
        data = FeedbackCreate(
            status_history=status_history_id, user_fio="Test User", score=5
        )
        assert data.status_history == status_history_id
        assert data.user_fio == "Test User"
        assert data.score == 5

    def test_with_different_scores(self):
        """Тест с разными оценками."""
        status_history_id = uuid4()
        for score in [1, 3, 5]:
            data = FeedbackCreate(
                status_history=status_history_id,
                user_fio="Test User",
                score=score,
            )
            assert data.score == score


class TestFeedbackDelete:
    """Тесты для FeedbackDelete."""

    def test_valid_delete(self):
        """Тест валидного удаления."""
        status_history_id = uuid4()
        data = FeedbackDelete(
            status_history=status_history_id, user_fio="Test User"
        )
        assert data.status_history == status_history_id
        assert data.user_fio == "Test User"


class TestFeedbackResponse:
    """Тесты для FeedbackResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        data = FeedbackResponse(message="Спасибо за обратную связь!")
        assert data.message == "Спасибо за обратную связь!"

    def test_different_messages(self):
        """Тест с разными сообщениями."""
        message1 = "Спасибо за обратную связь!"
        message2 = "Спасибо! Достаточно одного раза, больше не надо."

        data1 = FeedbackResponse(message=message1)
        data2 = FeedbackResponse(message=message2)

        assert data1.message == message1
        assert data2.message == message2
