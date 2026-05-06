from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    """Данные для создания фидбека."""

    model_config = ConfigDict(exclude_none=True)

    status_history: UUID
    user_fio: str
    score: int


class FeedbackDelete(BaseModel):
    """Данные для удаления фидбека."""

    model_config = ConfigDict(exclude_none=True)

    status_history: UUID
    user_fio: str


class FeedbackResponse(BaseModel):
    """Ответ после создания/обновления фидбека."""

    model_config = ConfigDict(exclude_none=True)

    message: str
