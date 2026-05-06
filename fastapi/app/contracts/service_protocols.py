"""Контракты (Protocol) для service-слоя alerts."""

from typing import Protocol
from uuid import UUID

from schemas.alerts import (
    AlertAutocompleteResponse,
    AlertDetail,
    AlertDetailCreate,
    AlertDetailUpdate,
    AlertListResponse,
    TagCloudResponse,
)
from schemas.dt import DTDetail, DTDetailCreate, DTDetailUpdate
from schemas.feedback import FeedbackCreate, FeedbackDelete, FeedbackResponse
from schemas.group_rules import GroupRuleAutocompleteResponse
from schemas.links import (
    LinkByAlertListResponse,
    LinkDetail,
    LinkDetailCreate,
    LinkDetailUpdate,
)
from schemas.pauses import (
    AlertPauseRemoveRequest,
    AlertPauseScheduleRequest,
    AlertPauseUpdateRequest,
    PauseHistoryResponse,
)
from schemas.screenshots import (
    ScreenshotCreate,
    ScreenshotDetail,
    ScreenshotSearchResponse,
    ScreenshotUpdate,
)
from schemas.subscriptions import (
    AlertByUserListResponse,
    SubscribeRequest,
    SubscriptionByUserResponse,
    SubscriptionByUserUpdate,
    SubscriptionUserListResponse,
    UnsubscribeRequest,
)
from schemas.users import (
    TelegramUserResponse,
    UserCreate,
    UserListResponse,
    UserUpdate,
)


class AlertsServiceProtocol(Protocol):
    async def search_alerts(
        self,
        query: str | None = None,
        tags: str | None = None,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> AlertListResponse: ...

    async def get_alert_detail(self, alert_id: UUID) -> AlertDetail: ...
    async def create_alert(self, data: AlertDetailCreate) -> bool: ...
    async def update_alert(self, data: AlertDetailUpdate) -> bool: ...
    async def delete_alert(self, alert_id: UUID) -> bool: ...
    async def autocomplete_alerts(
        self, query: str | None, limit: int
    ) -> AlertAutocompleteResponse: ...
    async def get_tag_cloud(
        self, alert_name: str | None = None, tags: str | None = None
    ) -> TagCloudResponse: ...
    async def duplicate_alert(self, alert_id: UUID) -> bool: ...


class PausesServiceProtocol(Protocol):
    async def get_alert_pauses(
        self,
        alert_id: UUID,
        filter_type: str = "all",
        order_by: str = "start_time",
        order_dir: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> PauseHistoryResponse: ...
    async def schedule_alert_pause(
        self, alert_id: UUID, data: AlertPauseScheduleRequest
    ) -> bool: ...
    async def stop_alert_pause(
        self, alert_id: UUID, data: AlertPauseRemoveRequest
    ) -> bool: ...
    async def update_alert_pause(
        self, alert_id: UUID, pause_id: UUID, data: AlertPauseUpdateRequest
    ) -> bool: ...
    async def stop_specific_alert_pause(
        self, alert_id: UUID, pause_id: UUID, data: AlertPauseRemoveRequest
    ) -> bool: ...
    async def delete_alert_pause(
        self, alert_id: UUID, pause_id: UUID
    ) -> bool: ...
    async def toggle_alert_pause(
        self, alert_id: UUID, login: str, comment: str | None = None
    ) -> bool: ...


class SubscriptionsServiceProtocol(Protocol):
    async def subscribe(self, data: SubscribeRequest) -> bool: ...
    async def unsubscribe(self, data: UnsubscribeRequest) -> bool: ...
    async def get_subscription_by_alert_and_user(
        self, alert_id: UUID, user_id: UUID
    ) -> SubscriptionByUserResponse: ...
    async def update_subscription_by_alert_and_user(
        self, data: SubscriptionByUserUpdate
    ) -> bool: ...
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
    ) -> SubscriptionUserListResponse: ...
    async def get_alerts_by_user(
        self,
        user_id: UUID,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
        subscribed_only: bool = False,
    ) -> AlertByUserListResponse: ...


class DTServiceProtocol(Protocol):
    async def get_dt(self, alert_id: UUID) -> DTDetail: ...
    async def create_dt(
        self, alert_id: UUID, data: DTDetailCreate
    ) -> bool: ...
    async def update_dt(
        self, alert_id: UUID, data: DTDetailUpdate
    ) -> bool: ...
    async def delete_dt(self, alert_id: UUID) -> bool: ...


class UsersServiceProtocol(Protocol):
    async def get_telegram_by_login(
        self, login: str
    ) -> TelegramUserResponse: ...
    async def create_user(self, data: UserCreate) -> bool: ...
    async def update_user(self, user_id: UUID, data: UserUpdate) -> bool: ...
    async def delete_user(self, user_id: UUID) -> bool: ...
    async def search_users(
        self,
        query: str | None = None,
        groups: bool | None = None,
        order_by: str = "samAccountName",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> UserListResponse: ...


class ScreenshotsServiceProtocol(Protocol):
    async def search_screenshots(
        self,
        query: str | None = None,
        order_by: str = "description",
        order_dir: str = "asc",
        limit: int = 1000,
        offset: int = 0,
    ) -> ScreenshotSearchResponse: ...
    async def get_screenshot(
        self, screenshot_id: UUID
    ) -> ScreenshotDetail: ...
    async def create_screenshot(self, data: ScreenshotCreate) -> UUID: ...
    async def update_screenshot(
        self, screenshot_id: UUID, data: ScreenshotUpdate
    ) -> bool: ...
    async def delete_screenshot(self, screenshot_id: UUID) -> bool: ...


class FeedbackServiceProtocol(Protocol):
    async def create_feedback(
        self, data: FeedbackCreate
    ) -> FeedbackResponse: ...
    async def delete_feedback(self, data: FeedbackDelete) -> bool: ...


class IndicatorsServiceProtocol(Protocol):
    async def get_indicators_autocomplete(
        self, query: str | None, limit: int
    ) -> dict: ...


class LinksServiceProtocol(Protocol):
    async def get_links_by_alert(
        self, alert_id: UUID
    ) -> LinkByAlertListResponse: ...
    async def get_link_detail(self, link_id: UUID) -> LinkDetail: ...
    async def create_link(self, data: LinkDetailCreate) -> bool: ...
    async def update_link(self, data: LinkDetailUpdate) -> bool: ...
    async def delete_link(self, link_id: UUID) -> bool: ...


class RulesServiceProtocol(Protocol):
    async def autocomplete_group_rules(
        self, query: str | None, limit: int
    ) -> GroupRuleAutocompleteResponse: ...
