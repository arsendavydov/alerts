"""
Сервис для работы с пользователями.
Содержит асинхронную бизнес-логику для работы с пользователями.
"""

from collections.abc import Mapping
from uuid import UUID

from contracts.repository_protocols import UsersRepositoryProtocol
from fastapi import HTTPException

from schemas.users import (
    TelegramUserResponse,
    UserCreate,
    UserListItem,
    UserListResponse,
    UserUpdate,
)
from utils import log


class UsersService:
    """Сервис для работы с пользователями."""

    def __init__(self, repository: UsersRepositoryProtocol):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с пользователями
        """
        self.repository = repository

    async def get_telegram_by_login(self, login: str) -> TelegramUserResponse:
        """Получить Telegram ID по логину."""
        try:
            row = await self.repository.get_telegram_by_login(login)
            if not row:
                raise HTTPException(
                    status_code=404, detail="Пользователь не найден"
                )
            mapping = getattr(row, "_mapping", None)
            if mapping is not None:
                row_dict = dict(mapping)
            elif isinstance(row, Mapping):
                row_dict = dict(row)
            elif isinstance(row, dict):
                row_dict = row
            else:
                row_dict = {}
            telegram_id = row_dict.get("telegram_user_id")
            return TelegramUserResponse(telegram_id=telegram_id)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[UsersService.get_telegram_by_login] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении Telegram пользователя: {e}",
            )

    async def create_user(self, data: UserCreate) -> bool:
        """Создать пользователя."""
        try:
            available_columns = await self.repository.get_available_columns()
            data_dict = data.model_dump(exclude_none=True)

            user_name = data_dict.get("samAccountName")
            group = data_dict.get("group", False)

            contacts_data = {}
            if "contacts" in data_dict and data_dict["contacts"] is not None:
                contacts_data = data_dict["contacts"]

            insert_fields = ["user_name", '"group"']
            insert_values = [user_name, group]

            for col_name in available_columns:
                if col_name in ("user_name", "group"):
                    continue
                if col_name in contacts_data:
                    insert_fields.append(col_name)
                    insert_values.append(contacts_data[col_name])

            await self.repository.create_user(insert_fields, insert_values)
            return True
        except Exception as e:
            log.error(f"[UsersService.create_user] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при создании пользователя: {e}",
            )

    async def update_user(self, user_id: UUID, data: UserUpdate) -> bool:
        """Обновить пользователя."""
        try:
            if not await self.repository.check_user_exists(user_id):
                raise HTTPException(
                    status_code=404, detail="Пользователь не найден"
                )

            available_columns = await self.repository.get_available_columns()
            data_dict = data.model_dump(exclude_none=True)

            user_name = data_dict.get("samAccountName")
            group = data_dict.get("group")

            contacts_data = {}
            if "contacts" in data_dict and data_dict["contacts"] is not None:
                contacts_data = data_dict["contacts"]

            update_fields: list[str] = []
            update_values: list[object] = []

            if user_name is not None:
                update_fields.append("user_name")
                update_values.append(user_name)

            if group is not None:
                update_fields.append('"group"')
                update_values.append(group)

            for col_name in available_columns:
                if col_name in ("user_name", "group"):
                    continue
                if col_name in contacts_data:
                    update_fields.append(col_name)
                    update_values.append(contacts_data[col_name])

            await self.repository.update_user(
                user_id, update_fields, update_values
            )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[UsersService.update_user] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обновлении пользователя: {e}",
            )

    async def delete_user(self, user_id: UUID) -> bool:
        """Удалить пользователя."""
        try:
            if not await self.repository.check_user_exists(user_id):
                raise HTTPException(
                    status_code=404, detail="Пользователь не найден"
                )

            await self.repository.delete_user(user_id)
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[UsersService.delete_user] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при удалении пользователя: {e}",
            )

    async def search_users(
        self,
        query: str | None = None,
        groups: bool | None = None,
        order_by: str = "samAccountName",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> UserListResponse:
        """
        Поиск пользователей для страницы 'Пользователи'.

        Возвращает список пользователей с:
        - user_id
        - samAccountName
        - group
        - contacts (все динамические поля из alerts.contacts, кроме id, user_name, group)
        """
        try:
            rows, total = await self.repository.search_users(
                query=query,
                groups=groups,
                order_by=order_by,
                order_dir=order_dir,
                limit=limit,
                offset=offset,
            )

            users: list[UserListItem] = []
            for row in rows:
                mapping = getattr(row, "_mapping", None)
                if mapping is not None:
                    row_dict = dict(mapping)
                elif isinstance(row, dict):
                    row_dict = row
                else:
                    try:
                        # type: ignore[attr-defined]
                        column_names = list(row.keys())  # noqa: B019
                        row_dict = {}
                        for idx, name in enumerate(column_names):
                            try:
                                row_dict[name] = row[name]
                            except Exception:
                                row_dict[name] = row[idx]
                    except Exception:
                        continue

                user_id = row_dict.get("id")
                user_name = row_dict.get("user_name")
                group_value = row_dict.get("group", False)

                contacts_data = {
                    key: value
                    for key, value in row_dict.items()
                    if key not in ("id", "user_name", "group")
                    and value is not None
                }

                user_item = UserListItem(
                    user_id=user_id,
                    samAccountName=user_name,
                    group=group_value,
                    contacts=contacts_data or None,
                )
                users.append(user_item)

            return UserListResponse(users=users, total=total)
        except Exception as e:
            log.error(f"[UsersService.search_users] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при поиске пользователей: {e}",
            )
