"""
Модульные тесты для валидации схем Screenshots.
Особое внимание к валидации JSON в image_data.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.screenshots import ScreenshotCreate, ScreenshotUpdate


class TestScreenshotCreate:
    """Тесты для ScreenshotCreate."""

    def test_valid_object_json(self):
        """Тест валидного JSON объекта."""
        data = ScreenshotCreate(
            name="test",
            description="desc",
            image_data='{"url": "test.jpg", "width": 1920}',
        )
        assert data.image_data == '{"url": "test.jpg", "width": 1920}'

    def test_valid_array_json(self):
        """Тест валидного JSON массива."""
        data = ScreenshotCreate(
            name="test",
            description="desc",
            image_data='["url1.jpg", "url2.jpg"]',
        )
        assert data.image_data == '["url1.jpg", "url2.jpg"]'

    def test_invalid_json(self):
        """Тест невалидного JSON."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotCreate(
                name="test", description="desc", image_data="invalid json"
            )
        assert len(exc_info.value.errors()) > 0

    def test_empty_image_data(self):
        """Тест пустого image_data."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotCreate(name="test", description="desc", image_data="")
        assert len(exc_info.value.errors()) > 0

    def test_whitespace_only_image_data(self):
        """Тест image_data только с пробелами."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotCreate(name="test", description="desc", image_data="   ")
        assert len(exc_info.value.errors()) > 0


class TestScreenshotUpdate:
    """Тесты для ScreenshotUpdate."""

    def test_valid_object_json(self):
        """Тест валидного JSON объекта."""
        data = ScreenshotUpdate(image_data='{"url": "test.jpg"}')
        assert data.image_data == '{"url": "test.jpg"}'

    def test_valid_array_json(self):
        """Тест валидного JSON массива."""
        data = ScreenshotUpdate(image_data='["url1.jpg"]')
        assert data.image_data == '["url1.jpg"]'

    def test_invalid_json(self):
        """Тест невалидного JSON."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotUpdate(image_data="invalid json")
        assert len(exc_info.value.errors()) > 0

    def test_all_fields_optional(self):
        """Тест что все поля опциональны."""
        data = ScreenshotUpdate()
        assert data.name is None
        assert data.description is None
        assert data.image_data is None

    def test_partial_update(self):
        """Тест частичного обновления."""
        data = ScreenshotUpdate(name="updated")
        assert data.name == "updated"
        assert data.description is None
        assert data.image_data is None

    def test_update_with_empty_string_image_data(self):
        """Тест обновления с пустой строкой image_data."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotUpdate(image_data="")
        assert len(exc_info.value.errors()) > 0

    def test_create_min_length_validation(self):
        """Тест валидации минимальной длины полей."""
        # name с пустой строкой
        with pytest.raises(ValidationError):
            ScreenshotCreate(
                name="", description="desc", image_data='{"url": "test.jpg"}'
            )

        # description с пустой строкой
        with pytest.raises(ValidationError):
            ScreenshotCreate(
                name="test", description="", image_data='{"url": "test.jpg"}'
            )

    def test_update_validator_none_passthrough(self):
        """Покрыть ветку validate_json: v is None."""
        assert ScreenshotUpdate.validate_json(None) is None

    def test_update_validator_empty_string_raises(self):
        with pytest.raises(ValueError):
            ScreenshotUpdate.validate_json(" ")
