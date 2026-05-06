"""
E2E тест: Полный жизненный цикл скриншотов.
Проверяет создание, поиск, обновление и удаление скриншотов.
"""

import json
from uuid import uuid4

import pytest
import requests

# Примечание: прокси отключен в conftest.py


class TestScreenshotsLifecycle:
    """E2E тест полного жизненного цикла скриншотов."""

    @pytest.fixture
    def base_url(self):
        """Базовый URL API."""
        return "http://localhost:8888/alerts/api/v1"

    # Примечание: cleanup_data определена в conftest.py

    def test_full_screenshots_lifecycle(self, base_url, cleanup_data):
        """
        Полный E2E тест жизненного цикла скриншотов.
        Проверяет создание, поиск, обновление и удаление скриншотов.
        """
        # ====================================================================
        # ШАГ 1: POST /screenshots - создание скриншотов с разными форматами
        # ====================================================================

        # 1.1: Создание скриншота с JSON объектом
        screenshot_data_object = {
            "name": f"E2E Test Screenshot Object {uuid4().hex[:8]}",
            "description": f"E2E test description for object screenshot {uuid4().hex[:8]}",
            "image_data": json.dumps(
                {
                    "url": "https://example.com/image.png",
                    "width": 1920,
                    "height": 1080,
                    "format": "png",
                }
            ),
        }

        create_object_response = requests.post(
            f"{base_url}/screenshots", json=screenshot_data_object
        )
        assert create_object_response.status_code == 200, (
            f"Не удалось создать скриншот с объектом: {create_object_response.text}"
        )
        screenshot_object_id = create_object_response.json()["screenshot_id"]
        assert screenshot_object_id is not None
        cleanup_data["screenshot_id"] = (
            screenshot_object_id  # Сохраняем для cleanup
        )

        # 1.2: Создание скриншота с JSON массивом
        screenshot_data_array = {
            "name": f"E2E Test Screenshot Array {uuid4().hex[:8]}",
            "description": f"E2E test description for array screenshot {uuid4().hex[:8]}",
            "image_data": json.dumps(
                [
                    "https://example.com/image1.png",
                    "https://example.com/image2.png",
                    "https://example.com/image3.png",
                ]
            ),
        }

        create_array_response = requests.post(
            f"{base_url}/screenshots", json=screenshot_data_array
        )
        assert create_array_response.status_code == 200, (
            f"Не удалось создать скриншот с массивом: {create_array_response.text}"
        )
        screenshot_array_id = create_array_response.json()["screenshot_id"]
        assert screenshot_array_id is not None

        # 1.3: Создание скриншота с простым описанием для поиска
        screenshot_data_search = {
            "name": f"E2E Search Test {uuid4().hex[:8]}",
            "description": f"Unique search term E2E_TEST_{uuid4().hex[:8]}",
            "image_data": json.dumps(
                {"url": "https://example.com/search-test.png"}
            ),
        }

        create_search_response = requests.post(
            f"{base_url}/screenshots", json=screenshot_data_search
        )
        assert create_search_response.status_code == 200, (
            f"Не удалось создать скриншот для поиска: {create_search_response.text}"
        )
        screenshot_search_id = create_search_response.json()["screenshot_id"]
        assert screenshot_search_id is not None

        # ====================================================================
        # ШАГ 2: GET /screenshots/{screenshot_id} - получение скриншотов по ID
        # ====================================================================

        # 2.1: Получение скриншота с объектом
        get_object_response = requests.get(
            f"{base_url}/screenshots/{screenshot_object_id}"
        )
        assert get_object_response.status_code == 200, (
            f"Не удалось получить скриншот: {get_object_response.text}"
        )
        object_data = get_object_response.json()
        assert object_data["screenshot_id"] == screenshot_object_id
        assert object_data["name"] == screenshot_data_object["name"]
        assert (
            object_data["description"] == screenshot_data_object["description"]
        )
        # Проверяем что image_data - валидный JSON
        parsed_image_data = json.loads(object_data["image_data"])
        assert isinstance(parsed_image_data, dict)
        assert parsed_image_data["url"] == "https://example.com/image.png"

        # 2.2: Получение скриншота с массивом
        get_array_response = requests.get(
            f"{base_url}/screenshots/{screenshot_array_id}"
        )
        assert get_array_response.status_code == 200
        array_data = get_array_response.json()
        assert array_data["screenshot_id"] == screenshot_array_id
        parsed_array_image_data = json.loads(array_data["image_data"])
        assert isinstance(parsed_array_image_data, list)
        assert len(parsed_array_image_data) == 3

        # ====================================================================
        # ШАГ 3: GET /screenshots/search - поиск скриншотов
        # ====================================================================

        # 3.1: Поиск без параметров (получить все)
        search_all_response = requests.get(
            f"{base_url}/screenshots/search", params={"limit": 100}
        )
        assert search_all_response.status_code == 200
        search_all_data = search_all_response.json()
        assert "screenshots" in search_all_data
        assert "total" in search_all_data
        assert "limit" in search_all_data
        assert "offset" in search_all_data
        assert isinstance(search_all_data["screenshots"], list)

        # Проверяем что наши скриншоты есть в списке
        all_screenshot_ids = {
            s["screenshot_id"] for s in search_all_data["screenshots"]
        }
        assert screenshot_object_id in all_screenshot_ids, (
            "Скриншот с объектом должен быть в списке"
        )
        assert screenshot_array_id in all_screenshot_ids, (
            "Скриншот с массивом должен быть в списке"
        )
        assert screenshot_search_id in all_screenshot_ids, (
            "Скриншот для поиска должен быть в списке"
        )

        # 3.2: Поиск по описанию
        search_query = screenshot_data_search["description"][
            :10
        ]  # Берем часть описания
        search_query_response = requests.get(
            f"{base_url}/screenshots/search",
            params={"query": search_query, "limit": 100},
        )
        assert search_query_response.status_code == 200
        search_query_data = search_query_response.json()
        assert "screenshots" in search_query_data
        # Проверяем что наш скриншот найден
        found_screenshot_ids = {
            s["screenshot_id"] for s in search_query_data["screenshots"]
        }
        assert screenshot_search_id in found_screenshot_ids, (
            f"Скриншот должен быть найден по запросу '{search_query}'"
        )

        # 3.3: Поиск с сортировкой по name (desc)
        search_sorted_response = requests.get(
            f"{base_url}/screenshots/search",
            params={"order_by": "name", "order_dir": "desc", "limit": 100},
        )
        assert search_sorted_response.status_code == 200
        search_sorted_data = search_sorted_response.json()
        assert "screenshots" in search_sorted_data

        # Проверяем сортировку (если есть минимум 2 скриншота)
        if len(search_sorted_data["screenshots"]) >= 2:
            screenshots_list = search_sorted_data["screenshots"]
            for i in range(len(screenshots_list) - 1):
                assert (
                    screenshots_list[i]["name"]
                    >= screenshots_list[i + 1]["name"]
                ), "Скриншоты должны быть отсортированы по name DESC"

        # 3.4: Пагинация
        page1_response = requests.get(
            f"{base_url}/screenshots/search", params={"limit": 2, "offset": 0}
        )
        assert page1_response.status_code == 200
        page1_data = page1_response.json()

        if page1_data.get("total", 0) > 2:
            page2_response = requests.get(
                f"{base_url}/screenshots/search",
                params={"limit": 2, "offset": 2},
            )
            assert page2_response.status_code == 200
            page2_data = page2_response.json()

            # Проверяем что результаты разные
            page1_ids = {s["screenshot_id"] for s in page1_data["screenshots"]}
            page2_ids = {s["screenshot_id"] for s in page2_data["screenshots"]}
            assert page1_ids != page2_ids, (
                "Пагинация должна возвращать разные результаты"
            )

        # ====================================================================
        # ШАГ 4: PATCH /screenshots/{screenshot_id} - обновление скриншотов
        # ====================================================================

        # 4.1: Обновление имени и описания
        update_name_desc_data = {
            "name": f"Updated {screenshot_data_object['name']}",
            "description": f"Updated description {uuid4().hex[:8]}",
        }

        update_name_desc_response = requests.patch(
            f"{base_url}/screenshots/{screenshot_object_id}",
            json=update_name_desc_data,
        )
        assert update_name_desc_response.status_code == 200, (
            f"Не удалось обновить имя и описание: {update_name_desc_response.text}"
        )
        assert update_name_desc_response.json() is True

        # Проверяем обновление
        get_updated_response = requests.get(
            f"{base_url}/screenshots/{screenshot_object_id}"
        )
        assert get_updated_response.status_code == 200
        updated_data = get_updated_response.json()
        assert updated_data["name"] == update_name_desc_data["name"]
        assert (
            updated_data["description"] == update_name_desc_data["description"]
        )
        # image_data не должен измениться
        assert (
            updated_data["image_data"] == screenshot_data_object["image_data"]
        )

        # 4.2: Обновление только image_data
        new_image_data = json.dumps(
            {
                "url": "https://updated.example.com/new-image.png",
                "width": 2560,
                "height": 1440,
                "format": "jpg",
                "updated": True,
            }
        )

        update_image_response = requests.patch(
            f"{base_url}/screenshots/{screenshot_object_id}",
            json={"image_data": new_image_data},
        )
        assert update_image_response.status_code == 200, (
            f"Не удалось обновить image_data: {update_image_response.text}"
        )
        assert update_image_response.json() is True

        # Проверяем обновление image_data
        get_image_updated_response = requests.get(
            f"{base_url}/screenshots/{screenshot_object_id}"
        )
        assert get_image_updated_response.status_code == 200
        image_updated_data = get_image_updated_response.json()
        parsed_new_image = json.loads(image_updated_data["image_data"])
        assert (
            parsed_new_image["url"]
            == "https://updated.example.com/new-image.png"
        )
        assert parsed_new_image["width"] == 2560

        # 4.3: Обновление всех полей одновременно
        update_all_data = {
            "name": f"Fully Updated {uuid4().hex[:8]}",
            "description": f"Fully updated description {uuid4().hex[:8]}",
            "image_data": json.dumps({"final": "update", "version": 2}),
        }

        update_all_response = requests.patch(
            f"{base_url}/screenshots/{screenshot_object_id}",
            json=update_all_data,
        )
        assert update_all_response.status_code == 200, (
            f"Не удалось обновить все поля: {update_all_response.text}"
        )
        assert update_all_response.json() is True

        # Проверяем обновление всех полей
        get_all_updated_response = requests.get(
            f"{base_url}/screenshots/{screenshot_object_id}"
        )
        assert get_all_updated_response.status_code == 200
        all_updated_data = get_all_updated_response.json()
        assert all_updated_data["name"] == update_all_data["name"]
        assert (
            all_updated_data["description"] == update_all_data["description"]
        )
        assert all_updated_data["image_data"] == update_all_data["image_data"]

        # ====================================================================
        # ШАГ 5: DELETE /screenshots/{screenshot_id} - удаление скриншотов
        # ====================================================================

        # 5.1: Удаление скриншота с массивом
        delete_array_response = requests.delete(
            f"{base_url}/screenshots/{screenshot_array_id}"
        )
        assert delete_array_response.status_code == 200, (
            f"Не удалось удалить скриншот с массивом: {delete_array_response.text}"
        )
        assert delete_array_response.json() is True

        # Проверяем что скриншот удален
        get_deleted_array_response = requests.get(
            f"{base_url}/screenshots/{screenshot_array_id}"
        )
        assert get_deleted_array_response.status_code == 404, (
            "Скриншот должен быть удален"
        )

        # 5.2: Удаление скриншота для поиска
        delete_search_response = requests.delete(
            f"{base_url}/screenshots/{screenshot_search_id}"
        )
        assert delete_search_response.status_code == 200, (
            f"Не удалось удалить скриншот для поиска: {delete_search_response.text}"
        )
        assert delete_search_response.json() is True

        # Проверяем что скриншот удален
        get_deleted_search_response = requests.get(
            f"{base_url}/screenshots/{screenshot_search_id}"
        )
        assert get_deleted_search_response.status_code == 404, (
            "Скриншот должен быть удален"
        )

        # 5.3: Проверяем что удаленные скриншоты не появляются в поиске
        search_after_delete_response = requests.get(
            f"{base_url}/screenshots/search", params={"limit": 1000}
        )
        assert search_after_delete_response.status_code == 200
        search_after_delete_data = search_after_delete_response.json()
        remaining_screenshot_ids = {
            s["screenshot_id"] for s in search_after_delete_data["screenshots"]
        }
        assert screenshot_array_id not in remaining_screenshot_ids, (
            "Удаленный скриншот с массивом не должен быть в поиске"
        )
        assert screenshot_search_id not in remaining_screenshot_ids, (
            "Удаленный скриншот для поиска не должен быть в поиске"
        )

        # 5.4: Основной скриншот остается (будет удален в cleanup)
        get_main_response = requests.get(
            f"{base_url}/screenshots/{screenshot_object_id}"
        )
        assert get_main_response.status_code == 200, (
            "Основной скриншот должен остаться"
        )

        # ====================================================================
        # ШАГ 6: Проверка обработки ошибок
        # ====================================================================

        # 6.1: Получение несуществующего скриншота
        fake_id = str(uuid4())
        get_fake_response = requests.get(f"{base_url}/screenshots/{fake_id}")
        assert get_fake_response.status_code == 404, (
            "Несуществующий скриншот должен вернуть 404"
        )

        # 6.2: Обновление несуществующего скриншота
        update_fake_response = requests.patch(
            f"{base_url}/screenshots/{fake_id}", json={"name": "Updated"}
        )
        assert update_fake_response.status_code == 404, (
            "Обновление несуществующего скриншота должно вернуть 404"
        )

        # 6.3: Удаление несуществующего скриншота
        delete_fake_response = requests.delete(
            f"{base_url}/screenshots/{fake_id}"
        )
        assert delete_fake_response.status_code == 404, (
            "Удаление несуществующего скриншота должно вернуть 404"
        )

        # 6.4: Создание скриншота с невалидным JSON в image_data
        invalid_json_data = {
            "name": f"Invalid JSON Test {uuid4().hex[:8]}",
            "description": f"Test invalid JSON {uuid4().hex[:8]}",
            "image_data": "not a valid json {",
        }

        create_invalid_response = requests.post(
            f"{base_url}/screenshots", json=invalid_json_data
        )
        assert create_invalid_response.status_code >= 400, (
            "Создание скриншота с невалидным JSON должно вернуть ошибку"
        )
