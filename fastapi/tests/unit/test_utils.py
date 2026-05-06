"""
Модульные тесты для utils.py.
После миграции на асинхронность utils.py содержит функции логирования и хелперы для работы с БД.
"""

from unittest.mock import patch

from utils.logging import (
    CorrelationIdFilter,
    get_correlation_id,
    log,
    set_correlation_id,
)


class TestUtils:
    """Тесты для утилит логирования."""

    def test_log_exists(self):
        """Тест наличия объекта логирования."""
        assert log is not None
        assert log.name == "alerts"

    @patch("utils.logging.LevelLog")
    def test_setup_logging_exception(self, mock_level_log):
        """Тест setup_logging при ошибке получения уровня логирования."""
        mock_level_log.__getitem__.side_effect = KeyError("Invalid level")
        mock_level_log.notset.value = 0

        import utils.logging as logging_module

        with patch.dict("os.environ", {"LEVEL_LOG": "invalid_level"}):
            logging_module.setup_logging()

        # Проверяем, что не было исключения
        assert logging_module.log is not None

    def test_correlation_id_set_get(self):
        """Тест установки и получения correlation-id."""
        set_correlation_id("test-cid")
        assert get_correlation_id() == "test-cid"

    def test_correlation_filter_sets_record_field(self):
        """Покрыть CorrelationIdFilter.filter."""
        import logging

        set_correlation_id("cid-1")
        record = logging.LogRecord(
            name="alerts",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="msg",
            args=(),
            exc_info=None,
        )
        assert CorrelationIdFilter().filter(record) is True
        assert record.__dict__["correlation_id"] == "cid-1"

    def test_resolve_log_file_path_accepts_absolute(self):
        """Покрыть ветку абсолютного LOG_FILE_PATH."""
        import utils.logging as logging_module

        with patch(
            "utils.logging.os.getenv", return_value="/tmp/alerts.log"
        ):
            resolved = logging_module._resolve_log_file_path()
        resolved_str = str(resolved)
        assert resolved.is_absolute()
        assert resolved_str.replace("\\", "/").endswith("/tmp/alerts.log")
