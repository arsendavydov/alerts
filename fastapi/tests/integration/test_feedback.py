"""
Интеграционные тесты для feedback endpoints.
"""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_feedback(
    client: AsyncClient, created_resources: dict[str, list]
):
    """Тест создания обратной связи."""
    # Используем тестовые данные как в lazy тестах
    test_status_history = UUID(
        "9dd606f8-8cd3-4a4c-8fe7-85bfca8e825c"
    )  # Тестовый UUID из lazy тестов
    test_user_fio = f"Test User {uuid.uuid4().hex[:8]}"

    feedback_data = {
        "status_history": str(test_status_history),
        "user_fio": test_user_fio,
        "score": 5,
    }

    response = await client.post("/api/v1/feedback/detail", json=feedback_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Спасибо за обратную связь!"  # Первая запись

    # Сохраняем данные для очистки
    created_resources["feedback"].append(
        {"status_history": test_status_history, "user_fio": test_user_fio}
    )


@pytest.mark.asyncio
async def test_update_feedback(
    client: AsyncClient, created_resources: dict[str, list]
):
    """Тест обновления обратной связи (через повторный POST)."""
    # Используем тестовые данные как в lazy тестах
    test_status_history = UUID("9dd606f8-8cd3-4a4c-8fe7-85bfca8e825c")
    test_user_fio = f"Test User {uuid.uuid4().hex[:8]}"

    # Создаем feedback
    create_data = {
        "status_history": str(test_status_history),
        "user_fio": test_user_fio,
        "score": 0,
    }

    create_response = await client.post(
        "/api/v1/feedback/detail", json=create_data
    )
    assert create_response.status_code == 200
    assert create_response.json()["message"] == "Спасибо за обратную связь!"

    # Обновляем feedback через повторный POST с другим score
    update_data = {
        "status_history": str(test_status_history),
        "user_fio": test_user_fio,
        "score": 1,
    }

    update_response = await client.post(
        "/api/v1/feedback/detail", json=update_data
    )
    assert update_response.status_code == 200
    assert (
        update_response.json()["message"]
        == "Спасибо! Достаточно одного раза, больше не надо."
    )

    # Сохраняем данные для очистки
    created_resources["feedback"].append(
        {"status_history": test_status_history, "user_fio": test_user_fio}
    )


@pytest.mark.asyncio
async def test_delete_feedback(
    client: AsyncClient, created_resources: dict[str, list]
):
    """Тест удаления обратной связи."""
    # Используем тестовые данные как в lazy тестах
    test_status_history = UUID("9dd606f8-8cd3-4a4c-8fe7-85bfca8e825c")
    test_user_fio = f"Test User {uuid.uuid4().hex[:8]}"

    # Создаем feedback
    create_data = {
        "status_history": str(test_status_history),
        "user_fio": test_user_fio,
        "score": 5,
    }

    create_response = await client.post(
        "/api/v1/feedback/detail", json=create_data
    )
    assert create_response.status_code == 200

    # Удаляем feedback
    delete_data = {
        "status_history": str(test_status_history),
        "user_fio": test_user_fio,
    }

    # httpx.AsyncClient.delete() не поддерживает json параметр, используем request()
    delete_response = await client.request(
        "DELETE", "/api/v1/feedback/detail", json=delete_data
    )
    assert delete_response.status_code == 200
    assert delete_response.json() is True

    # Проверяем что feedback удален (повторное удаление должно вернуть 404)
    delete_again_response = await client.request(
        "DELETE", "/api/v1/feedback/detail", json=delete_data
    )
    assert delete_again_response.status_code == 404


@pytest.mark.asyncio
async def test_feedback_create_and_update(
    client: AsyncClient, created_resources: dict[str, list]
):
    """Тест создания и обновления feedback в одном тесте (как в lazy тестах)."""
    # Используем тестовые данные как в lazy тестах
    test_status_history = UUID("9dd606f8-8cd3-4a4c-8fe7-85bfca8e825c")
    test_user_fio = f"Test User {uuid.uuid4().hex[:8]}"

    # POST - создание первого фидбека (score=0)
    feedback_data_1 = {
        "status_history": str(test_status_history),
        "user_fio": test_user_fio,
        "score": 0,
    }

    create_result_1 = await client.post(
        "/api/v1/feedback/detail", json=feedback_data_1
    )
    assert create_result_1.status_code == 200
    assert create_result_1.json()["message"] == "Спасибо за обратную связь!"

    # POST - обновление фидбека (score=1) - должен вернуть "Спасибо! Достаточно одного раза, больше не надо."
    feedback_data_2 = {
        "status_history": str(test_status_history),
        "user_fio": test_user_fio,
        "score": 1,
    }

    update_result = await client.post(
        "/api/v1/feedback/detail", json=feedback_data_2
    )
    assert update_result.status_code == 200
    assert (
        update_result.json()["message"]
        == "Спасибо! Достаточно одного раза, больше не надо."
    )

    # Сохраняем данные для очистки
    created_resources["feedback"].append(
        {"status_history": test_status_history, "user_fio": test_user_fio}
    )
