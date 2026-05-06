"""
Модульные тесты для валидации схем Users.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.users import (
    ContactFieldInfo,
    TelegramGroupAutocompleteResponse,
    TelegramGroupItem,
    TelegramUserResponse,
    UserContacts,
    UserCreate,
    UserDetail,
    UserFormStructureResponse,
    UserListItem,
    UserListResponse,
    UserUpdate,
)


class TestUserContacts:
    """Тесты для UserContacts."""

    def test_valid_contacts(self):
        """Тест валидных контактов."""
        data = UserContacts()
        # extra='allow' позволяет добавлять любые поля
        assert data.model_config.get("extra") == "allow"

    def test_with_dynamic_fields(self):
        """Тест с динамическими полями."""
        data = UserContacts(telegram="12345", email="test@test.com")
        # Проверяем что поля доступны через __dict__ или getattr
        assert hasattr(data, "telegram") or "telegram" in data.model_dump()


class TestUserDetail:
    """Тесты для UserDetail."""

    def test_valid_detail(self):
        """Тест валидной детальной информации."""
        user_id = uuid4()
        data = UserDetail(user_id=user_id, user_name="test_user", group=False)
        assert data.user_id == user_id
        assert data.user_name == "test_user"
        assert data.group is False

    def test_with_contacts(self):
        """Тест с контактами."""
        user_id = uuid4()
        contacts = UserContacts()
        data = UserDetail(
            user_id=user_id,
            user_name="test_user",
            group=False,
            contacts=contacts,
        )
        assert data.contacts is not None


class TestUserListItemAndResponse:
    """Тесты для UserListItem и UserListResponse."""

    def test_user_list_item_minimal(self):
        """Тест минимального элемента списка пользователей."""
        user_id = uuid4()
        item = UserListItem(
            user_id=user_id,
            samAccountName="test_user",
            group=False,
        )
        assert item.user_id == user_id
        assert item.samAccountName == "test_user"
        assert item.group is False
        assert item.contacts is None

    def test_user_list_response(self):
        """Тест ответа списка пользователей."""
        user_id = uuid4()
        item = UserListItem(
            user_id=user_id,
            samAccountName="test_user",
            group=False,
            contacts=UserContacts(email="test@test.com"),
        )
        resp = UserListResponse(users=[item], total=1)
        assert resp.total == 1
        assert len(resp.users) == 1
        assert resp.users[0].samAccountName == "test_user"


class TestUserCreate:
    """Тесты для UserCreate."""

    def test_valid_create(self):
        """Тест валидного создания."""
        data = UserCreate(samAccountName="test_user", group=False)
        assert data.samAccountName == "test_user"
        assert data.group is False

    def test_default_group(self):
        """Тест дефолтного значения group."""
        data = UserCreate(samAccountName="test_user")
        assert data.group is False  # Дефолтное значение

    def test_with_contacts(self):
        """Тест с контактами."""
        contacts = UserContacts()
        data = UserCreate(samAccountName="test_user", contacts=contacts)
        assert data.contacts is not None


class TestUserUpdate:
    """Тесты для UserUpdate."""

    def test_all_fields_optional(self):
        """Тест что все поля опциональны."""
        data = UserUpdate()
        assert data.samAccountName is None
        assert data.group is None
        assert data.contacts is None

    def test_partial_update(self):
        """Тест частичного обновления."""
        data = UserUpdate(samAccountName="updated_user")
        assert data.samAccountName == "updated_user"
        assert data.group is None


class TestTelegramUserResponse:
    """Тесты для TelegramUserResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        data = TelegramUserResponse(telegram_id="12345")
        assert data.telegram_id == "12345"


class TestTelegramGroupItem:
    """Тесты для TelegramGroupItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        data = TelegramGroupItem(user_name="group1", telegram="12345")
        assert data.user_name == "group1"
        assert data.telegram == "12345"


class TestTelegramGroupAutocompleteResponse:
    """Тесты для TelegramGroupAutocompleteResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        item = TelegramGroupItem(user_name="group1", telegram="12345")
        data = TelegramGroupAutocompleteResponse(
            telegram_groups=[item], total=1
        )
        assert len(data.telegram_groups) == 1
        assert data.total == 1


class TestContactFieldInfo:
    """Тесты для ContactFieldInfo."""

    def test_valid_field_info(self):
        """Тест валидной информации о поле."""
        data = ContactFieldInfo(
            name="telegram", data_type="varchar", is_nullable=True
        )
        assert data.name == "telegram"
        assert data.data_type == "varchar"
        assert data.is_nullable is True


class TestUserFormStructureResponse:
    """Тесты для UserFormStructureResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        field = ContactFieldInfo(
            name="telegram", data_type="varchar", is_nullable=True
        )
        data = UserFormStructureResponse(fields=[field])
        assert len(data.fields) == 1
        assert data.fields[0].name == "telegram"
