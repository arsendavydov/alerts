from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserContacts(BaseModel):
    """Контактная информация пользователя (динамические поля из alerts.contacts, кроме id, user_name, group)."""

    model_config = ConfigDict(exclude_none=True, extra="allow")
    # Все колонки из alerts.contacts (кроме id, user_name, group) попадают сюда динамически как есть


class UserDetail(BaseModel):
    """Детальная информация о пользователе."""

    model_config = ConfigDict(exclude_none=True)

    user_id: UUID
    user_name: str
    contacts: UserContacts | None = None
    group: bool


class UserListItem(BaseModel):
    """Элемент списка пользователей для страницы 'Пользователи'."""

    model_config = ConfigDict(exclude_none=True)

    user_id: UUID
    samAccountName: str  # В БД хранится как user_name
    group: bool
    contacts: UserContacts | None = None


class UserListResponse(BaseModel):
    """Ответ со списком пользователей для страницы 'Пользователи'."""

    model_config = ConfigDict(exclude_none=True)

    users: list[UserListItem]
    total: int


class UserCreate(BaseModel):
    """Данные для создания нового пользователя."""

    model_config = ConfigDict(exclude_none=True)

    samAccountName: str  # В БД сохраняется как user_name
    group: bool = False  # Дефолтное значение false (как в БД)
    contacts: UserContacts | None = None
    # Все остальные поля из alerts.contacts (кроме id, user_name, group) передаются в объекте contacts


class UserUpdate(BaseModel):
    """Данные для обновления существующего пользователя."""

    model_config = ConfigDict(exclude_none=True)

    samAccountName: str | None = None  # В БД сохраняется как user_name
    group: bool | None = None
    contacts: UserContacts | None = None
    # Все остальные поля из alerts.contacts (кроме id, user_name, group) передаются в объекте contacts


class TelegramUserResponse(BaseModel):
    """Ответ для запроса telegram пользователя по login."""

    model_config = ConfigDict(exclude_none=True)

    telegram_id: str


class TelegramGroupItem(BaseModel):
    """Элемент автодополнения групп Telegram."""

    model_config = ConfigDict(exclude_none=True)

    user_name: str
    telegram: str


class TelegramGroupAutocompleteResponse(BaseModel):
    """Ответ с результатами автодополнения групп Telegram."""

    model_config = ConfigDict(exclude_none=True)

    telegram_groups: list[TelegramGroupItem]
    total: int


class ContactFieldInfo(BaseModel):
    """Информация о поле таблицы contacts."""

    model_config = ConfigDict(exclude_none=True)

    name: str  # Название колонки
    data_type: str  # Тип данных PostgreSQL
    is_nullable: bool  # Может ли быть NULL


class UserFormStructureResponse(BaseModel):
    """Ответ со структурой таблицы contacts для динамической отрисовки формы."""

    model_config = ConfigDict(exclude_none=True)

    fields: list[ContactFieldInfo]  # Все поля таблицы (кроме id)
