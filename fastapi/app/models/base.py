"""Базовые декларации ORM-моделей SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый декларативный класс для ORM-моделей."""
