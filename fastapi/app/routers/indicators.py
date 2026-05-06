from contracts.service_protocols import IndicatorsServiceProtocol
from dependencies import get_indicators_service

from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/alerts/api/v1/indicators", tags=["indicators"])

# @router.get(
#     "/search",
#     response_model=dict,
#     summary="Поиск индикаторов",
#     description="Поиск, фильтрация и пагинация индикаторов с возможностью сортировки. Возвращает объект с массивом и total."
# )
# async def get_indicators_search(
#     query: Optional[str] = Query(None, min_length=1, description="Поиск по indicator_name"),
#     limit: int = Query(50, ge=1, le=100, description="Сколько индикаторов вернуть"),
#     offset: int = Query(0, ge=0, description="Смещение для пагинации"),
#     order_by: str = Query("create_date", description="Поле сортировки: indicator_name, source_name, system_name, product_name, description, enabled, create_date, update_date"),
#     order_dir: str = Query("asc", description="Направление сортировки: asc или desc")
# ):
#     allowed_fields = {
#         "indicator_name": "e.event_name",
#         "source_name": "src.name",
#         "system_name": "s.name",
#         "product_name": "p.product_name",
#         "description": "e.description",
#         "enabled": "e.enabled",
#         "create_date": "e.create_date",
#         "update_date": "e.update_date"
#     }
#     if order_by not in allowed_fields:
#         raise HTTPException(status_code=400, detail="order_by must be one of: indicator_name, source_name, system_name, product_name, description, enabled, create_date, update_date")
#     if order_dir.lower() not in ("asc", "desc"):
#         raise HTTPException(status_code=400, detail="order_dir must be 'asc' or 'desc'")
#     try:
#         is_database_connection_alive()
#         with conn.cursor() as cursor:
#             base_query = """
#                 SELECT
#                     e.id,
#                     e.event_name AS indicator_name,
#                     e.description,
#                     e.system,
#                     s.name AS system_name,
#                     e.product,
#                     p.product_name AS product_name,
#                     e.source,
#                     src.name AS source_name,
#                     e.enabled,
#                     e.create_date,
#                     e.update_date
#                 FROM dictionary.events e
#                 LEFT JOIN dictionary.system s ON e.system = s.id
#                 LEFT JOIN dictionary.product p ON e.product = p.id
#                 LEFT JOIN dictionary.source src ON e.source = src.id
#             """
#
#             if query:
#                 count_query = f"""
#                     SELECT COUNT(*) FROM (
#                         {base_query}
#                         WHERE e.event_name ILIKE %s
#                     ) AS subquery
#                 """
#                 cursor.execute(count_query, (f'%{query}%',))
#                 total = cursor.fetchone()[0]
#
#                 data_query = f"""
#                     {base_query}
#                     WHERE e.event_name ILIKE %s
#                     ORDER BY
#                         CASE WHEN e.event_name = %s THEN 0 ELSE 1 END ASC,
#                         {allowed_fields[order_by]} {order_dir.upper()}
#                     LIMIT %s OFFSET %s
#                 """
#                 cursor.execute(data_query, (f'%{query}%', query, limit, offset))
#             else:
#                 count_query = f"""
#                     SELECT COUNT(*) FROM (
#                         {base_query}
#                     ) AS subquery
#                 """
#                 cursor.execute(count_query)
#                 total = cursor.fetchone()[0]
#
#                 data_query = f"""
#                     {base_query}
#                     ORDER BY {allowed_fields[order_by]} {order_dir.upper()}
#                     LIMIT %s OFFSET %s
#                 """
#                 cursor.execute(data_query, (limit, offset))
#
#             rows = cursor.fetchall()
#
#             indicators = [IndicatorListItem(
#                 id=row[0],
#                 indicator_name=row[1],
#                 description=row[2],
#                 system=row[3],
#                 system_name=row[4],
#                 product=row[5],
#                 product_name=row[6],
#                 source=row[7],
#                 source_name=row[8],
#                 enabled=row[9],
#                 create_date=row[10],
#                 update_date=row[11]
#             ) for row in rows]
#         return {"indicators": indicators, "total": total}
#     except Exception as e:
#         log.error(f"[get_indicators_search] Error: {e}")
#         raise HTTPException(status_code=500, detail=f"Error getting indicators list: {e}")


@router.get(
    "/autocomplete",
    response_model=dict,
    summary="Автодополнение индикаторов",
    description="Поиск индикаторов по имени для автодополнения. Возвращает только имена индикаторов.",
    response_model_exclude_none=True,
)
async def get_indicators_autocomplete(
    query: str | None = Query(None, description="Поиск по indicator_name"),
    limit: int = Query(
        10, ge=1, le=50, description="Сколько индикаторов вернуть"
    ),
    service: IndicatorsServiceProtocol = Depends(get_indicators_service),
):
    """Автодополнение индикаторов."""
    return await service.get_indicators_autocomplete(query, limit)
