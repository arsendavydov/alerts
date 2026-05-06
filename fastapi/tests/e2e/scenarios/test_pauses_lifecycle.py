"""
E2E тест: Полный жизненный цикл пауз алерта.
Проверяет создание алерта, установку и снятие пауз всеми возможными способами,
и удаление пауз и алерта.
"""

import time
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import requests

# Примечание: прокси отключен в conftest.py


class TestPausesLifecycle:
    """E2E тест полного жизненного цикла пауз алерта."""

    @pytest.fixture
    def base_url(self):
        """Базовый URL API."""
        return "http://localhost:8888/alerts/api/v1"

    # Примечание: cleanup_data определена в conftest.py

    def _get_indicator_id(self, base_url: str) -> UUID | None:
        """Получить первый доступный indicator_id."""
        response = requests.get(
            f"{base_url}/indicators/autocomplete", params={"limit": 1}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("indicators"):
                return UUID(data["indicators"][0]["indicator_id"])
        return None

    def _get_group_rule_id(self, base_url: str) -> UUID | None:
        """Получить первый доступный group_rule_id."""
        response = requests.get(
            f"{base_url}/group_rules/autocomplete", params={"limit": 1}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("group_rules"):
                return UUID(data["group_rules"][0]["group_rule_id"])
        return None

    def _create_test_alert(self, base_url: str) -> UUID | None:
        """Создать тестовый алерт и вернуть его ID."""
        # Получаем реальные indicator_id и group_rule_id
        indicator_id = self._get_indicator_id(base_url)
        group_rule_id = self._get_group_rule_id(base_url)

        if not indicator_id or not group_rule_id:
            pytest.skip(
                "Не удалось получить indicator_id или group_rule_id для создания алерта"
            )

        alert_data = {
            "alert_name": f"e2e_pause_test_{uuid4()}",
            "indicator_id": str(indicator_id),
            "group_rule_id": str(group_rule_id),
            "description": "E2E test alert for pauses",
            "image": '{"type": "svg", "content": "<svg>Test</svg>"}',
            "tags": ["e2e", "pause", "test"],
        }

        response = requests.post(f"{base_url}/alerts/detail", json=alert_data)
        assert response.status_code == 200, (
            f"Не удалось создать алерт: {response.text}"
        )

        # Находим созданный алерт по имени
        search_response = requests.get(
            f"{base_url}/alerts/search",
            params={"query": alert_data["alert_name"], "limit": 10},
        )
        assert search_response.status_code == 200
        search_data = search_response.json()

        for alert in search_data.get("alerts", []):
            if alert.get("alert_name") == alert_data["alert_name"]:
                return UUID(alert["alert_id"])

        pytest.fail("Созданный алерт не найден в поиске")

    def _get_current_time_with_tz(self) -> datetime:
        """Получить текущее время с таймзоной +03:00."""
        return datetime.now(timezone(timedelta(hours=3)))

    def _check_alert_paused(self, base_url: str, alert_id: UUID) -> bool:
        """Проверить, находится ли алерт на паузе."""
        # Используем endpoint для получения активных пауз - это самый надежный способ
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "active", "limit": 1},
        )
        if pauses_response.status_code == 200:
            pauses_data = pauses_response.json()
            # Если есть хотя бы одна активная пауза, алерт на паузе
            return len(pauses_data.get("pauses", [])) > 0

        # Fallback на детали алерта
        detail_response = requests.get(
            f"{base_url}/alerts/detail", params={"alert_id": str(alert_id)}
        )
        if detail_response.status_code == 200:
            alert_data = detail_response.json()
            return alert_data.get("paused", False)

        # Fallback на поиск, если детали недоступны
        search_response = requests.get(
            f"{base_url}/alerts/search", params={"query": "", "limit": 1000}
        )
        if search_response.status_code == 200:
            data = search_response.json()
            for alert in data.get("alerts", []):
                if UUID(alert["alert_id"]) == alert_id:
                    return alert.get("paused", False)
        return False

    def test_full_pauses_lifecycle(self, base_url, cleanup_data):
        """
        Полный E2E тест жизненного цикла пауз алерта.
        Проверяет все способы установки и снятия пауз с учетом текущего дня.
        """
        test_user = "e2e_test_user"
        now = self._get_current_time_with_tz()

        # ====================================================================
        # ШАГ 1: Создание тестового алерта
        # ====================================================================
        alert_id = self._create_test_alert(base_url)
        assert alert_id is not None, "Не удалось создать тестовый алерт"
        cleanup_data["alert_id"] = alert_id

        # Проверяем, что алерт создан и не на паузе
        assert not self._check_alert_paused(base_url, alert_id), (
            "Алерт не должен быть на паузе после создания"
        )

        # ====================================================================
        # ШАГ 2: PATCH /alerts/pause - безусловная пауза (toggle)
        # ====================================================================
        # 2.1: Установка паузы (когда алерт не на паузе)
        toggle_data = {"alert_id": str(alert_id), "login": test_user}
        response = requests.patch(f"{base_url}/alerts/pause", json=toggle_data)
        assert response.status_code == 200, (
            f"Не удалось установить паузу: {response.text}"
        )
        assert response.json() is True

        # Небольшая задержка для обновления БД и фиксации транзакции
        time.sleep(0.2)

        # Проверяем, что алерт на паузе (используем endpoint пауз для надежности)
        assert self._check_alert_paused(base_url, alert_id), (
            "Алерт должен быть на паузе после toggle"
        )

        # 2.2: Снятие паузы (когда алерт на паузе)
        response = requests.patch(f"{base_url}/alerts/pause", json=toggle_data)
        assert response.status_code == 200, (
            f"Не удалось снять паузу: {response.text}"
        )
        assert response.json() is True

        # Небольшая задержка для обновления БД и фиксации транзакции
        time.sleep(0.2)

        # Проверяем, что алерт не на паузе
        assert not self._check_alert_paused(base_url, alert_id), (
            "Алерт не должен быть на паузе после toggle"
        )

        # ====================================================================
        # ШАГ 3: POST /alerts/{alert_id}/pause/schedule - условная пауза
        # ====================================================================
        # 3.1: Бессрочная пауза (без end_time)
        schedule_data_indefinite = {"login": test_user}
        response = requests.post(
            f"{base_url}/alerts/{alert_id}/pause/schedule",
            json=schedule_data_indefinite,
        )
        assert response.status_code == 200, (
            f"Не удалось создать бессрочную паузу: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что алерт на паузе
        assert self._check_alert_paused(base_url, alert_id), (
            "Алерт должен быть на паузе (бессрочная)"
        )

        # Получаем ID созданной паузы
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        assert pauses_response.status_code == 200
        pauses_data = pauses_response.json()
        assert len(pauses_data.get("pauses", [])) > 0, (
            "Должна быть активная пауза"
        )
        indefinite_pause_id = pauses_data["pauses"][0]["pause_id"]
        cleanup_data["pause_ids"].append(indefinite_pause_id)

        # 3.2: Снимаем бессрочную паузу через PATCH /pause/stop
        stop_data = {"login": test_user}
        response = requests.patch(
            f"{base_url}/alerts/{alert_id}/pause/stop", json=stop_data
        )
        assert response.status_code == 200, (
            f"Не удалось остановить паузу: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что алерт не на паузе
        assert not self._check_alert_paused(base_url, alert_id), (
            "Алерт не должен быть на паузе после stop"
        )

        # 3.3: Пауза с указанными датами (в будущем)
        future_start = now + timedelta(hours=1)
        future_end = now + timedelta(hours=3)
        schedule_data_future = {
            "login": test_user,
            "start_time": future_start.isoformat(),
            "end_time": future_end.isoformat(),
        }
        response = requests.post(
            f"{base_url}/alerts/{alert_id}/pause/schedule",
            json=schedule_data_future,
        )
        assert response.status_code == 200, (
            f"Не удалось создать будущую паузу: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что алерт НЕ на паузе (пауза в будущем)
        assert not self._check_alert_paused(base_url, alert_id), (
            "Алерт не должен быть на паузе (пауза в будущем)"
        )

        # Получаем ID будущей паузы
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "future"},
        )
        assert pauses_response.status_code == 200
        pauses_data = pauses_response.json()
        assert len(pauses_data.get("pauses", [])) > 0, (
            "Должна быть будущая пауза"
        )
        future_pause_id = pauses_data["pauses"][0]["pause_id"]
        cleanup_data["pause_ids"].append(future_pause_id)

        # 3.4: Пауза в прошлом (для тестирования фильтрации)
        past_start = now - timedelta(hours=3)
        past_end = now - timedelta(hours=1)
        schedule_data_past = {
            "login": test_user,
            "start_time": past_start.isoformat(),
            "end_time": past_end.isoformat(),
        }
        response = requests.post(
            f"{base_url}/alerts/{alert_id}/pause/schedule",
            json=schedule_data_past,
        )
        assert response.status_code == 200, (
            f"Не удалось создать прошлую паузу: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что алерт не на паузе (пауза в прошлом)
        assert not self._check_alert_paused(base_url, alert_id), (
            "Алерт не должен быть на паузе (пауза в прошлом)"
        )

        # Получаем ID прошлой паузы
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "past"},
        )
        assert pauses_response.status_code == 200
        pauses_data = pauses_response.json()
        assert len(pauses_data.get("pauses", [])) > 0, (
            "Должна быть прошлая пауза"
        )
        past_pause_id = pauses_data["pauses"][0]["pause_id"]
        cleanup_data["pause_ids"].append(past_pause_id)

        # 3.5: Активная пауза (начинается сейчас, заканчивается через час)
        active_start = now - timedelta(minutes=5)  # Началась 5 минут назад
        active_end = now + timedelta(hours=1)  # Закончится через час
        schedule_data_active = {
            "login": test_user,
            "start_time": active_start.isoformat(),
            "end_time": active_end.isoformat(),
        }
        response = requests.post(
            f"{base_url}/alerts/{alert_id}/pause/schedule",
            json=schedule_data_active,
        )
        assert response.status_code == 200, (
            f"Не удалось создать активную паузу: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что алерт на паузе
        assert self._check_alert_paused(base_url, alert_id), (
            "Алерт должен быть на паузе (активная пауза)"
        )

        # Получаем ID активной паузы
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        assert pauses_response.status_code == 200
        pauses_data = pauses_response.json()
        assert len(pauses_data.get("pauses", [])) > 0, (
            "Должна быть активная пауза"
        )
        active_pause_id = pauses_data["pauses"][0]["pause_id"]
        cleanup_data["pause_ids"].append(active_pause_id)

        # ====================================================================
        # ШАГ 4: PATCH /alerts/{alert_id}/pause/{pause_id} - изменение паузы
        # ====================================================================
        # 4.1: Изменение start_time активной паузы
        new_start = now - timedelta(minutes=10)  # Началась 10 минут назад
        update_data_start = {
            "login": test_user,
            "start_time": new_start.isoformat(),
        }
        response = requests.patch(
            f"{base_url}/alerts/{alert_id}/pause/{active_pause_id}",
            json=update_data_start,
        )
        assert response.status_code == 200, (
            f"Не удалось изменить start_time: {response.text}"
        )
        assert response.json() is True

        # 4.2: Изменение end_time активной паузы
        new_end = now + timedelta(hours=2)  # Закончится через 2 часа
        update_data_end = {"login": test_user, "end_time": new_end.isoformat()}
        response = requests.patch(
            f"{base_url}/alerts/{alert_id}/pause/{active_pause_id}",
            json=update_data_end,
        )
        assert response.status_code == 200, (
            f"Не удалось изменить end_time: {response.text}"
        )
        assert response.json() is True

        # 4.3: Сделать паузу бессрочной (пустая строка для end_time)
        update_data_indefinite = {"login": test_user, "end_time": ""}
        response = requests.patch(
            f"{base_url}/alerts/{alert_id}/pause/{active_pause_id}",
            json=update_data_indefinite,
        )
        assert response.status_code == 200, (
            f"Не удалось сделать паузу бессрочной: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что пауза стала бессрочной
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        assert pauses_response.status_code == 200
        pauses_data = pauses_response.json()
        updated_pause = next(
            (
                p
                for p in pauses_data.get("pauses", [])
                if p["pause_id"] == active_pause_id
            ),
            None,
        )
        assert updated_pause is not None, "Пауза должна быть найдена"
        assert updated_pause.get("end_time") is None, (
            "Пауза должна быть бессрочной (end_time = NULL)"
        )

        # ====================================================================
        # ШАГ 5: PATCH /alerts/{alert_id}/pause/{pause_id}/stop - остановка конкретной паузы
        # ====================================================================
        # 5.1: Остановка активной бессрочной паузы
        response = requests.patch(
            f"{base_url}/alerts/{alert_id}/pause/{active_pause_id}/stop",
            json=stop_data,
        )
        assert response.status_code == 200, (
            f"Не удалось остановить конкретную паузу: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что алерт не на паузе
        assert not self._check_alert_paused(base_url, alert_id), (
            "Алерт не должен быть на паузе после остановки"
        )

        # 5.2: Остановка будущей паузы (end_time = start_time)
        response = requests.patch(
            f"{base_url}/alerts/{alert_id}/pause/{future_pause_id}/stop",
            json=stop_data,
        )
        assert response.status_code == 200, (
            f"Не удалось остановить будущую паузу: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что будущая пауза остановлена
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        assert pauses_response.status_code == 200
        pauses_data = pauses_response.json()
        stopped_future_pause = next(
            (
                p
                for p in pauses_data.get("pauses", [])
                if p["pause_id"] == future_pause_id
            ),
            None,
        )
        assert stopped_future_pause is not None, (
            "Будущая пауза должна быть найдена"
        )
        assert stopped_future_pause.get("end_time") is not None, (
            "Будущая пауза должна быть остановлена (end_time установлен)"
        )

        # 5.3: Попытка остановить прошлую паузу (должна вернуть 400)
        response = requests.patch(
            f"{base_url}/alerts/{alert_id}/pause/{past_pause_id}/stop",
            json=stop_data,
        )
        assert response.status_code == 400, (
            "Остановка прошлой паузы должна вернуть 400"
        )

        # ====================================================================
        # ШАГ 6: GET /alerts/{alert_id}/pause - получение истории пауз
        # ====================================================================
        # 6.1: Получение всех пауз
        response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        assert response.status_code == 200
        all_pauses_data = response.json()
        assert "pauses" in all_pauses_data
        assert "total" in all_pauses_data
        assert all_pauses_data["total"] >= len(cleanup_data["pause_ids"]), (
            "Должно быть минимум столько пауз, сколько мы создали"
        )

        # 6.2: Получение активных пауз
        response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        assert response.status_code == 200
        active_pauses_data = response.json()
        assert "pauses" in active_pauses_data
        # После всех операций активных пауз быть не должно
        assert len(active_pauses_data.get("pauses", [])) == 0, (
            "Активных пауз быть не должно"
        )

        # 6.3: Получение будущих пауз
        response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "future"},
        )
        assert response.status_code == 200
        future_pauses_data = response.json()
        assert "pauses" in future_pauses_data
        # Будущая пауза была остановлена, поэтому будущих пауз быть не должно
        assert len(future_pauses_data.get("pauses", [])) == 0, (
            "Будущих пауз быть не должно (была остановлена)"
        )

        # 6.4: Получение прошлых пауз
        response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "past"},
        )
        assert response.status_code == 200
        past_pauses_data = response.json()
        assert "pauses" in past_pauses_data
        assert len(past_pauses_data.get("pauses", [])) >= 1, (
            "Должна быть минимум одна прошлая пауза"
        )

        # 6.5: Сортировка и пагинация
        response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
                "limit": 10,
                "offset": 0,
            },
        )
        assert response.status_code == 200
        sorted_pauses_data = response.json()
        assert "pauses" in sorted_pauses_data

        # Проверяем сортировку (если есть минимум 2 паузы)
        if len(sorted_pauses_data.get("pauses", [])) >= 2:
            pauses_list = sorted_pauses_data["pauses"]
            for i in range(len(pauses_list) - 1):
                current_start = datetime.fromisoformat(
                    pauses_list[i]["start_time"].replace("Z", "+00:00")
                )
                next_start = datetime.fromisoformat(
                    pauses_list[i + 1]["start_time"].replace("Z", "+00:00")
                )
                assert current_start >= next_start, (
                    "Паузы должны быть отсортированы по start_time DESC"
                )

        # ====================================================================
        # ШАГ 7: DELETE /alerts/{alert_id}/pause/{pause_id} - удаление пауз
        # ====================================================================
        # Удаляем все созданные паузы
        # Создаем копию списка, так как будем удалять элементы во время итерации
        pause_ids_to_delete = list(cleanup_data["pause_ids"])
        for pause_id in pause_ids_to_delete:
            response = requests.delete(
                f"{base_url}/alerts/{alert_id}/pause/{pause_id}"
            )
            # Если пауза уже удалена или не найдена (404), это нормально - пропускаем
            if response.status_code == 404:
                # Пауза уже была удалена, убираем из cleanup_data
                if pause_id in cleanup_data["pause_ids"]:
                    cleanup_data["pause_ids"].remove(pause_id)
                continue
            assert response.status_code == 200, (
                f"Не удалось удалить паузу {pause_id}: {response.text}"
            )
            assert response.json() is True
            # Убираем удаленную паузу из cleanup_data, чтобы cleanup не пытался удалить ее снова
            if pause_id in cleanup_data["pause_ids"]:
                cleanup_data["pause_ids"].remove(pause_id)

        # Проверяем, что все паузы удалены
        response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        assert response.status_code == 200
        remaining_pauses_data = response.json()
        # Могут остаться паузы, созданные через toggle, но наши должны быть удалены
        remaining_pause_ids = {
            p["pause_id"] for p in remaining_pauses_data.get("pauses", [])
        }
        for pause_id in pause_ids_to_delete:
            if pause_id in remaining_pause_ids:
                # Проверяем только те паузы, которые мы пытались удалить
                assert pause_id not in remaining_pause_ids, (
                    f"Пауза {pause_id} должна быть удалена"
                )

        # ====================================================================
        # ШАГ 8: Удаление алерта (каскадное удаление всех оставшихся пауз)
        # ====================================================================
        response = requests.delete(
            f"{base_url}/alerts/detail", params={"alert_id": str(alert_id)}
        )
        assert response.status_code == 200, (
            f"Не удалось удалить алерт: {response.text}"
        )
        assert response.json() is True

        # Проверяем, что алерт удален
        get_response = requests.get(
            f"{base_url}/alerts/detail", params={"alert_id": str(alert_id)}
        )
        assert get_response.status_code == 404, "Алерт должен быть удален"

        # Проверяем, что паузы тоже удалены (каскадное удаление)
        pauses_response = requests.get(
            f"{base_url}/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        assert pauses_response.status_code == 404, (
            "После удаления алерта паузы тоже должны быть недоступны (404)"
        )
