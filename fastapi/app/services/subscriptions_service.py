"""
Сервис для работы с подписками пользователей на алерты.
Содержит асинхронную бизнес-логику для работы с подписками.
"""

from typing import Any
from uuid import UUID

from contracts.repository_protocols import SubscriptionsRepositoryProtocol
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_db import async_session_scope

from repositories.subscriptions_repository import SubscriptionsRepository
from schemas.subscriptions import (
    AlertByUserItem,
    AlertByUserListResponse,
    SubscribeRequest,
    SubscriptionByUserResponse,
    SubscriptionByUserUpdate,
    SubscriptionContacts,
    SubscriptionStatusItem,
    SubscriptionStatusUpdateItem,
    SubscriptionUserItem,
    SubscriptionUserListResponse,
    UnsubscribeRequest,
)
from schemas.users import UserContacts
from utils import log


class SubscriptionsService:
    """Сервис для работы с подписками."""

    def __init__(
        self, repository: SubscriptionsRepositoryProtocol | None = None
    ):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с подписками
        """
        self.repository = repository or SubscriptionsRepository()

    @staticmethod
    def _as_dict(row: Any) -> dict[str, Any]:
        if isinstance(row, dict):
            return row
        mapping = getattr(row, "_mapping", None)
        if mapping is not None:
            return dict(mapping)
        keys_method = getattr(row, "keys", None)
        if callable(keys_method):
            try:
                keys = list(keys_method())
                result: dict[str, Any] = {}
                for idx, key in enumerate(keys):
                    try:
                        result[key] = row[key]
                    except Exception:
                        result[key] = row[idx]
                return result
            except Exception:
                return {}
        return {}

    @staticmethod
    def _build_contacts_dict_for_subscribe(
        alerts_contacts_columns: list[str],
        user_column_names: list[str],
        user_row: Any,
    ) -> dict[str, bool]:
        """Собрать словарь каналов alerts_contacts для новой подписки из строки contacts."""
        user_data_dict = SubscriptionsService._as_dict(user_row)
        if not user_data_dict and not isinstance(user_row, dict):
            try:
                row_values = list(user_row)
                for idx, col_name in enumerate(user_column_names):
                    if idx < len(row_values):
                        user_data_dict[col_name] = row_values[idx]
            except Exception:
                user_data_dict = {}

        contacts_dict: dict[str, bool] = {}
        for ac_field_name in alerts_contacts_columns:
            same_name_value = user_data_dict.get(ac_field_name)
            id_field_name = f"{ac_field_name}_id"
            id_field_value = user_data_dict.get(id_field_name)
            if same_name_value is not None or id_field_value is not None:
                contacts_dict[ac_field_name] = True
        return contacts_dict

    @staticmethod
    def _subscription_channel_field_pairs_for_update(
        notification_channels: SubscriptionContacts,
        available_columns: list[str],
    ) -> tuple[list[str], list[Any]]:
        """Поля и значения для `update_subscription_channels` с учётом разрешённых колонок."""
        contacts_dict = notification_channels.model_dump(exclude_none=True)
        update_fields: list[str] = []
        update_values: list[Any] = []
        for field_name, field_value in contacts_dict.items():
            if field_name in available_columns:
                update_fields.append(field_name)
                update_values.append(field_value)
        return update_fields, update_values

    async def _apply_subscription_contact_columns(
        self,
        session: AsyncSession,
        subscription_id: UUID,
        notification_channels: SubscriptionContacts,
    ) -> None:
        """Обновить динамические каналы `alerts_contacts` в рамках переданной сессии."""
        available_columns = await self.repository.get_alerts_contacts_columns(
            session
        )
        update_fields, update_values = (
            self._subscription_channel_field_pairs_for_update(
                notification_channels, available_columns
            )
        )
        if not update_fields:
            return
        await self.repository.update_subscription_channels(
            subscription_id,
            update_fields,
            update_values,
            session,
        )
        log.info(
            f"Updated notification_channels for subscription {subscription_id}"
        )

    async def _resolve_notification_status_id(
        self,
        session: AsyncSession,
        status_id_str: str,
    ) -> Any:
        """Разрешить `status_id` из UUID-строки или по имени/строковому id из справочника статусов."""
        try:
            return UUID(status_id_str)
        except (ValueError, TypeError):
            pass
        all_statuses = await self.repository.get_all_notification_statuses(
            session
        )
        for status_row in all_statuses:
            status_dict = self._as_dict(status_row)
            row_id = status_dict.get("id")
            row_name = status_dict.get("status_name")
            if str(row_id) == status_id_str or row_name == status_id_str:
                if row_id is None:
                    continue
                return row_id
        raise HTTPException(
            status_code=400,
            detail=f"Статус с идентификатором '{status_id_str}' не найден.",
        )

    async def _apply_one_subscription_status_item(
        self,
        session: AsyncSession,
        subscription_id: UUID,
        status_item: SubscriptionStatusUpdateItem,
        current_statuses: dict[Any, Any],
    ) -> None:
        """Один элемент из `statuses`: создать/обновить/удалить запись `alerts_contacts_status`."""
        status_dict = status_item.model_dump(exclude_unset=True)
        status_id_str = status_dict["status_id"]
        status_id = await self._resolve_notification_status_id(
            session, status_id_str
        )

        if "repeat" in status_dict:
            repeat_value = status_dict["repeat"]
            if status_id in current_statuses:
                await self.repository.update_subscription_status(
                    current_statuses[status_id],
                    repeat_value,
                    session,
                )
                log.info(
                    f"Updated status {status_id} with repeat={repeat_value} for subscription {subscription_id}"
                )
            else:
                await self.repository.create_subscription_status(
                    subscription_id,
                    status_id,
                    repeat_value,
                    session,
                )
                log.info(
                    f"Created status {status_id} with repeat={repeat_value} for subscription {subscription_id}"
                )
        elif status_id in current_statuses:
            await self.repository.delete_subscription_status(
                current_statuses[status_id], session
            )
            log.info(
                f"Deleted status {status_id} for subscription {subscription_id}"
            )

    async def _apply_subscription_status_items(
        self,
        session: AsyncSession,
        subscription_id: UUID,
        statuses: list[SubscriptionStatusUpdateItem],
    ) -> None:
        """Применить список правок статусов подписки в одной сессии."""
        current_statuses = (
            await self.repository.get_current_subscription_statuses(
                subscription_id, session
            )
        )
        for status_item in statuses:
            await self._apply_one_subscription_status_item(
                session, subscription_id, status_item, current_statuses
            )

    async def subscribe(self, data: SubscribeRequest) -> bool:
        """
        Подписка пользователя на алерт.

        Args:
            data: Данные для подписки (alert_id, user_id)

        Returns:
            bool: True при успешной подписке

        Raises:
            HTTPException: При ошибке валидации, отсутствии алерта/пользователя, или если подписка уже существует
        """
        try:
            async with async_session_scope() as session:
                if not await self.repository.check_alert_exists(
                    data.alert_id, session
                ):
                    raise HTTPException(
                        status_code=404, detail="Алерт не найден"
                    )

                existing_subscription = (
                    await self.repository.check_subscription_exists(
                        data.alert_id, data.user_id, session
                    )
                )
                if existing_subscription:
                    raise HTTPException(
                        status_code=409,
                        detail="Пользователь уже подписан на этот алерт",
                    )

                user_row = await self.repository.get_user_data(
                    data.user_id, session
                )
                if not user_row:
                    raise HTTPException(
                        status_code=404, detail="Пользователь не найден"
                    )

                alerts_contacts_columns = (
                    await self.repository.get_alerts_contacts_columns(session)
                )
                user_column_names = await self.repository.get_user_columns(
                    session
                )
                contacts_dict = self._build_contacts_dict_for_subscribe(
                    alerts_contacts_columns, user_column_names, user_row
                )

                subscription_id = await self.repository.create_subscription(
                    data.alert_id,
                    data.user_id,
                    contacts_dict,
                    session,
                )

            log.info(
                f"Created subscription {subscription_id} for alert {data.alert_id} and user {data.user_id}"
            )
            return True

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[SubscriptionsService.subscribe] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при подписке: {e}"
            )

    async def unsubscribe(self, data: UnsubscribeRequest) -> bool:
        """
        Отписка пользователя от алерта.

        Args:
            data: Данные для отписки (alert_id, user_id)

        Returns:
            bool: True при успешной отписке

        Raises:
            HTTPException: При отсутствии подписки или ошибке БД
        """
        try:
            async with async_session_scope() as session:
                subscription_id = (
                    await self.repository.check_subscription_exists(
                        data.alert_id, data.user_id, session
                    )
                )
                if not subscription_id:
                    raise HTTPException(
                        status_code=404, detail="Подписка не найдена"
                    )

                deleted_statuses = (
                    await self.repository.delete_subscription_statuses(
                        subscription_id, session
                    )
                )
                log.info(
                    f"Deleted {deleted_statuses} status records for subscription {subscription_id}"
                )

                await self.repository.delete_subscription(
                    subscription_id, session
                )
                log.info(
                    f"Deleted subscription {subscription_id} for alert {data.alert_id} and user {data.user_id}"
                )

            return True

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[SubscriptionsService.unsubscribe] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при отписке: {e}"
            )

    async def get_subscription_by_alert_and_user(
        self, alert_id: UUID, user_id: UUID
    ) -> SubscriptionByUserResponse:
        """
        Получение детальной информации о подписке пользователя на алерт.

        Args:
            alert_id: ID алерта
            user_id: ID пользователя

        Returns:
            SubscriptionByUserResponse: Детальная информация о подписке

        Raises:
            HTTPException: При отсутствии подписки или ошибке БД
        """
        try:
            # Находим подписку
            subscription_id = await self.repository.check_subscription_exists(
                alert_id, user_id
            )
            if not subscription_id:
                raise HTTPException(
                    status_code=404, detail="Подписка не найдена"
                )

            # Получаем все данные подписки из alerts.alerts_contacts
            subscription_row = await self.repository.get_subscription_by_id(
                subscription_id
            )
            if not subscription_row:
                raise HTTPException(
                    status_code=404, detail="Подписка не найдена"
                )

            # Получаем колонки подписки
            ac_columns = await self.repository.get_alerts_contacts_columns()
            ac_column_names = ["id", "alert", "contact", *ac_columns]

            # Формируем словарь contacts (все поля кроме id, alert, contact)
            contacts_dict = {}
            subscription_row_dict = self._as_dict(subscription_row)
            if subscription_row_dict:
                for col_name in ac_column_names:
                    if col_name in ("id", "alert", "contact"):
                        continue
                    value = subscription_row_dict.get(col_name)
                    if value is not None:
                        contacts_dict[col_name] = value
            else:
                try:
                    subscription_row_values = list(subscription_row)
                    for idx, col_name in enumerate(ac_column_names):
                        if col_name in ("id", "alert", "contact"):
                            continue
                        if idx < len(subscription_row_values):
                            value = subscription_row_values[idx]
                            if value is not None:
                                contacts_dict[col_name] = value
                except Exception:
                    contacts_dict = {}

            # Создаем объект notification_channels, если есть хотя бы одно поле
            notification_channels = (
                SubscriptionContacts(**contacts_dict)
                if contacts_dict
                else None
            )

            # Получаем все статусы с send_notification=true
            all_statuses = (
                await self.repository.get_all_notification_statuses()
            )

            # Получаем статусы для этой подписки из alerts.alerts_contacts_status
            subscription_statuses = (
                await self.repository.get_subscription_statuses(
                    subscription_id
                )
            )

            # Формируем список статусов
            statuses = []
            for status_row in all_statuses:
                status_dict = self._as_dict(status_row)
                status_id = status_dict.get("id")
                status_name = status_dict.get("status_name")
                repeat = subscription_statuses.get(status_id)
                statuses.append(
                    SubscriptionStatusItem(
                        status_id=str(status_id),
                        status_name=status_name,
                        repeat=repeat,
                    )
                )

            return SubscriptionByUserResponse(
                subscription_id=subscription_id,
                notification_channels=notification_channels,
                statuses=statuses,
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(
                f"[SubscriptionsService.get_subscription_by_alert_and_user] Error: {e}"
            )
            raise HTTPException(
                status_code=500, detail=f"Ошибка при получении подписки: {e}"
            )

    async def update_subscription_by_alert_and_user(
        self, data: SubscriptionByUserUpdate
    ) -> bool:
        """
        Обновление подписки пользователя на алерт.

        Args:
            data: Данные для обновления (alert_id, user_id, notification_channels, statuses)

        Returns:
            bool: True при успешном обновлении

        Raises:
            HTTPException: При отсутствии подписки или ошибке БД
        """
        try:
            async with async_session_scope() as session:
                subscription_id = (
                    await self.repository.check_subscription_exists(
                        data.alert_id, data.user_id, session
                    )
                )
                if not subscription_id:
                    raise HTTPException(
                        status_code=404, detail="Подписка не найдена"
                    )

                if data.notification_channels:
                    await self._apply_subscription_contact_columns(
                        session, subscription_id, data.notification_channels
                    )

                if data.statuses:
                    await self._apply_subscription_status_items(
                        session, subscription_id, data.statuses
                    )

            return True

        except HTTPException:
            raise
        except Exception as e:
            log.error(
                f"[SubscriptionsService.update_subscription_by_alert_and_user] Error: {e}"
            )
            raise HTTPException(
                status_code=500, detail=f"Ошибка при обновлении подписки: {e}"
            )

    async def get_subscription_users(
        self,
        alert_id: UUID,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "samAccountName",
        order_dir: str = "asc",
        subscribed_only: bool = False,
        groups: bool | None = None,
    ) -> SubscriptionUserListResponse:
        """
        Получение списка всех пользователей для страницы подписок алерта.

        Args:
            alert_id: ID алерта
            query: Поисковый запрос по samAccountName или email (опционально)
            limit: Количество записей на странице
            offset: Смещение для пагинации
            order_by: Поле для сортировки (user_id, samAccountName, email)
            order_dir: Направление сортировки (asc/desc)
            subscribed_only: Показывать только пользователей с подпиской
            groups: Фильтр по полю group (True - группы, False - обычные пользователи)

        Returns:
            SubscriptionUserListResponse: Список пользователей с информацией о подписке
        """
        try:
            # Проверяем существование алерта
            if not await self.repository.check_alert_exists(alert_id):
                raise HTTPException(status_code=404, detail="Алерт не найден")

            # Получаем список пользователей
            rows, total = await self.repository.get_subscription_users(
                alert_id=alert_id,
                query=query,
                groups=groups,
                subscribed_only=subscribed_only,
                order_by=order_by,
                order_dir=order_dir,
                limit=limit,
                offset=offset,
            )

            # Получаем колонки для парсинга
            user_column_names = await self.repository.get_user_columns()
            column_names = [
                *user_column_names,
                "is_subscribed",
                "subscription_id",
            ]

            # Определяем индексы основных полей
            id_idx = column_names.index("id") if "id" in column_names else 0
            user_name_idx = (
                column_names.index("user_name")
                if "user_name" in column_names
                else 1
            )
            group_idx = (
                column_names.index("group") if "group" in column_names else 2
            )
            is_subscribed_idx = (
                column_names.index("is_subscribed")
                if "is_subscribed" in column_names
                else len(column_names) - 2
            )
            subscription_id_idx = (
                column_names.index("subscription_id")
                if "subscription_id" in column_names
                else len(column_names) - 1
            )

            users = []
            for row in rows:
                row_dict = self._as_dict(row)
                row_list = list(row_dict.values()) if row_dict else row

                # Создаем словарь с данными пользователя
                user_data = {
                    "user_id": row_dict.get("id")
                    if row_dict
                    else row_list[id_idx]
                    if id_idx < len(row_list)
                    else None,
                    "samAccountName": row_dict.get("user_name")
                    if row_dict
                    else row_list[user_name_idx]
                    if user_name_idx < len(row_list)
                    else None,
                    "group": row_dict.get("group")
                    if row_dict
                    else row_list[group_idx]
                    if group_idx < len(row_list)
                    else None,
                }

                # Формируем объект contacts с динамическими полями
                contacts_data = {}
                for col_name in column_names:
                    if col_name not in (
                        "id",
                        "user_name",
                        "group",
                        "is_subscribed",
                        "subscription_id",
                    ):
                        value = (
                            row_dict.get(col_name) if row_dict else None
                        )
                        if value is None and not row_dict:
                            try:
                                idx = column_names.index(col_name)
                                if idx < len(row_list):
                                    value = row_list[idx]
                            except (ValueError, IndexError):
                                pass
                        if value is not None:
                            contacts_data[col_name] = value

                if contacts_data:
                    user_data["contacts"] = UserContacts(**contacts_data)

                # Если пользователь подписан, добавляем notification_channels и statuses
                is_subscribed = (
                    row_dict.get("is_subscribed")
                    if row_dict
                    else (
                        row_list[is_subscribed_idx]
                        if is_subscribed_idx < len(row_list)
                        else False
                    )
                )
                subscription_id = (
                    row_dict.get("subscription_id")
                    if row_dict
                    else (
                        row_list[subscription_id_idx]
                        if subscription_id_idx < len(row_list)
                        else None
                    )
                )

                if is_subscribed and subscription_id:
                    # Получаем все поля из alerts.alerts_contacts динамически
                    ac_row = await self.repository.get_subscription_by_id(
                        subscription_id
                    )
                    if ac_row:
                        ac_columns = (
                            await self.repository.get_alerts_contacts_columns()
                        )
                        ac_column_names = [
                            "id",
                            "alert",
                            "contact",
                            *ac_columns,
                        ]
                        notification_channels_data = {}
                        ac_row_dict = self._as_dict(ac_row)
                        if ac_row_dict:
                            for col_name in ac_column_names:
                                if col_name in ("id", "alert", "contact"):
                                    continue
                                value = ac_row_dict.get(col_name)
                                if value is not None:
                                    notification_channels_data[col_name] = (
                                        value
                                    )
                        else:
                            try:
                                ac_row_values = list(ac_row)
                                for idx, col_name in enumerate(
                                    ac_column_names
                                ):
                                    if col_name in ("id", "alert", "contact"):
                                        continue
                                    if idx < len(ac_row_values):
                                        value = ac_row_values[idx]
                                        if value is not None:
                                            notification_channels_data[
                                                col_name
                                            ] = value
                            except Exception:
                                notification_channels_data = {}

                        if notification_channels_data:
                            user_data["notification_channels"] = (
                                SubscriptionContacts(
                                    **notification_channels_data
                                )
                            )

                    # Получаем все статусы с send_notification=true
                    all_statuses = (
                        await self.repository.get_all_notification_statuses()
                    )

                    # Получаем статусы для этой подписки
                    subscription_statuses = (
                        await self.repository.get_subscription_statuses(
                            subscription_id
                        )
                    )

                    # Формируем список статусов
                    statuses_list = []
                    for status_row in all_statuses:
                        status_dict = self._as_dict(status_row)
                        status_id = status_dict.get("id")
                        status_name = status_dict.get("status_name")
                        repeat = subscription_statuses.get(status_id)
                        if repeat is not None:
                            statuses_list.append(
                                SubscriptionStatusItem(
                                    status_id=str(status_id),
                                    status_name=status_name,
                                    repeat=repeat,
                                )
                            )
                        else:
                            statuses_list.append(
                                SubscriptionStatusItem(
                                    status_id=str(status_id),
                                    status_name=status_name,
                                )
                            )

                    if statuses_list:
                        user_data["statuses"] = statuses_list

                users.append(SubscriptionUserItem(**user_data))

            return SubscriptionUserListResponse(users=users, total=total)

        except HTTPException:
            raise
        except Exception as e:
            log.error(
                f"[SubscriptionsService.get_subscription_users] Error: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении списка пользователей для подписок: {e}",
            )

    async def get_alerts_by_user(
        self,
        user_id: UUID,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
        subscribed_only: bool = False,
    ) -> AlertByUserListResponse:
        """
        Получить список алертов для страницы подписок пользователя.

        По умолчанию возвращает все алерты с сортировкой по alert_name.
        Для алертов, на которые пользователь подписан, заполняются notification_channels
        (булевы флаги telegram, email, pachca и др.) и statuses. Для неподписанных
        notification_channels и statuses отсутствуют (null). Если `subscribed_only=True`,
        возвращаются только алерты, на которые пользователь подписан.
        """
        try:
            if not await self.repository.check_user_exists(user_id):
                raise HTTPException(
                    status_code=404, detail="Пользователь не найден"
                )

            channel_columns = (
                await self.repository.get_alerts_contacts_columns()
            )

            rows, total = await self.repository.get_alerts_by_user(
                user_id=user_id,
                order_by=order_by,
                order_dir=order_dir,
                limit=limit,
                offset=offset,
                subscribed_only=subscribed_only,
            )

            alerts: list[AlertByUserItem] = []

            for row in rows:
                if isinstance(row, dict):
                    row_dict = row
                else:
                    try:
                        column_names = list(row.keys())  # noqa: B019
                        row_dict = {
                            name: row[idx]
                            for idx, name in enumerate(column_names)
                        }
                    except Exception:
                        continue

                alert_id = row_dict.get("alert_id") or row_dict.get("alert")
                alert_name = row_dict.get("alert_name")
                subscription_id = row_dict.get("subscription_id")

                # notification_channels и statuses - только при наличии подписки (как у списка пользователей алерта)
                notification_channels = None
                statuses_list: list[SubscriptionStatusItem] | None = None
                if subscription_id is not None:
                    notification_data = {
                        k: row_dict[k]
                        for k in channel_columns
                        if k in row_dict and row_dict[k] is not None
                    }
                    if notification_data:
                        notification_channels = SubscriptionContacts(
                            **notification_data
                        )

                    all_statuses = (
                        await self.repository.get_all_notification_statuses()
                    )
                    subscription_statuses = (
                        await self.repository.get_subscription_statuses(
                            subscription_id
                        )
                    )
                    statuses_list = []
                    for status_row in all_statuses:
                        status_dict = self._as_dict(status_row)
                        status_id = status_dict.get("id")
                        status_name = status_dict.get("status_name")
                        repeat = subscription_statuses.get(status_id)
                        if repeat is not None:
                            statuses_list.append(
                                SubscriptionStatusItem(
                                    status_id=str(status_id),
                                    status_name=status_name,
                                    repeat=repeat,
                                )
                            )
                        else:
                            statuses_list.append(
                                SubscriptionStatusItem(
                                    status_id=str(status_id),
                                    status_name=status_name,
                                )
                            )

                alerts.append(
                    AlertByUserItem(
                        alert_id=alert_id,
                        alert_name=alert_name,
                        notification_channels=notification_channels,
                        statuses=statuses_list,
                    )
                )

            return AlertByUserListResponse(alerts=alerts, total=total)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[SubscriptionsService.get_alerts_by_user] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении списка алертов по пользователю: {e}",
            )
