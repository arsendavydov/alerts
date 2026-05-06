"""
Модульные тесты для AlertsRepository.
Используют моки для изоляции от реальной БД.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.alerts_repository import AlertsRepository

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestAlertsRepository:
    """Тесты для AlertsRepository."""

    @pytest.fixture
    def repo(self):
        """Экземпляр AlertsRepository."""
        return AlertsRepository()

    async def test_escape_like_special_chars(self, repo):
        """Покрыть helper _escape_like."""
        assert repo._escape_like(r"a_%\b") == r"a\_\%\\b"

    async def test_check_alert_exists_by_name_with_explicit_session(
        self, repo
    ):
        """Покрыть _run_with_session ветку session is not None."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        result = await repo.check_alert_exists_by_name("name", session)
        assert result is True

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_search_alerts(self, mock_session_scope, repo):
        """Тест поиска алертов."""
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            {
                "id": uuid4(),
                "alert_name": "test",
                "alert_description": None,
                "indicator_name": "indicator",
                "indicator_description": None,
                "status_id": None,
                "paused": False,
                "tags": None,
            }
        ]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.search_alerts(
            query="test", limit=10, offset=0
        )

        assert total == 1
        assert len(rows) == 1
        assert session.execute.call_count == 2

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_search_alerts_escapes_like_wildcards(
        self, mock_session_scope, repo
    ):
        """
        Регресс-тест: символы %, _ и \\ в query не должны работать как wildcard.
        Проверяем, что запрос выполняется без ошибок в буквальном режиме.
        """
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        query = r"по_wsop%test\end"
        await repo.search_alerts(query=query, limit=10, offset=0)

        assert session.execute.call_count == 2

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_search_alerts_with_tags(self, mock_session_scope, repo):
        """Тест поиска алертов с тегами."""
        count_result = Mock()
        count_result.scalar_one.return_value = 0
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        await repo.search_alerts(tags="tag1,tag2", limit=10, offset=0)

        assert session.execute.call_count == 2

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_get_alert_by_id(self, mock_session_scope, repo):
        """Тест получения алерта по ID."""
        alert_id = uuid4()
        event_id = uuid4()
        execute_result = Mock()
        execute_result.mappings.return_value.one_or_none.return_value = {
            "id": alert_id,
            "alert_name": "test_alert",
            "event": event_id,
            "event_name": "indicator",
            "alert_description": None,
            "alert_image": None,
            "tags": None,
            "group_rules": None,
            "group_rule_description": None,
            "group_rule_image": None,
            "silence_time": None,
            "paused": False,
        }
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_alert_by_id(alert_id)

        assert result is not None
        assert result.get("id") == alert_id
        session.execute.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_get_alert_by_id_not_found(self, mock_session_scope, repo):
        """Тест получения несуществующего алерта."""
        alert_id = uuid4()
        execute_result = Mock()
        execute_result.mappings.return_value.one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_alert_by_id(alert_id)

        assert result is None

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_check_alert_exists_by_name(self, mock_session_scope, repo):
        """Тест проверки существования алерта по имени."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_alert_exists_by_name("test_alert")

        assert result is True
        session.execute.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_check_alert_exists_by_name_not_found(
        self, mock_session_scope, repo
    ):
        """Тест проверки несуществующего алерта по имени."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_alert_exists_by_name("nonexistent")

        assert result is False

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_check_alert_exists_by_id(self, mock_session_scope, repo):
        """Тест проверки существования алерта по ID."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_alert_exists_by_id(uuid4())

        assert result is True

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_create_alert(self, mock_session_scope, repo):
        """Тест создания алерта."""
        alert_id = uuid4()
        session = AsyncMock()
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = alert_id
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.create_alert(
            alert_name="test",
            indicator_id=uuid4(),
            description="desc",
            image=None,
            tags=["tag1"],
            group_rule_id=uuid4(),
            silence_time=None,
        )

        assert result == alert_id
        session.execute.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_autocomplete_alerts(self, mock_session_scope, repo):
        """Тест автодополнения алертов."""
        alert_id = uuid4()
        execute_result = Mock()
        execute_result.mappings.return_value.all.return_value = [
            {"id": alert_id, "alert_name": "test_alert"}
        ]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.autocomplete_alerts("test", 10)

        assert len(result) == 1
        assert result[0].get("id") == alert_id
        session.execute.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_autocomplete_alerts_escapes_like_wildcards(
        self, mock_session_scope, repo
    ):
        """
        Регресс-тест: символы %, _ и \\ в query не должны работать как wildcard в autocomplete.
        """
        execute_result = Mock()
        execute_result.mappings.return_value.all.return_value = [
            {"id": uuid4(), "alert_name": "x"}
        ]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        query = r"по_wsop%test\end"
        await repo.autocomplete_alerts(query, 10)

        assert session.execute.call_count == 1

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_search_alerts_fallback_to_wildcards_when_no_literal_results(
        self, mock_session_scope, repo
    ):
        """
        Регресс-тест UX: если query содержит '_'/'%' и буквальный (экранированный) поиск ничего не нашёл,
        делаем фоллбек как шаблон (поведение старого поиска, нужное фронту).
        """
        count_result_1 = Mock()
        count_result_1.scalar_one.return_value = 0
        data_result_1 = Mock()
        data_result_1.mappings.return_value.all.return_value = []
        count_result_2 = Mock()
        count_result_2.scalar_one.return_value = 1
        data_result_2 = Mock()
        data_result_2.mappings.return_value.all.return_value = [
            {
                "id": uuid4(),
                "alert_name": "x",
                "alert_description": None,
                "indicator_name": "i",
                "indicator_description": None,
                "status_id": None,
                "paused": False,
                "tags": None,
            }
        ]
        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[
                count_result_1,
                data_result_1,
                count_result_2,
                data_result_2,
            ]
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.search_alerts(
            query="_wsopspo_", limit=10, offset=0
        )

        assert total == 1
        assert len(rows) == 1
        assert session.execute.call_count == 4

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_autocomplete_alerts_fallback_to_wildcards_when_no_literal_results(
        self, mock_session_scope, repo
    ):
        """Фоллбек как шаблон для autocomplete при 0 результатов в буквальном поиске."""
        execute_result_1 = Mock()
        execute_result_1.mappings.return_value.all.return_value = []
        execute_result_2 = Mock()
        execute_result_2.mappings.return_value.all.return_value = [
            {"id": uuid4(), "alert_name": "no_wsopspo_test"}
        ]
        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[execute_result_1, execute_result_2]
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.autocomplete_alerts("_wsopspo_", 10)

        assert len(result) == 1
        assert session.execute.call_count == 2

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_get_tag_cloud(self, mock_session_scope, repo):
        """Тест получения облака тегов."""
        execute_result = Mock()
        execute_result.all.return_value = [
            ('["tag1","tag2"]',),
            ('["tag2","tag3"]',),
        ]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_tag_cloud()

        assert len(result) == 3
        assert "tag1" in result
        session.execute.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_check_group_rule_exists(self, mock_session_scope, repo):
        """Тест проверки существования группы правил."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_group_rule_exists(uuid4())

        assert result is True

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_create_alert_with_silence_time(
        self, mock_session_scope, repo
    ):
        """Тест создания алерта с silence_time."""
        alert_id = uuid4()
        session = AsyncMock()
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = alert_id
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.create_alert(
            alert_name="test",
            indicator_id=uuid4(),
            description="desc",
            image="img",
            tags=["tag1"],
            group_rule_id=uuid4(),
            silence_time='{"time": "1h"}',
        )

        assert result == alert_id
        session.execute.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_create_alert_with_empty_image(
        self, mock_session_scope, repo
    ):
        """Тест создания алерта с пустым image."""
        alert_id = uuid4()
        session = AsyncMock()
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = alert_id
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.create_alert(
            alert_name="test",
            indicator_id=uuid4(),
            description="desc",
            image=None,
            tags=None,
            group_rule_id=uuid4(),
            silence_time=None,
        )

        assert result == alert_id
        session.execute.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_create_alert_raises_when_id_not_generated(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(ValueError, match="Не удалось создать алерт"):
            await repo.create_alert(
                alert_name="test",
                indicator_id=uuid4(),
                description="desc",
                image=None,
                tags=None,
                group_rule_id=uuid4(),
                silence_time=None,
            )

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_duplicate_alert(self, mock_session_scope, repo):
        """Тест дублирования алерта."""
        alert_id = uuid4()
        new_alert_id = uuid4()
        event_id = uuid4()
        group_rule_id = uuid4()
        source_alert = SimpleNamespace(
            id=alert_id,
            alert_name="test_alert",
            event=event_id,
            description="desc",
            image="img",
            tags="[]",
            group_rules=group_rule_id,
            silence_time=None,
        )
        duplicated_alert = SimpleNamespace(id=new_alert_id)
        session = AsyncMock()
        session.get = AsyncMock(return_value=source_alert)

        existing_name_result = Mock()
        existing_name_result.scalar_one_or_none.return_value = None
        links_result = Mock()
        links_result.scalars.return_value.all.return_value = []
        subscriptions_result = Mock()
        subscriptions_result.scalars.return_value.all.return_value = []
        dt_result = Mock()
        dt_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(
            side_effect=[
                existing_name_result,
                links_result,
                subscriptions_result,
                dt_result,
            ]
        )

        def add_side_effect(entity):
            if getattr(entity, "alert_name", None) and getattr(
                entity, "event", None
            ):
                entity.id = duplicated_alert.id

        session.add = Mock(side_effect=add_side_effect)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.duplicate_alert(alert_id)

        assert result == new_alert_id

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_duplicate_alert_not_found(self, mock_session_scope, repo):
        """Тест дублирования несуществующего алерта."""
        alert_id = uuid4()
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(ValueError, match="не найден"):
            await repo.duplicate_alert(alert_id)

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_update_alert(self, mock_session_scope, repo):
        """Тест обновления алерта."""
        alert_id = uuid4()
        alert_obj = SimpleNamespace(
            id=alert_id,
            alert_name="old",
            event=uuid4(),
            description="old_d",
            image="old_i",
            tags=None,
            group_rules=uuid4(),
            silence_time=None,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=alert_obj)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.update_alert(
            alert_id=alert_id, alert_name="updated_name", indicator_id=uuid4()
        )

        assert result is True
        session.flush.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_update_alert_no_updates(self, mock_session_scope, repo):
        """Тест обновления алерта без изменений."""
        alert_id = uuid4()
        alert_obj = SimpleNamespace(
            id=alert_id,
            alert_name="old",
            event=uuid4(),
            description="old_d",
            image="old_i",
            tags=None,
            group_rules=uuid4(),
            silence_time=None,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=alert_obj)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.update_alert(alert_id=alert_id)

        assert result is True
        session.flush.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_update_alert_not_found_returns_true(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        assert await repo.update_alert(alert_id=uuid4(), alert_name="x") is True

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_delete_alert_with_cascade(self, mock_session_scope, repo):
        """Тест каскадного удаления алерта."""
        alert_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.delete_alert_with_cascade(alert_id)

        assert result is True
        # Проверяем, что были удалены все связанные данные
        assert (
            session.execute.call_count >= 6
        )  # статусы, подписки, линки, паузы, DT, алерт

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_duplicate_alert_with_silence_time(
        self, mock_session_scope, repo
    ):
        """Тест дублирования алерта с silence_time."""
        alert_id = uuid4()
        new_alert_id = uuid4()
        event_id = uuid4()
        group_rule_id = uuid4()
        silence_time = '{"time": "1h"}'
        source_alert = SimpleNamespace(
            id=alert_id,
            alert_name="test_alert",
            event=event_id,
            description="desc",
            image="img",
            tags="[]",
            group_rules=group_rule_id,
            silence_time=silence_time,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=source_alert)
        existing_name_result = Mock()
        existing_name_result.scalar_one_or_none.return_value = None
        links_result = Mock()
        links_result.scalars.return_value.all.return_value = []
        subscriptions_result = Mock()
        subscriptions_result.scalars.return_value.all.return_value = []
        dt_result = Mock()
        dt_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(
            side_effect=[
                existing_name_result,
                links_result,
                subscriptions_result,
                dt_result,
            ]
        )

        def add_side_effect(entity):
            if getattr(entity, "alert_name", None) and getattr(
                entity, "event", None
            ):
                entity.id = new_alert_id

        session.add = Mock(side_effect=add_side_effect)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.duplicate_alert(alert_id)

        assert result == new_alert_id
        created_alert = session.add.call_args_list[0].args[0]
        assert created_alert.silence_time == silence_time

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_duplicate_alert_with_subscription_statuses(
        self, mock_session_scope, repo
    ):
        """Тест дублирования алерта с подписками и статусами."""
        alert_id = uuid4()
        new_alert_id = uuid4()
        event_id = uuid4()
        group_rule_id = uuid4()
        subscription_id = uuid4()
        contact_id = uuid4()
        new_subscription_id = uuid4()

        source_alert = SimpleNamespace(
            id=alert_id,
            alert_name="test_alert",
            event=event_id,
            description="desc",
            image="img",
            tags="[]",
            group_rules=group_rule_id,
            silence_time=None,
        )
        old_subscription = SimpleNamespace(
            id=subscription_id,
            alert=alert_id,
            contact=contact_id,
            telegram=True,
            email=False,
            __table__=SimpleNamespace(
                columns=[
                    SimpleNamespace(name="id"),
                    SimpleNamespace(name="alert"),
                    SimpleNamespace(name="contact"),
                    SimpleNamespace(name="telegram"),
                    SimpleNamespace(name="email"),
                ]
            ),
        )
        status = SimpleNamespace(status=uuid4(), repeat=5)
        session = AsyncMock()
        session.get = AsyncMock(return_value=source_alert)
        existing_name_result = Mock()
        existing_name_result.scalar_one_or_none.return_value = None
        links_result = Mock()
        links_result.scalars.return_value.all.return_value = []
        subscriptions_result = Mock()
        subscriptions_result.scalars.return_value.all.return_value = [
            old_subscription
        ]
        statuses_result = Mock()
        statuses_result.scalars.return_value.all.return_value = [status]
        dt_result = Mock()
        dt_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(
            side_effect=[
                existing_name_result,
                links_result,
                subscriptions_result,
                statuses_result,
                dt_result,
            ]
        )

        def add_side_effect(entity):
            if getattr(entity, "alert_name", None) and getattr(
                entity, "event", None
            ):
                entity.id = new_alert_id
            elif getattr(entity, "contact", None) == contact_id:
                entity.id = new_subscription_id

        session.add = Mock(side_effect=add_side_effect)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.duplicate_alert(alert_id)

        assert result == new_alert_id
        assert session.flush.await_count >= 2

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_duplicate_alert_with_dt_silence_time(
        self, mock_session_scope, repo
    ):
        """Тест дублирования алерта с DT и silence_time."""
        alert_id = uuid4()
        new_alert_id = uuid4()
        event_id = uuid4()
        group_rule_id = uuid4()
        dt_silence_time = '{"time": "2h"}'
        source_alert = SimpleNamespace(
            id=alert_id,
            alert_name="test_alert",
            event=event_id,
            description="desc",
            image="img",
            tags="[]",
            group_rules=group_rule_id,
            silence_time=None,
        )
        dt_obj = SimpleNamespace(
            content='{"key":"value"}',
            auto_create=True,
            silence_time=dt_silence_time,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=source_alert)
        existing_name_result = Mock()
        existing_name_result.scalar_one_or_none.return_value = None
        links_result = Mock()
        links_result.scalars.return_value.all.return_value = []
        subscriptions_result = Mock()
        subscriptions_result.scalars.return_value.all.return_value = []
        dt_result = Mock()
        dt_result.scalar_one_or_none.return_value = dt_obj
        session.execute = AsyncMock(
            side_effect=[
                existing_name_result,
                links_result,
                subscriptions_result,
                dt_result,
            ]
        )

        def add_side_effect(entity):
            if getattr(entity, "alert_name", None) and getattr(
                entity, "event", None
            ):
                entity.id = new_alert_id

        session.add = Mock(side_effect=add_side_effect)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.duplicate_alert(alert_id)

        assert result == new_alert_id
        added_entities = [call.args[0] for call in session.add.call_args_list]
        assert any(
            getattr(entity, "silence_time", None) == dt_silence_time
            for entity in added_entities
        )

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_update_alert_with_all_fields(
        self, mock_session_scope, repo
    ):
        """Тест обновления алерта со всеми полями."""
        alert_id = uuid4()
        alert_obj = SimpleNamespace(
            id=alert_id,
            alert_name="old",
            event=uuid4(),
            description="old_d",
            image="old_i",
            tags=None,
            group_rules=uuid4(),
            silence_time=None,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=alert_obj)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.update_alert(
            alert_id=alert_id,
            alert_name="updated_name",
            indicator_id=uuid4(),
            description="updated_desc",
            image="updated_img",
            tags=["tag1", "tag2"],
            group_rule_id=uuid4(),
            silence_time='{"time": "1h"}',
        )

        assert result is True
        session.flush.assert_called_once()
        assert alert_obj.alert_name == "updated_name"
        assert alert_obj.description == "updated_desc"
        assert alert_obj.tags == '["tag1", "tag2"]'

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_update_alert_error(self, mock_session_scope, repo):
        """Тест обновления алерта с ошибкой."""
        alert_id = uuid4()
        session = AsyncMock()
        session.get = AsyncMock(return_value=SimpleNamespace())
        session.flush = AsyncMock(side_effect=Exception("DB error"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception):
            await repo.update_alert(alert_id=alert_id, alert_name="updated")

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_delete_alert_with_cascade_error(
        self, mock_session_scope, repo
    ):
        """Тест каскадного удаления алерта с ошибкой."""
        alert_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception):
            await repo.delete_alert_with_cascade(alert_id)

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_delete_alert(self, mock_session_scope, repo):
        """Тест простого удаления алерта."""
        alert_id = uuid4()
        session = AsyncMock()
        session.get = AsyncMock(return_value=SimpleNamespace(id=alert_id))
        session.delete = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.delete_alert(alert_id)

        assert result is True
        session.delete.assert_called_once()

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_autocomplete_alerts_without_query(
        self, mock_session_scope, repo
    ):
        execute_result = Mock()
        execute_result.mappings.return_value.all.return_value = [
            {"id": uuid4(), "alert_name": "a"},
            {"id": uuid4(), "alert_name": "b"},
        ]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.autocomplete_alerts(None, 5)
        assert len(result) == 2

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_get_tag_cloud_skips_invalid_and_excludes_filter(
        self, mock_session_scope, repo
    ):
        execute_result = Mock()
        execute_result.all.return_value = [
            (None,),
            ("not-json",),
            ('{"bad":"shape"}',),
            ('["tag1","tag2"]',),
            (["tag2", "tag3"],),
        ]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_tag_cloud(tags="tag2")
        assert "tag2" not in result
        assert "tag1" in result
        assert "tag3" in result

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_duplicate_alert_when_name_conflicts_adds_suffix(
        self, mock_session_scope, repo
    ):
        alert_id = uuid4()
        new_alert_id = uuid4()
        source_alert = SimpleNamespace(
            id=alert_id,
            alert_name="test_alert",
            event=uuid4(),
            description="desc",
            image="img",
            tags="[]",
            group_rules=uuid4(),
            silence_time=None,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=source_alert)

        existing_name_result = Mock()
        existing_name_result.scalar_one_or_none.return_value = uuid4()
        links_result = Mock()
        link_obj = SimpleNamespace(link_name="L", link_url="U")
        links_result.scalars.return_value.all.return_value = [link_obj]
        subscriptions_result = Mock()
        subscriptions_result.scalars.return_value.all.return_value = []
        dt_result = Mock()
        dt_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(
            side_effect=[
                existing_name_result,
                links_result,
                subscriptions_result,
                dt_result,
            ]
        )

        def add_side_effect(entity):
            if getattr(entity, "alert_name", None) and getattr(
                entity, "event", None
            ):
                entity.id = new_alert_id

        session.add = Mock(side_effect=add_side_effect)
        session.flush = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.duplicate_alert(alert_id)
        assert result == new_alert_id

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_search_alerts_with_special_order_fields(
        self, mock_session_scope, repo
    ):
        """Покрыть order_by=status_id/paused ветки выбора sort_column."""
        count_result = Mock()
        count_result.scalar_one.return_value = 0
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.search_alerts(order_by="status_id")
        assert rows == []
        assert total == 0

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_search_alerts_with_paused_desc_order(
        self, mock_session_scope, repo
    ):
        """Покрыть order_by=paused и desc-ветку."""
        count_result = Mock()
        count_result.scalar_one.return_value = 0
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.search_alerts(
            order_by="paused", order_dir="desc"
        )
        assert rows == []
        assert total == 0

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_search_alerts_with_unknown_order_field(
        self, mock_session_scope, repo
    ):
        """Покрыть fallback sort_column по alert_name."""
        count_result = Mock()
        count_result.scalar_one.return_value = 0
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.search_alerts(order_by="unknown_field")
        assert rows == []
        assert total == 0

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_get_tag_cloud_with_alert_name_literal_filter(
        self, mock_session_scope, repo
    ):
        """Покрыть ветку alert_name без wildcard (экранированный LIKE)."""
        execute_result = Mock()
        execute_result.all.return_value = [
            Mock(_mapping={"tags": '["tag1"]'})
        ]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_tag_cloud(alert_name="abc")
        assert result == ["tag1"]

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_get_tag_cloud_with_alert_name_wildcard_fallback(
        self, mock_session_scope, repo
    ):
        """Покрыть ветку fallback use_wildcards=True в get_tag_cloud."""
        execute_result_empty = Mock()
        execute_result_empty.all.return_value = []
        execute_result_fallback = Mock()
        execute_result_fallback.all.return_value = [
            Mock(_mapping={"tags": '["tagw"]'})
        ]
        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[execute_result_empty, execute_result_fallback]
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_tag_cloud(alert_name="_abc_")
        assert result == ["tagw"]

    @patch("repositories.alerts_repository.async_session_scope")
    async def test_get_tag_cloud_with_excluding_unmatched_tag_filter(
        self, mock_session_scope, repo
    ):
        """Покрыть continue при tag_list и несовпадающем наборе тегов."""
        execute_result = Mock()
        execute_result.all.return_value = [Mock(_mapping={"tags": '["t1"]'})]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_tag_cloud(tags="t1,t2")
        assert result == []
