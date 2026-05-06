"""
Модульные тесты для AlertsService.
Используют моки репозиториев для изоляции от БД.
"""

import json
from typing import ClassVar
from unittest.mock import ANY, AsyncMock, patch
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.alerts_repository import AlertsRepository
from schemas.alerts import AlertDetailCreate, AlertDetailUpdate
from services.alerts_service import AlertsService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestAlertsService:
    """Тесты для AlertsService."""

    @pytest.fixture(autouse=True)
    def _stub_uow_session(self):
        cm = AsyncMock()
        cm.__aenter__.return_value = None
        cm.__aexit__.return_value = None
        with patch(
            "services.alerts_service.async_session_scope", return_value=cm
        ):
            yield

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=AlertsRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр AlertsService с моком репозитория."""
        return AlertsService(repository=mock_repo)

    def _search_row(
        self,
        alert_id,
        alert_name="test_alert",
        indicator_name="indicator",
        tags=None,
    ):
        """Строка результата search_alerts (dict, как asyncpg.Record)."""
        return {
            "id": alert_id,
            "alert_name": alert_name,
            "alert_description": None,
            "indicator_name": indicator_name,
            "indicator_description": None,
            "status_id": None,
            "paused": False,
            "tags": tags,
        }

    async def test_search_alerts_success(self, service, mock_repo):
        """Тест успешного поиска алертов."""
        alert_id = uuid4()
        mock_repo.search_alerts.return_value = (
            [self._search_row(alert_id)],
            1,
        )
        result = await service.search_alerts(query="test")
        assert result.total == 1
        assert len(result.alerts) == 1
        assert result.alerts[0].alert_id == alert_id
        mock_repo.search_alerts.assert_called_once()

    async def test_search_alerts_with_tags_json(self, service, mock_repo):
        """Тест поиска алертов с тегами в JSON формате."""
        alert_id = uuid4()
        tags_json = json.dumps(["tag1", "tag2"])
        mock_repo.search_alerts.return_value = (
            [self._search_row(alert_id, tags=tags_json)],
            1,
        )
        result = await service.search_alerts(query="test")
        assert result.alerts[0].tags == ["tag1", "tag2"]

    async def test_search_alerts_with_mapping_row(self, service, mock_repo):
        """Позитивный ORM-style кейс: search row приходит через _mapping."""
        alert_id = uuid4()

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": alert_id,
                "alert_name": "mapped_alert",
                "alert_description": None,
                "indicator_name": "mapped_indicator",
                "indicator_description": None,
                "status_id": None,
                "paused": True,
                "tags": None,
            }

        mock_repo.search_alerts.return_value = ([RowObj()], 1)
        result = await service.search_alerts(query="mapped")
        assert result.total == 1
        assert result.alerts[0].alert_id == alert_id
        assert result.alerts[0].paused is True

    async def test_search_alerts_with_keys_row(self, service, mock_repo):
        """Позитивный ORM-style кейс: search row приходит через keys()/index."""
        alert_id = uuid4()

        class RowObj:
            def keys(self):
                return [
                    "id",
                    "alert_name",
                    "alert_description",
                    "indicator_name",
                    "indicator_description",
                    "status_id",
                    "paused",
                    "tags",
                ]

            def __getitem__(self, idx):
                return [
                    alert_id,
                    "keys_alert",
                    None,
                    "keys_indicator",
                    None,
                    None,
                    False,
                    None,
                ][idx]

        mock_repo.search_alerts.return_value = ([RowObj()], 1)
        result = await service.search_alerts(query="keys")
        assert result.total == 1
        assert result.alerts[0].alert_id == alert_id
        assert result.alerts[0].alert_name == "keys_alert"

    async def test_search_alerts_error(self, service, mock_repo):
        """Тест обработки ошибки при поиске."""
        mock_repo.search_alerts.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.search_alerts()

        assert exc_info.value.status_code == 500

    async def test_get_alert_detail_success(self, service, mock_repo):
        """Тест успешного получения деталей алерта."""
        alert_id = uuid4()
        indicator_id = uuid4()
        group_rule_id = uuid4()
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "test_alert",
            "event": indicator_id,
            "event_name": "indicator_name",
            "description": "description",
            "image": "image",
            "tags": None,
            "group_rules": group_rule_id,
            "silence_time": None,
        }
        result = await service.get_alert_detail(alert_id)
        assert result.alert_id == alert_id
        assert result.alert_name == "test_alert"
        assert result.indicator.indicator_id == indicator_id
        mock_repo.get_alert_by_id.assert_called_once_with(alert_id)

    async def test_get_alert_detail_not_found(self, service, mock_repo):
        """Тест получения несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.get_alert_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_alert_detail(alert_id)

        assert exc_info.value.status_code == 404
        assert "не найден" in exc_info.value.detail

    async def test_get_alert_detail_with_tags(self, service, mock_repo):
        """Тест получения алерта с тегами."""
        alert_id = uuid4()
        tags_json = json.dumps(["tag1", "tag2"])
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "test",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": tags_json,
            "group_rules": None,
            "silence_time": None,
        }
        result = await service.get_alert_detail(alert_id)
        assert result.tags == ["tag1", "tag2"]

    async def test_get_alert_detail_with_mapping_row(self, service, mock_repo):
        """Позитивный ORM-style кейс: detail row приходит через _mapping."""
        alert_id = uuid4()
        indicator_id = uuid4()

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": alert_id,
                "alert_name": "mapped_detail",
                "event": indicator_id,
                "event_name": "mapped_event",
                "alert_description": "desc",
                "alert_image": "img",
                "tags": '["x"]',
                "group_rules": None,
                "silence_time": None,
                "paused": False,
            }

        mock_repo.get_alert_by_id.return_value = RowObj()
        result = await service.get_alert_detail(alert_id)
        assert result.alert_id == alert_id
        assert result.indicator.indicator_id == indicator_id
        assert result.tags == ["x"]

    async def test_get_alert_detail_includes_group_rule_and_fields(
        self, service, mock_repo
    ):
        """Покрыть description/image/group_rule/silence_time в detail."""
        alert_id = uuid4()
        group_rule_id = uuid4()
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "test",
            "event": uuid4(),
            "event_name": "ind",
            "alert_description": "desc",
            "alert_image": "img",
            "tags": None,
            "group_rules": group_rule_id,
            "group_rule_description": "grd",
            "group_rule_image": "gri",
            "silence_time": '{"k":"v"}',
            "paused": None,
        }
        result = await service.get_alert_detail(alert_id)
        assert result.description == "desc"
        assert result.image == "img"
        assert result.group_rule is not None
        assert result.group_rule.group_rule_id == group_rule_id

    async def test_create_alert_success(self, service, mock_repo):
        """Тест успешного создания алерта."""
        mock_repo.check_alert_exists_by_name.return_value = False
        mock_repo.check_group_rule_exists.return_value = True
        mock_repo.create_alert.return_value = uuid4()

        data = AlertDetailCreate(
            alert_name="test_alert",
            indicator_id=uuid4(),
            description="test description",
            image="test_image",
            group_rule_id=uuid4(),
        )

        result = await service.create_alert(data)

        assert result is True
        mock_repo.check_alert_exists_by_name.assert_called_once_with(
            "test_alert", ANY
        )
        mock_repo.check_group_rule_exists.assert_called_once_with(
            data.group_rule_id, ANY
        )
        mock_repo.create_alert.assert_called_once()

    async def test_create_alert_duplicate_name(self, service, mock_repo):
        """Тест создания алерта с дублирующимся именем."""
        mock_repo.check_alert_exists_by_name.return_value = True

        data = AlertDetailCreate(
            alert_name="existing_alert",
            indicator_id=uuid4(),
            description="test description",
            image="test_image",
            group_rule_id=uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_alert(data)

        assert exc_info.value.status_code == 400
        assert "уже существует" in exc_info.value.detail

    async def test_create_alert_invalid_group_rule(self, service, mock_repo):
        """Тест создания алерта с несуществующей группой правил."""
        mock_repo.check_alert_exists_by_name.return_value = False
        mock_repo.check_group_rule_exists.return_value = False

        data = AlertDetailCreate(
            alert_name="test",
            indicator_id=uuid4(),
            description="test description",
            image="test_image",
            group_rule_id=uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_alert(data)

        assert exc_info.value.status_code == 400
        assert "группа правил не найдена" in exc_info.value.detail

    async def test_create_alert_invalid_silence_time(self, service, mock_repo):
        """Тест создания алерта с невалидным silence_time - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        with pytest.raises(ValidationError) as exc_info:
            AlertDetailCreate(
                alert_name="test",
                indicator_id=uuid4(),
                description="test description",
                image="test_image",
                group_rule_id=uuid4(),
                silence_time="invalid json",
            )

        # Проверяем что ошибка связана с silence_time
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("silence_time",) for err in errors)

    async def test_update_alert_success(self, service, mock_repo):
        """Тест успешного обновления алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "old_name",
            "event": uuid4(),
            "event_name": "indicator",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": None,
        }
        # Имя не дублируется (старое имя отличается от нового)
        mock_repo.check_alert_exists_by_name.return_value = False
        mock_repo.update_alert.return_value = True

        data = AlertDetailUpdate(alert_id=alert_id, alert_name="updated_name")

        result = await service.update_alert(data)

        assert result is True
        mock_repo.check_alert_exists_by_id.assert_called_once_with(
            alert_id, ANY
        )
        mock_repo.update_alert.assert_called_once()

    async def test_update_alert_not_found(self, service, mock_repo):
        """Тест обновления несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = False

        data = AlertDetailUpdate(alert_id=alert_id, alert_name="updated")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert(data)

        assert exc_info.value.status_code == 404

    async def test_delete_alert_success(self, service, mock_repo):
        """Тест успешного удаления алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True
        mock_repo.delete_alert_with_cascade.return_value = True

        result = await service.delete_alert(alert_id)

        assert result is True
        mock_repo.check_alert_exists_by_id.assert_called_once_with(
            alert_id, ANY
        )
        mock_repo.delete_alert_with_cascade.assert_called_once_with(
            alert_id, ANY
        )

    async def test_delete_alert_not_found(self, service, mock_repo):
        """Тест удаления несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_alert(alert_id)

        assert exc_info.value.status_code == 404

    async def test_autocomplete_alerts(self, service, mock_repo):
        """Тест автодополнения алертов."""
        alert_id = uuid4()
        mock_repo.autocomplete_alerts.return_value = [
            {"id": alert_id, "alert_name": "test_alert"}
        ]

        result = await service.autocomplete_alerts("test", 10)

        assert len(result.alerts) == 1
        assert result.alerts[0].alert_id == alert_id
        mock_repo.autocomplete_alerts.assert_called_once_with("test", 10)

    async def test_autocomplete_alerts_with_mapping_row(
        self, service, mock_repo
    ):
        """Позитивный ORM-style кейс: autocomplete row приходит через _mapping."""
        alert_id = uuid4()

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": alert_id,
                "alert_name": "mapped_auto",
            }

        mock_repo.autocomplete_alerts.return_value = [RowObj()]

        result = await service.autocomplete_alerts("mapped", 10)

        assert len(result.alerts) == 1
        assert result.alerts[0].alert_id == alert_id
        assert result.alerts[0].alert_name == "mapped_auto"

    async def test_autocomplete_alerts_with_keys_row(self, service, mock_repo):
        """Позитивный ORM-style кейс: autocomplete row через keys()/index."""
        alert_id = uuid4()

        class RowObj:
            def keys(self):
                return ["id", "alert_name"]

            def __getitem__(self, idx):
                return [alert_id, "keys_auto"][idx]

        mock_repo.autocomplete_alerts.return_value = [RowObj()]
        result = await service.autocomplete_alerts("keys", 10)
        assert len(result.alerts) == 1
        assert result.alerts[0].alert_id == alert_id
        assert result.alerts[0].alert_name == "keys_auto"

    async def test_get_tag_cloud(self, service, mock_repo):
        """Тест получения облака тегов."""
        mock_repo.get_tag_cloud.return_value = ["tag1", "tag2", "tag3"]

        result = await service.get_tag_cloud()

        assert len(result.tags) == 3
        assert "tag1" in result.tags
        mock_repo.get_tag_cloud.assert_called_once_with(
            alert_name=None, tags=None
        )

    async def test_duplicate_alert_success(self, service, mock_repo):
        """Тест успешного дублирования алерта."""
        alert_id = uuid4()
        new_alert_id = uuid4()
        mock_repo.duplicate_alert.return_value = new_alert_id

        result = await service.duplicate_alert(alert_id)

        assert result is True
        mock_repo.duplicate_alert.assert_called_once_with(alert_id, ANY)

    async def test_duplicate_alert_not_found(self, service, mock_repo):
        """Тест дублирования несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.duplicate_alert.side_effect = ValueError("Алерт не найден")

        with pytest.raises(HTTPException) as exc_info:
            await service.duplicate_alert(alert_id)

        assert exc_info.value.status_code == 404
        assert "не найден" in exc_info.value.detail

    async def test_search_alerts_invalid_tags_json(self, service, mock_repo):
        """Тест поиска алертов с невалидным JSON в тегах."""
        alert_id = uuid4()
        mock_repo.search_alerts.return_value = (
            [self._search_row(alert_id, tags="invalid json")],
            1,
        )
        result = await service.search_alerts(query="test")
        assert result.alerts[0].tags is None

    async def test_search_alerts_sets_optional_fields(self, service, mock_repo):
        """Покрыть optional-поля alert_description/indicator_description/status_id/tags."""
        alert_id = uuid4()
        mock_repo.search_alerts.return_value = (
            [
                {
                    "id": alert_id,
                    "alert_name": "a",
                    "alert_description": "ad",
                    "indicator_name": "i",
                    "indicator_description": "id",
                    "status_id": uuid4(),
                    "paused": True,
                    "tags": '["t1"]',
                }
            ],
            1,
        )
        result = await service.search_alerts(query="a")
        item = result.alerts[0]
        assert item.alert_description == "ad"
        assert item.indicator_description == "id"
        assert item.status_id is not None
        assert item.tags == ["t1"]

    async def test_get_alert_detail_with_silence_time(
        self, service, mock_repo
    ):
        """Тест получения алерта с silence_time."""
        alert_id = uuid4()
        silence_time_json = json.dumps({"monday": "09:00-18:00"})
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "test",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": silence_time_json,
        }
        result = await service.get_alert_detail(alert_id)
        assert result.silence_time == {"monday": "09:00-18:00"}

    async def test_get_alert_detail_with_invalid_silence_time_json(
        self, service, mock_repo
    ):
        """Тест получения алерта с невалидным JSON в silence_time."""
        alert_id = uuid4()
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "test",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": "invalid json",
        }
        result = await service.get_alert_detail(alert_id)
        assert result.silence_time == "invalid json"

    async def test_get_alert_detail_with_invalid_tags_json(
        self, service, mock_repo
    ):
        """Покрыть except для парсинга tags в detail."""
        alert_id = uuid4()
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "test",
            "event": uuid4(),
            "event_name": "ind",
            "alert_description": None,
            "alert_image": None,
            "tags": "{bad",
            "group_rules": None,
            "silence_time": None,
            "paused": False,
        }
        result = await service.get_alert_detail(alert_id)
        assert result.tags is None

    async def test_get_alert_detail_with_empty_silence_time(
        self, service, mock_repo
    ):
        """Тест получения алерта с пустым silence_time."""
        alert_id = uuid4()
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "test",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": "   ",
        }
        result = await service.get_alert_detail(alert_id)
        assert result.silence_time == {}

    async def test_get_alert_detail_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении деталей алерта."""
        alert_id = uuid4()
        mock_repo.get_alert_by_id.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_alert_detail(alert_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении алерта" in exc_info.value.detail

    async def test_create_alert_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при создании алерта."""
        mock_repo.check_alert_exists_by_name.return_value = False
        mock_repo.check_group_rule_exists.return_value = True
        mock_repo.create_alert.side_effect = Exception("Ошибка БД")

        data = AlertDetailCreate(
            alert_name="test",
            indicator_id=uuid4(),
            description="test",
            image="test",
            group_rule_id=uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_alert(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при создании алерта" in exc_info.value.detail

    async def test_update_alert_with_empty_silence_time(
        self, service, mock_repo
    ):
        """Тест обновления алерта с пустым silence_time."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "old_name",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": None,
        }
        mock_repo.check_alert_exists_by_name.return_value = False
        mock_repo.update_alert.return_value = True
        data = AlertDetailUpdate(alert_id=alert_id, silence_time="")

        result = await service.update_alert(data)

        assert result is True
        # Проверяем, что silence_time передается как пустая строка для установки NULL в БД
        call_args = mock_repo.update_alert.call_args
        assert (
            call_args[1]["silence_time"] == ""
        )  # Пустая строка означает установку NULL в БД

    async def test_update_alert_invalid_silence_time_json(
        self, service, mock_repo
    ):
        """Тест обновления алерта с невалидным JSON в silence_time - валидация происходит в схеме."""
        from pydantic import ValidationError

        # Валидация происходит на уровне схемы, до вызова сервиса
        with pytest.raises(ValidationError) as exc_info:
            AlertDetailUpdate(alert_id=uuid4(), silence_time="invalid json")

        # Проверяем что ошибка связана с silence_time
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("silence_time",) for err in errors)

    async def test_update_alert_duplicate_name(self, service, mock_repo):
        """Тест обновления алерта с дублирующимся именем."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "old_name",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": None,
        }
        mock_repo.check_alert_exists_by_name.return_value = (
            True  # Имя уже существует
        )

        data = AlertDetailUpdate(alert_id=alert_id, alert_name="existing_name")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert(data)

        assert exc_info.value.status_code == 400
        assert "уже существует" in exc_info.value.detail

    async def test_update_alert_duplicate_name_with_mapping_existing_row(
        self, service, mock_repo
    ):
        """Позитивный ORM-style кейс: existing_alert в update приходит через _mapping."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True

        class ExistingAlertRow:
            _mapping: ClassVar[dict[str, object]] = {
                "id": alert_id,
                "alert_name": "old_name",
            }

        mock_repo.get_alert_by_id.return_value = ExistingAlertRow()
        mock_repo.check_alert_exists_by_name.return_value = True

        data = AlertDetailUpdate(alert_id=alert_id, alert_name="existing_name")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert(data)

        assert exc_info.value.status_code == 400
        assert "уже существует" in exc_info.value.detail

    async def test_update_alert_invalid_group_rule(self, service, mock_repo):
        """Тест обновления алерта с несуществующей группой правил."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "old_name",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": None,
        }
        mock_repo.check_alert_exists_by_name.return_value = False
        mock_repo.check_group_rule_exists.return_value = False

        data = AlertDetailUpdate(alert_id=alert_id, group_rule_id=uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert(data)

        assert exc_info.value.status_code == 400
        assert "группа правил не найдена" in exc_info.value.detail

    async def test_update_alert_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при обновлении алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True
        mock_repo.get_alert_by_id.return_value = {
            "id": alert_id,
            "alert_name": "old_name",
            "event": uuid4(),
            "event_name": "ind",
            "description": None,
            "image": None,
            "tags": None,
            "group_rules": None,
            "silence_time": None,
        }
        mock_repo.check_alert_exists_by_name.return_value = False
        mock_repo.update_alert.side_effect = Exception("Ошибка БД")

        data = AlertDetailUpdate(alert_id=alert_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.update_alert(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при обновлении алерта" in exc_info.value.detail

    async def test_delete_alert_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при удалении алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists_by_id.return_value = True
        mock_repo.delete_alert_with_cascade.side_effect = Exception(
            "Ошибка БД"
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_alert(alert_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при удалении алерта" in exc_info.value.detail

    async def test_autocomplete_alerts_error_handling(
        self, service, mock_repo
    ):
        """Тест обработки ошибки при автодополнении."""
        mock_repo.autocomplete_alerts.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.autocomplete_alerts("test", 10)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении автодополнения" in exc_info.value.detail

    async def test_get_tag_cloud_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении облака тегов."""
        mock_repo.get_tag_cloud.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_tag_cloud()

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении облака тегов" in exc_info.value.detail

    async def test_duplicate_alert_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при дублировании алерта."""
        alert_id = uuid4()
        mock_repo.duplicate_alert.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.duplicate_alert(alert_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при дублировании алерта" in exc_info.value.detail

    async def test_duplicate_alert_http_exception_passthrough(
        self, service, mock_repo
    ):
        """Покрыть except HTTPException: raise в duplicate_alert."""
        from fastapi import HTTPException as FastAPIHTTPException

        alert_id = uuid4()
        mock_repo.duplicate_alert.side_effect = FastAPIHTTPException(
            status_code=400, detail="bad"
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.duplicate_alert(alert_id)
        assert exc_info.value.status_code == 400
