"""
Конфигурация и фикстуры для E2E тестов.
"""

import contextlib
import os
from uuid import UUID

import pytest
import requests

# Отключаем прокси для e2e тестов (как в интеграционных тестах)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)


@pytest.fixture(scope="function")
def cleanup_data():
    """
    Фикстура для хранения данных для очистки в E2E тестах.
    Используется тестами для сохранения ID созданных ресурсов.
    """
    return {
        "user_id": None,
        "alert_id": None,
        "dt_id": None,
        "link_ids": [],
        "screenshot_id": None,
        "pause_id": None,
        "pause_ids": [],
    }


@pytest.fixture(scope="function", autouse=True)
def cleanup_e2e_resources(request):
    """
    Автоматическая очистка созданных ресурсов после каждого E2E теста.
    Работает даже если тест упал с ошибкой.

    Использует request.getfixturevalue для получения cleanup_data из теста,
    если фикстура доступна.
    """
    yield

    # Пытаемся получить cleanup_data из теста
    try:
        cleanup_data = request.getfixturevalue("cleanup_data")
    except Exception:
        # Если фикстура недоступна, пропускаем очистку
        return

    base_url = "http://localhost:8888/alerts/api/v1"

    # Очистка в обратном порядке зависимостей
    # Сначала удаляем зависимости, потом основные ресурсы

    # Удаляем pauses (если есть alert_id и pause_ids)
    if cleanup_data.get("alert_id") and cleanup_data.get("pause_ids"):
        for pause_id in cleanup_data["pause_ids"]:
            try:
                alert_id = cleanup_data["alert_id"]
                # Если alert_id - это имя (не UUID), нужно найти UUID
                if isinstance(alert_id, str):
                    try:
                        UUID(
                            alert_id
                        )  # Проверяем, является ли это валидным UUID
                        # Это UUID, используем как есть
                    except (ValueError, AttributeError):
                        # Это не UUID, значит имя - ищем по имени
                        search_response = requests.get(
                            f"{base_url}/alerts/search",
                            params={"query": alert_id, "limit": 10},
                        )
                        if search_response.status_code == 200:
                            alerts = search_response.json().get("alerts", [])
                            for alert in alerts:
                                if alert.get("alert_name") == alert_id:
                                    alert_id = alert["alert_id"]
                                    break
                            else:
                                continue  # Не нашли алерт, пропускаем
                        else:
                            continue

                delete_response = requests.delete(
                    f"{base_url}/alerts/{alert_id}/pause/{pause_id}"
                )
                # Если пауза уже удалена (404), это нормально - просто пропускаем
                if delete_response.status_code == 404:
                    continue
            except Exception:
                pass

    # Удаляем alerts (последними, так как на них могут быть зависимости)
    # Каскадно удаляет связанные данные (links, subscriptions, pauses, dt)
    if cleanup_data.get("alert_id"):
        try:
            alert_id = cleanup_data["alert_id"]
            # Если это имя (не UUID), нужно найти UUID
            if isinstance(alert_id, str):
                try:
                    UUID(alert_id)  # Проверяем, является ли это валидным UUID
                    # Это UUID, используем как есть
                except (ValueError, AttributeError):
                    # Это не UUID, значит имя - ищем по имени
                    search_response = requests.get(
                        f"{base_url}/alerts/search",
                        params={"query": alert_id, "limit": 10},
                    )
                    if search_response.status_code == 200:
                        alerts = search_response.json().get("alerts", [])
                        for alert in alerts:
                            if alert.get("alert_name") == alert_id:
                                alert_id = alert["alert_id"]
                                break
                        else:
                            alert_id = None  # Не нашли алерт
                    else:
                        alert_id = None

            if alert_id:
                requests.delete(
                    f"{base_url}/alerts/detail",
                    params={"alert_id": str(alert_id)},
                )
        except Exception:
            pass

    # Удаляем users
    if cleanup_data.get("user_id"):
        try:
            user_id = cleanup_data["user_id"]
            # Если это не UUID (начинается не с цифры или содержит дефисы неправильно),
            # пытаемся найти UUID через subscriptions/search
            try:
                UUID(user_id)  # Проверяем, является ли это валидным UUID
                # Это UUID, используем как есть
            except (ValueError, AttributeError):
                # Это не UUID, значит samAccountName - ищем UUID через subscriptions/search
                # Используем любой алерт для поиска
                search_alerts_response = requests.get(
                    f"{base_url}/alerts/search",
                    params={"query": "", "limit": 1},
                )
                if search_alerts_response.status_code == 200:
                    alerts = search_alerts_response.json().get("alerts", [])
                    if alerts:
                        test_alert_id = alerts[0]["alert_id"]
                        users_search_response = requests.get(
                            f"{base_url}/alerts/{test_alert_id}/subscriptions/search",
                            params={"query": user_id, "limit": 100},
                        )
                        if users_search_response.status_code == 200:
                            users = users_search_response.json().get(
                                "users", []
                            )
                            for user in users:
                                if user.get("samAccountName") == user_id:
                                    user_id = user["user_id"]
                                    break
                            else:
                                return  # Не нашли пользователя, пропускаем удаление
                        else:
                            return  # Не удалось найти пользователя
                    else:
                        return  # Нет алертов для поиска
                else:
                    return  # Не удалось получить список алертов

            # Удаляем пользователя по UUID (актуальный endpoint: /users/{user_id})
            delete_response = requests.delete(f"{base_url}/users/{user_id}")
            # 400 может быть если формат неправильный, но мы уже проверили UUID
            if delete_response.status_code not in [200, 404]:
                pass  # Игнорируем ошибки удаления
        except Exception:
            pass

    # Удаляем links
    if cleanup_data.get("link_ids"):
        for link_id in cleanup_data["link_ids"]:
            with contextlib.suppress(Exception):
                requests.delete(
                    f"{base_url}/links/detail",
                    params={"link_id": str(link_id)},
                )

    # Удаляем screenshots
    if cleanup_data.get("screenshot_id"):
        with contextlib.suppress(Exception):
            requests.delete(
                f"{base_url}/screenshots/{cleanup_data['screenshot_id']}"
            )

    # Удаляем dt (через alert_id)
    if cleanup_data.get("alert_id") and cleanup_data.get("dt_id"):
        try:
            alert_id = cleanup_data["alert_id"]
            # Если это имя (не UUID), нужно найти UUID
            if isinstance(alert_id, str):
                try:
                    UUID(alert_id)  # Проверяем, является ли это валидным UUID
                    # Это UUID, используем как есть
                except (ValueError, AttributeError):
                    # Это не UUID, значит имя - ищем по имени
                    search_response = requests.get(
                        f"{base_url}/alerts/search",
                        params={"query": alert_id, "limit": 10},
                    )
                    if search_response.status_code == 200:
                        alerts = search_response.json().get("alerts", [])
                        for alert in alerts:
                            if alert.get("alert_name") == alert_id:
                                alert_id = alert["alert_id"]
                                break
                        else:
                            alert_id = None  # Не нашли алерт
                    else:
                        alert_id = None

            if alert_id:
                requests.delete(f"{base_url}/alerts/{alert_id}/dt")
        except Exception:
            pass
