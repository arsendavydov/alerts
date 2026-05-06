from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroupRuleAutocompleteItem(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    group_rule_id: UUID = Field(description="ID группы правил")
    description: str = Field(description="Описание группы правил")
    image: str | None = Field(
        default=None, description="JSON-изображение/схема для группы правил"
    )


class GroupRuleAutocompleteResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    group_rules: list[GroupRuleAutocompleteItem]
    total: int
