from typing import Literal
from uuid import UUID

from contracts.service_protocols import UsersServiceProtocol
from dependencies import get_users_service

from fastapi import APIRouter, Body, Depends, Path, Query
from schemas.users import (
    TelegramUserResponse,
    UserCreate,
    UserListResponse,
    UserUpdate,
)

router = APIRouter(prefix="/alerts/api/v1", tags=["users"])


@router.get(
    "/users/{login}/telegram",
    response_model=TelegramUserResponse,
    summary="Получить Telegram ID пользователя по login",
    description="Точный регистронезависимый поиск по login. Возвращает telegram_id.",
    response_model_exclude_none=True,
)
async def get_telegram_by_login(
    login: str = Path(
        ..., min_length=1, description="Логин пользователя (login)"
    ),
    service: UsersServiceProtocol = Depends(get_users_service),
):
    return await service.get_telegram_by_login(login)


@router.get(
    "/users/search",
    response_model=UserListResponse,
    summary="Поиск пользователей для раздела 'Пользователи'",
    description=(
        "Поиск по пользователям (alerts.contacts) с пагинацией, сортировкой и фильтрацией. "
        "Поиск работает по user_name (samAccountName) и email (если колонка есть). "
        "Возвращает пользователя, признак group и все контакты."
    ),
    response_model_exclude_none=True,
)
async def search_users(
    query: str | None = Query(
        None,
        min_length=1,
        description="Поиск по samAccountName (user_name) или email (регистронезависимо, частичное совпадение)",
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Сколько пользователей вернуть"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    order_by: Literal["samAccountName", "email"] = Query(
        "samAccountName",
        description="Поле сортировки",
    ),
    order_dir: Literal["asc", "desc"] = Query(
        "asc",
        description="Направление сортировки",
    ),
    groups: bool | None = Query(
        None,
        description="Фильтр по группам: true - только группы, false - только обычные пользователи",
    ),
    service: UsersServiceProtocol = Depends(get_users_service),
) -> UserListResponse:
    return await service.search_users(
        query=query,
        groups=groups,
        order_by=order_by,
        order_dir=order_dir,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/users",
    summary="Создать пользователя",
    description="Создать нового пользователя с указанными параметрами. ID генерируется автоматически. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def create_user(
    data: UserCreate = Body(...),
    service: UsersServiceProtocol = Depends(get_users_service),
):
    return await service.create_user(data)


@router.patch(
    "/users/{user_id}",
    summary="Обновить пользователя",
    description="Обновить существующего пользователя по ID. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def update_user(
    user_id: UUID = Path(..., description="ID пользователя"),
    data: UserUpdate = Body(...),
    service: UsersServiceProtocol = Depends(get_users_service),
):
    return await service.update_user(user_id, data)


@router.delete(
    "/users/{user_id}",
    summary="Удалить пользователя",
    description="Удалить пользователя по ID. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def delete_user(
    user_id: UUID = Path(..., description="ID пользователя"),
    service: UsersServiceProtocol = Depends(get_users_service),
):
    return await service.delete_user(user_id)
