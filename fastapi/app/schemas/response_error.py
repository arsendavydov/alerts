from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ResponseStatus(str, Enum):
    ok = "ok"
    error = "error"


class MessageError(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    type: str
    error: str
    trace: str | None = None  # Трейсбек только в dev режиме, в prod - None


class response_error(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    status: ResponseStatus = Field(description="Статус")
    message: MessageError = Field(description="Сообщение")
