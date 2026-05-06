"""
Модульные тесты для UsersService.
"""

from collections.abc import Mapping
from typing import ClassVar
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.users_repository import UsersRepository
from schemas.users import UserCreate, UserListResponse, UserUpdate
from services.users_service import UsersService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestUsersService:
    """Тесты для UsersService."""

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=UsersRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр UsersService с моком репозитория."""
        return UsersService(repository=mock_repo)

    async def test_get_telegram_by_login_success(self, service, mock_repo):
        """Тест успешного получения Telegram ID."""
        mock_repo.get_telegram_by_login.return_value = {
            "telegram_user_id": "123456789"
        }

        result = await service.get_telegram_by_login("test_user")

        assert result.telegram_id == "123456789"
        mock_repo.get_telegram_by_login.assert_called_once_with("test_user")

    async def test_get_telegram_by_login_with_mapping_row(
        self, service, mock_repo
    ):
        """Позитивный ORM-style кейс: telegram строка приходит через _mapping."""

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "telegram_user_id": "987654321"
            }

        mock_repo.get_telegram_by_login.return_value = RowObj()

        result = await service.get_telegram_by_login("test_user")

        assert result.telegram_id == "987654321"
        mock_repo.get_telegram_by_login.assert_called_once_with("test_user")

    async def test_get_telegram_by_login_with_mapping_protocol_row(
        self, service, mock_repo
    ):
        """Регрессия: row может быть Mapping (как SQLAlchemy RowMapping)."""

        class RowMappingLike(Mapping):
            def __init__(self):
                self._data = {"telegram_user_id": "555777"}

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

            def __len__(self):
                return len(self._data)

        mock_repo.get_telegram_by_login.return_value = RowMappingLike()

        result = await service.get_telegram_by_login("test_user")

        assert result.telegram_id == "555777"
        mock_repo.get_telegram_by_login.assert_called_once_with("test_user")

    async def test_get_telegram_by_login_not_found(self, service, mock_repo):
        """Тест получения Telegram ID для несуществующего пользователя."""
        mock_repo.get_telegram_by_login.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_telegram_by_login("nonexistent")

        assert exc_info.value.status_code == 404

    async def test_create_user_success(self, service, mock_repo):
        """Тест успешного создания пользователя."""
        mock_repo.get_available_columns.return_value = [
            "user_name",
            "group",
            "telegram",
        ]

        data = UserCreate(
            samAccountName="test_user",
            group=False,
            contacts={"telegram": "123456789"},
        )

        result = await service.create_user(data)

        assert result is True
        mock_repo.create_user.assert_called_once()

    async def test_create_user_no_contacts(self, service, mock_repo):
        """Тест создания пользователя без контактов."""
        mock_repo.get_available_columns.return_value = ["user_name", "group"]

        data = UserCreate(samAccountName="test_user", group=False)

        result = await service.create_user(data)

        assert result is True

    async def test_update_user_success(self, service, mock_repo):
        """Тест успешного обновления пользователя."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_available_columns.return_value = [
            "user_name",
            "group",
            "telegram",
        ]

        data = UserUpdate(
            samAccountName="updated_user", contacts={"telegram": "987654321"}
        )

        result = await service.update_user(user_id, data)

        assert result is True
        mock_repo.check_user_exists.assert_called_once_with(user_id)
        mock_repo.update_user.assert_called_once()

    async def test_update_user_not_found(self, service, mock_repo):
        """Тест обновления несуществующего пользователя."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = False

        data = UserUpdate(samAccountName="updated_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_user(user_id, data)

        assert exc_info.value.status_code == 404

    async def test_delete_user_success(self, service, mock_repo):
        """Тест успешного удаления пользователя."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True

        result = await service.delete_user(user_id)

        assert result is True
        mock_repo.check_user_exists.assert_called_once_with(user_id)
        mock_repo.delete_user.assert_called_once_with(user_id)

    async def test_delete_user_not_found(self, service, mock_repo):
        """Тест удаления несуществующего пользователя."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_user(user_id)

        assert exc_info.value.status_code == 404

    async def test_get_telegram_by_login_error_handling(
        self, service, mock_repo
    ):
        """Тест обработки ошибки при получении Telegram ID."""
        mock_repo.get_telegram_by_login.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_telegram_by_login("test_user")

        assert exc_info.value.status_code == 500
        assert (
            "Ошибка при получении Telegram пользователя"
            in exc_info.value.detail
        )

    async def test_create_user_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при создании пользователя."""
        mock_repo.get_available_columns.return_value = ["user_name", "group"]
        mock_repo.create_user.side_effect = Exception("Ошибка БД")

        data = UserCreate(samAccountName="test_user", group=False)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_user(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при создании пользователя" in exc_info.value.detail

    async def test_update_user_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при обновлении пользователя."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_available_columns.return_value = ["user_name", "group"]
        mock_repo.update_user.side_effect = Exception("Ошибка БД")

        data = UserUpdate(samAccountName="updated_user")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_user(user_id, data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при обновлении пользователя" in exc_info.value.detail

    async def test_delete_user_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при удалении пользователя."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.delete_user.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_user(user_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при удалении пользователя" in exc_info.value.detail

    async def test_update_user_with_group(self, service, mock_repo):
        """Тест обновления пользователя с полем group."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_available_columns.return_value = ["user_name", "group"]
        mock_repo.update_user.return_value = True

        data = UserUpdate(group=True)

        result = await service.update_user(user_id, data)

        assert result is True
        # Проверяем, что group включен в обновление
        call_args = mock_repo.update_user.call_args
        assert '"group"' in str(call_args) or "group" in str(call_args)

    async def test_search_users_success(self, service, mock_repo):
        """Тест успешного поиска пользователей."""
        mock_repo.search_users.return_value = (
            [
                {
                    "id": uuid4(),
                    "user_name": "user1",
                    "group": False,
                    "email": "user1@test.com",
                }
            ],
            1,
        )

        result = await service.search_users(query="user1", limit=10, offset=0)

        assert isinstance(result, UserListResponse)
        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].samAccountName == "user1"

    async def test_search_users_with_mapping_row(self, service, mock_repo):
        """Позитивный ORM-style кейс: строка результата через _mapping."""

        user_id = uuid4()

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": user_id,
                "user_name": "mapped_user",
                "group": False,
                "email": "mapped@example.com",
            }

        mock_repo.search_users.return_value = ([RowObj()], 1)

        result = await service.search_users()

        assert isinstance(result, UserListResponse)
        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].user_id == user_id
        assert result.users[0].samAccountName == "mapped_user"

    async def test_search_users_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при поиске пользователей."""
        mock_repo.search_users.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.search_users(query="user1")

        assert exc_info.value.status_code == 500
        assert "Ошибка при поиске пользователей" in exc_info.value.detail

    async def test_search_users_skips_bad_non_dict_row(self, service, mock_repo):
        """Покрыть ветку continue при ошибке keys()."""

        class BadRow:
            def keys(self):
                raise RuntimeError("bad")

        mock_repo.search_users.return_value = ([BadRow()], 1)
        result = await service.search_users()
        assert result.total == 1
        assert result.users == []

    async def test_search_users_with_non_dict_row_keys(self, service, mock_repo):
        """Покрыть ветку keys()/index для не-dict строки."""

        class RowObj:
            def keys(self):
                return ["id", "user_name", "group", "email"]

            def __getitem__(self, idx):
                return [uuid4(), "u2", False, "u2@example.com"][idx]

        mock_repo.search_users.return_value = ([RowObj()], 1)
        result = await service.search_users()
        assert result.total == 1
        assert result.users[0].samAccountName == "u2"
