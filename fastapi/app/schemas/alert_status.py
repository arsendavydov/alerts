from pydantic import BaseModel, ConfigDict, Field


class AlertStatusListItem(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    status_id: str = Field(description="ID статуса (char, 1)")
    status_name: str = Field(description="Название статуса")
    first_action_text_template: str | None = Field(
        None, description="Текст первого действия"
    )
    continue_action_text_template: str | None = Field(
        None, description="Текст продолжения действия"
    )


class AlertStatusListResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    statuses: list[AlertStatusListItem] = Field(
        description="Массив статусов алерта"
    )


class AlertStatusCreate(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    status_id: str = Field(description="ID статуса (char, 1)")
    status_name: str = Field(description="Название статуса")
    first_action_text_template: str | None = Field(
        None, description="Текст первого действия"
    )
    continue_action_text_template: str | None = Field(
        None, description="Текст продолжения действия"
    )


class AlertStatusUpdate(AlertStatusCreate):
    pass
