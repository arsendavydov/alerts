import json
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScreenshotSearchItem(BaseModel):
    """Элемент поиска для скриншота."""

    model_config = ConfigDict(exclude_none=True)

    screenshot_id: UUID = Field(description="ID скриншота")
    name: str = Field(description="Название скриншота")
    description: str = Field(
        description="Описание скриншота (поиск по этому полю)"
    )
    image_data: str = Field(
        description="Данные изображения (JSON строка или массив), фронт соберет из этого JSON"
    )


class ScreenshotSearchResponse(BaseModel):
    """Ответ поиска для скриншотов."""

    model_config = ConfigDict(exclude_none=True)

    screenshots: list[ScreenshotSearchItem]
    total: int
    limit: int
    offset: int


class ScreenshotDetail(BaseModel):
    """Детальная информация о скриншоте."""

    model_config = ConfigDict(exclude_none=True)

    screenshot_id: UUID = Field(description="ID скриншота")
    name: str = Field(description="Название скриншота")
    description: str = Field(description="Описание скриншота")
    image_data: str = Field(description="Данные изображения (JSON строка)")


class ScreenshotCreate(BaseModel):
    """Данные для создания нового скриншота."""

    model_config = ConfigDict(exclude_none=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название скриншота (обязательное)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Описание скриншота (обязательное)",
    )
    image_data: str = Field(
        ...,
        min_length=1,
        description="Данные изображения в формате JSON (обязательное, должен быть валидный JSON)",
    )

    @field_validator("image_data")
    @classmethod
    def validate_json(cls, v: str) -> str:
        """Валидация, что image_data является валидным JSON."""
        if not v or not v.strip():
            raise ValueError("image_data не может быть пустым")
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"image_data должен быть валидным JSON: {e}")
        return v


class ScreenshotUpdate(BaseModel):
    """Данные для обновления существующего скриншота."""

    model_config = ConfigDict(exclude_none=True)

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Название скриншота"
    )
    description: str | None = Field(
        None, min_length=1, max_length=255, description="Описание скриншота"
    )
    image_data: str | None = Field(
        None,
        min_length=1,
        description="Данные изображения в формате JSON (должен быть валидный JSON)",
    )

    @field_validator("image_data")
    @classmethod
    def validate_json(cls, v: str | None) -> str | None:
        """Валидация, что image_data является валидным JSON, если передан."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("image_data не может быть пустым")
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"image_data должен быть валидным JSON: {e}")
        return v
