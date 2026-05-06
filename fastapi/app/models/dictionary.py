"""ORM-модели таблиц schema dictionary."""

from typing import ClassVar

from sqlalchemy import Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class EventOrm(Base):
    """Модель таблицы `dictionary.events`."""

    __tablename__ = "events"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "dictionary"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
