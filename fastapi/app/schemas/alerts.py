import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AlertListItem(BaseModel):
    """Элемент списка алертов с полной информацией."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    alert_name: str
    alert_description: str | None = None
    indicator_name: str
    indicator_description: str | None = None
    status_id: str | None = None
    paused: bool = False
    tags: list[str] | None = None


class AlertListResponse(BaseModel):
    """Ответ со списком алертов и метаданными пагинации."""

    model_config = ConfigDict(exclude_none=True)

    alerts: list[AlertListItem]
    total: int


class IndicatorInfo(BaseModel):
    """Информация об индикаторе."""

    model_config = ConfigDict(exclude_none=True)

    indicator_id: UUID
    indicator_name: str


class GroupRuleInfo(BaseModel):
    """Информация о группе правил."""

    model_config = ConfigDict(exclude_none=True)
    group_rule_id: UUID
    description: str | None = None
    image: str | None = None


class AlertDetail(BaseModel):
    """Детальная информация об алерте."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    alert_name: str
    indicator: IndicatorInfo
    description: str | None = None
    image: str | None = None
    tags: list[str] | None = None
    # Краткая информация о группе правил (для отображения деталей на странице алерта)
    group_rule: GroupRuleInfo | None = None
    silence_time: Any | None = Field(
        default=None,
        description="JSON объект (распарсенный из строки), может быть NULL",
    )


class AlertDetailCreate(BaseModel):
    """Данные для создания нового алерта."""

    model_config = ConfigDict(exclude_none=True)

    alert_name: str = Field(
        ...,
        max_length=255,
        description="Название алерта, VARCHAR(255) NOT NULL",
    )
    indicator_id: UUID  # event in database
    description: str = Field(
        ...,
        max_length=255,
        description="Описание алерта, VARCHAR(255) NOT NULL (может быть пустой строкой)",
    )
    image: str = Field(
        ...,
        description="Изображение, TEXT NOT NULL (может быть пустой строкой)",
    )
    tags: list[str] | None = None
    # Обязательная привязка к группе правил
    group_rule_id: UUID
    silence_time: str | None = Field(
        None,
        max_length=1000,
        description="JSON строка, опциональное, VARCHAR(1000)",
    )

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


class AlertDetailUpdate(BaseModel):
    """Данные для обновления существующего алерта."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    alert_name: str | None = Field(
        None,
        max_length=255,
        description="Название алерта, VARCHAR(255) NOT NULL",
    )
    indicator_id: UUID | None = None  # event in database
    description: str | None = Field(
        None,
        max_length=255,
        description="Описание алерта, VARCHAR(255) NOT NULL (может быть пустой строкой)",
    )
    image: str | None = Field(
        None,
        description="Изображение, TEXT NOT NULL (может быть пустой строкой)",
    )
    tags: list[str] | None = None
    # ID группы правил при изменении
    group_rule_id: UUID | None = None
    silence_time: str | None = Field(
        None,
        max_length=1000,
        description="JSON строка, опциональное, VARCHAR(1000). Пустая строка означает установку NULL в БД",
    )

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


class TagCloudResponse(BaseModel):
    """Ответ с облаком тегов."""

    model_config = ConfigDict(exclude_none=True)

    tags: list[str]
    total: int


class AlertAutocomplete(BaseModel):
    """Элемент автодополнения алертов."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    alert_name: str


class AlertAutocompleteResponse(BaseModel):
    """Ответ с результатами автодополнения алертов."""

    model_config = ConfigDict(exclude_none=True)

    alerts: list[AlertAutocomplete]
    total: int
