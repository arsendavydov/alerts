from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LinkDetail(BaseModel):
    """Детальная информация о линке."""

    model_config = ConfigDict(exclude_none=True)

    link_id: UUID
    alert_id: UUID
    alert_name: str
    link_name: str
    link_url: str


class LinkDetailCreate(BaseModel):
    """Данные для создания нового линка."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    link_name: str = Field(
        ...,
        max_length=255,
        description="Название ссылки, VARCHAR(255) NOT NULL",
    )
    link_url: str = Field(
        ..., max_length=255, description="URL ссылки, VARCHAR(255) NOT NULL"
    )


class LinkDetailUpdate(BaseModel):
    """Данные для обновления существующего линка."""

    model_config = ConfigDict(exclude_none=True)

    link_id: UUID
    link_name: str | None = Field(
        None,
        max_length=255,
        description="Название ссылки, VARCHAR(255) NOT NULL",
    )
    link_url: str | None = Field(
        None, max_length=255, description="URL ссылки, VARCHAR(255) NOT NULL"
    )


class LinkByAlertListItem(BaseModel):
    """Элемент списка линков для конкретного алерта (без alert_id и alert_name)."""

    model_config = ConfigDict(exclude_none=True)

    link_id: UUID
    link_name: str
    link_url: str


class LinkByAlertListResponse(BaseModel):
    """Ответ со списком линков для конкретного алерта."""

    model_config = ConfigDict(exclude_none=True)

    links: list[LinkByAlertListItem]
    total: int
