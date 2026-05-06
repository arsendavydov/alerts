"""
Модульные тесты для валидации схем DT.
"""

import sys
from pathlib import Path
from uuid import uuid4

import pytest

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.dt import DTDetail, DTDetailCreate, DTDetailUpdate


class TestDTDetail:
    """Тесты для DTDetail."""

    def test_valid_detail(self):
        """Тест валидной детальной информации."""
        dt_id = uuid4()
        alert_id = uuid4()
        data = DTDetail(
            dt_id=dt_id,
            alert_id=alert_id,
            content={"key": "value"},
            auto_create=True,
        )
        assert data.dt_id == dt_id
        assert data.alert_id == alert_id
        assert data.content == {"key": "value"}
        assert data.auto_create is True

    def test_with_silence_time(self):
        """Тест с silence_time."""
        dt_id = uuid4()
        alert_id = uuid4()
        data = DTDetail(
            dt_id=dt_id,
            alert_id=alert_id,
            content={"key": "value"},
            auto_create=True,
            silence_time={"time": "1h"},
        )
        assert data.silence_time == {"time": "1h"}


class TestDTDetailCreate:
    """Тесты для DTDetailCreate."""

    def test_valid_create(self):
        """Тест валидного создания."""
        data = DTDetailCreate(content='{"key": "value"}', auto_create=True)
        assert data.content == '{"key": "value"}'
        assert data.auto_create is True

    def test_with_silence_time(self):
        """Тест с silence_time."""
        data = DTDetailCreate(
            content='{"key": "value"}',
            auto_create=False,
            silence_time='{"time": "1h"}',
        )
        assert data.silence_time == '{"time": "1h"}'

    def test_silence_time_empty_string_becomes_none(self):
        """Покрыть validator silence_time: пустая строка -> None."""
        data = DTDetailCreate(content="{}", auto_create=True, silence_time=" ")
        assert data.silence_time is None


class TestDTDetailUpdate:
    """Тесты для DTDetailUpdate."""

    def test_all_fields_optional(self):
        """Тест что все поля опциональны."""
        data = DTDetailUpdate()
        assert data.content is None
        assert data.auto_create is None
        assert data.silence_time is None

    def test_partial_update(self):
        """Тест частичного обновления."""
        data = DTDetailUpdate(content='{"key": "updated"}')
        assert data.content == '{"key": "updated"}'
        assert data.auto_create is None

    def test_silence_time_empty_string_kept_for_nulling(self):
        """Покрыть validator silence_time: пустая строка -> ''."""
        data = DTDetailUpdate(silence_time=" ")
        assert data.silence_time == ""

    def test_update_content_empty_raises(self):
        with pytest.raises(Exception):
            DTDetailUpdate(content=" ")

    def test_update_silence_time_invalid_json_raises(self):
        with pytest.raises(Exception):
            DTDetailUpdate(silence_time="{bad")

    def test_create_validators_direct_paths(self):
        """Покрыть ветки validate_content_json и validate_silence_time_json в Create."""
        with pytest.raises(ValueError):
            DTDetailCreate.validate_content_json(" ")
        with pytest.raises(ValueError):
            DTDetailCreate.validate_content_json("x" * 3001)
        assert DTDetailCreate.validate_content_json('{"ok":1}') == '{"ok":1}'
        with pytest.raises(ValueError):
            DTDetailCreate.validate_silence_time_json("x" * 1001)
        assert DTDetailCreate.validate_silence_time_json(None) is None
        assert DTDetailCreate.validate_silence_time_json('{"ok":1}') == '{"ok":1}'

    def test_update_validators_direct_paths(self):
        """Покрыть ветки validate_content_json и validate_silence_time_json в Update."""
        assert DTDetailUpdate.validate_content_json(None) is None
        with pytest.raises(ValueError):
            DTDetailUpdate.validate_content_json(" ")
        with pytest.raises(ValueError):
            DTDetailUpdate.validate_content_json("x" * 3001)
        assert DTDetailUpdate.validate_content_json('{"ok":1}') == '{"ok":1}'
        assert DTDetailUpdate.validate_silence_time_json(None) is None
        with pytest.raises(ValueError):
            DTDetailUpdate.validate_silence_time_json("x" * 1001)
        assert DTDetailUpdate.validate_silence_time_json('{"ok":1}') == '{"ok":1}'
