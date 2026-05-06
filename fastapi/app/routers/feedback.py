from contracts.service_protocols import FeedbackServiceProtocol
from dependencies import get_feedback_service

from fastapi import APIRouter, Body, Depends
from schemas.feedback import FeedbackCreate, FeedbackDelete, FeedbackResponse

router = APIRouter(prefix="/alerts/api/v1/feedback", tags=["feedback"])


@router.post(
    "/detail",
    response_model=FeedbackResponse,
    summary="Создать фидбек",
    description="Создать новую запись фидбека или обновить существующую.",
    response_model_exclude_none=True,
)
async def create_feedback(
    data: FeedbackCreate = Body(...),
    service: FeedbackServiceProtocol = Depends(get_feedback_service),
) -> FeedbackResponse:
    """Создание новой записи фидбека или обновление существующей."""
    return await service.create_feedback(data)


@router.delete(
    "/detail",
    summary="Удалить фидбек",
    description="Удалить запись фидбека по status_history и user_fio. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def delete_feedback(
    data: FeedbackDelete = Body(...),
    service: FeedbackServiceProtocol = Depends(get_feedback_service),
) -> bool:
    """Удаление записи фидбека."""
    return await service.delete_feedback(data)
