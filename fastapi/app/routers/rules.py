from contracts.service_protocols import RulesServiceProtocol
from dependencies import get_rules_service

from fastapi import APIRouter, Depends, Query
from schemas.group_rules import GroupRuleAutocompleteResponse

router = APIRouter(prefix="/alerts/api/v1/group_rules", tags=["group_rules"])


@router.get(
    "/autocomplete",
    response_model=GroupRuleAutocompleteResponse,
    summary="Автокомплит групп правил",
    description="Поиск по description в alerts.group_rules. Возвращает объекты с group_rule_id, description, image",
    response_model_exclude_none=True,
)
async def autocomplete_group_rules(
    query: str | None = Query(
        None, min_length=1, description="Поиск по description"
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Сколько записей вернуть"
    ),
    service: RulesServiceProtocol = Depends(get_rules_service),
) -> GroupRuleAutocompleteResponse:
    """Автокомплит групп правил."""
    return await service.autocomplete_group_rules(query, limit)
