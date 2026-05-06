"""
Модульные тесты для валидации схем GroupRules.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.group_rules import (
    GroupRuleAutocompleteItem,
    GroupRuleAutocompleteResponse,
)


class TestGroupRuleAutocompleteItem:
    """Тесты для GroupRuleAutocompleteItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        group_rule_id = uuid4()
        data = GroupRuleAutocompleteItem(
            group_rule_id=group_rule_id, description="Test Description"
        )
        assert data.group_rule_id == group_rule_id
        assert data.description == "Test Description"

    def test_with_image(self):
        """Тест с изображением."""
        group_rule_id = uuid4()
        data = GroupRuleAutocompleteItem(
            group_rule_id=group_rule_id,
            description="Test Description",
            image="test.jpg",
        )
        assert data.image == "test.jpg"

    def test_without_image(self):
        """Тест без изображения."""
        group_rule_id = uuid4()
        data = GroupRuleAutocompleteItem(
            group_rule_id=group_rule_id, description="Test Description"
        )
        assert data.image is None


class TestGroupRuleAutocompleteResponse:
    """Тесты для GroupRuleAutocompleteResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        group_rule_id = uuid4()
        item = GroupRuleAutocompleteItem(
            group_rule_id=group_rule_id, description="Test Description"
        )
        data = GroupRuleAutocompleteResponse(group_rules=[item], total=1)
        assert len(data.group_rules) == 1
        assert data.total == 1

    def test_empty_response(self):
        """Тест пустого ответа."""
        data = GroupRuleAutocompleteResponse(group_rules=[], total=0)
        assert len(data.group_rules) == 0
        assert data.total == 0
