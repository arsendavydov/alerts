"""
Сервис для работы с группами правил.
Содержит асинхронную бизнес-логику для работы с группами правил.
"""

from typing import Any

from contracts.repository_protocols import RulesRepositoryProtocol
from fastapi import HTTPException

from schemas.group_rules import (
    GroupRuleAutocompleteItem,
    GroupRuleAutocompleteResponse,
)
from utils import log


class RulesService:
    """Сервис для работы с группами правил."""

    def __init__(self, repository: RulesRepositoryProtocol):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с группами правил
        """
        self.repository = repository

    @staticmethod
    def _as_dict(row: object) -> dict[str, Any]:
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
                    result[key] = row[idx]  # type: ignore[index]
                return result
            except Exception:
                return {}
        return {}

    async def autocomplete_group_rules(
        self, query: str | None, limit: int
    ) -> GroupRuleAutocompleteResponse:
        """Автокомплит групп правил."""
        try:
            rows, total = await self.repository.search_group_rules(
                query, limit
            )
            items = []
            for row in rows:
                row_dict = self._as_dict(row)
                items.append(
                    GroupRuleAutocompleteItem(
                        group_rule_id=row_dict.get("id"),
                        description=row_dict.get("description") or "",
                        image=row_dict.get("image"),
                    )
                )
            return GroupRuleAutocompleteResponse(
                group_rules=items, total=total
            )
        except Exception as e:
            log.error(f"[RulesService.autocomplete_group_rules] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при автокомплите групп правил: {e}",
            )
