"""ORM-модели таблиц домена alerts."""

from datetime import datetime
from typing import ClassVar

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AlertOrm(Base):
    """Модель таблицы `alerts.alerts`."""

    __tablename__ = "alerts"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    alert_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_rules: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    silence_time: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )


class GroupRuleOrm(Base):
    """Модель таблицы `alerts.group_rules`."""

    __tablename__ = "group_rules"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image: Mapped[str | None] = mapped_column(Text, nullable=True)


class PauseHistoryOrm(Base):
    """Модель таблицы `alerts.pause_history`."""

    __tablename__ = "pause_history"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    alert: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    start_user: Mapped[str | None] = mapped_column(String, nullable=True)
    end_user: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class StatusHistoryOrm(Base):
    """Модель таблицы `alerts.status_history`."""

    __tablename__ = "status_history"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    alert_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    status_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    create_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AlertStatusOrm(Base):
    """Модель таблицы `alerts.status`."""

    __tablename__ = "status"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    status_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class RulesChangeStatusOrm(Base):
    """Модель таблицы `alerts.rules_change_status`."""

    __tablename__ = "rules_change_status"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    new_alert_status: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    send_notification: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )


class AlertLinkOrm(Base):
    """Модель таблицы `alerts.alerts_links`."""

    __tablename__ = "alerts_links"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    alert: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    link_name: Mapped[str | None] = mapped_column(String, nullable=True)
    link_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class AlertContactOrm(Base):
    """Модель таблицы `alerts.alerts_contacts` (базовые поля)."""

    __tablename__ = "alerts_contacts"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    alert: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    contact: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)


class AlertContactStatusOrm(Base):
    """Модель таблицы `alerts.alerts_contacts_status`."""

    __tablename__ = "alerts_contacts_status"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    alert_contact: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    repeat: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AlertDtOrm(Base):
    """Модель таблицы `alerts.alerts_dt`."""

    __tablename__ = "alerts_dt"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    alert: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_create: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    silence_time: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )


class DtScreenshotOrm(Base):
    """Модель таблицы `alerts.dt_screenshot`."""

    __tablename__ = "dt_screenshot"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_data: Mapped[str | None] = mapped_column(Text, nullable=True)


class FeedbackOrm(Base):
    """Модель таблицы `alerts.feedback`."""

    __tablename__ = "feedback"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    status_history: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    contact: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)


class ContactOrm(Base):
    """Минимальная карта `alerts.contacts` по `id`.

    Используется для удаления и проверки существования.
    """

    __tablename__ = "contacts"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "alerts"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)


class TelegramSprUserOrm(Base):
    """Модель таблицы `telegram_bot.spr_users`."""

    __tablename__ = "spr_users"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "telegram_bot"}

    login_name: Mapped[str] = mapped_column(String, primary_key=True)
    telegram_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
