from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def _parse_datetime(v):
    """Пустая строка - как есть; строка с датой - в datetime; остальное - без изменений."""
    if v is None or v == "":
        return v
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return v
    return v


class AlertPauseRequest(BaseModel):
    """Данные для переключения состояния паузы алерта."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    login: str
    comment: str | None = None


class AlertPauseScheduleRequest(BaseModel):
    """Данные для установки условной паузы алерта с указанием времени начала и окончания."""

    model_config = ConfigDict(
        exclude_none=True,
        json_schema_extra={
            "example": {
                "login": "user123",
                "start_time": "2026-01-01T10:00:00+03:00",
                "end_time": "2026-01-01T18:00:00+03:00",
            }
        },
    )

    login: str = Field(
        ...,
        description="Пользователь, который устанавливает паузу (используется для start_user и/или end_user)",
    )
    start_time: datetime | str | None = Field(
        None,
        description="Время начала паузы с таймзоной (например: '2026-01-01T10:00:00+03:00'). Если передать без таймзоны, PostgreSQL интерпретирует как локальное время сервера БД (+03:00). Если не указано или пустая строка, БД установит now()",
    )
    end_time: datetime | str | None = Field(
        None,
        description="Время окончания паузы с таймзоной (например: '2026-01-01T18:00:00+03:00'). Если передать без таймзоны, PostgreSQL интерпретирует как локальное время сервера БД (+03:00). Если не указан (None) или пустая строка, пауза будет бессрочной (end_time = NULL)",
    )
    comment: str | None = Field(
        None,
        description="Необязательный комментарий к паузе",
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_datetime_or_empty_string(cls, v):
        """Пустая строка - как есть; ISO-строка - в datetime для asyncpg."""
        return _parse_datetime(v)


class AlertPauseRemoveRequest(BaseModel):
    """Данные для снятия всех активных пауз алерта."""

    model_config = ConfigDict(exclude_none=True)

    login: (
        str  # Пользователь, который снимает паузу (используется для end_user)
    )
    comment: str | None = None


class AlertPauseUpdateRequest(BaseModel):
    """Данные для изменения условной паузы алерта."""

    model_config = ConfigDict(
        exclude_none=True,
        json_schema_extra={
            "example": {
                "login": "user123",
                "start_time": "2026-01-01T10:00:00+03:00",
                "end_time": "2026-01-01T18:00:00+03:00",
            }
        },
    )

    login: str | None = Field(
        None,
        description="Пользователь (используется для start_user и/или end_user в зависимости от указанных полей)",
    )
    start_time: datetime | str | None = Field(
        None,
        description="Время начала паузы с таймзоной (например: '2026-01-01T10:00:00+03:00'). Если передать без таймзоны, PostgreSQL интерпретирует как локальное время сервера БД (+03:00). Если пустая строка, установится now()",
    )
    end_time: datetime | str | None = Field(
        None,
        description="Время окончания паузы с таймзоной (например: '2026-01-01T18:00:00+03:00'). Если передать без таймзоны, PostgreSQL интерпретирует как локальное время сервера БД (+03:00). Если не указан (None) или пустая строка, пауза станет бессрочной (end_time = NULL, end_user = NULL)",
    )
    comment: str | None = Field(
        None,
        description="Необязательный комментарий к паузе",
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_datetime_or_empty_string(cls, v):
        """Пустая строка - как есть; ISO-строка - в datetime для asyncpg."""
        return _parse_datetime(v)

    @model_validator(mode="after")
    def validate_login_required(self):
        """Проверяет, что если указан start_time или end_time (не пустая строка), то обязательно указан login."""
        # Проверяем start_time: если это datetime (не None и не пустая строка), нужен login
        start_time_provided = (
            self.start_time is not None and self.start_time != ""
        )
        # Проверяем end_time: если это datetime (не None и не пустая строка), нужен login
        end_time_provided = self.end_time is not None and self.end_time != ""

        if (start_time_provided or end_time_provided) and self.login is None:
            raise ValueError(
                "login обязателен, если указан start_time или end_time (не пустая строка)"
            )
        return self


class PauseHistoryItem(BaseModel):
    """Элемент истории паузы алерта."""

    model_config = ConfigDict(exclude_none=True)

    pause_id: UUID  # id из pause_history
    start_time: datetime = Field(
        ...,
        description="Время начала паузы с таймзоной (например: '2025-12-17T10:00:00+03:00')",
    )
    end_time: datetime | None = Field(
        None,
        description="Время окончания паузы с таймзоной (например: '2025-12-17T18:00:00+03:00') или NULL для бессрочной паузы",
    )
    start_user: str | None = None
    end_user: str | None = None
    comment: str | None = None


class PauseHistoryResponse(BaseModel):
    """Ответ со списком пауз алерта."""

    model_config = ConfigDict(exclude_none=True)

    pauses: list[PauseHistoryItem]
    total: int
