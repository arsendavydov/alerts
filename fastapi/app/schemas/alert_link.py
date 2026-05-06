from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertLinkListItem(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    link_id: UUID = Field(description="ID ссылки")
    alert_id: UUID = Field(description="ID алерта (uuid)")
    link_name: str = Field(description="Название ссылки")
    link_url: str = Field(description="URL ссылки")


class AlertLinkListResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    links: list[AlertLinkListItem] = Field(
        description="Массив ссылок, привязанных к алерту"
    )


class AlertLinkAutocomplete(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    link_id: UUID = Field(description="ID ссылки")
    link_name: str = Field(description="Название ссылки")


class AlertLinkCreate(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID = Field(description="ID алерта (uuid)")
    link_name: str = Field(
        ...,
        max_length=255,
        description="Название ссылки, VARCHAR(255) NOT NULL",
    )
    link_url: str = Field(
        ..., max_length=255, description="URL ссылки, VARCHAR(255) NOT NULL"
    )
