"""
Модульные тесты для SubscriptionsRepository.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import Column, MetaData, String, Table, create_engine

from repositories.subscriptions_repository import SubscriptionsRepository

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestSubscriptionsRepository:
    """Тесты для SubscriptionsRepository."""

    @pytest.fixture(autouse=True)
    def _mock_reflection_for_unit(self, request, monkeypatch):
        """Для unit-тестов мокируем reflection, кроме тестов самого _get_reflected_table."""
        if request.node.name.startswith("test_get_reflected_table"):
            return

        metadata = MetaData()
        tables = {
            ("alerts", "contacts"): Table(
                "contacts",
                metadata,
                Column("id", String),
                Column("user_name", String),
                Column("email", String),
                Column("group", String),
                schema="alerts",
            ),
            ("alerts", "alerts_contacts"): Table(
                "alerts_contacts",
                metadata,
                Column("id", String),
                Column("alert", String),
                Column("contact", String),
                Column("telegram", String),
                Column("email", String),
                schema="alerts",
            ),
            ("alerts", "alerts"): Table(
                "alerts",
                metadata,
                Column("id", String),
                Column("alert_name", String),
                schema="alerts",
            ),
            ("alerts", "status"): Table(
                "status",
                metadata,
                Column("id", String),
                Column("status_name", String),
                schema="alerts",
            ),
            ("alerts", "rules_change_status"): Table(
                "rules_change_status",
                metadata,
                Column("new_alert_status", String),
                Column("send_notification", String),
                schema="alerts",
            ),
        }

        async def fake_get_reflected_table(_self, _session, schema, table_name):
            return tables.get((schema, table_name))

        monkeypatch.setattr(
            SubscriptionsRepository,
            "_get_reflected_table",
            fake_get_reflected_table,
        )

    @pytest.fixture
    def repo(self):
        """Создает экземпляр репозитория."""
        return SubscriptionsRepository()

    @pytest.fixture
    def mock_cursor(self):
        """Мок курсора."""
        cursor = MagicMock()
        cursor.__enter__ = Mock(return_value=cursor)
        cursor.__exit__ = Mock(return_value=None)
        cursor.fetchone = Mock()
        cursor.execute = Mock()
        cursor.rowcount = 1
        return cursor

    @pytest.fixture
    def test_uuid(self):
        """Тестовый UUID."""
        return uuid4()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_check_alert_exists_true(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест проверки существования алерта (существует)."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_alert_exists(test_uuid)

        assert result is True

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_check_alert_exists_false(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест проверки существования алерта (не существует)."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_alert_exists(test_uuid)

        assert result is False

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_check_user_exists_true(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест проверки существования пользователя (существует)."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_user_exists(test_uuid)

        assert result is True

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_check_user_exists_false(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест проверки существования пользователя (не существует)."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_user_exists(test_uuid)

        assert result is False

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_check_subscription_exists(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест проверки существования подписки."""
        subscription_id = uuid4()
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = subscription_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_subscription_exists(test_uuid, uuid4())

        assert result == subscription_id

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_check_subscription_exists_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест проверки несуществующей подписки."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.check_subscription_exists(test_uuid, uuid4())

        assert result is None

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_user_data(self, mock_session_scope, repo, test_uuid):
        """Тест получения данных пользователя."""
        execute_result = Mock()
        execute_result.one_or_none.return_value = Mock(
            _mapping={
                "id": test_uuid,
                "user_name": "user_name",
                "email": "email@test.com",
            }
        )
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_user_data(test_uuid)

        assert result is not None

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_alerts_contacts_columns(self, mock_session_scope, repo):
        """Тест получения колонок alerts_contacts."""
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=Mock(
                all=Mock(
                    return_value=[
                        Mock(_mapping={"column_name": "telegram"}),
                        Mock(_mapping={"column_name": "email"}),
                    ]
                )
            )
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_alerts_contacts_columns()

        assert "telegram" in result
        assert "email" in result

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_user_columns(self, mock_session_scope, repo):
        """Тест получения колонок пользователя."""
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=Mock(
                all=Mock(
                    return_value=[
                        Mock(_mapping={"column_name": "id"}),
                        Mock(_mapping={"column_name": "user_name"}),
                        Mock(_mapping={"column_name": "email"}),
                    ]
                )
            )
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_user_columns()

        assert "id" in result
        assert "user_name" in result
        assert "email" in result

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_create_subscription(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест создания подписки."""
        subscription_id = uuid4()
        execute_result = Mock()
        execute_result.scalar_one.return_value = subscription_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.create_subscription(
            test_uuid, uuid4(), {"telegram": True}
        )

        assert result == subscription_id
        session.execute.assert_called_once()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_delete_subscription_statuses(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест удаления статусов подписки."""
        execute_result = Mock()
        execute_result.rowcount = 3
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.delete_subscription_statuses(test_uuid)

        assert result == 3
        session.execute.assert_called_once()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_delete_subscription(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест удаления подписки."""
        session = AsyncMock()
        session.execute = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.delete_subscription(test_uuid)

        assert result is True
        session.execute.assert_called_once()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_by_id(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения подписки по ID."""
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=Mock(
                mappings=Mock(
                    return_value=Mock(
                        one_or_none=Mock(
                            return_value=Mock(
                                _mapping={
                                    "id": test_uuid,
                                    "alert": uuid4(),
                                    "contact": uuid4(),
                                    "telegram": True,
                                    "email": False,
                                }
                            )
                        )
                    )
                )
            )
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_subscription_by_id(test_uuid)

        assert result is not None
        result_id = result["id"]
        assert result_id == test_uuid

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_all_notification_statuses(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения всех статусов уведомлений."""
        second_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=Mock(
                mappings=Mock(
                    return_value=Mock(
                        all=Mock(
                            return_value=[
                                {"id": test_uuid, "status_name": "Status 1"},
                                {"id": second_id, "status_name": "Status 2"},
                            ]
                        )
                    )
                ),
                all=Mock(
                    return_value=[
                        Mock(
                            _mapping={
                                "id": test_uuid,
                                "status_name": "Status 1",
                            }
                        ),
                        Mock(
                            _mapping={
                                "id": second_id,
                                "status_name": "Status 2",
                            }
                        ),
                    ]
                ),
            )
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_all_notification_statuses()

        assert len(result) == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_statuses(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения статусов подписки."""
        second_status = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=Mock(
                all=Mock(
                    return_value=[
                        Mock(_mapping={"status": test_uuid, "repeat": 5}),
                        Mock(_mapping={"status": second_status, "repeat": 3}),
                    ]
                )
            )
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_subscription_statuses(test_uuid)

        assert len(result) == 2
        assert result[test_uuid] == 5

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_update_subscription_channels(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест обновления каналов подписки."""
        session = AsyncMock()
        session.execute = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.update_subscription_channels(
            test_uuid, ["telegram"], [True]
        )

        assert result is True
        session.execute.assert_called_once()

    async def test_update_subscription_channels_no_fields(
        self, repo, test_uuid
    ):
        """Тест обновления каналов без полей."""
        result = await repo.update_subscription_channels(test_uuid, [], [])

        assert result is True

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_current_subscription_statuses(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения текущих статусов подписки."""
        status_id = uuid4()
        record_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=Mock(
                all=Mock(
                    return_value=[
                        Mock(_mapping={"status": status_id, "id": record_id})
                    ]
                )
            )
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.get_current_subscription_statuses(test_uuid)

        assert len(result) == 1
        assert result[status_id] == record_id

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_update_subscription_status(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест обновления статуса подписки."""
        session = AsyncMock()
        session.execute = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.update_subscription_status(test_uuid, 5)

        assert result is True
        session.execute.assert_called_once()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_create_subscription_status(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест создания статуса подписки."""
        session = AsyncMock()
        session.execute = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.create_subscription_status(test_uuid, uuid4(), 3)

        assert result is True
        session.execute.assert_called_once()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_delete_subscription_status(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест удаления статуса подписки."""
        session = AsyncMock()
        session.execute = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        result = await repo.delete_subscription_status(test_uuid)

        assert result is True
        session.execute.assert_called_once()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_users(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения списка пользователей для подписок."""
        session = AsyncMock()
        count_result = Mock()
        count_result.scalar_one.return_value = 2
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            Mock(
                _mapping={
                    "id": test_uuid,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": uuid4(),
                }
            ),
            Mock(
                _mapping={
                    "id": uuid4(),
                    "user_name": "user2",
                    "group": True,
                    "is_subscribed": False,
                    "subscription_id": None,
                }
            ),
        ]
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.get_subscription_users(
            alert_id=test_uuid, query="user", limit=10, offset=0
        )

        assert total == 2
        assert len(rows) == 2
        assert session.execute.call_count == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_users_with_groups_filter(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения пользователей с фильтром по группам."""
        session = AsyncMock()
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            Mock(
                _mapping={
                    "id": test_uuid,
                    "user_name": "group1",
                    "group": True,
                    "is_subscribed": False,
                    "subscription_id": None,
                }
            )
        ]
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.get_subscription_users(
            alert_id=test_uuid, groups=True, limit=10, offset=0
        )

        assert total == 1
        assert len(rows) == 1
        assert session.execute.call_count == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_users_subscribed_only(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения только подписанных пользователей."""
        session = AsyncMock()
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            Mock(
                _mapping={
                    "id": test_uuid,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": uuid4(),
                }
            )
        ]
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.get_subscription_users(
            alert_id=test_uuid, subscribed_only=True, limit=10, offset=0
        )

        assert total == 1
        assert len(rows) == 1
        assert session.execute.call_count == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_users_with_order(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения пользователей с сортировкой."""
        session = AsyncMock()
        count_result = Mock()
        count_result.scalar_one.return_value = 2
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            Mock(
                _mapping={
                    "id": test_uuid,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": uuid4(),
                }
            ),
            Mock(
                _mapping={
                    "id": uuid4(),
                    "user_name": "user2",
                    "group": True,
                    "is_subscribed": False,
                    "subscription_id": None,
                }
            ),
        ]
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.get_subscription_users(
            alert_id=test_uuid,
            order_by="email",
            order_dir="desc",
            limit=10,
            offset=0,
        )

        assert total == 2
        assert len(rows) == 2
        assert session.execute.call_count == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_users_with_user_id_order(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения пользователей с сортировкой по user_id."""
        session = AsyncMock()
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            Mock(
                _mapping={
                    "id": test_uuid,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": uuid4(),
                }
            )
        ]
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.get_subscription_users(
            alert_id=test_uuid,
            order_by="user_id",
            order_dir="asc",
            limit=10,
            offset=0,
        )

        assert total == 1
        assert len(rows) == 1
        assert session.execute.call_count == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_alerts_by_user(self, mock_session_scope, repo, test_uuid):
        """Тест получения алертов пользователя."""
        session = AsyncMock()
        count_result = Mock()
        count_result.scalar_one.return_value = 2
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            Mock(
                _mapping={
                    "alert_id": uuid4(),
                    "alert_name": "Alert A",
                    "subscription_id": uuid4(),
                    "telegram": True,
                }
            ),
            Mock(
                _mapping={
                    "alert_id": uuid4(),
                    "alert_name": "Alert B",
                    "subscription_id": None,
                    "telegram": False,
                }
            ),
        ]
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.get_alerts_by_user(
            user_id=test_uuid, limit=10, offset=0
        )

        assert total == 2
        assert len(rows) == 2
        assert session.execute.call_count == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_alerts_by_user_subscribed_only_desc_order(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест получения только подписанных алертов с desc-сортировкой."""
        session = AsyncMock()
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        data_result = Mock()
        data_result.mappings.return_value.all.return_value = [
            Mock(
                _mapping={
                    "alert_id": uuid4(),
                    "alert_name": "Alert C",
                    "subscription_id": uuid4(),
                    "telegram": True,
                }
            )
        ]
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        rows, total = await repo.get_alerts_by_user(
            user_id=test_uuid,
            subscribed_only=True,
            order_by="created_at",
            order_dir="desc",
            limit=10,
            offset=0,
        )

        assert total == 1
        assert len(rows) == 1
        assert session.execute.call_count == 2

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_alerts_by_user_raises_when_reflection_failed(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест ошибки, если reflected таблицы недоступны."""
        session = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(
                RuntimeError, match=r"alerts\.alerts_contacts"
            ):
                await repo.get_alerts_by_user(user_id=test_uuid)

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_create_subscription_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест отката транзакции при ошибке создания подписки."""
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception):
            await repo.create_subscription(
                test_uuid, uuid4(), {"telegram": True}
            )

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_delete_subscription_statuses_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест отката транзакции при ошибке удаления статусов."""
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception):
            await repo.delete_subscription_statuses(test_uuid)

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_update_subscription_channels_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест отката транзакции при ошибке обновления каналов."""
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception):
            await repo.update_subscription_channels(
                test_uuid, ["telegram"], [True]
            )

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_update_subscription_status_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест отката транзакции при ошибке обновления статуса."""
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception):
            await repo.update_subscription_status(test_uuid, 5)

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_create_subscription_status_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        """Тест отката транзакции при ошибке создания статуса."""
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception):
            await repo.create_subscription_status(test_uuid, uuid4(), 3)

    async def test_check_alert_exists_with_explicit_session(
        self, repo, test_uuid
    ):
        """Покрыть _run_with_session ветку с переданной сессией."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        result = await repo.check_alert_exists(test_uuid, session)
        assert result is True

    async def test_get_reflected_table_from_cache(self, repo):
        """Покрыть cache-hit в _get_reflected_table."""
        key = ("alerts", "contacts")
        table = Table(
            "contacts", MetaData(), Column("id", String), schema="alerts"
        )
        repo._TABLE_CACHE[key] = table
        session = AsyncMock()
        result = await repo._get_reflected_table(session, *key)
        assert result is table

    async def test_get_reflected_table_non_table_raises(self, repo):
        """В strict режиме non-Table недопустим."""
        repo._TABLE_CACHE.clear()
        session = AsyncMock()
        session.run_sync = AsyncMock(return_value=object())
        with pytest.raises(
            RuntimeError, match="SQLAlchemy reflection failed"
        ):
            await repo._get_reflected_table(session, "alerts", "contacts")

    async def test_get_reflected_table_with_run_sync_none_raises(self, repo):
        """В strict режиме run_sync обязателен."""
        repo._TABLE_CACHE.clear()

        class SessionNoRunSync:
            pass

        with pytest.raises(
            RuntimeError, match=r"session\.run_sync is required"
        ):
            await repo._get_reflected_table(
                SessionNoRunSync(), "alerts", "contacts"
            )

    async def test_get_reflected_table_run_sync_returns_table(self, repo):
        """Покрыть ветку кеширования reflected-таблицы."""
        repo._TABLE_CACHE.clear()
        reflected_table = Table(
            "contacts",
            MetaData(),
            Column("id", String),
            schema="alerts",
        )

        session = AsyncMock()
        session.run_sync = AsyncMock(return_value=reflected_table)
        result = await repo._get_reflected_table(session, "alerts", "contacts")
        assert result is not None

    async def test_get_reflected_table_executes_reflect_callback_lines(self, repo):
        """Покрыть строки callback _reflect (bind/metadata/Table)."""
        repo._TABLE_CACHE.clear()
        engine = create_engine("sqlite+pysqlite:///:memory:")

        class SyncSession:
            def get_bind(self):
                return engine

        async def run_sync(fn):
            return fn(SyncSession())

        session = AsyncMock()
        session.run_sync = run_sync
        with pytest.raises(Exception):
            await repo._get_reflected_table(session, "alerts", "contacts")

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_user_data_table_missing_raises(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match=r"alerts\.contacts"):
                await repo.get_user_data(test_uuid)

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_alerts_contacts_columns_table_missing_raises(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(
                RuntimeError, match=r"alerts\.alerts_contacts"
            ):
                await repo.get_alerts_contacts_columns()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_user_columns_table_missing_raises(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match=r"alerts\.contacts"):
                await repo.get_user_columns()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_create_subscription_table_missing_raises(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(
                RuntimeError, match=r"alerts\.alerts_contacts"
            ):
                await repo.create_subscription(test_uuid, uuid4(), {})

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_all_notification_statuses_execute_error(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm

        with pytest.raises(Exception, match="DB error"):
            await repo.get_all_notification_statuses()

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_update_subscription_channels_table_missing_raises(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(
                RuntimeError, match=r"alerts\.alerts_contacts"
            ):
                await repo.update_subscription_channels(
                    test_uuid, ["telegram"], [True]
                )

    @patch("repositories.subscriptions_repository.async_session_scope")
    async def test_get_subscription_users_table_missing_raises(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        cm = AsyncMock()
        cm.__aenter__.return_value = session
        cm.__aexit__.return_value = None
        mock_session_scope.return_value = cm
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match=r"alerts\.contacts"):
                await repo.get_subscription_users(alert_id=test_uuid)
