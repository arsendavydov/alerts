"""
Сервис для работы с индикаторами.
Содержит асинхронную бизнес-логику для работы с индикаторами.
"""

from typing import Any

from contracts.repository_protocols import IndicatorsRepositoryProtocol
from fastapi import HTTPException

from utils import log


class IndicatorsService:
    """Сервис для работы с индикаторами."""

    def __init__(self, repository: IndicatorsRepositoryProtocol):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с индикаторами
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

    async def get_indicators_autocomplete(
        self, query: str | None, limit: int
    ) -> dict:
        """Автодополнение индикаторов."""
        try:
            rows = await self.repository.autocomplete_indicators(query, limit)
            indicators = []
            for row in rows:
                row_dict = self._as_dict(row)
                indicators.append(
                    {
                        "indicator_id": str(row_dict.get("id")),
                        "indicator_name": row_dict.get("indicator_name"),
                    }
                )
            return {"indicators": indicators, "total": len(indicators)}
        except Exception as e:
            log.error(
                f"[IndicatorsService.get_indicators_autocomplete] Error: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении списка индикаторов: {e}",
            )
