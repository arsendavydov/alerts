"""
Модульные тесты для валидации схем Pauses.
Особое внимание к валидации datetime и пустых строк.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.pauses import (
    AlertPauseRemoveRequest,
    AlertPauseRequest,
    AlertPauseScheduleRequest,
    AlertPauseUpdateRequest,
    PauseHistoryItem,
    PauseHistoryResponse,
    _parse_datetime,
)


class TestAlertPauseRequest:
    """Тесты для AlertPauseRequest."""

    def test_valid_request(self):
        """Тест валидного запроса."""
        data = AlertPauseRequest(
            alert_id=uuid4(), login="test_user", comment="manual pause"
        )
        assert data.alert_id is not None
        assert data.login == "test_user"
        assert data.comment == "manual pause"

    def test_empty_login(self):
        """Тест с пустым login."""
        # Пустой login допустим (нет валидации min_length)
        data = AlertPauseRequest(alert_id=uuid4(), login="")
        assert data.login == ""


class TestAlertPauseScheduleRequest:
    """Тесты для AlertPauseScheduleRequest."""

    def test_valid_with_datetime(self):
        """Тест валидного запроса с datetime."""
        data = AlertPauseScheduleRequest(
            login="test_user",
            start_time="2026-01-01T10:00:00+03:00",
            end_time="2026-01-01T18:00:00+03:00",
        )
        assert data.login == "test_user"
        assert data.start_time is not None
        assert data.end_time is not None

    def test_valid_with_empty_strings(self):
        """Тест валидного запроса с пустыми строками."""
        data = AlertPauseScheduleRequest(
            login="test_user", start_time="", end_time=""
        )
        assert data.start_time == ""
        assert data.end_time == ""

    def test_valid_with_none(self):
        """Тест валидного запроса с None."""
        data = AlertPauseScheduleRequest(
            login="test_user", start_time=None, end_time=None
        )
        assert data.start_time is None
        assert data.end_time is None

    def test_minimal_valid(self):
        """Тест минимального валидного запроса (только login)."""
        data = AlertPauseScheduleRequest(login="test_user")
        assert data.login == "test_user"
        assert data.start_time is None
        assert data.end_time is None


class TestAlertPauseRemoveRequest:
    """Тесты для AlertPauseRemoveRequest."""

    def test_valid_request(self):
        """Тест валидного запроса."""
        data = AlertPauseRemoveRequest(login="test_user", comment="stop reason")
        assert data.login == "test_user"
        assert data.comment == "stop reason"

    def test_empty_login(self):
        """Тест с пустым login."""
        data = AlertPauseRemoveRequest(login="")
        assert data.login == ""


class TestAlertPauseUpdateRequest:
    """Тесты для AlertPauseUpdateRequest."""

    def test_valid_with_datetime(self):
        """Тест валидного запроса с datetime и login."""
        data = AlertPauseUpdateRequest(
            login="test_user",
            start_time="2026-01-01T10:00:00+03:00",
            end_time="2026-01-01T18:00:00+03:00",
        )
        assert data.login == "test_user"
        assert data.start_time is not None
        assert data.end_time is not None

    def test_valid_with_empty_strings(self):
        """Тест валидного запроса с пустыми строками."""
        data = AlertPauseUpdateRequest(
            login="test_user", start_time="", end_time=""
        )
        assert data.start_time == ""
        assert data.end_time == ""

    def test_valid_with_none(self):
        """Тест валидного запроса с None (login не обязателен)."""
        data = AlertPauseUpdateRequest(
            login=None, start_time=None, end_time=None
        )
        assert data.login is None
        assert data.start_time is None
        assert data.end_time is None

    def test_login_required_with_start_time(self):
        """Тест что login обязателен при указании start_time."""
        with pytest.raises(ValidationError) as exc_info:
            AlertPauseUpdateRequest(
                login=None, start_time="2026-01-01T10:00:00+03:00"
            )
        errors = exc_info.value.errors()
        assert any(
            "login обязателен" in str(error.get("msg", "")) for error in errors
        )

    def test_login_required_with_end_time(self):
        """Тест что login обязателен при указании end_time."""
        with pytest.raises(ValidationError) as exc_info:
            AlertPauseUpdateRequest(
                login=None, end_time="2026-01-01T18:00:00+03:00"
            )
        errors = exc_info.value.errors()
        assert any(
            "login обязателен" in str(error.get("msg", "")) for error in errors
        )

    def test_login_required_with_both_times(self):
        """Тест что login обязателен при указании обоих времен."""
        with pytest.raises(ValidationError) as exc_info:
            AlertPauseUpdateRequest(
                login=None,
                start_time="2026-01-01T10:00:00+03:00",
                end_time="2026-01-01T18:00:00+03:00",
            )
        errors = exc_info.value.errors()
        assert any(
            "login обязателен" in str(error.get("msg", "")) for error in errors
        )

    def test_empty_strings_dont_require_login(self):
        """Тест что пустые строки не требуют login."""
        data = AlertPauseUpdateRequest(login=None, start_time="", end_time="")
        assert data.login is None
        assert data.start_time == ""
        assert data.end_time == ""


class TestPauseHistoryItem:
    """Тесты для PauseHistoryItem."""

    def test_valid_with_end_time(self):
        """Тест валидного элемента с end_time."""
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)
        data = PauseHistoryItem(
            pause_id=pause_id,
            start_time=start_time,
            end_time=end_time,
            start_user="user1",
            end_user="user2",
            comment="some note",
        )
        assert data.pause_id == pause_id
        assert data.start_time == start_time
        assert data.end_time == end_time
        assert data.start_user == "user1"
        assert data.end_user == "user2"
        assert data.comment == "some note"

    def test_valid_without_end_time(self):
        """Тест валидного элемента без end_time (бессрочная пауза)."""
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc)
        data = PauseHistoryItem(
            pause_id=pause_id,
            start_time=start_time,
            end_time=None,
            start_user="user1",
            end_user=None,
        )
        assert data.pause_id == pause_id
        assert data.start_time == start_time
        assert data.end_time is None
        assert data.start_user == "user1"
        assert data.end_user is None


class TestPauseHistoryResponse:
    """Тесты для PauseHistoryResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        pause_id = uuid4()
        item = PauseHistoryItem(
            pause_id=pause_id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
        )
        data = PauseHistoryResponse(pauses=[item], total=1)
        assert len(data.pauses) == 1
        assert data.total == 1
        assert data.pauses[0].pause_id == pause_id

    def test_empty_response(self):
        """Тест пустого ответа."""
        data = PauseHistoryResponse(pauses=[], total=0)
        assert len(data.pauses) == 0
        assert data.total == 0


class TestPauseParseDatetime:
    """Тесты для покрытие внутренних веток _parse_datetime через validators."""

    def test_invalid_datetime_string_kept_as_string(self):
        data = AlertPauseScheduleRequest(
            login="u", start_time="bad-date", end_time=None
        )
        assert data.start_time == "bad-date"

    def test_datetime_instance_pass_through(self):
        dt = datetime.now(timezone.utc)
        data = AlertPauseScheduleRequest(login="u", start_time=dt, end_time=None)
        assert data.start_time == dt

    def test_non_string_non_datetime_value_kept(self):
        assert _parse_datetime(123) == 123
