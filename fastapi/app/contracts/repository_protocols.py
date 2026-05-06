"""Контракты (Protocol) для repository-слоя alerts."""

from typing import Any, Protocol
from uuid import UUID


class AlertsRepositoryProtocol(Protocol):
    async def search_alerts(
        self,
        query: str | None = None,
        tags: str | None = None,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Any], int]: ...

    async def get_alert_by_id(
        self, alert_id: UUID, session: Any = None
    ) -> Any | None: ...
    async def check_alert_exists_by_name(
        self, alert_name: str, session: Any = None
    ) -> bool: ...
    async def check_alert_exists_by_id(
        self, alert_id: UUID, session: Any = None
    ) -> bool: ...
    async def check_group_rule_exists(
        self, group_rule_id: UUID, session: Any = None
    ) -> bool: ...
    async def create_alert(
        self,
        alert_name: str,
        indicator_id: UUID,
        description: str | None,
        image: str | None,
        tags: list[str] | None,
        group_rule_id: UUID,
        silence_time: str | None,
        session: Any = None,
    ) -> UUID: ...
    async def update_alert(
        self,
        alert_id: UUID,
        alert_name: str | None = None,
        indicator_id: UUID | None = None,
        description: str | None = None,
        image: str | None = None,
        tags: list[str] | None = None,
        group_rule_id: UUID | None = None,
        silence_time: str | None = None,
        session: Any = None,
    ) -> bool: ...
    async def delete_alert_with_cascade(
        self, alert_id: UUID, session: Any = None
    ) -> bool: ...
    async def autocomplete_alerts(
        self, query: str | None, limit: int
    ) -> list[Any]: ...
    async def get_tag_cloud(
        self, alert_name: str | None = None, tags: str | None = None
    ) -> list[str]: ...
    async def duplicate_alert(
        self, alert_id: UUID, session: Any = None
    ) -> UUID: ...


class PausesRepositoryProtocol(Protocol):
    async def check_alert_exists(
        self, alert_id: UUID, session: Any = None
    ) -> bool: ...
    async def get_pauses(
        self,
        alert_id: UUID,
        filter_type: str = "all",
        order_by: str = "start_time",
        order_dir: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Any], int]: ...
    async def create_pause(
        self,
        alert_id: UUID,
        login: str,
        start_time: Any = None,
        end_time: Any = None,
        use_now_for_start: bool = False,
        comment: str | None = None,
    ) -> UUID: ...
    async def stop_all_active_pauses(
        self,
        alert_id: UUID,
        login: str,
        comment: Any = None,
        session: Any = None,
    ) -> int: ...
    async def get_pause_by_id(
        self, pause_id: UUID, alert_id: UUID, session: Any = None
    ) -> Any | None: ...
    async def update_pause(
        self,
        pause_id: UUID,
        alert_id: UUID,
        start_time: Any = None,
        use_now_for_start: bool = False,
        end_time: Any = None,
        end_time_set_to_none: bool = False,
        login: str | None = None,
        comment: Any = None,
    ) -> bool: ...
    async def stop_specific_pause(
        self,
        pause_id: UUID,
        alert_id: UUID,
        login: str,
        comment: Any = None,
    ) -> bool: ...
    async def delete_pause(
        self, pause_id: UUID, alert_id: UUID, session: Any = None
    ) -> bool: ...
    async def toggle_alert_pause(
        self, alert_id: UUID, login: str, comment: str | None = None
    ) -> bool: ...


class SubscriptionsRepositoryProtocol(Protocol):
    async def check_alert_exists(
        self, alert_id: UUID, session: Any = None
    ) -> bool: ...
    async def check_user_exists(
        self, user_id: UUID, session: Any = None
    ) -> bool: ...
    async def check_subscription_exists(
        self, alert_id: UUID, user_id: UUID, session: Any = None
    ) -> Any | None: ...
    async def get_user_data(
        self, user_id: UUID, session: Any = None
    ) -> Any | None: ...
    async def get_alerts_contacts_columns(
        self, session: Any = None
    ) -> list[str]: ...
    async def get_user_columns(self, session: Any = None) -> list[str]: ...
    async def create_subscription(
        self,
        alert_id: UUID,
        user_id: UUID,
        contacts_dict: dict[str, Any],
        session: Any = None,
    ) -> UUID: ...
    async def delete_subscription_statuses(
        self, subscription_id: UUID, session: Any = None
    ) -> int: ...
    async def delete_subscription(
        self, subscription_id: UUID, session: Any = None
    ) -> bool: ...
    async def get_subscription_by_id(
        self, subscription_id: UUID, session: Any = None
    ) -> Any | None: ...
    async def get_all_notification_statuses(
        self, session: Any = None
    ) -> list[Any]: ...
    async def get_subscription_statuses(
        self, subscription_id: UUID, session: Any = None
    ) -> dict[Any, Any]: ...
    async def update_subscription_channels(
        self,
        subscription_id: UUID,
        update_fields: list[str],
        update_values: list[Any],
        session: Any = None,
    ) -> bool: ...
    async def get_current_subscription_statuses(
        self, subscription_id: UUID, session: Any = None
    ) -> dict[Any, UUID]: ...
    async def update_subscription_status(
        self, status_record_id: UUID, repeat: int, session: Any = None
    ) -> bool: ...
    async def create_subscription_status(
        self,
        subscription_id: UUID,
        status_id: UUID,
        repeat: int,
        session: Any = None,
    ) -> bool: ...
    async def delete_subscription_status(
        self, status_record_id: UUID, session: Any = None
    ) -> bool: ...
    async def get_subscription_users(
        self,
        alert_id: UUID,
        query: str | None = None,
        groups: bool | None = None,
        subscribed_only: bool = False,
        order_by: str = "samAccountName",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
        session: Any = None,
    ) -> tuple[list[Any], int]: ...
    async def get_alerts_by_user(
        self,
        user_id: UUID,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
        subscribed_only: bool = False,
        session: Any = None,
    ) -> tuple[list[Any], int]: ...


class DTRepositoryProtocol(Protocol):
    async def check_alert_exists(self, alert_id: UUID) -> bool: ...
    async def get_dt_by_alert_id(self, alert_id: UUID) -> Any | None: ...
    async def check_dt_exists(self, alert_id: UUID) -> bool: ...
    async def create_dt(
        self,
        alert_id: UUID,
        content: str,
        auto_create: bool,
        silence_time: str | None = None,
    ) -> UUID: ...
    async def update_dt(
        self,
        alert_id: UUID,
        content: str | None = None,
        auto_create: bool | None = None,
        silence_time: str | None = None,
    ) -> bool: ...
    async def delete_dt(self, alert_id: UUID) -> bool: ...


class UsersRepositoryProtocol(Protocol):
    async def get_telegram_by_login(self, login: str) -> Any | None: ...
    async def check_user_exists(self, user_id: UUID) -> bool: ...
    async def get_available_columns(self) -> list[Any]: ...
    async def create_user(
        self, fields: list[Any], values: list[Any]
    ) -> UUID: ...
    async def update_user(
        self, user_id: UUID, fields: list[Any], values: list[Any]
    ) -> bool: ...
    async def delete_user(self, user_id: UUID) -> bool: ...
    async def search_users(
        self,
        query: str | None = None,
        groups: bool | None = None,
        order_by: str = "samAccountName",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Any], int]: ...


class ScreenshotsRepositoryProtocol(Protocol):
    async def search_screenshots(
        self,
        query: str | None = None,
        order_by: str = "description",
        order_dir: str = "asc",
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[list[Any], int]: ...
    async def get_screenshot_by_id(
        self, screenshot_id: UUID
    ) -> Any | None: ...
    async def create_screenshot(
        self, name: str, description: str, image_data: str
    ) -> UUID: ...
    async def update_screenshot(
        self,
        screenshot_id: UUID,
        name: str | None = None,
        description: str | None = None,
        image_data: str | None = None,
    ) -> bool: ...
    async def delete_screenshot(self, screenshot_id: UUID) -> bool: ...
    async def check_screenshot_exists(self, screenshot_id: UUID) -> bool: ...


class LinksRepositoryProtocol(Protocol):
    async def get_links_by_alert(self, alert_id: UUID) -> list[Any]: ...
    async def get_link_by_id(self, link_id: UUID) -> Any | None: ...
    async def create_link(
        self, alert_id: UUID, link_name: str, link_url: str
    ) -> UUID: ...
    async def update_link(
        self,
        link_id: UUID,
        link_name: str | None = None,
        link_url: str | None = None,
    ) -> bool: ...
    async def delete_link(self, link_id: UUID) -> bool: ...
    async def check_link_exists(self, link_id: UUID) -> bool: ...


class FeedbackRepositoryProtocol(Protocol):
    async def get_feedback_by_status_and_contact(
        self, status_history: UUID, contact: str
    ) -> Any | None: ...
    async def create_feedback(
        self, feedback_id: UUID, status_history: UUID, contact: str, score: int
    ) -> UUID: ...
    async def update_feedback(self, feedback_id: UUID, score: int) -> bool: ...
    async def delete_feedback(
        self, status_history: UUID, contact: str
    ) -> bool: ...


class IndicatorsRepositoryProtocol(Protocol):
    async def autocomplete_indicators(
        self, query: str | None = None, limit: int = 10
    ) -> list[Any]: ...


class RulesRepositoryProtocol(Protocol):
    async def search_group_rules(
        self, query: str | None = None, limit: int = 50
    ) -> tuple[list[Any], int]: ...
