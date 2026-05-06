import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DTDetail(BaseModel):
    """Детальная информация о DT для алерта."""

    model_config = ConfigDict(exclude_none=True)

    dt_id: UUID
    alert_id: UUID
    content: Any  # JSON объект (распарсенный из строки)
    auto_create: bool
    silence_time: Any | None = Field(
        default=None,
        description="JSON объект (распарсенный из строки), может быть NULL",
    )


class DTDetailCreate(BaseModel):
    """Данные для создания нового DT для алерта."""

    model_config = ConfigDict(exclude_none=True)

    content: str = Field(
        ...,
        max_length=3000,
        description="JSON строка, обязательное, VARCHAR(3000) NOT NULL",
    )
    auto_create: bool = Field(
        description="Обязательное поле, BOOL NOT NULL (в БД DEFAULT false)"
    )
    silence_time: str | None = Field(
        None,
        max_length=1000,
        description="JSON строка, опциональное, VARCHAR(1000) NULL",
    )

    @field_validator("content")
    @classmethod
    def validate_content_json(cls, v: str) -> str:
        """Валидация, что content является валидным JSON."""
        if not v or not v.strip():
            raise ValueError("content не может быть пустым")
        if len(v) > 3000:
            raise ValueError("content не может превышать 3000 символов")
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"content должен быть валидным JSON: {e}")
        return v

    @field_validator("silence_time")
    @classmethod
    def validate_silence_time_json(cls, v: str | None) -> str | None:
        """Валидация, что silence_time является валидным JSON, если передан."""
        if v is None:
            return v
        if not v.strip():
            return None  # Пустая строка трактуется как None
        if len(v) > 1000:
            raise ValueError("silence_time не может превышать 1000 символов")
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"silence_time должен быть валидным JSON: {e}")
        return v


class DTDetailUpdate(BaseModel):
    """Данные для обновления существующего DT для алерта."""

    model_config = ConfigDict(exclude_none=True)

    content: str | None = Field(
        None,
        max_length=3000,
        description="JSON строка, опциональное, VARCHAR(3000) NOT NULL. Пустая строка означает установку NULL в БД (но поле NOT NULL, поэтому это не применимо)",
    )
    auto_create: bool | None = Field(
        default=None, description="Опциональное, BOOL NOT NULL"
    )
    silence_time: str | None = Field(
        None,
        max_length=1000,
        description="JSON строка, опциональное, VARCHAR(1000) NULL. Пустая строка означает установку NULL в БД",
    )

    @field_validator("content")
    @classmethod
    def validate_content_json(cls, v: str | None) -> str | None:
        """
        Валидация, что content является валидным JSON, если передан.
        Для обновления: None означает не обновлять поле.
        Примечание: content в БД NOT NULL, поэтому пустая строка недопустима.
        """
        if v is None:
            return v  # None означает "не обновлять поле"
        if not v.strip():
            raise ValueError("content не может быть пустым (в БД NOT NULL)")
        if len(v) > 3000:
            raise ValueError("content не может превышать 3000 символов")
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"content должен быть валидным JSON: {e}")
        return v

    @field_validator("silence_time")
    @classmethod
    def validate_silence_time_json(cls, v: str | None) -> str | None:
        """
        Валидация, что silence_time является валидным JSON, если передан.
        Для обновления: пустая строка означает установку NULL в БД, None означает не обновлять поле.
        """
        if v is None:
            return v  # None означает "не обновлять поле"
        if not v.strip():
            return ""  # Пустая строка означает "установить NULL в БД" (не валидируем как JSON)
        if len(v) > 1000:
            raise ValueError("silence_time не может превышать 1000 символов")
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"silence_time должен быть валидным JSON: {e}")
        return v
