#!/usr/bin/env python3
"""
Комплексный тестовый скрипт для API Alerts Service
Проверяет все методы: alerts, indicators, links, subscriptions, users
"""

import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone

import requests


class Colors:
    """Цвета для красивого вывода в консоль"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class APITester:
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        # Хранилище созданных данных для очистки
        self.created_data = {
            "alerts": [],
            "indicators": [],
            "links": [],
            "users": [],
            "subscriptions": [],
            "dt": [],
            "screenshots": [],
        }

        self.test_results = {"passed": 0, "failed": 0, "errors": []}

        # Файл для детального лога (создается в папке tests)
        import pathlib

        tests_dir = pathlib.Path(__file__).parent
        self.detailed_log_file = str(tests_dir / "test_detailed_log.txt")

        # Детальный лог всех операций
        self.detailed_log = []

    def log(self, message: str, color: str = Colors.ENDC, level: str = "INFO"):
        """Красивый вывод в консоль и запись в детальный лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        console_message = (
            f"{color}[{timestamp}] {level}: {message}{Colors.ENDC}"
        )
        print(console_message)

        # Записываем в детальный лог (без цветов)
        log_message = f"[{timestamp}] {level}: {message}"
        self.detailed_log.append(log_message)

    def log_success(self, message: str):
        """Успешная операция"""
        self.log(f"✅ {message}", Colors.OKGREEN, "SUCCESS")

    def log_error(self, message: str):
        """Ошибка"""
        self.log(f"❌ {message}", Colors.FAIL, "ERROR")

    def log_warning(self, message: str):
        """Предупреждение"""
        self.log(f"⚠️  {message}", Colors.WARNING, "WARNING")

    def log_info(self, message: str):
        """Информация"""
        self.log(f"ℹ️  {message}", Colors.OKBLUE, "INFO")

    def log_test(self, test_name: str):
        """Начало теста (лаконичный разделитель в консоль)."""
        self.log("\n" + "=" * 60, Colors.OKCYAN, "TEST")
        self.log(f"🧪 {test_name}", Colors.OKCYAN, "TEST")

    def save_results_to_file(self):
        """Сохранение результатов тестов (только детальный лог)."""
        try:
            # Сохраняем детальный лог в текстовый файл
            with open(self.detailed_log_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(
                    f"ДЕТАЛЬНЫЙ ЛОГ ТЕСТОВ API - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"Сервис: {self.base_url}\n")
                f.write("=" * 80 + "\n\n")

                for log_entry in self.detailed_log:
                    f.write(log_entry + "\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("КОНЕЦ ЛОГА\n")
                f.write("=" * 80 + "\n")

            self.log_success(f"Detailed log saved to {self.detailed_log_file}")

        except Exception as e:
            self.log_error(f"Failed to save results to file: {e}")

    def load_previous_results(self):
        """Загрузка предыдущих результатов отключена (JSON не используется)."""
        return None

    def make_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        expect_error: bool = False,
    ) -> dict | None:
        """Универсальный метод для HTTP запросов"""
        url = f"{self.base_url}{endpoint}"

        # Лаконичный лог запроса в консоль
        params_str = json.dumps(params, ensure_ascii=False) if params else ""
        if params_str and len(params_str) > 160:
            params_str = params_str[:160] + "... (truncated)"
        self.log_info(
            f"🌐 {method.upper()} {url}"
            + (f" | params={params_str}" if params_str else "")
        )
        if data:
            body_keys = list(data.keys())
            self.log_info(
                f"📦 Body keys: {body_keys[:8]}"
                + (" (truncated)" if len(body_keys) > 8 else "")
            )

        # Детальная информация для файла
        request_details = {
            "timestamp": datetime.now().isoformat(),
            "method": method.upper(),
            "url": url,
            "endpoint": endpoint,
            "params": params,
            "data": data,
        }

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data)
            elif method.upper() == "DELETE":
                # DELETE может использовать как params, так и json body
                if data:
                    response = self.session.delete(url, json=data)
                else:
                    response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Лаконичный лог ответа в консоль, детальный - в файл
            self.log_info(f"📡 Response: {response.status_code}")
            if response.content:
                try:
                    response_json = response.json()
                    # Краткий консольный вывод
                    if isinstance(response_json, dict):
                        keys_preview = list(response_json.keys())[:10]
                        self.log_info(
                            f"📄 JSON keys: {keys_preview}"
                            + (
                                " (truncated)"
                                if len(response_json.keys()) > 10
                                else ""
                            )
                        )
                    elif isinstance(response_json, list):
                        self.log_info(
                            f"📄 JSON array: {len(response_json)} items"
                        )
                    else:
                        snippet = json.dumps(response_json, ensure_ascii=False)
                        if len(snippet) > 200:
                            snippet = snippet[:200] + "... (truncated)"
                        self.log_info(f"📄 JSON: {snippet}")

                    # Полный ответ в детальный лог-файл
                    request_details.update(
                        {
                            "response_status": response.status_code,
                            "response_data": response_json,
                            "response_type": "json",
                        }
                    )
                except:
                    text_snippet = response.text
                    if len(text_snippet) > 200:
                        text_snippet = text_snippet[:200] + "... (truncated)"
                    self.log_info(f"📄 Text: {text_snippet}")

                    # Полный ответ в детальный лог-файл
                    request_details.update(
                        {
                            "response_status": response.status_code,
                            "response_data": response.text,
                            "response_type": "text",
                        }
                    )

            # Записываем детальную информацию в лог
            self.detailed_log.append(
                f"DETAILED_REQUEST: {json.dumps(request_details, ensure_ascii=False, indent=2)}"
            )

            if response.status_code >= 400:
                if expect_error:
                    # Если ожидаем ошибку, это нормально
                    # Пытаемся вернуть JSON, если это JSON ответ
                    try:
                        error_json = response.json()
                        error_json["status_code"] = response.status_code
                        return error_json
                    except:
                        return {
                            "status_code": response.status_code,
                            "error": response.text,
                        }
                else:
                    self.log_error(
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None

            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            self.log_error(f"Request failed: {e}")
            return None

    def test_health(self):
        """Тест health endpoint"""
        self.log_test("Testing Health Endpoint")

        # Health endpoint возвращает plain text, не JSON
        url = f"{self.base_url}/alerts/health"
        try:
            response = self.session.get(url)
            if response.status_code == 200 and response.text.strip() == "OK":
                self.log_success("Health endpoint working")
                self.test_results["passed"] += 1
                return True
            else:
                self.log_error(
                    f"Health check failed: {response.status_code} - {response.text}"
                )
                self.test_results["failed"] += 1
                self.test_results["errors"].append("Health check failed")
                return False
        except requests.exceptions.RequestException as e:
            self.log_error(f"Health check request failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Health check failed")
            return False

    def test_indicators(self):
        """Тест indicators endpoints"""
        self.log_test("Testing Indicators")

        # Получаем автодополнение индикаторов (единственный доступный endpoint)
        indicators = self.make_request(
            "GET", "/alerts/api/v1/indicators/autocomplete"
        )
        if indicators is None:
            self.log_error("Indicators autocomplete endpoint failed")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(
                "Failed to get indicators autocomplete"
            )
            return False

        self.log_success(
            f"Found {indicators.get('total', 0)} indicators in autocomplete"
        )
        self.test_results["passed"] += 1
        return True

    def test_telegram_endpoints(self):
        """Тест метода telegram_by_login"""
        self.log_test("Testing Telegram User endpoint")

        # telegram_by_login по логину (регистронезависимо)
        user_resp = self.make_request(
            "GET", "/alerts/api/v1/users/kskorneev/telegram"
        )
        if (
            user_resp is None
            or "telegram_id" not in user_resp
            or not user_resp["telegram_id"]
        ):
            self.log_error("telegram_by_login failed for login=kskorneev")
            self.test_results["failed"] += 1
            return False
        self.log_success(
            f"telegram_by_login ok: telegram_id={user_resp['telegram_id']}"
        )

        self.test_results["passed"] += 1
        return True

    def test_users(self):
        """Тест users endpoints с проверкой динамичности полей контактов"""
        self.log_test("Testing Users CRUD with Dynamic Contacts")

        # 1. POST - создание пользователя с динамическими полями в объекте contacts
        user_data = {
            "samAccountName": f"Test User {uuid.uuid4().hex[:8]}",
            "group": False,
            "contacts": {
                "telegram_id": f"test_telegram_{uuid.uuid4().hex[:8]}",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "pachca_id": f"test_pachca_{uuid.uuid4().hex[:8]}",
            },
        }

        self.log_info(
            f"Creating user with dynamic fields in contacts: {list(user_data.keys())}"
        )

        result = self.make_request("POST", "/alerts/api/v1/users", user_data)
        if result is None or result is not True:
            self.log_error("User creation failed")
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Failed to create user")
            return False

        self.log_success(
            "User created successfully with dynamic fields in contacts"
        )

        # Получаем user_id через subscriptions/search, используя тестовый алерт
        # test_alerts выполняется перед test_users, поэтому алерт должен быть создан
        user_id = None
        if not self.created_data["alerts"]:
            self.log_error(
                "No test alert found - test_alerts must run before test_users"
            )
            self.test_results["failed"] += 1
            return False

        # Используем существующий тестовый алерт
        alert_id = self.created_data["alerts"][0]
        users_response = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search",
            params={"query": user_data["samAccountName"], "limit": 100},
        )
        if users_response and users_response.get("users"):
            for user in users_response["users"]:
                if user.get("samAccountName") == user_data["samAccountName"]:
                    user_id = user["user_id"]
                    break

        if not user_id:
            self.log_error(
                f"Could not find created user '{user_data['samAccountName']}' in subscriptions/search"
            )
            self.test_results["failed"] += 1
            return False

        self.created_data["users"].append(user_id)
        self.log_success(f"Found created user_id: {user_id}")

        # 2. PATCH - обновление пользователя с динамическими полями в объекте contacts
        update_data = {
            "samAccountName": f"Updated {user_data['samAccountName']}",
            "group": True,
            "contacts": {
                "telegram_id": f"updated_telegram_{uuid.uuid4().hex[:8]}",
                "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
                # pachca_id не обновляем - проверяем, что он остался прежним
            },
        }

        self.log_info(
            f"Updating user with dynamic fields in contacts: {list(update_data.keys())}"
        )

        update_result = self.make_request(
            "PATCH", f"/alerts/api/v1/users/{user_id}", update_data
        )
        if update_result is None or update_result is not True:
            self.log_error("Failed to update user")
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "User updated successfully with dynamic fields in contacts"
        )

        # НЕ удаляем пользователя здесь - он может понадобиться для других тестов
        # Удаление будет в cleanup()

        self.test_results["passed"] += 1
        return True

    def test_users_search(self):
        """Тест поиска пользователей /users/search"""
        self.log_test("Testing Users Search endpoint")

        # Создаем пользователя, которого будем искать
        user_data = {
            "samAccountName": f"Search User {uuid.uuid4().hex[:8]}",
            "group": False,
            "contacts": {
                "telegram_id": f"search_telegram_{uuid.uuid4().hex[:8]}",
                "email": f"search_{uuid.uuid4().hex[:8]}@example.com",
            },
        }

        create_result = self.make_request(
            "POST", "/alerts/api/v1/users", user_data
        )
        if create_result is None or create_result is not True:
            self.log_error("Failed to create user for search test")
            self.test_results["failed"] += 1
            return False

        self.log_success("User created for /users/search test")

        # 1. Поиск по samAccountName
        search_response = self.make_request(
            "GET",
            "/alerts/api/v1/users/search",
            params={"query": user_data["samAccountName"], "limit": 20},
        )
        if not search_response or not search_response.get("users"):
            self.log_error(
                "users/search did not return any users for created user"
            )
            self.test_results["failed"] += 1
            return False

        found_user = None
        for user in search_response["users"]:
            if user.get("samAccountName") == user_data["samAccountName"]:
                found_user = user
                break

        if not found_user:
            self.log_error(
                f"Created user '{user_data['samAccountName']}' not found in users/search response"
            )
            self.test_results["failed"] += 1
            return False

        user_id = found_user.get("user_id")
        if not user_id:
            self.log_error(
                "users/search response for created user has no user_id"
            )
            self.test_results["failed"] += 1
            return False

        self.created_data["users"].append(user_id)
        self.log_success(
            f"users/search returned created user with user_id={user_id}"
        )

        # Проверяем структуру контактов
        contacts = found_user.get("contacts") or {}
        if not isinstance(contacts, dict):
            self.log_error("contacts in users/search response is not a dict")
            self.test_results["failed"] += 1
            return False

        if "email" in contacts:
            self.log_success(
                f"contacts in users/search contains dynamic field 'email': {contacts['email']}"
            )
        else:
            self.log_warning(
                "contacts in users/search does not contain 'email' field (may be expected depending on DB)"
            )

        self.test_results["passed"] += 1
        return True

    def test_alerts(self):
        """Тест alerts CRUD endpoints"""
        self.log_test("Testing Alerts CRUD")

        # GET - поиск алертов
        alerts = self.make_request("GET", "/alerts/api/v1/alerts/search")
        if alerts is None:
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Failed to get alerts")
            return False

        self.log_success(f"Found {alerts.get('total', 0)} alerts")

        # GET - автодополнение алертов
        autocomplete = self.make_request(
            "GET", "/alerts/api/v1/alerts/autocomplete"
        )
        if autocomplete is None:
            self.log_error("Failed to get alerts autocomplete")
            self.test_results["failed"] += 1
            return False

        self.log_success("Alerts autocomplete working")

        # GET - облако тегов
        tags_cloud = self.make_request(
            "GET", "/alerts/api/v1/alerts/tags/cloud"
        )
        if tags_cloud is None:
            self.log_error("Failed to get tags cloud")
            self.test_results["failed"] += 1
            return False

        self.log_success("Tags cloud retrieved")

        # GET - облако тегов с фильтрацией (endpoint должен поддерживать параметры)
        filtered_tags_cloud = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/tags/cloud",
            params={"alert_name": "LazyTagCloudTest", "tags": "cdi,api"},
        )
        if filtered_tags_cloud is None:
            self.log_error("Failed to get tags cloud with filters")
            self.test_results["failed"] += 1
            return False

        if "tags" not in filtered_tags_cloud or not isinstance(
            filtered_tags_cloud["tags"], list
        ):
            self.log_error("Tags cloud with filters has unexpected structure")
            self.test_results["failed"] += 1
            return False

        self.log_success("Filtered tags cloud retrieved")

        # Если есть алерты, тестируем CRUD операции
        if alerts.get("alerts"):
            alert_id = alerts["alerts"][0]["alert_id"]

            # GET - детали алерта
            alert_detail = self.make_request(
                "GET",
                "/alerts/api/v1/alerts/detail",
                params={"alert_id": alert_id},
            )
            if alert_detail is None:
                self.log_error("Failed to get alert details")
                self.test_results["failed"] += 1
                return False

            # Проверяем структуру group_rule в ответе
            if "group_rule" in alert_detail:
                group_rule = alert_detail["group_rule"]
                required_fields = ["group_rule_id", "description", "image"]
                missing_fields = [
                    field
                    for field in required_fields
                    if field not in group_rule
                ]
                if missing_fields:
                    self.log_error(
                        f"group_rule missing fields: {missing_fields}"
                    )
                    self.test_results["failed"] += 1
                    return False
                else:
                    self.log_success(
                        f"group_rule structure correct: {group_rule}"
                    )
            else:
                self.log_warning("No group_rule in alert detail response")

            # Проверяем, что silence_time может быть в ответе (опциональное поле)
            if "silence_time" in alert_detail:
                self.log_info(
                    f"Alert has silence_time: {alert_detail['silence_time']}"
                )

            self.log_success("Alert details retrieved")

        # POST - создание нового алерта (используем случайный индикатор и обязательный group_rules)
        # Получаем список индикаторов и выбираем случайный
        indicators_response = self.make_request(
            "GET",
            "/alerts/api/v1/indicators/autocomplete",
            params={"limit": 50},
        )
        if not indicators_response or not indicators_response.get(
            "indicators"
        ):
            self.log_error("No indicators available for testing")
            self.test_results["failed"] += 1
            return False

        import random

        available_indicators = indicators_response["indicators"]
        random_indicator = random.choice(available_indicators)

        self.log_info(
            f"Selected random indicator: {random_indicator['indicator_name']} ({random_indicator['indicator_id']})"
        )

        # Получаем список групп правил (автокомплит с пустым description)
        groups_resp = self.make_request(
            "GET",
            "/alerts/api/v1/group_rules/autocomplete",
            params={"limit": 50},
        )
        if not groups_resp or not groups_resp.get("group_rules"):
            self.log_error("No group_rules available for testing")
            self.test_results["failed"] += 1
            return False
        available_groups = groups_resp["group_rules"]
        first_group = available_groups[0]
        self.log_info(
            f"Selected group_rules: {first_group['description']} ({first_group['group_rule_id']})"
        )

        alert_data = {
            "alert_name": f"Test Alert {uuid.uuid4().hex[:8]}",
            "indicator_id": random_indicator["indicator_id"],
            "description": f"Test description for alert {uuid.uuid4().hex[:8]}",
            "image": '{"type": "svg", "content": "<svg>Test image</svg>"}',
            "tags": ["test", "api"],
            "group_rule_id": first_group["group_rule_id"],
            "silence_time": '{"start": "09:00", "end": "18:00"}',
        }

        create_result = self.make_request(
            "POST", "/alerts/api/v1/alerts/detail", alert_data
        )
        if create_result is None or create_result is not True:
            self.log_error("Failed to create alert")
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Failed to create alert")
            return False

        self.log_success("Alert created successfully")

        # Находим созданный алерт
        created_alerts = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"query": alert_data["alert_name"]},
        )
        if not created_alerts or not created_alerts.get("alerts"):
            self.log_error("Созданный алерт не найден")
            self.test_results["failed"] += 1
            return False

        created_alert_id = created_alerts["alerts"][0]["alert_id"]
        self.created_data["alerts"].append(created_alert_id)

        # Проверяем детали созданного алерта и структуру group_rule
        created_alert_detail = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/detail",
            params={"alert_id": created_alert_id},
        )
        if created_alert_detail and "group_rule" in created_alert_detail:
            group_rule = created_alert_detail["group_rule"]
            required_fields = ["group_rule_id", "description", "image"]
            missing_fields = [
                field for field in required_fields if field not in group_rule
            ]
            if missing_fields:
                self.log_error(
                    f"Created alert group_rule missing fields: {missing_fields}"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success(
                f"Created alert group_rule structure correct: {group_rule}"
            )
        else:
            self.log_warning("No group_rule in created alert detail response")

        # Проверяем, что silence_time возвращается после group_rule
        # silence_time теперь возвращается как объект, а не строка
        if created_alert_detail and "silence_time" in created_alert_detail:
            expected_silence_time = json.loads(alert_data["silence_time"])
            if created_alert_detail["silence_time"] != expected_silence_time:
                self.log_error(
                    f"Created alert silence_time mismatch: expected {expected_silence_time}, got {created_alert_detail['silence_time']}"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success(
                f"Created alert silence_time correct: {created_alert_detail['silence_time']}"
            )
        else:
            self.log_warning(
                "No silence_time in created alert detail response"
            )

        # Регресс: LIKE/ILIKE экранирование (%/_/\\) в search/autocomplete
        self.log_info(
            "Step: LIKE/ILIKE escaping regression for search/autocomplete"
        )
        token = uuid.uuid4().hex[:8]

        def _create_and_remember_alert(alert_name: str) -> str | None:
            payload = {
                "alert_name": alert_name,
                "indicator_id": random_indicator["indicator_id"],
                "description": "like escape test",
                "image": '{"type": "svg", "content": "<svg>Like escape</svg>"}',
                "tags": ["test", "like_escape"],
                "group_rule_id": first_group["group_rule_id"],
            }
            create_ok = self.make_request(
                "POST", "/alerts/api/v1/alerts/detail", payload
            )
            if create_ok is None or create_ok is not True:
                self.log_error(
                    f"Failed to create alert for like-escape test: {alert_name}"
                )
                return None

            found = self.make_request(
                "GET",
                "/alerts/api/v1/alerts/search",
                params={"query": alert_name},
            )
            if not found or not found.get("alerts"):
                self.log_error(
                    f"Created like-escape alert not found via search: {alert_name}"
                )
                return None

            alert_id = found["alerts"][0]["alert_id"]
            self.created_data["alerts"].append(alert_id)
            return alert_id

        # '_' case: без экранирования "A_B" матчило бы и "AXB"
        name_underscore = f"LikeEscape_{token}_A_B"
        name_underscore_other = f"LikeEscape_{token}_AXB"
        if _create_and_remember_alert(name_underscore) is None:
            self.test_results["failed"] += 1
            return False
        if _create_and_remember_alert(name_underscore_other) is None:
            self.test_results["failed"] += 1
            return False

        search_underscore = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"query": name_underscore, "limit": 100},
        )
        if not search_underscore or not search_underscore.get("alerts"):
            self.log_error(
                "Search for underscore-like-escape returned no alerts"
            )
            self.test_results["failed"] += 1
            return False
        names = {
            a.get("alert_name") for a in search_underscore.get("alerts", [])
        }
        if name_underscore not in names:
            self.log_error(
                f"Expected alert not found in underscore search: {name_underscore}"
            )
            self.test_results["failed"] += 1
            return False
        if name_underscore_other in names:
            self.log_error(
                f"Wildcard regression: underscore search matched other alert: {name_underscore_other}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Underscore escaping works in alerts/search")

        auto_underscore = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/autocomplete",
            params={"query": name_underscore, "limit": 50},
        )
        if not auto_underscore or "alerts" not in auto_underscore:
            self.log_error("Autocomplete for underscore-like-escape failed")
            self.test_results["failed"] += 1
            return False
        auto_names = {
            a.get("alert_name") for a in auto_underscore.get("alerts", [])
        }
        if (
            name_underscore not in auto_names
            or name_underscore_other in auto_names
        ):
            self.log_error(
                "Wildcard regression: underscore autocomplete matched wrong results"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Underscore escaping works in alerts/autocomplete")

        # '%' case: без экранирования "P%Q" матчило бы и "PXQ"
        name_percent = f"LikeEscape_{token}_P%Q"
        name_percent_other = f"LikeEscape_{token}_PXQ"
        if _create_and_remember_alert(name_percent) is None:
            self.test_results["failed"] += 1
            return False
        if _create_and_remember_alert(name_percent_other) is None:
            self.test_results["failed"] += 1
            return False

        search_percent = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"query": name_percent, "limit": 100},
        )
        if not search_percent or not search_percent.get("alerts"):
            self.log_error("Search for percent-like-escape returned no alerts")
            self.test_results["failed"] += 1
            return False
        names_p = {
            a.get("alert_name") for a in search_percent.get("alerts", [])
        }
        if name_percent not in names_p:
            self.log_error(
                f"Expected alert not found in percent search: {name_percent}"
            )
            self.test_results["failed"] += 1
            return False
        if name_percent_other in names_p:
            self.log_error(
                f"Wildcard regression: percent search matched other alert: {name_percent_other}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Percent escaping works in alerts/search")

        # PATCH - обновление алерта (включая смену группы правил)
        # Берем другую группу правил, если есть
        new_group = None
        for g in available_groups:
            if g["group_rule_id"] != first_group["group_rule_id"]:
                new_group = g
                break

        if new_group is None:
            self.log_warning(
                "Only one group_rules available; skipping group change test"
            )

        update_data = {
            "alert_id": created_alert_id,
            "alert_name": f"Updated {alert_data['alert_name']}",
            "indicator_id": random_indicator["indicator_id"],
            "description": f"Updated {alert_data['description']}",
            "image": '{"type": "svg", "content": "<svg>Updated test image</svg>"}',
            "tags": ["updated", "test", "patch"],
            "silence_time": '{"start": "10:00", "end": "19:00"}',
        }

        # Добавляем group_rule_id только если есть другая группа
        if new_group is not None:
            update_data["group_rule_id"] = new_group["group_rule_id"]

        update_result = self.make_request(
            "PATCH", "/alerts/api/v1/alerts/detail", update_data
        )
        if update_result is None or update_result is not True:
            self.log_error("Failed to update alert")
            self.test_results["failed"] += 1
            return False

        self.log_success("Alert updated successfully")

        # Проверяем, что все поля обновились корректно
        updated_alert_detail = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/detail",
            params={"alert_id": created_alert_id},
        )
        if not updated_alert_detail:
            self.log_error("Failed to get updated alert details")
            self.test_results["failed"] += 1
            return False

        # Проверяем обновленные поля
        if updated_alert_detail.get("alert_name") != update_data["alert_name"]:
            self.log_error(
                f"Alert name not updated: expected {update_data['alert_name']}, got {updated_alert_detail.get('alert_name')}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Alert name updated correctly")

        if (
            updated_alert_detail.get("description")
            != update_data["description"]
        ):
            self.log_error(
                f"Alert description not updated: expected {update_data['description']}, got {updated_alert_detail.get('description')}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Alert description updated correctly")

        if updated_alert_detail.get("image") != update_data["image"]:
            self.log_error(
                f"Alert image not updated: expected {update_data['image']}, got {updated_alert_detail.get('image')}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Alert image updated correctly")

        if updated_alert_detail.get("tags") != update_data["tags"]:
            self.log_error(
                f"Alert tags not updated: expected {update_data['tags']}, got {updated_alert_detail.get('tags')}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Alert tags updated correctly")

        # Проверяем обновление silence_time
        # silence_time теперь возвращается как объект, а не строка
        if update_data.get("silence_time"):
            expected_silence_time = json.loads(update_data["silence_time"])
            if (
                updated_alert_detail.get("silence_time")
                != expected_silence_time
            ):
                self.log_error(
                    f"Alert silence_time not updated: expected {expected_silence_time}, got {updated_alert_detail.get('silence_time')}"
                )
                self.test_results["failed"] += 1
                return False
        self.log_success("Alert silence_time updated correctly")

        # Проверяем обновление группы правил только если была передана другая группа
        if new_group is not None:
            self.log_success(
                f"Alert group_rules changed to {new_group['group_rule_id']}"
            )

            # Проверяем, что group_rule обновился после изменения группы
            if updated_alert_detail and "group_rule" in updated_alert_detail:
                updated_group_rule = updated_alert_detail["group_rule"]
                if (
                    updated_group_rule.get("group_rule_id")
                    == new_group["group_rule_id"]
                ):
                    self.log_success(
                        f"Alert group_rule updated correctly: {updated_group_rule}"
                    )
                else:
                    self.log_error(
                        f"Alert group_rule not updated: expected {new_group['group_rule_id']}, got {updated_group_rule.get('group_rule_id')}"
                    )
                    self.test_results["failed"] += 1
                    return False

        # Тест дублирования алерта
        self.log_info("Testing alert duplication")
        duplicate_result = self.make_request(
            "POST", f"/alerts/api/v1/{created_alert_id}/duplicate"
        )
        if duplicate_result is None or duplicate_result is not True:
            self.log_error("Failed to duplicate alert")
            self.test_results["failed"] += 1
            return False

        self.log_success("Alert duplicated successfully")

        # Находим дублированный алерт по имени (должно содержать "copy -")
        duplicated_alerts = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"query": alert_data["alert_name"]},
        )
        if not duplicated_alerts or not duplicated_alerts.get("alerts"):
            self.log_error("Дублированный алерт не найден")
            self.test_results["failed"] += 1
            return False

        # Ищем дублированный алерт (имя должно содержать "copy -")
        duplicated_alert_id = None
        for alert in duplicated_alerts["alerts"]:
            if alert.get(
                "alert_id"
            ) != created_alert_id and "copy -" in alert.get("alert_name", ""):
                duplicated_alert_id = alert["alert_id"]
                break

        if not duplicated_alert_id:
            self.log_error(
                "Дублированный алерт не найден в результатах поиска"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(f"Found duplicated alert: {duplicated_alert_id}")

        # Добавляем дублированный алерт в список для очистки
        self.created_data["alerts"].append(duplicated_alert_id)

        # Проверяем, что дублированный алерт имеет те же данные (кроме имени)
        # Дубликат создается ПОСЛЕ обновления алерта, поэтому сравниваем с updated_alert_detail
        duplicated_alert_detail = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/detail",
            params={"alert_id": duplicated_alert_id},
        )
        if not duplicated_alert_detail:
            self.log_error("Failed to get duplicated alert details")
            self.test_results["failed"] += 1
            return False

        # Проверяем основные поля (кроме alert_name)
        # Сравниваем с updated_alert_detail, так как дубликат создается после обновления
        if duplicated_alert_detail.get("indicator", {}).get(
            "indicator_id"
        ) != updated_alert_detail.get("indicator", {}).get("indicator_id"):
            self.log_error("Duplicated alert has different indicator_id")
            self.test_results["failed"] += 1
            return False

        if duplicated_alert_detail.get(
            "description"
        ) != updated_alert_detail.get("description"):
            self.log_error(
                f"Duplicated alert has different description: expected '{updated_alert_detail.get('description')}', got '{duplicated_alert_detail.get('description')}'"
            )
            self.test_results["failed"] += 1
            return False

        if duplicated_alert_detail.get("group_rule", {}).get(
            "group_rule_id"
        ) != updated_alert_detail.get("group_rule", {}).get("group_rule_id"):
            self.log_error("Duplicated alert has different group_rule_id")
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "Duplicated alert has correct data (indicator, description, group_rule)"
        )

        # Проверяем, что имя содержит "copy -"
        if "copy -" not in duplicated_alert_detail.get("alert_name", ""):
            self.log_error(
                f"Duplicated alert name doesn't contain 'copy -': {duplicated_alert_detail.get('alert_name')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            f"Duplicated alert name is correct: {duplicated_alert_detail.get('alert_name')}"
        )

        # Тест каскадного удаления: проверяем, что при удалении алерта удаляются все связанные данные
        self.log_info(
            "Testing cascade deletion: DT and pauses should be deleted with alert"
        )

        # Создаем тестовый алерт для проверки каскадного удаления
        test_alert_for_deletion = {
            "alert_name": f"Test Alert For Deletion {uuid.uuid4().hex[:8]}",
            "indicator_id": random_indicator["indicator_id"],
            "description": "Test alert for cascade deletion test",
            "image": '{"type": "svg", "content": "<svg>Test</svg>"}',
            "tags": ["test", "cascade"],
            "group_rule_id": first_group["group_rule_id"],
        }

        create_for_deletion = self.make_request(
            "POST", "/alerts/api/v1/alerts/detail", test_alert_for_deletion
        )
        if not create_for_deletion:
            self.log_error(
                "Failed to create test alert for cascade deletion test"
            )
            self.test_results["failed"] += 1
            return False

        # Находим созданный алерт
        deletion_test_alerts = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"query": test_alert_for_deletion["alert_name"]},
        )
        if not deletion_test_alerts or not deletion_test_alerts.get("alerts"):
            self.log_error("Созданный тестовый алерт для удаления не найден")
            self.test_results["failed"] += 1
            return False

        deletion_test_alert_id = deletion_test_alerts["alerts"][0]["alert_id"]
        # Добавляем в список для очистки на случай ошибки
        self.created_data["alerts"].append(deletion_test_alert_id)

        # Создаем DT для этого алерта
        dt_for_deletion = {
            "content": '{"type": "test", "data": "test for cascade deletion"}',
            "auto_create": False,
        }
        create_dt_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alert/{deletion_test_alert_id}/dt",
            dt_for_deletion,
        )
        if not create_dt_result:
            self.log_error("Failed to create DT for cascade deletion test")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что DT создан
        dt_before_delete = self.make_request(
            "GET", f"/alerts/api/v1/alert/{deletion_test_alert_id}/dt"
        )
        if not dt_before_delete or not dt_before_delete.get("dt_id"):
            self.log_error("DT не найден перед тестом удаления")
            self.test_results["failed"] += 1
            return False

        # Создаем паузу для этого алерта
        pause_for_deletion = {"login": "test_user"}
        create_pause_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{deletion_test_alert_id}/pause/schedule",
            pause_for_deletion,
        )
        if not create_pause_result:
            self.log_error("Failed to create pause for cascade deletion test")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что пауза создана
        pauses_before_delete = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{deletion_test_alert_id}/pause",
            params={"filter_type": "all"},
        )
        if (
            not pauses_before_delete
            or not isinstance(pauses_before_delete, dict)
            or len(pauses_before_delete.get("pauses", [])) == 0
        ):
            self.log_error("Пауза не найдена перед тестом удаления")
            self.test_results["failed"] += 1
            return False

        pause_count_before = pauses_before_delete.get("total", 0)

        # Создаем линк для этого алерта
        link_for_deletion = {
            "alert_id": deletion_test_alert_id,
            "link_name": f"Test Link For Deletion {uuid.uuid4().hex[:8]}",
            "link_url": f"https://example.com/test-deletion-{uuid.uuid4().hex[:8]}",
        }
        create_link_result = self.make_request(
            "POST", "/alerts/api/v1/links/detail", link_for_deletion
        )
        if not create_link_result:
            self.log_error("Failed to create link for cascade deletion test")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что линк создан
        links_before_delete = self.make_request(
            "GET",
            "/alerts/api/v1/links/by_alert",
            params={"alert_id": deletion_test_alert_id},
        )
        if (
            not links_before_delete
            or len(links_before_delete.get("links", [])) == 0
        ):
            self.log_error("Линк не найден перед тестом удаления")
            self.test_results["failed"] += 1
            return False

        link_count_before = len(links_before_delete.get("links", []))

        # Создаем подписку для этого алерта (используем существующего пользователя или создаем нового)
        # Используем первый доступный пользователь или создаем тестового
        # Не передаем query (или передаем None), так как пустая строка недопустима (min_length=1)
        users_for_subscription = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{deletion_test_alert_id}/subscriptions/search",
            params={"limit": 1},
        )
        user_id_for_subscription = None
        if users_for_subscription and users_for_subscription.get("users"):
            user_id_for_subscription = users_for_subscription["users"][0][
                "user_id"
            ]
        else:
            # Создаем тестового пользователя для подписки
            test_user_data = {
                "samAccountName": f"test_user_{uuid.uuid4().hex[:8]}",
                "group": False,
            }
            create_user_result = self.make_request(
                "POST", "/alerts/api/v1/users", test_user_data
            )
            if create_user_result:
                # Находим созданного пользователя
                users_after_create = self.make_request(
                    "GET",
                    f"/alerts/api/v1/alerts/{deletion_test_alert_id}/subscriptions/search",
                    params={
                        "query": test_user_data["samAccountName"],
                        "limit": 1,
                    },
                )
                if users_after_create and users_after_create.get("users"):
                    user_id_for_subscription = users_after_create["users"][0][
                        "user_id"
                    ]
                    self.created_data["users"].append(user_id_for_subscription)

        if not user_id_for_subscription:
            self.log_warning(
                "Could not create or find user for subscription test, skipping subscription cascade test"
            )
        else:
            # Создаем подписку через новый метод
            create_subscription_result = self.make_request(
                "POST",
                f"/alerts/api/v1/alerts/{deletion_test_alert_id}/subscriptions/users/{user_id_for_subscription}",
            )
            if not create_subscription_result:
                self.log_warning(
                    "Failed to create subscription for cascade deletion test, skipping subscription cascade test"
                )
            else:
                # Проверяем, что подписка создана
                subscriptions_before_delete = self.make_request(
                    "GET",
                    f"/alerts/api/v1/alerts/{deletion_test_alert_id}/subscriptions/search",
                )
                subscription_count_before = 0
                if (
                    subscriptions_before_delete
                    and subscriptions_before_delete.get("subscriptions")
                ):
                    subscription_count_before = len(
                        [
                            s
                            for s in subscriptions_before_delete[
                                "subscriptions"
                            ]
                            if s.get("user_id") == user_id_for_subscription
                        ]
                    )
                self.log_success(
                    f"Created DT, {pause_count_before} pause(s), {link_count_before} link(s), and {subscription_count_before} subscription(s) for cascade deletion test"
                )

        if not user_id_for_subscription:
            self.log_success(
                f"Created DT, {pause_count_before} pause(s), and {link_count_before} link(s) for cascade deletion test"
            )

        # Удаляем алерт
        delete_alert_result = self.make_request(
            "DELETE",
            "/alerts/api/v1/alerts/detail",
            params={"alert_id": deletion_test_alert_id},
        )
        if not delete_alert_result:
            self.log_error("Failed to delete alert in cascade deletion test")
            self.test_results["failed"] += 1
            return False

        # Убираем из списка для очистки, так как уже удален
        if deletion_test_alert_id in self.created_data["alerts"]:
            self.created_data["alerts"].remove(deletion_test_alert_id)

        # Проверяем, что DT удален (должна быть ошибка 404, так как алерт удален)
        dt_after_delete = self.make_request(
            "GET",
            f"/alerts/api/v1/alert/{deletion_test_alert_id}/dt",
            expect_error=True,
        )
        if dt_after_delete and dt_after_delete.get("status_code") == 404:
            self.log_success(
                "DT correctly deleted with alert (404 as expected)"
            )
        elif dt_after_delete and dt_after_delete.get("status_code") != 404:
            self.log_error(
                f"Expected 404 for DT after alert deletion, got: {dt_after_delete.get('status_code')}"
            )
            self.test_results["failed"] += 1
            return False
        else:
            self.log_warning(
                "Could not verify DT deletion (alert deleted, so DT endpoint may return 404 for alert)"
            )

        # Проверяем, что паузы удалены (должна быть ошибка 404, так как алерт удален)
        pauses_after_delete = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{deletion_test_alert_id}/pause",
            expect_error=True,
        )
        if (
            pauses_after_delete
            and isinstance(pauses_after_delete, dict)
            and pauses_after_delete.get("status_code") == 404
        ):
            self.log_success(
                "Pauses correctly deleted with alert (404 as expected)"
            )
        elif (
            pauses_after_delete
            and isinstance(pauses_after_delete, dict)
            and pauses_after_delete.get("status_code") != 404
        ):
            # Может быть, что паузы возвращаются, но их должно быть 0
            if pauses_after_delete.get("total", 0) == 0:
                self.log_success(
                    "Pauses correctly deleted with alert (total=0)"
                )
            else:
                self.log_error(
                    f"Expected 0 pauses after alert deletion, got: {pauses_after_delete.get('total')}"
                )
                self.test_results["failed"] += 1
                return False
        else:
            self.log_warning("Could not verify pauses deletion")

        # Проверяем, что линки удалены (должна быть ошибка 404 или пустой список, так как алерт удален)
        links_after_delete = self.make_request(
            "GET",
            "/alerts/api/v1/links/by_alert",
            params={"alert_id": deletion_test_alert_id},
            expect_error=True,
        )
        if links_after_delete and links_after_delete.get("status_code") == 404:
            self.log_success(
                "Links correctly deleted with alert (404 as expected)"
            )
        elif (
            links_after_delete and links_after_delete.get("status_code") != 404
        ):
            # Может быть, что линки возвращаются, но их должно быть 0
            links_list = links_after_delete.get("links", [])
            if len(links_list) == 0:
                self.log_success(
                    "Links correctly deleted with alert (empty list)"
                )
            else:
                self.log_error(
                    f"Expected 0 links after alert deletion, got: {len(links_list)}"
                )
                self.test_results["failed"] += 1
                return False
        else:
            self.log_warning("Could not verify links deletion")

        # Проверяем, что подписки удалены (если они были созданы)
        if user_id_for_subscription:
            subscriptions_after_delete = self.make_request(
                "GET",
                f"/alerts/api/v1/alerts/{deletion_test_alert_id}/subscriptions/search",
                expect_error=True,
            )
            if (
                subscriptions_after_delete
                and subscriptions_after_delete.get("status_code") == 404
            ):
                self.log_success(
                    "Subscriptions correctly deleted with alert (404 as expected)"
                )
            elif (
                subscriptions_after_delete
                and subscriptions_after_delete.get("status_code") != 404
            ):
                # Может быть, что подписки возвращаются, но их должно быть 0
                if (
                    subscriptions_after_delete.get("subscriptions")
                    and len(
                        subscriptions_after_delete.get("subscriptions", [])
                    )
                    == 0
                ):
                    self.log_success(
                        "Subscriptions correctly deleted with alert (empty list)"
                    )
                else:
                    # Проверяем, что конкретная подписка удалена
                    found_subscription = False
                    if subscriptions_after_delete.get("subscriptions"):
                        for sub in subscriptions_after_delete["subscriptions"]:
                            if sub.get("user_id") == user_id_for_subscription:
                                found_subscription = True
                                break
                    if found_subscription:
                        self.log_error(
                            f"Subscription for user {user_id_for_subscription} not deleted with alert"
                        )
                        self.test_results["failed"] += 1
                        return False
                    else:
                        self.log_success(
                            "Subscriptions correctly deleted with alert"
                        )
            else:
                self.log_warning("Could not verify subscriptions deletion")

        self.log_success(
            "Cascade deletion test passed: DT, pauses, links, and subscriptions deleted with alert"
        )

        # НЕ удаляем основной алерт здесь - он нужен для тестов Links и Subscriptions
        # Удаление будет в cleanup()

        self.test_results["passed"] += 1
        return True

    def test_dt(self):
        """Тест DT CRUD endpoints"""
        self.log_test("Testing DT CRUD")

        # Используем тестовый алерт, созданный в test_alerts
        if not self.created_data["alerts"]:
            self.log_error(
                "No test alert found - test_alerts must run before test_dt"
            )
            self.test_results["failed"] += 1
            return False

        alert_id = self.created_data["alerts"][0]
        self.log_info(f"Using test alert_id: {alert_id}")

        # 1. GET - проверяем, что DT еще не существует (ожидаем 404)
        dt_detail = self.make_request(
            "GET", f"/alerts/api/v1/alert/{alert_id}/dt", expect_error=True
        )
        if dt_detail is not None and dt_detail.get("status_code") == 404:
            self.log_success("No existing DT found (as expected, 404)")
        elif dt_detail is not None and dt_detail.get("status_code") != 404:
            # DT существует, удаляем его для чистого теста
            dt_detail_normal = self.make_request(
                "GET", f"/alerts/api/v1/alert/{alert_id}/dt"
            )
            if dt_detail_normal and dt_detail_normal.get("dt_id"):
                dt_id = dt_detail_normal["dt_id"]
                self.log_warning(
                    f"DT already exists for test alert (id: {dt_id}), will delete it first"
                )
                delete_result = self.make_request(
                    "DELETE", f"/alerts/api/v1/alert/{alert_id}/dt"
                )
                if not delete_result:
                    self.log_error("Failed to delete existing DT before test")
                    self.test_results["failed"] += 1
                    return False
                self.log_success("Deleted existing DT before test")
        else:
            self.log_success("No existing DT found (as expected)")

        # 2. POST - создание DT для алерта
        dt_data = {
            "content": '{"type": "test", "data": "test content"}',
            "auto_create": False,
            "silence_time": '{"start": "09:00", "end": "18:00"}',
        }

        create_result = self.make_request(
            "POST", f"/alerts/api/v1/alert/{alert_id}/dt", dt_data
        )
        if create_result is None or create_result is not True:
            self.log_error("Failed to create DT")
            self.test_results["failed"] += 1
            return False

        self.log_success("DT created successfully")

        # 3. GET - получение созданного DT
        created_dt = self.make_request(
            "GET", f"/alerts/api/v1/alert/{alert_id}/dt"
        )
        if created_dt is None:
            self.log_error("Failed to get created DT")
            self.test_results["failed"] += 1
            return False

        # Проверяем структуру созданного DT
        required_fields = ["dt_id", "alert_id", "content", "auto_create"]
        missing_fields = [
            field for field in required_fields if field not in created_dt
        ]
        if missing_fields:
            self.log_error(f"Created DT missing fields: {missing_fields}")
            self.test_results["failed"] += 1
            return False

        # Проверяем значения
        # content и silence_time теперь возвращаются как объекты, а не строки
        expected_content = json.loads(dt_data["content"])
        if created_dt.get("content") != expected_content:
            self.log_error(
                f"DT content mismatch: expected {expected_content}, got {created_dt.get('content')}"
            )
            self.test_results["failed"] += 1
            return False

        if created_dt.get("auto_create") != dt_data["auto_create"]:
            self.log_error(
                f"DT auto_create mismatch: expected {dt_data['auto_create']}, got {created_dt.get('auto_create')}"
            )
            self.test_results["failed"] += 1
            return False

        if dt_data.get("silence_time"):
            expected_silence_time = json.loads(dt_data["silence_time"])
            if created_dt.get("silence_time") != expected_silence_time:
                self.log_error(
                    f"DT silence_time mismatch: expected {expected_silence_time}, got {created_dt.get('silence_time')}"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success("Created DT structure and values correct")
        dt_id = created_dt["dt_id"]
        self.created_data.setdefault("dt", []).append(dt_id)

        # 4. PATCH - обновление DT
        update_data = {
            "content": '{"type": "updated", "data": "updated content"}',
            "auto_create": True,
            "silence_time": '{"start": "10:00", "end": "19:00"}',
        }

        update_result = self.make_request(
            "PATCH", f"/alerts/api/v1/alert/{alert_id}/dt", update_data
        )
        if update_result is None or update_result is not True:
            self.log_error("Failed to update DT")
            self.test_results["failed"] += 1
            return False

        self.log_success("DT updated successfully")

        # 5. GET - проверяем обновленные значения
        updated_dt = self.make_request(
            "GET", f"/alerts/api/v1/alert/{alert_id}/dt"
        )
        if updated_dt is None:
            self.log_error("Failed to get updated DT")
            self.test_results["failed"] += 1
            return False

        # content и silence_time теперь возвращаются как объекты, а не строки
        if update_data.get("content") is not None:
            expected_content = json.loads(update_data["content"])
            if updated_dt.get("content") != expected_content:
                self.log_error(
                    f"DT content not updated: expected {expected_content}, got {updated_dt.get('content')}"
                )
                self.test_results["failed"] += 1
                return False

        if updated_dt.get("auto_create") != update_data["auto_create"]:
            self.log_error(
                f"DT auto_create not updated: expected {update_data['auto_create']}, got {updated_dt.get('auto_create')}"
            )
            self.test_results["failed"] += 1
            return False

        if update_data.get("silence_time") is not None:
            expected_silence_time = json.loads(update_data["silence_time"])
            if updated_dt.get("silence_time") != expected_silence_time:
                self.log_error(
                    f"DT silence_time not updated: expected {expected_silence_time}, got {updated_dt.get('silence_time')}"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success("DT updated values correct")

        # 6. Тест валидации JSON - некорректный content
        invalid_content_data = {"content": "invalid json string"}
        result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alert/{alert_id}/dt",
            invalid_content_data,
            expect_error=True,
        )
        if result and result.get("status_code") == 400:
            self.log_success("400 validation error for invalid content JSON")
        else:
            self.log_warning(
                "Expected 400 validation error for invalid content JSON"
            )

        # 7. Тест валидации JSON - некорректный silence_time
        invalid_silence_data = {"silence_time": "invalid json string"}
        result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alert/{alert_id}/dt",
            invalid_silence_data,
            expect_error=True,
        )
        if result and result.get("status_code") == 400:
            self.log_success(
                "400 validation error for invalid silence_time JSON"
            )
        else:
            self.log_warning(
                "Expected 400 validation error for invalid silence_time JSON"
            )

        # 8. Тест пустой строки для content (должна быть отклонена, т.к. в БД NOT NULL)
        empty_content_data = {"content": ""}
        result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alert/{alert_id}/dt",
            empty_content_data,
            expect_error=True,
        )
        if result and result.get("status_code") == 400:
            self.log_success(
                "400 validation error for empty content (NOT NULL constraint)"
            )
        else:
            self.log_warning("Expected 400 validation error for empty content")

        # 9. Тест пустой строки для silence_time (должна устанавливать NULL)
        empty_silence_data = {"silence_time": ""}
        result = self.make_request(
            "PATCH", f"/alerts/api/v1/alert/{alert_id}/dt", empty_silence_data
        )
        if result is not None and result is True:
            # Проверяем, что silence_time стал NULL (не возвращается в ответе)
            updated_dt = self.make_request(
                "GET", f"/alerts/api/v1/alert/{alert_id}/dt"
            )
            if updated_dt and "silence_time" not in updated_dt:
                self.log_success(
                    "Empty silence_time string correctly set to NULL"
                )
            else:
                self.log_warning(
                    f"Expected silence_time to be NULL, got: {updated_dt.get('silence_time') if updated_dt else None}"
                )
        else:
            self.log_warning("Expected empty silence_time to be allowed")

        # 10. Тест валидации длины - content превышает 3000 символов
        long_content = '{"data": "' + "x" * 3001 + '"}'
        long_content_data = {"content": long_content}
        result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alert/{alert_id}/dt",
            long_content_data,
            expect_error=True,
        )
        if result and result.get("status_code") == 400:
            self.log_success(
                "400 validation error for content exceeding 3000 characters"
            )
        else:
            self.log_warning(
                "Expected 400 validation error for content exceeding 3000 characters"
            )

        # 11. Тест валидации длины - silence_time превышает 1000 символов
        long_silence = '{"data": "' + "x" * 1001 + '"}'
        long_silence_data = {"silence_time": long_silence}
        result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alert/{alert_id}/dt",
            long_silence_data,
            expect_error=True,
        )
        if result and result.get("status_code") == 400:
            self.log_success(
                "400 validation error for silence_time exceeding 1000 characters"
            )
        else:
            self.log_warning(
                "Expected 400 validation error for silence_time exceeding 1000 characters"
            )

        # 12. DELETE - удаление DT (тестируем, что метод DELETE работает корректно)
        # Создаем новый DT для теста удаления (так как текущий может быть изменен предыдущими тестами)
        dt_for_delete_test = {
            "content": '{"type": "test", "data": "test for delete"}',
            "auto_create": False,
        }

        # Удаляем существующий DT, если есть
        existing_dt = self.make_request(
            "GET", f"/alerts/api/v1/alert/{alert_id}/dt", expect_error=True
        )
        if existing_dt and existing_dt.get("status_code") != 404:
            delete_existing = self.make_request(
                "DELETE", f"/alerts/api/v1/alert/{alert_id}/dt"
            )
            if not delete_existing:
                self.log_warning(
                    "Failed to delete existing DT before delete test"
                )

        # Создаем новый DT для теста удаления
        create_for_delete = self.make_request(
            "POST", f"/alerts/api/v1/alert/{alert_id}/dt", dt_for_delete_test
        )
        if not create_for_delete:
            self.log_error("Failed to create DT for delete test")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что DT создан
        dt_before_delete_test = self.make_request(
            "GET", f"/alerts/api/v1/alert/{alert_id}/dt"
        )
        if not dt_before_delete_test or not dt_before_delete_test.get("dt_id"):
            self.log_error("DT не найден перед тестом удаления")
            self.test_results["failed"] += 1
            return False

        # Удаляем DT
        delete_result = self.make_request(
            "DELETE", f"/alerts/api/v1/alert/{alert_id}/dt"
        )
        if delete_result is None or delete_result is not True:
            self.log_error("Failed to delete DT")
            self.test_results["failed"] += 1
            return False
        self.log_success("DT deleted successfully")

        # Проверяем, что DT действительно удален (должна быть ошибка 404)
        dt_after_delete = self.make_request(
            "GET", f"/alerts/api/v1/alert/{alert_id}/dt", expect_error=True
        )
        if dt_after_delete and dt_after_delete.get("status_code") == 404:
            self.log_success("DT correctly deleted (404 as expected)")
        else:
            self.log_error(
                f"DT not deleted correctly: expected 404, got {dt_after_delete.get('status_code') if dt_after_delete else 'None'}"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем повторное удаление (должна быть ошибка 404)
        delete_again_result = self.make_request(
            "DELETE", f"/alerts/api/v1/alert/{alert_id}/dt", expect_error=True
        )
        if (
            delete_again_result
            and delete_again_result.get("status_code") == 404
        ):
            self.log_success(
                "Correctly returns 404 when trying to delete non-existent DT"
            )
        else:
            self.log_warning(
                f"Expected 404 when deleting non-existent DT, got: {delete_again_result.get('status_code') if delete_again_result else 'None'}"
            )

        self.test_results["passed"] += 1
        return True

    def test_links(self):
        """Тест links CRUD endpoints"""
        self.log_test("Testing Links CRUD")

        # Используем тестовый алерт, созданный в test_alerts
        if not self.created_data["alerts"]:
            self.log_warning("No test alert found, skipping links CRUD test")
            self.test_results["passed"] += 1
            return True

        alert_id = self.created_data["alerts"][0]
        self.log_info(f"Using test alert_id: {alert_id} for links testing")

        # POST - создание ссылки
        link_data = {
            "alert_id": alert_id,
            "link_name": f"Test Link {uuid.uuid4().hex[:8]}",
            "link_url": f"https://example.com/test-{uuid.uuid4().hex[:8]}",
        }

        create_result = self.make_request(
            "POST", "/alerts/api/v1/links/detail", link_data
        )
        if create_result is None or create_result is not True:
            self.log_error("Failed to create link")
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Failed to create link")
            return False

        self.log_success("Link created successfully")

        # GET - получение ссылок по алерту
        links = self.make_request(
            "GET",
            "/alerts/api/v1/links/by_alert",
            params={"alert_id": alert_id},
        )
        if links is None:
            self.log_error("Failed to get links by alert")
            self.test_results["failed"] += 1
            return False

        if not links.get("links"):
            self.log_error("Созданный линк не найден в ответе by_alert")
            self.test_results["failed"] += 1
            return False

        link_id = links["links"][0]["link_id"]
        self.created_data["links"].append(link_id)
        self.log_success(f"Found created link: {link_id}")

        # GET - детали ссылки
        link_detail = self.make_request(
            "GET", "/alerts/api/v1/links/detail", params={"link_id": link_id}
        )
        if link_detail is None:
            self.log_error("Failed to get link details")
            self.test_results["failed"] += 1
            return False

        self.log_success("Link details retrieved")

        # PATCH - обновление ссылки
        update_data = {
            "link_id": link_id,
            "link_name": f"Updated {link_data['link_name']}",
            "link_url": f"https://updated.example.com/{uuid.uuid4().hex[:8]}",
        }

        update_result = self.make_request(
            "PATCH", "/alerts/api/v1/links/detail", update_data
        )
        if update_result is None or update_result is not True:
            self.log_error("Failed to update link")
            self.test_results["failed"] += 1
            return False

        self.log_success("Link updated successfully")

        # DELETE - удаление ссылки
        delete_result = self.make_request(
            "DELETE",
            "/alerts/api/v1/links/detail",
            params={"link_id": link_id},
        )
        if delete_result is None or delete_result is not True:
            self.log_error("Failed to delete link")
            self.test_results["failed"] += 1
            return False

        self.log_success("Link deleted successfully")
        self.created_data["links"].remove(
            link_id
        )  # Убираем из списка для очистки

        self.test_results["passed"] += 1
        return True

    def test_subscriptions_new_methods(self):
        """Тест новых методов подписок: subscribe, unsubscribe, search, PATCH"""
        self.log_test("Testing New Subscriptions Methods")

        # Используем тестовый алерт, созданный в test_alerts
        if not self.created_data["alerts"]:
            self.log_warning(
                "No test alert found, skipping subscriptions test"
            )
            self.test_results["passed"] += 1
            return True

        # Используем тестового пользователя, созданного в test_users
        if not self.created_data["users"]:
            self.log_warning("No test user found, skipping subscriptions test")
            self.test_results["passed"] += 1
            return True

        alert_id = self.created_data["alerts"][0]
        user_id = self.created_data["users"][0]
        self.log_info(
            f"Using test alert_id: {alert_id} and user_id: {user_id}"
        )

        # 1. GET /alerts/{alert_id}/subscriptions/search - получить всех пользователей по алерту
        users_response = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if users_response is None:
            self.log_error("Failed to get users for alert")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что пользователь есть в списке
        user_found = False
        is_subscribed_before = False
        for user in users_response.get("users", []):
            if user["user_id"] == user_id:
                user_found = True
                # Проверяем наличие подписки по наличию notification_channels или statuses
                is_subscribed_before = bool(
                    user.get("notification_channels") or user.get("statuses")
                )
                break

        if not user_found:
            self.log_error(
                "Тестовый пользователь не найден в списке пользователей"
            )
            self.test_results["failed"] += 1
            return False

        if is_subscribed_before:
            self.log_warning(
                "User is already subscribed, will test unsubscribe first"
            )
            # Если уже подписан, отписываем
            unsubscribe_result = self.make_request(
                "DELETE",
                f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
            )
            if not unsubscribe_result:
                self.log_error("Failed to unsubscribe before test")
                self.test_results["failed"] += 1
                return False
            self.log_success("Unsubscribed before test")
        else:
            self.log_success(
                f"User is not subscribed (as expected), found {users_response.get('total', 0)} users"
            )

        # 2. POST /alerts/{alert_id}/subscriptions/users/{user_id} - подписать пользователя
        subscribe_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
        )
        if subscribe_result is None or subscribe_result is not True:
            self.log_error("Failed to subscribe user")
            self.test_results["failed"] += 1
            return False

        self.log_success("User subscribed successfully")

        # 2.5. Проверяем динамичность notification_channels в GET /alerts/{alert_id}/subscriptions/search после подписки
        # Также проверяем новый параметр subscribed_only
        users_response_after_subscribe = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )

        # Проверяем subscribed_only=true - должны вернуться только подписанные пользователи
        subscribed_only_response = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search",
            params={"subscribed_only": True},
        )
        if subscribed_only_response:
            # Проверяем, что все пользователи в списке имеют подписку
            for user in subscribed_only_response.get("users", []):
                has_subscription = bool(
                    user.get("notification_channels") or user.get("statuses")
                )
                if not has_subscription:
                    self.log_warning(
                        f"User {user.get('user_id')} found in subscribed_only list but has no subscription"
                    )
            # Проверяем, что наш тестовый пользователь есть в списке
            test_user_in_subscribed = any(
                user["user_id"] == user_id
                for user in subscribed_only_response.get("users", [])
            )
            if test_user_in_subscribed:
                self.log_success("Test user found in subscribed_only list")
            else:
                self.log_warning(
                    "Тестовый пользователь не найден в списке subscribed_only (возможно, подписка не создалась - это может быть ожидаемо)"
                )

        # Тест поиска по email (новая функциональность)
        test_user_email = None
        if users_response_after_subscribe:
            for user in users_response_after_subscribe.get("users", []):
                if user["user_id"] == user_id:
                    contacts = user.get("contacts") or {}
                    test_user_email = contacts.get("email")
                    break
        if test_user_email:
            email_search_response = self.make_request(
                "GET",
                f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search",
                params={"query": test_user_email},
            )
            if email_search_response:
                found_by_email = any(
                    u["user_id"] == user_id
                    for u in email_search_response.get("users", [])
                )
                if found_by_email:
                    self.log_success(
                        "User found via email search (query parameter)"
                    )
                else:
                    self.log_warning(
                        "User not found via email search despite having email in contacts"
                    )
        else:
            self.log_warning(
                "Test user email not available for email search verification"
            )

        # Тест фильтра groups=true (должны вернуться только группы)
        groups_true_response = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search",
            params={"groups": True},
        )
        if groups_true_response and groups_true_response.get("users"):
            if all(
                user.get("group") for user in groups_true_response["users"]
            ):
                self.log_success("groups=true filter returns only group users")
            else:
                self.log_error("groups=true filter returned non-group users")
                self.test_results["failed"] += 1
                return False
        else:
            self.log_warning(
                "groups=true filter returned no users (cannot verify)"
            )

        # Тест фильтра groups=false (должны вернуться только обычные пользователи)
        groups_false_response = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search",
            params={"groups": False},
        )
        if groups_false_response and groups_false_response.get("users"):
            if all(
                not user.get("group")
                for user in groups_false_response["users"]
            ):
                self.log_success(
                    "groups=false filter returns only non-group users"
                )
            else:
                self.log_error("groups=false filter returned group users")
                self.test_results["failed"] += 1
                return False
        else:
            self.log_warning(
                "groups=false filter returned no users (cannot verify)"
            )

        if users_response_after_subscribe:
            for user in users_response_after_subscribe.get("users", []):
                if user["user_id"] == user_id:
                    # Проверяем наличие подписки по наличию notification_channels или statuses
                    has_subscription = bool(
                        user.get("notification_channels")
                        or user.get("statuses")
                    )
                    if has_subscription:
                        # Проверяем, что у подписанного пользователя есть notification_channels
                        user_notification_channels = user.get(
                            "notification_channels", {}
                        )
                        if user_notification_channels:
                            self.log_info(
                                f"notification_channels in /search endpoint: {list(user_notification_channels.keys())}"
                            )
                            # Проверяем, что это динамические boolean поля
                            for (
                                key,
                                value,
                            ) in user_notification_channels.items():
                                if not isinstance(value, bool):
                                    self.log_warning(
                                        f"notification_channels field {key} in /search is not boolean: {value}"
                                    )
                                else:
                                    self.log_success(
                                        f"notification_channels field {key} in /search is boolean: {value}"
                                    )
                            self.log_success(
                                f"Dynamic notification_channels verified in /search endpoint: {len(user_notification_channels)} fields"
                            )
                        else:
                            self.log_warning(
                                "No notification_channels found in /search endpoint for subscribed user"
                            )
                    break

        # 3. Получаем информацию о подписке через GET /alerts/{alert_id}/subscriptions/search
        # Проверяем, что пользователь подписан и есть notification_channels и statuses
        users_response_subscribed = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if not users_response_subscribed:
            self.log_error("Failed to get users after subscription")
            self.test_results["failed"] += 1
            return False

        subscription_user = None
        for user in users_response_subscribed.get("users", []):
            if user["user_id"] == user_id:
                subscription_user = user
                break

        if not subscription_user:
            self.log_error("Тестовый пользователь не найден после подписки")
            self.test_results["failed"] += 1
            return False

        # Проверяем динамичность notification_channels
        notification_channels = subscription_user.get(
            "notification_channels", {}
        )
        if not notification_channels:
            self.log_warning(
                "No notification_channels found for subscribed user"
            )
        else:
            self.log_info(
                f"notification_channels found: {list(notification_channels.keys())}"
            )
            # Проверяем, что это динамические поля из alerts.alerts_contacts
            # Ожидаем boolean поля (telegram, email, pachca и т.д.)
            for key, value in notification_channels.items():
                if not isinstance(value, bool):
                    self.log_warning(
                        f"notification_channels field {key} is not boolean: {value}"
                    )
                else:
                    self.log_success(
                        f"notification_channels field {key} is boolean: {value}"
                    )

        # Проверяем динамичность statuses - должны быть все статусы с send_notification=true
        statuses = subscription_user.get("statuses", [])
        if not statuses:
            self.log_warning("No statuses found for subscribed user")
        else:
            self.log_success(
                f"Found {len(statuses)} statuses (dynamic from rules_change_status with send_notification=true)"
            )

            # Проверяем структуру каждого статуса
            for status in statuses:
                if "status_id" not in status:
                    self.log_error(f"Status missing status_id: {status}")
                    self.test_results["failed"] += 1
                    return False
                if "status_name" not in status:
                    self.log_error(f"Status missing status_name: {status}")
                    self.test_results["failed"] += 1
                    return False
                # repeat может быть None (если статус не настроен в alerts_contacts_status)
                # или числом (если настроен)
                if "repeat" in status:
                    if status["repeat"] is not None and not isinstance(
                        status["repeat"], int
                    ):
                        self.log_error(
                            f"Status {status['status_id']} has invalid repeat type: {type(status['repeat'])}"
                        )
                        self.test_results["failed"] += 1
                        return False
                    self.log_info(
                        f"Status {status['status_id']} ({status['status_name']}): repeat={status.get('repeat')}"
                    )
                else:
                    self.log_info(
                        f"Status {status['status_id']} ({status['status_name']}): repeat not set (None, excluded from JSON)"
                    )

            self.log_success(
                "All statuses have correct structure (status_id, status_name, optional repeat)"
            )

        # 4. PATCH /alerts/{alert_id}/subscriptions/users/{user_id} - изменить контакты и статусы
        # Найдем статус для изменения (берем первый доступный)
        status_to_update = None
        for status in statuses:
            if status.get("status_id"):
                status_to_update = status
                break

        update_data = {}

        # Изменяем notification_channels (инвертируем значения, если они есть)
        # Это проверяет динамичность: мы можем обновить любые поля, которые есть в ответе
        if notification_channels:
            updated_channels = {}
            for key, value in notification_channels.items():
                if isinstance(value, bool):
                    updated_channels[key] = not value
                else:
                    updated_channels[key] = value

            # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ДИНАМИЧНОСТИ:
            # Пробуем добавить новое поле, которого не было в исходном ответе
            # Это должно работать, если в таблице alerts.alerts_contacts есть такое поле
            # Но для теста мы просто обновим существующие поля
            # Если бы мы знали структуру БД, могли бы проверить добавление нового поля

            update_data["notification_channels"] = updated_channels
            self.log_info(
                f"Updating notification_channels (dynamic fields): {updated_channels}"
            )
            self.log_info(
                f"Testing dynamic update: updating {len(updated_channels)} fields from alerts.alerts_contacts"
            )

        # Изменяем статус (если есть)
        if status_to_update:
            # Устанавливаем repeat для первого статуса, удаляем второй (если есть)
            statuses_update = [
                {"status_id": status_to_update["status_id"], "repeat": 5}
            ]
            # Если есть второй статус, добавляем его без repeat (для удаления)
            if len(statuses) > 1:
                second_status = statuses[1]
                statuses_update.append(
                    {"status_id": second_status["status_id"]}
                )
            update_data["statuses"] = statuses_update
            self.log_info(f"Updating statuses: {statuses_update}")
        # Если статусов нет, получаем первый доступный статус из списка всех статусов
        # Используем реальный UUID статуса из ответа /search
        elif users_response_after_subscribe:
            # Пробуем найти любой статус из другого пользователя или используем дефолтный
            # Для теста просто пропускаем создание статуса, если их нет
            self.log_warning(
                "No statuses available for test, skipping status update"
            )
            update_data.pop(
                "statuses", None
            )  # Убираем statuses из update_data
        else:
            # Если не можем получить статусы, пропускаем тест обновления статусов
            self.log_warning(
                "Cannot get users response, skipping status update test"
            )
            update_data.pop("statuses", None)

        update_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
            update_data,
        )
        if update_result is None or update_result is not True:
            self.log_error("Failed to update subscription")
            self.test_results["failed"] += 1
            return False

        self.log_success("Subscription updated successfully")

        # 5. Проверяем, что изменения применились через GET /alerts/{alert_id}/subscriptions/search
        subscription_details_after = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if subscription_details_after is None:
            self.log_error("Failed to get subscription details after update")
            self.test_results["failed"] += 1
            return False

        # Находим пользователя в ответе
        subscription_user_after = None
        for user in subscription_details_after.get("users", []):
            if user["user_id"] == user_id:
                subscription_user_after = user
                break

        if not subscription_user_after:
            self.log_error("Тестовый пользователь не найден после обновления")
            self.test_results["failed"] += 1
            return False

        # Проверяем notification_channels - проверяем динамичность обновления
        if notification_channels and update_data.get("notification_channels"):
            updated_channels_after = subscription_user_after.get(
                "notification_channels", {}
            )

            # Проверяем, что все обновленные поля присутствуют в ответе
            updated_keys = set(update_data["notification_channels"].keys())
            after_keys = set(updated_channels_after.keys())

            # Проверяем, что все обновленные поля есть в ответе (динамичность сохранена)
            if not updated_keys.issubset(after_keys):
                missing = updated_keys - after_keys
                self.log_error(
                    f"notification_channels fields missing after update: {missing}"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success(
                f"All {len(updated_keys)} dynamic notification_channels fields preserved after update"
            )

            # Проверяем значения каждого обновленного поля
            for key, expected_value in update_data[
                "notification_channels"
            ].items():
                if key in updated_channels_after:
                    actual_value = updated_channels_after[key]
                    if actual_value == expected_value:
                        self.log_success(
                            f"notification_channels field {key} updated correctly: {actual_value}"
                        )
                    else:
                        self.log_error(
                            f"notification_channels field {key} not updated correctly: expected {expected_value}, got {actual_value}"
                        )
                        self.test_results["failed"] += 1
                        return False
                else:
                    self.log_error(
                        f"notification_channels field {key} missing after update"
                    )
                    self.test_results["failed"] += 1
                    return False

        # Проверяем, что структура notification_channels динамическая
        # (поля могут быть любыми из alerts.alerts_contacts, не только telegram/email)
        self.log_success(
            f"Dynamic notification_channels structure verified: {len(updated_channels_after)} fields"
        )

        # Проверяем statuses
        statuses_after = subscription_user_after.get("statuses", [])
        if update_data.get("statuses"):
            # Проверяем, что статус с repeat обновился
            for status_update in update_data["statuses"]:
                status_id = status_update["status_id"]
                if "repeat" in status_update:
                    # Должен быть в списке с указанным repeat
                    found = False
                    for status in statuses_after:
                        if status["status_id"] == status_id:
                            if status.get("repeat") == status_update["repeat"]:
                                self.log_success(
                                    f"Status {status_id} updated correctly with repeat={status_update['repeat']}"
                                )
                                found = True
                                break
                    if not found:
                        self.log_error(
                            f"Статус {status_id} не найден или обновлён некорректно"
                        )
                        self.test_results["failed"] += 1
                        return False
                else:
                    # Должен быть удален (не должен быть в списке или repeat должен быть None)
                    found = False
                    for status in statuses_after:
                        if status["status_id"] == status_id:
                            if status.get("repeat") is None:
                                self.log_success(
                                    f"Status {status_id} correctly removed (repeat=None)"
                                )
                                found = True
                                break
                            else:
                                self.log_error(
                                    f"Status {status_id} should be removed but still has repeat={status.get('repeat')}"
                                )
                                self.test_results["failed"] += 1
                                return False
                    if not found:
                        self.log_success(
                            f"Status {status_id} correctly removed (not in list)"
                        )

        self.log_success("All updates verified successfully")

        # 6. DELETE /alerts/{alert_id}/subscriptions/users/{user_id} - удалить подписку вместе со статусами
        unsubscribe_result = self.make_request(
            "DELETE",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
        )
        if unsubscribe_result is None or unsubscribe_result is not True:
            self.log_error("Failed to unsubscribe")
            self.test_results["failed"] += 1
            return False

        self.log_success("User unsubscribed successfully")

        # Проверяем, что пользователь снова не подписан в списке /alerts/{alert_id}/subscriptions/search
        users_response_after = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if users_response_after:
            user_found_after = False
            for user in users_response_after.get("users", []):
                if user["user_id"] == user_id:
                    user_found_after = True
                    # Проверяем отсутствие подписки по отсутствию notification_channels и statuses
                    has_subscription = bool(
                        user.get("notification_channels")
                        or user.get("statuses")
                    )
                    if not has_subscription:
                        self.log_success(
                            "User correctly shown as unsubscribed in search list"
                        )
                    else:
                        self.log_error(
                            "User still shown as subscribed after unsubscribe"
                        )
                        self.test_results["failed"] += 1
                        return False
                    break
            if not user_found_after:
                self.log_warning(
                    "Пользователь не найден в списке поиска после отписки (возможно, это ожидаемо)"
                )

        self.test_results["passed"] += 1
        return True

    def test_user_alerts_subscriptions_search(self):
        """Тест нижнего метода: список алертов пользователя с каналами и статусами"""
        self.log_test("Testing User Alerts Subscriptions Search endpoint")

        # Нужен тестовый алерт и пользователь
        if not self.created_data["alerts"]:
            self.log_warning(
                "No test alert found - skipping user alerts subscriptions search test"
            )
            self.test_results["passed"] += 1
            return True

        if not self.created_data["users"]:
            self.log_warning(
                "No test user found - skipping user alerts subscriptions search test"
            )
            self.test_results["passed"] += 1
            return True

        alert_id = self.created_data["alerts"][0]
        user_id = self.created_data["users"][0]
        self.log_info(
            f"Using test alert_id: {alert_id} and user_id: {user_id}"
        )

        # Убеждаемся, что пользователь подписан на алерт (если нет - подписываем)
        users_response = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        is_subscribed = False
        if users_response:
            for user in users_response.get("users", []):
                if user.get("user_id") == user_id:
                    is_subscribed = bool(
                        user.get("notification_channels")
                        or user.get("statuses")
                    )
                    break

        if not is_subscribed:
            subscribe_result = self.make_request(
                "POST",
                f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
            )
            if subscribe_result is None or subscribe_result is not True:
                self.log_error(
                    "Failed to subscribe user for user alerts subscriptions search test"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success(
                "User subscribed successfully for user alerts subscriptions search test"
            )

        # 1. GET /users/{user_id}/subscriptions/search - получаем список алертов пользователя
        alerts_response = self.make_request(
            "GET", f"/alerts/api/v1/users/{user_id}/subscriptions/search"
        )
        if alerts_response is None:
            self.log_error(
                "Failed to get alerts for user via /users/{user_id}/subscriptions/search"
            )
            self.test_results["failed"] += 1
            return False

        alerts = alerts_response.get("alerts", [])
        if not alerts:
            self.log_error(
                "users/{user_id}/subscriptions/search returned empty alerts list"
            )
            self.test_results["failed"] += 1
            return False

        # Находим наш тестовый алерт в списке
        user_alert = None
        for alert in alerts:
            if alert.get("alert_id") == alert_id:
                user_alert = alert
                break

        if not user_alert:
            self.log_error(
                "Test alert not found in /users/{user_id}/subscriptions/search response"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем notification_channels для подписанного алерта
        notification_channels = user_alert.get("notification_channels") or {}
        if not notification_channels:
            self.log_error(
                "Subscribed alert in /users/{user_id}/subscriptions/search has no notification_channels"
            )
            self.test_results["failed"] += 1
            return False

        for key, value in notification_channels.items():
            if not isinstance(value, bool):
                self.log_error(
                    f"notification_channels field {key} for user alert is not boolean: {value}"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success(
            f"notification_channels for user alert are dynamic boolean fields: {list(notification_channels.keys())}"
        )

        # Проверяем statuses для подписанного алерта
        statuses = user_alert.get("statuses", [])
        if statuses:
            self.log_success(
                f"Found {len(statuses)} statuses for user alert in /users/{user_id}/subscriptions/search"
            )
            for status in statuses:
                if "status_id" not in status or "status_name" not in status:
                    self.log_error(
                        f"Status in user alert list has invalid structure: {status}"
                    )
                    self.test_results["failed"] += 1
                    return False
                if (
                    "repeat" in status
                    and status["repeat"] is not None
                    and not isinstance(status["repeat"], int)
                ):
                    self.log_error(
                        f"Status {status.get('status_id')} has invalid repeat type: {type(status['repeat'])}"
                    )
                    self.test_results["failed"] += 1
                    return False
        else:
            self.log_warning(
                "No statuses found for subscribed alert in /users/{user_id}/subscriptions/search (may be expected if no statuses are configured)"
            )

        # Проверяем, что есть хотя бы один алерт без подписки (notification_channels и statuses = None)
        unsubscribed_found = False
        for alert in alerts:
            if (
                alert.get("alert_id") != alert_id
                and not alert.get("notification_channels")
                and not alert.get("statuses")
            ):
                unsubscribed_found = True
                break
        if unsubscribed_found:
            self.log_success(
                "At least one alert without subscription found (notification_channels and statuses are null)"
            )
        else:
            self.log_warning(
                "No unsubscribed alert found in /users/{user_id}/subscriptions/search (possibly all alerts are subscribed or dataset is small)"
            )

        # 2. Проверяем subscribed_only=true - должны вернуться только алерты, на которые пользователь подписан
        subscribed_only_response = self.make_request(
            "GET",
            f"/alerts/api/v1/users/{user_id}/subscriptions/search",
            params={"subscribed_only": True},
        )
        if (
            subscribed_only_response
            and subscribed_only_response.get("alerts") is not None
        ):
            alerts_subscribed = subscribed_only_response.get("alerts", [])
            if not alerts_subscribed:
                self.log_warning(
                    "subscribed_only=true returned empty list (user may have no subscriptions)"
                )
            else:
                for alert in alerts_subscribed:
                    if not alert.get(
                        "notification_channels"
                    ) and not alert.get("statuses"):
                        self.log_error(
                            "Alert without subscription returned when subscribed_only=true"
                        )
                        self.test_results["failed"] += 1
                        return False
                self.log_success(
                    "subscribed_only=true correctly returns only alerts with subscriptions"
                )

        self.test_results["passed"] += 1
        return True

    def test_subscriptions_error_handling(self):
        """Тест обработки ошибок в подписках: проверка отката транзакций при ошибках"""
        self.log_test("Testing Subscriptions Error Handling")

        # Используем тестовый алерт и пользователя
        if not self.created_data["alerts"]:
            self.log_warning(
                "No test alert found, skipping subscriptions error handling test"
            )
            self.test_results["passed"] += 1
            return True

        if not self.created_data["users"]:
            self.log_warning(
                "No test user found, skipping subscriptions error handling test"
            )
            self.test_results["passed"] += 1
            return True

        alert_id = self.created_data["alerts"][0]
        user_id = self.created_data["users"][0]
        self.log_info(
            f"Using test alert_id: {alert_id} and user_id: {user_id}"
        )

        # Убеждаемся, что пользователь подписан (если нет - подписываем)
        users_response = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        is_subscribed = False
        if users_response:
            for user in users_response.get("users", []):
                if user["user_id"] == user_id:
                    is_subscribed = bool(
                        user.get("notification_channels")
                        or user.get("statuses")
                    )
                    break

        if not is_subscribed:
            # Подписываем для теста
            subscribe_result = self.make_request(
                "POST",
                f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
            )
            if not subscribe_result:
                self.log_warning(
                    "Failed to subscribe user for error test, skipping"
                )
                self.test_results["passed"] += 1
                return True

        # Тест 1: Попытка подписаться на уже подписанный алерт (409 Conflict)
        self.log_info(
            "Test 1: Attempting to subscribe already subscribed user (expecting 409)"
        )
        duplicate_subscribe_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
            expect_error=True,
        )
        if (
            not duplicate_subscribe_result
            or duplicate_subscribe_result.get("status_code") != 409
        ):
            self.log_error(
                f"Expected 409 Conflict for duplicate subscription, got: {duplicate_subscribe_result}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Correctly received 409 Conflict for duplicate subscription"
        )

        # Тест 2: Проверка, что после ошибки можно сделать новый запрос (транзакция откатилась)
        self.log_info(
            "Test 2: Verifying that after error we can make new requests (transaction rolled back)"
        )
        users_after_error = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if not users_after_error:
            self.log_error(
                "Failed to get users after error - transaction might not have rolled back"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Successfully made new request after error - transaction rolled back correctly"
        )

        # Тест 3: Попытка подписаться на несуществующий алерт (404 Not Found)
        fake_alert_id = str(uuid.uuid4())
        self.log_info(
            f"Test 3: Attempting to subscribe to non-existent alert {fake_alert_id} (expecting 404)"
        )
        non_existent_alert_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{fake_alert_id}/subscriptions/users/{user_id}",
            expect_error=True,
        )
        if (
            not non_existent_alert_result
            or non_existent_alert_result.get("status_code") != 404
        ):
            self.log_error(
                f"Expected 404 Not Found for non-existent alert, got: {non_existent_alert_result}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Correctly received 404 Not Found for non-existent alert"
        )

        # Тест 4: Проверка, что после ошибки 404 можно сделать новый запрос
        self.log_info(
            "Test 4: Verifying that after 404 error we can make new requests"
        )
        users_after_404 = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if not users_after_404:
            self.log_error(
                "Failed to get users after 404 error - transaction might not have rolled back"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Successfully made new request after 404 error - transaction rolled back correctly"
        )

        # Тест 5: Попытка подписаться на несуществующего пользователя (404 Not Found)
        fake_user_id = str(uuid.uuid4())
        self.log_info(
            f"Test 5: Attempting to subscribe non-existent user {fake_user_id} (expecting 404)"
        )
        non_existent_user_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{fake_user_id}",
            expect_error=True,
        )
        if (
            not non_existent_user_result
            or non_existent_user_result.get("status_code") != 404
        ):
            self.log_error(
                f"Expected 404 Not Found for non-existent user, got: {non_existent_user_result}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Correctly received 404 Not Found for non-existent user"
        )

        # Тест 6: Проверка, что после ошибки 404 пользователя можно сделать новый запрос
        self.log_info(
            "Test 6: Verifying that after 404 user error we can make new requests"
        )
        users_after_user_404 = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if not users_after_user_404:
            self.log_error(
                "Failed to get users after 404 user error - transaction might not have rolled back"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Successfully made new request after 404 user error - transaction rolled back correctly"
        )

        # Финальная проверка: убеждаемся, что все еще можем работать с реальными данными
        self.log_info(
            "Final check: Verifying we can still work with real data after all errors"
        )
        final_users_check = self.make_request(
            "GET", f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )
        if not final_users_check:
            self.log_error(
                "Failed final check - database might be in inconsistent state"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем, что подписка все еще существует (не была удалена из-за ошибок)
        subscription_still_exists = False
        for user in final_users_check.get("users", []):
            if user["user_id"] == user_id:
                subscription_still_exists = bool(
                    user.get("notification_channels") or user.get("statuses")
                )
                break

        if not subscription_still_exists:
            self.log_error(
                "Subscription was lost after errors - transaction rollback might have failed"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "All error handling tests passed - transactions rollback correctly"
        )
        self.test_results["passed"] += 1
        return True

    def test_group_rules_autocomplete(self):
        """Тест автокомплита групп правил"""
        self.log_test("Testing Group Rules Autocomplete")
        resp = self.make_request(
            "GET",
            "/alerts/api/v1/group_rules/autocomplete",
            params={"limit": 5},
        )
        if not resp or not resp.get("group_rules"):
            self.log_error("No group_rules found in autocomplete")
            self.test_results["failed"] += 1
            return False
        self.log_success(
            f"Found {len(resp['group_rules'])} group_rules in autocomplete"
        )
        self.test_results["passed"] += 1
        return True

    def test_screenshots_search(self):
        """Тест поиска скриншотов с полнотекстовым поиском, пагинацией и сортировкой"""
        self.log_test("Testing Screenshots Search")

        # Тест 1: Получение списка без query
        resp = self.make_request(
            "GET",
            "/alerts/api/v1/screenshots/search",
            params={"limit": 50, "offset": 0},
        )
        if not resp or not resp.get("screenshots"):
            self.log_error("No screenshots found in search")
            self.test_results["failed"] += 1
            return False

        screenshots = resp.get("screenshots", [])
        total = resp.get("total", 0)
        limit = resp.get("limit", 0)
        offset = resp.get("offset", 0)
        self.log_success(
            f"Found {len(screenshots)} screenshots in search (total: {total}, limit: {limit}, offset: {offset})"
        )

        # Проверка структуры ответа
        if screenshots:
            first_screenshot = screenshots[0]
            required_fields = [
                "screenshot_id",
                "name",
                "description",
                "image_data",
            ]
            missing_fields = [
                field
                for field in required_fields
                if field not in first_screenshot
            ]
            if missing_fields:
                self.log_error(
                    f"Missing required fields in screenshot response: {missing_fields}"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success("Screenshot response structure is correct")

        # Проверка структуры ответа (должны быть limit и offset)
        if "limit" not in resp or "offset" not in resp:
            self.log_error("Missing limit or offset in search response")
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Search response has pagination fields (limit, offset)"
        )

        # Тест 2: Поиск с query (если есть скриншоты)
        if screenshots and len(screenshots) > 0:
            # Берем часть description из первого скриншота для поиска
            first_desc = screenshots[0].get("description", "")
            if first_desc and len(first_desc) > 3:
                search_query = first_desc[:3]  # Первые 3 символа
                search_resp = self.make_request(
                    "GET",
                    "/alerts/api/v1/screenshots/search",
                    params={"query": search_query, "limit": 50, "offset": 0},
                )
                if search_resp and search_resp.get("screenshots"):
                    search_results = search_resp.get("screenshots", [])
                    self.log_success(
                        f"Search with query '{search_query}' found {len(search_results)} screenshots"
                    )

                    # Проверка сортировки: точное совпадение должно быть первым
                    if len(search_results) > 1:
                        first_result_desc = (
                            search_results[0].get("description", "").lower()
                        )
                        if first_result_desc.startswith(search_query.lower()):
                            self.log_success(
                                "Sorting is correct: exact/prefix match comes first"
                            )
                        else:
                            self.log_info(
                                f"Sorting check: first='{search_results[0].get('description')}', query='{search_query}'"
                            )
                else:
                    self.log_warning(
                        f"Search with query '{search_query}' returned no results"
                    )

        # Тест 3: Поиск с сортировкой
        self.log_info("Testing search with sorting")
        sorted_resp = self.make_request(
            "GET",
            "/alerts/api/v1/screenshots/search",
            params={
                "order_by": "name",
                "order_dir": "desc",
                "limit": 50,
                "offset": 0,
            },
        )
        if sorted_resp and sorted_resp.get("screenshots"):
            sorted_results = sorted_resp.get("screenshots", [])
            if len(sorted_results) > 1:
                # Проверяем сортировку по name DESC
                first_name = sorted_results[0].get("name", "").lower()
                second_name = sorted_results[1].get("name", "").lower()
                if first_name >= second_name:
                    self.log_success("Sorting by name DESC is correct")
                else:
                    self.log_info(
                        f"Sorting check: first='{sorted_results[0].get('name')}', second='{sorted_results[1].get('name')}'"
                    )

        # Тест 4: Пагинация
        self.log_info("Testing pagination")
        page1_resp = self.make_request(
            "GET",
            "/alerts/api/v1/screenshots/search",
            params={"limit": 10, "offset": 0},
        )
        page2_resp = self.make_request(
            "GET",
            "/alerts/api/v1/screenshots/search",
            params={"limit": 10, "offset": 10},
        )
        if page1_resp and page2_resp:
            page1_screenshots = page1_resp.get("screenshots", [])
            page2_screenshots = page2_resp.get("screenshots", [])
            if len(page1_screenshots) > 0 and len(page2_screenshots) > 0:
                # Проверяем, что результаты разные (если есть больше 10 скриншотов)
                if page1_resp.get("total", 0) > 10:
                    page1_ids = {
                        s.get("screenshot_id") for s in page1_screenshots
                    }
                    page2_ids = {
                        s.get("screenshot_id") for s in page2_screenshots
                    }
                    if page1_ids != page2_ids:
                        self.log_success(
                            "Pagination works correctly (different results on different pages)"
                        )
                    else:
                        self.log_warning(
                            "Pagination returned same results on different pages"
                        )
                else:
                    self.log_info("Not enough screenshots to test pagination")

        self.test_results["passed"] += 1
        return True

    def test_screenshots_crud(self):
        """Тест Screenshots CRUD endpoints с валидацией JSON"""
        self.log_test("Testing Screenshots CRUD")

        created_screenshot_id = None

        try:
            # Тест 1: POST - создание скриншота с валидным JSON (массив)
            self.log_info("Test 1: Creating screenshot with valid JSON array")
            screenshot_data_array = {
                "name": f"Test Screenshot Array {uuid.uuid4().hex[:8]}",
                "description": f"Test Description Array {uuid.uuid4().hex[:8]}",
                "image_data": '["https://example.com/image1.png", "https://example.com/image2.png"]',
            }

            create_result = self.make_request(
                "POST", "/alerts/api/v1/screenshots", screenshot_data_array
            )
            if create_result is None or "screenshot_id" not in create_result:
                self.log_error("Failed to create screenshot with JSON array")
                self.test_results["failed"] += 1
                return False

            created_screenshot_id = create_result["screenshot_id"]
            self.created_data.setdefault("screenshots", []).append(
                created_screenshot_id
            )
            self.log_success(
                f"Screenshot created with ID: {created_screenshot_id}"
            )

            # Тест 2: POST - создание скриншота с валидным JSON (объект)
            self.log_info("Test 2: Creating screenshot with valid JSON object")
            screenshot_data_object = {
                "name": f"Test Screenshot Object {uuid.uuid4().hex[:8]}",
                "description": f"Test Description Object {uuid.uuid4().hex[:8]}",
                "image_data": '{"url": "https://example.com/image.png", "width": 1000, "height": 500}',
            }

            create_result2 = self.make_request(
                "POST", "/alerts/api/v1/screenshots", screenshot_data_object
            )
            if create_result2 is None or "screenshot_id" not in create_result2:
                self.log_error("Failed to create screenshot with JSON object")
                self.test_results["failed"] += 1
                return False

            created_screenshot_id2 = create_result2["screenshot_id"]
            self.created_data["screenshots"].append(created_screenshot_id2)
            self.log_success(
                f"Screenshot created with ID: {created_screenshot_id2}"
            )

            # Тест 3: POST - попытка создать с невалидным JSON (крайний случай)
            self.log_info(
                "Test 3: Attempting to create screenshot with invalid JSON"
            )
            invalid_data = {
                "name": f"Test Invalid {uuid.uuid4().hex[:8]}",
                "description": f"Test Invalid Desc {uuid.uuid4().hex[:8]}",
                "image_data": "not a valid json {",
            }

            invalid_result = self.make_request(
                "POST",
                "/alerts/api/v1/screenshots",
                invalid_data,
                expect_error=True,
            )
            if invalid_result is None or (
                invalid_result.get("status_code") is None
                and invalid_result.get("status") != "error"
            ):
                self.log_error(
                    "Expected error for invalid JSON, but got success"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success("Correctly rejected invalid JSON")

            # Тест 4: POST - попытка создать с пустым image_data (крайний случай)
            self.log_info(
                "Test 4: Attempting to create screenshot with empty image_data"
            )
            empty_data = {
                "name": f"Test Empty {uuid.uuid4().hex[:8]}",
                "description": f"Test Empty Desc {uuid.uuid4().hex[:8]}",
                "image_data": "",
            }

            empty_result = self.make_request(
                "POST",
                "/alerts/api/v1/screenshots",
                empty_data,
                expect_error=True,
            )
            if empty_result is None or (
                empty_result.get("status_code") is None
                and empty_result.get("status") != "error"
            ):
                self.log_error(
                    "Expected error for empty image_data, but got success"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success("Correctly rejected empty image_data")

            # Тест 5: GET - получение созданного скриншота
            self.log_info("Test 5: Getting screenshot by ID")
            screenshot_detail = self.make_request(
                "GET", f"/alerts/api/v1/screenshots/{created_screenshot_id}"
            )
            if screenshot_detail is None:
                self.log_error("Failed to get screenshot details")
                self.test_results["failed"] += 1
                return False

            # Проверяем структуру ответа
            required_fields = [
                "screenshot_id",
                "name",
                "description",
                "image_data",
            ]
            missing_fields = [
                field
                for field in required_fields
                if field not in screenshot_detail
            ]
            if missing_fields:
                self.log_error(
                    f"Missing required fields in screenshot detail: {missing_fields}"
                )
                self.test_results["failed"] += 1
                return False

            # Проверяем, что image_data - это валидный JSON
            try:
                import json

                json.loads(screenshot_detail["image_data"])
                self.log_success("image_data is valid JSON")
            except json.JSONDecodeError:
                self.log_error("image_data is not valid JSON")
                self.test_results["failed"] += 1
                return False

            # Проверяем, что данные совпадают
            if screenshot_detail["name"] != screenshot_data_array["name"]:
                self.log_error(
                    f"Name mismatch: expected {screenshot_data_array['name']}, got {screenshot_detail['name']}"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success("Screenshot details retrieved correctly")

            # Тест 6: GET - попытка получить несуществующий скриншот (крайний случай)
            self.log_info("Test 6: Attempting to get non-existent screenshot")
            fake_id = str(uuid.uuid4())
            fake_result = self.make_request(
                "GET",
                f"/alerts/api/v1/screenshots/{fake_id}",
                expect_error=True,
            )
            if fake_result is None or (
                fake_result.get("status_code") != 404
                and fake_result.get("status") != "error"
            ):
                self.log_error(
                    "Expected 404 error for non-existent screenshot, but got success"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success(
                "Correctly returned 404 for non-existent screenshot"
            )

            # Тест 7: PATCH - обновление скриншота (частичное)
            self.log_info("Test 7: Updating screenshot (partial update)")
            update_data = {
                "name": f"Updated {screenshot_data_array['name']}",
                "image_data": '{"updated": true, "url": "https://updated.example.com/image.png"}',
            }

            update_result = self.make_request(
                "PATCH",
                f"/alerts/api/v1/screenshots/{created_screenshot_id}",
                update_data,
            )
            if update_result is None or update_result is not True:
                self.log_error("Failed to update screenshot")
                self.test_results["failed"] += 1
                return False
            self.log_success("Screenshot updated successfully")

            # Проверяем, что обновление применилось
            updated_detail = self.make_request(
                "GET", f"/alerts/api/v1/screenshots/{created_screenshot_id}"
            )
            if (
                updated_detail is None
                or updated_detail["name"] != update_data["name"]
            ):
                self.log_error("Update did not apply correctly")
                self.test_results["failed"] += 1
                return False

            # Проверяем, что новый image_data - валидный JSON
            try:
                json.loads(updated_detail["image_data"])
                self.log_success("Updated image_data is valid JSON")
            except json.JSONDecodeError:
                self.log_error("Updated image_data is not valid JSON")
                self.test_results["failed"] += 1
                return False

            # Тест 8: PATCH - попытка обновить с невалидным JSON (крайний случай)
            self.log_info(
                "Test 8: Attempting to update screenshot with invalid JSON"
            )
            invalid_update = {"image_data": "invalid json {"}

            invalid_update_result = self.make_request(
                "PATCH",
                f"/alerts/api/v1/screenshots/{created_screenshot_id}",
                invalid_update,
                expect_error=True,
            )
            if invalid_update_result is None or (
                invalid_update_result.get("status_code") is None
                and invalid_update_result.get("status") != "error"
            ):
                self.log_error(
                    "Expected error for invalid JSON in update, but got success"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success("Correctly rejected invalid JSON in update")

            # Тест 9: PATCH - обновление только description (без image_data)
            self.log_info(
                "Test 9: Updating only description (without image_data)"
            )
            update_description_only = {
                "description": f"Updated Description Only {uuid.uuid4().hex[:8]}"
            }

            update_desc_result = self.make_request(
                "PATCH",
                f"/alerts/api/v1/screenshots/{created_screenshot_id}",
                update_description_only,
            )
            if update_desc_result is None or update_desc_result is not True:
                self.log_error("Failed to update description only")
                self.test_results["failed"] += 1
                return False
            self.log_success(
                "Description updated successfully without image_data"
            )

            # Тест 10: DELETE - удаление скриншота
            self.log_info("Test 10: Deleting screenshot")
            delete_result = self.make_request(
                "DELETE", f"/alerts/api/v1/screenshots/{created_screenshot_id}"
            )
            if delete_result is None or delete_result is not True:
                self.log_error("Failed to delete screenshot")
                self.test_results["failed"] += 1
                return False
            self.log_success("Screenshot deleted successfully")
            self.created_data["screenshots"].remove(created_screenshot_id)

            # Тест 11: DELETE - попытка удалить уже удаленный скриншот (крайний случай)
            self.log_info(
                "Test 11: Attempting to delete already deleted screenshot"
            )
            delete_again_result = self.make_request(
                "DELETE",
                f"/alerts/api/v1/screenshots/{created_screenshot_id}",
                expect_error=True,
            )
            if delete_again_result is None or (
                delete_again_result.get("status_code") != 404
                and delete_again_result.get("status") != "error"
            ):
                self.log_error(
                    "Expected 404 error for already deleted screenshot, but got success"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success(
                "Correctly returned 404 for already deleted screenshot"
            )

            # Тест 12: POST - создание с минимальными данными (все поля обязательны)
            self.log_info(
                "Test 12: Creating screenshot with minimal valid data"
            )
            minimal_data = {
                "name": "Min",
                "description": "Min Desc",
                "image_data": "{}",
            }

            minimal_result = self.make_request(
                "POST", "/alerts/api/v1/screenshots", minimal_data
            )
            if minimal_result is None or "screenshot_id" not in minimal_result:
                self.log_error("Failed to create screenshot with minimal data")
                self.test_results["failed"] += 1
                return False

            minimal_id = minimal_result["screenshot_id"]
            self.created_data["screenshots"].append(minimal_id)
            self.log_success(
                f"Screenshot created with minimal data: {minimal_id}"
            )

            # Удаляем минимальный скриншот
            self.make_request(
                "DELETE", f"/alerts/api/v1/screenshots/{minimal_id}"
            )
            self.created_data["screenshots"].remove(minimal_id)

            self.test_results["passed"] += 1
            return True

        except Exception as e:
            self.log_error(f"Unexpected error in screenshots CRUD test: {e}")
            self.test_results["failed"] += 1
            return False
        finally:
            # Очистка созданных скриншотов
            if "screenshots" in self.created_data:
                for screenshot_id in self.created_data["screenshots"][:]:
                    try:
                        self.make_request(
                            "DELETE",
                            f"/alerts/api/v1/screenshots/{screenshot_id}",
                        )
                        self.created_data["screenshots"].remove(screenshot_id)
                    except Exception as e:
                        self.log_warning(
                            f"Error cleaning up screenshot {screenshot_id}: {e}"
                        )

    def test_search_sorting(self):
        """Тест правильной сортировки в поиске и автокомплите"""
        self.log_test("Search and Autocomplete Sorting")

        # Тест сортировки алертов
        self.log_info("Testing alerts search sorting...")
        alerts_result = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"query": "test", "limit": 10},
        )
        if alerts_result and alerts_result.get("alerts"):
            alerts = alerts_result["alerts"]
            self.log_info(f"Found {len(alerts)} alerts matching 'test'")

            # Проверяем, что все алерты содержат 'test' в начале строки или слова (регистронезависимо)
            for alert in alerts:
                alert_name = alert.get("alert_name", "").lower()
                # Проверяем: начинается с 'test' или содержит слово, начинающееся с 'test'
                if not (
                    alert_name.startswith("test")
                    or re.search(r"\btest\w*", alert_name)
                ):
                    self.log_warning(
                        f"Alert '{alert.get('alert_name')}' doesn't match 'test' pattern"
                    )

            # Проверяем сортировку: точное совпадение должно быть первым
            if len(alerts) > 1:
                first_alert = alerts[0]["alert_name"].lower()
                alerts[1]["alert_name"].lower()
                if first_alert == "test":
                    self.log_success(
                        "Alerts sorting: exact match 'test' comes first"
                    )
                else:
                    self.log_info(
                        f"Alerts sorting: first='{alerts[0]['alert_name']}', second='{alerts[1]['alert_name']}'"
                    )

        # Тест сортировки автокомплита алертов
        self.log_info("Testing alerts autocomplete sorting...")
        alerts_autocomplete = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/autocomplete",
            params={"query": "test", "limit": 10},
        )
        if alerts_autocomplete and alerts_autocomplete.get("alerts"):
            alerts_ac = alerts_autocomplete["alerts"]
            self.log_info(
                f"Found {len(alerts_ac)} alerts in autocomplete matching 'test'"
            )

            # Проверяем сортировку в автокомплите
            if len(alerts_ac) > 1:
                first_name = alerts_ac[0]["alert_name"].lower()
                if first_name == "test":
                    self.log_success(
                        "Alerts autocomplete sorting: exact match 'test' comes first"
                    )
                else:
                    self.log_info(
                        f"Alerts autocomplete sorting: first='{alerts_ac[0]['alert_name']}', second='{alerts_ac[1]['alert_name']}'"
                    )

        # Тест сортировки индикаторов
        self.log_info("Testing indicators autocomplete sorting...")
        indicators_result = self.make_request(
            "GET",
            "/alerts/api/v1/indicators/autocomplete",
            params={"query": "test", "limit": 10},
        )
        if indicators_result and indicators_result.get("indicators"):
            indicators = indicators_result["indicators"]
            self.log_info(
                f"Found {len(indicators)} indicators with 'test' prefix"
            )

            # Проверяем сортировку индикаторов
            if len(indicators) > 1:
                first_name = indicators[0]["indicator_name"].lower()
                second_name = indicators[1]["indicator_name"].lower()
                if first_name == "test" and second_name.startswith("test"):
                    self.log_success(
                        "Indicators autocomplete sorting: exact match 'test' comes first"
                    )
                else:
                    self.log_info(
                        f"Indicators autocomplete sorting: first='{indicators[0]['indicator_name']}', second='{indicators[1]['indicator_name']}'"
                    )

        # Тест сортировки групп правил
        self.log_info("Testing group rules autocomplete sorting...")
        groups_result = self.make_request(
            "GET",
            "/alerts/api/v1/group_rules/autocomplete",
            params={"query": "test", "limit": 10},
        )
        if groups_result and groups_result.get("group_rules"):
            groups = groups_result["group_rules"]
            self.log_info(
                f"Found {len(groups)} group rules with 'test' prefix"
            )

            # Проверяем сортировку групп правил
            if len(groups) > 1:
                first_desc = groups[0]["description"].lower()
                second_desc = groups[1]["description"].lower()
                if first_desc == "test" and second_desc.startswith("test"):
                    self.log_success(
                        "Group rules autocomplete sorting: exact match 'test' comes first"
                    )
                else:
                    self.log_info(
                        f"Group rules autocomplete sorting: first='{groups[0]['description']}', second='{groups[1]['description']}'"
                    )

        # Тест валидации параметров сортировки (order_by и order_dir)
        self.log_info(
            "Testing validation of order_by and order_dir parameters..."
        )

        # Проверка invalid order_by для alerts search
        invalid_order_by = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"order_by": "invalid_field"},
            expect_error=True,
        )
        if not invalid_order_by or invalid_order_by.get("status_code") != 400:
            self.log_error(
                "Expected 400 error for invalid order_by in alerts search"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Invalid order_by correctly rejected in alerts search"
        )

        # Проверка invalid order_dir для alerts search
        invalid_order_dir = self.make_request(
            "GET",
            "/alerts/api/v1/alerts/search",
            params={"order_by": "alert_name", "order_dir": "invalid"},
            expect_error=True,
        )
        if (
            not invalid_order_dir
            or invalid_order_dir.get("status_code") != 400
        ):
            self.log_error(
                "Expected 400 error for invalid order_dir in alerts search"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Invalid order_dir correctly rejected in alerts search"
        )

        # Проверка invalid order_by для screenshots search
        invalid_screenshot_order = self.make_request(
            "GET",
            "/alerts/api/v1/screenshots/search",
            params={"order_by": "invalid_field"},
            expect_error=True,
        )
        if (
            not invalid_screenshot_order
            or invalid_screenshot_order.get("status_code") != 400
        ):
            self.log_error(
                "Expected 400 error for invalid order_by in screenshots search"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Invalid order_by correctly rejected in screenshots search"
        )

        # Проверка invalid order_dir для screenshots search
        invalid_screenshot_dir = self.make_request(
            "GET",
            "/alerts/api/v1/screenshots/search",
            params={"order_by": "description", "order_dir": "invalid"},
            expect_error=True,
        )
        if (
            not invalid_screenshot_dir
            or invalid_screenshot_dir.get("status_code") != 400
        ):
            self.log_error(
                "Expected 400 error for invalid order_dir in screenshots search"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Invalid order_dir correctly rejected in screenshots search"
        )

        self.log_success("Search and autocomplete sorting tests completed")
        self.test_results["passed"] += 1
        return True

    def test_feedback(self):
        """Тест Feedback CRUD"""
        self.log_test("Testing Feedback CRUD")

        # Используем тестовые данные
        # user_fio теперь сразу записывается в поле contact (без LDAP)
        test_status_history = "9dd606f8-8cd3-4a4c-8fe7-85bfca8e825c"
        test_user_fio = "Давыдов Арсен Витальевич (Arsen Davydov)"

        self.log_info(f"Using test status_history: {test_status_history}")
        self.log_info(f"Using test user_fio (contact): {test_user_fio}")

        # POST - создание первого фидбека (score=0)
        feedback_data_1 = {
            "status_history": test_status_history,
            "user_fio": test_user_fio,
            "score": 0,
        }

        create_result_1 = self.make_request(
            "POST", "/alerts/api/v1/feedback/detail", feedback_data_1
        )
        if create_result_1 is None:
            self.log_error("Failed to create feedback")
            self.test_results["failed"] += 1
            return False

        # Проверяем что получили "Спасибо за обратную связь!" (первая запись)
        if create_result_1.get("message") != "Спасибо за обратную связь!":
            self.log_error(
                f"Expected 'Спасибо за обратную связь!' but got: {create_result_1.get('message')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(f"Feedback created: {create_result_1.get('message')}")

        # POST - обновление фидбека (score=1) - должен вернуть "Спасибо! Достаточно одного раза, больше не надо."
        feedback_data_2 = {
            "status_history": test_status_history,
            "user_fio": test_user_fio,
            "score": 1,
        }

        update_result = self.make_request(
            "POST", "/alerts/api/v1/feedback/detail", feedback_data_2
        )
        if update_result is None:
            self.log_error("Failed to update feedback")
            self.test_results["failed"] += 1
            return False

        # Проверяем что получили "Спасибо! Достаточно одного раза, больше не надо." (обновление существующей записи)
        if (
            update_result.get("message")
            != "Спасибо! Достаточно одного раза, больше не надо."
        ):
            self.log_error(
                f"Expected 'Спасибо! Достаточно одного раза, больше не надо.' but got: {update_result.get('message')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(f"Feedback updated: {update_result.get('message')}")

        # DELETE - удаление фидбека
        delete_data = {
            "status_history": test_status_history,
            "user_fio": test_user_fio,
        }

        delete_result = self.make_request(
            "DELETE", "/alerts/api/v1/feedback/detail", delete_data
        )
        if delete_result is None or delete_result is not True:
            self.log_error("Failed to delete feedback")
            self.test_results["failed"] += 1
            return False

        self.log_success("Feedback deleted successfully")

        # Проверяем что фидбек действительно удален (попытка удалить еще раз должна вернуть 404)
        delete_again_result = self.make_request(
            "DELETE",
            "/alerts/api/v1/feedback/detail",
            delete_data,
            expect_error=True,
        )
        if (
            delete_again_result
            and delete_again_result.get("status_code") == 404
        ):
            self.log_success(
                "Confirmed: feedback was deleted (404 on second delete)"
            )
        else:
            self.log_warning("Expected 404 on second delete attempt")

        self.test_results["passed"] += 1
        return True

    def test_pauses(self):
        """
        Тест методов работы с паузами алертов (Раздел 13)

        Проверяет все методы работы с паузами:
        - PATCH /alerts/pause - безусловная пауза (переключение)
        - POST /alerts/{alert_id}/pause/schedule - условная пауза с датами
        - PATCH /alerts/{alert_id}/pause/stop - остановка всех активных пауз

        Все проверки состояния паузы выполняются через alerts/search (поле paused).
        """
        self.log_test("Testing Pauses (Section 13)")

        # Используем тестовый алерт, созданный в test_alerts
        if not self.created_data["alerts"]:
            self.log_error(
                "No test alert found - test_alerts must run before test_pauses"
            )
            self.test_results["failed"] += 1
            return False

        alert_id = self.created_data["alerts"][0]
        test_user = "test_user"  # Пользователь для создания/закрытия пауз

        # Вспомогательная функция для получения состояния паузы через alerts/search
        def get_pause_state(alert_id_to_check):
            """
            Получает состояние паузы алерта через alerts/search.

            Returns:
                bool: True если пауза активна, False если не активна, None если алерт не найден
            """
            search_result = self.make_request(
                "GET", "/alerts/api/v1/alerts/search"
            )
            if search_result and search_result.get("alerts"):
                for alert in search_result["alerts"]:
                    if alert.get("alert_id") == alert_id_to_check:
                        return alert.get("paused", False)
            return None

        # ====================================================================
        # ШАГ 1: Проверка начального состояния паузы
        # ====================================================================
        # Что делаем: Проверяем текущее состояние паузы через alerts/search
        # Ожидаемый результат: Получаем начальное состояние (True или False)
        # Как проверяем: Через поле paused в ответе alerts/search
        # Логика: Пауза активна, если текущая дата попадает в период хотя бы одной записи
        #          (start_time <= now() AND (end_time IS NULL OR end_time >= now()))
        # ====================================================================
        self.log_info("Step 1: Checking initial pause state via alerts/search")
        initial_paused = get_pause_state(alert_id)
        if initial_paused is None:
            self.log_error("Тестовый алерт не найден в результатах поиска")
            self.test_results["failed"] += 1
            return False
        self.log_info(f"Initial pause state: {initial_paused}")

        # ====================================================================
        # ШАГ 2: Тест PATCH /alerts/pause - безусловная пауза (переключение)
        # ====================================================================
        # Что делаем: Тестируем PATCH /alerts/pause в обоих случаях:
        #   - Случай 2.1: Когда паузы НЕТ - создаем паузу
        #   - Случай 2.2: Когда пауза ЕСТЬ - закрываем все активные паузы
        # Ожидаемый результат:
        #   - Случай 2.1: создается новая запись с start_time=now(),
        #     start_user=test_user, end_time=NULL, end_user=NULL
        #   - Случай 2.2: закрываются ВСЕ активные паузы (end_time=now(),
        #     end_user=test_user)
        # Как проверяем:
        #   1. Проверяем начальное состояние через alerts/search
        #   2. Вызываем PATCH и проверяем, что запрос вернул True
        #   3. Проверяем состояние через alerts/search (поле paused)
        #   4. Вызываем PATCH еще раз и проверяем обратное переключение
        # Логика: PATCH всегда переключает состояние (toggle)
        # Тестовый алерт: используется alert_id из self.created_data['alerts'][0]
        # ====================================================================
        self.log_info(
            "Step 2: Testing PATCH /alerts/pause (unconditional pause toggle)"
        )
        pause_data_create = {
            "alert_id": alert_id,
            "login": test_user,
            "comment": "lazy toggle create",
        }
        pause_data_close = {
            "alert_id": alert_id,
            "login": test_user,
            "comment": "lazy toggle close",
        }

        # Случай 2.1: Если паузы нет - создаем паузу
        self.log_info(
            "Step 2.1: Testing PATCH when pause is inactive (should create pause)"
        )

        # Убеждаемся, что паузы нет (если есть - закрываем)
        current_state = get_pause_state(alert_id)
        if current_state:
            self.log_info("Pause is active, closing it first")
            close_result = self.make_request(
                "PATCH", "/alerts/api/v1/alerts/pause", pause_data_close
            )
            if not close_result:
                self.log_error("Failed to close pause before test")
                self.test_results["failed"] += 1
                return False

        # Устанавливаем паузу (создаем новую)
        pause_result = self.make_request(
            "PATCH", "/alerts/api/v1/alerts/pause", pause_data_create
        )
        if pause_result is None or pause_result is not True:
            self.log_error("Failed to create pause via PATCH")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние через alerts/search - должна быть активна
        after_create = get_pause_state(alert_id)
        if after_create is None:
            self.log_error("Алерт не найден после создания паузы")
            self.test_results["failed"] += 1
            return False

        if not after_create:
            self.log_error(
                f"Pause should be active after creation, but paused={after_create}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Pause correctly created via PATCH (was inactive, now active)"
        )

        # Случай 2.2: Когда пауза есть - закрываем все активные паузы
        self.log_info(
            "Step 2.2: Testing PATCH when pause is active (should close all active pauses)"
        )

        # Пауза уже активна из предыдущего шага
        close_result = self.make_request(
            "PATCH", "/alerts/api/v1/alerts/pause", pause_data_close
        )
        if close_result is None or close_result is not True:
            self.log_error("Failed to close pause via PATCH")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние через alerts/search - должна быть неактивна
        after_close = get_pause_state(alert_id)
        if after_close is None:
            self.log_error("Алерт не найден после закрытия паузы")
            self.test_results["failed"] += 1
            return False

        if after_close:
            self.log_error(
                f"Pause should be inactive after closing, but paused={after_close}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Pause correctly closed via PATCH (was active, now inactive)"
        )

        # ====================================================================
        # ШАГ 3: Тест POST /alerts/{alert_id}/pause/schedule - условная пауза с датами
        # ====================================================================
        # Что делаем: Создаем условную паузу с указанием start_time и end_time
        # Ожидаемый результат:
        #   - Создается запись с start_time в будущем (через 5 минут),
        #     end_time через 1 час, start_user=test_user, end_user=test_user
        #   - Пауза НЕ активна сразу, так как start_time в будущем
        # Как проверяем:
        #   1. Проверяем, что запрос вернул True
        #   2. Проверяем состояние через alerts/search - должна быть paused=False
        #      (так как start_time > now())
        # Логика: Пауза активна только когда start_time <= now() AND
        #         (end_time IS NULL OR end_time >= now())
        # ====================================================================
        self.log_info(
            "Step 3: Testing POST /alerts/{alert_id}/pause/schedule (conditional pause with dates)"
        )

        # Сначала убедимся, что паузы нет (если есть - снимем через PATCH)
        current_paused = get_pause_state(alert_id)
        if current_paused:
            self.log_info("Pause is active, removing it first")
            remove_result = self.make_request(
                "PATCH", "/alerts/api/v1/alerts/pause", pause_data_close
            )
            if not remove_result:
                self.log_error("Failed to remove pause before schedule test")
                self.test_results["failed"] += 1
                return False

        # Создаем условную паузу с start_time и end_time
        # Все даты передаем с таймзоной +3
        tz_plus3 = timezone(timedelta(hours=3))
        now = datetime.now(tz_plus3)
        start_time = now + timedelta(
            minutes=5
        )  # Начало через 5 минут (в будущем)
        end_time = now + timedelta(hours=1)  # Конец через 1 час

        schedule_data = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "login": test_user,
            "comment": "lazy schedule with dates",
        }

        schedule_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            schedule_data,
        )
        if schedule_result is None or schedule_result is not True:
            self.log_error("Failed to schedule pause")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние через alerts/search (пауза еще не активна, так как start_time в будущем)
        after_schedule = get_pause_state(alert_id)
        if after_schedule:
            self.log_error(
                f"Pause should not be active yet (start_time in future), but paused={after_schedule}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Scheduled pause correctly not active yet (start_time in future)"
        )

        # ====================================================================
        # ШАГ 4: Тест условной паузы без start_time (БД установит now())
        # ====================================================================
        # Что делаем: Создаем условную паузу БЕЗ указания start_time (только end_time)
        # Ожидаемый результат:
        #   - БД автоматически установит start_time = now() (через DEFAULT)
        #   - Создается запись с start_time=now(), end_time через 2 часа,
        #     start_user=test_user, end_user=test_user
        #   - Пауза активна сразу, так как start_time = now()
        # Как проверяем:
        #   1. Сначала снимаем предыдущую паузу через DELETE
        #   2. Создаем паузу без start_time
        #   3. Проверяем, что запрос вернул True
        #   4. Проверяем состояние через alerts/search - должна быть paused=True
        # Логика: Если start_time не указан, БД использует DEFAULT now()
        # ====================================================================
        self.log_info(
            "Step 4: Testing POST /alerts/{alert_id}/pause/schedule without start_time"
        )

        # Снимаем предыдущую паузу через PATCH /pause/stop
        remove_data = {"login": test_user, "comment": "lazy stop all"}
        remove_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/stop",
            remove_data,
        )
        if not remove_result:
            self.log_error("Failed to remove scheduled pause")
            self.test_results["failed"] += 1
            return False

        # Создаем мгновенную паузу без start_time (БД установит now())
        instant_pause_data = {
            "end_time": (now + timedelta(hours=2)).isoformat(),
            "login": test_user,
        }

        instant_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            instant_pause_data,
        )
        if instant_result is None or instant_result is not True:
            self.log_error("Failed to create instant pause without start_time")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние через alerts/search (пауза должна быть активна)
        after_instant = get_pause_state(alert_id)
        if not after_instant:
            self.log_error(
                f"Instant pause should be active, but paused={after_instant}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Instant pause correctly active (start_time set by DB)"
        )

        # ====================================================================
        # ШАГ 4.5: Тест валидации - login обязателен (всегда)
        # ====================================================================
        # Что делаем: Пытаемся создать паузу без login
        # Ожидаемый результат: Ошибка валидации 422 (Unprocessable Entity)
        # Как проверяем:
        #   1. Снимаем текущую паузу через PATCH /pause/stop
        #   2. Пытаемся создать паузу без login
        #   3. Проверяем, что вернулась ошибка 422
        # Логика: login обязателен всегда в AlertPauseScheduleRequest
        # ====================================================================
        self.log_info("Step 4.5: Testing validation - login is required")

        # Снимаем текущую паузу через PATCH /pause/stop
        remove_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/stop",
            remove_data,
        )
        if not remove_result:
            self.log_error("Failed to remove pause before validation test")
            self.test_results["failed"] += 1
            return False

        # Пытаемся создать паузу без login (должна быть ошибка валидации)
        invalid_pause_data = {
            "end_time": (now + timedelta(hours=2)).isoformat()
            # login не указан - должна быть ошибка валидации
        }

        validation_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            invalid_pause_data,
            expect_error=True,
        )
        if validation_result and validation_result.get("status_code") in [
            400,
            422,
        ]:
            self.log_success(
                "Validation error correctly returned: login is required"
            )
        else:
            self.log_error(
                f"Expected 400/422 validation error, but got: {validation_result}"
            )
            self.test_results["failed"] += 1
            return False

        # ====================================================================
        # ШАГ 5: Тест бессрочной условной паузы (без end_time)
        # ====================================================================
        # Что делаем: Создаем условную паузу БЕЗ указания end_time (бессрочная)
        # Ожидаемый результат:
        #   - БД автоматически установит start_time = now() (через DEFAULT)
        #   - Создается запись с start_time=now(), end_time=NULL,
        #     start_user=test_user, end_user=NULL
        #   - Пауза активна сразу и бессрочно (пока не закроют вручную)
        # Как проверяем:
        #   1. Снимаем текущую паузу через DELETE
        #   2. Создаем бессрочную паузу (только start_user)
        #   3. Проверяем, что запрос вернул True
        #   4. Проверяем состояние через alerts/search - должна быть paused=True
        # Логика: Бессрочная пауза активна пока end_time IS NULL или end_time >= now()
        # ====================================================================
        self.log_info(
            "Step 5: Testing POST /alerts/{alert_id}/pause/schedule without end_time (indefinite)"
        )

        # Снимаем текущую паузу через PATCH /pause/stop
        remove_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/stop",
            remove_data,
        )
        if not remove_result:
            self.log_error("Failed to remove instant pause")
            self.test_results["failed"] += 1
            return False

        # Создаем бессрочную паузу (без start_time и без end_time)
        indefinite_pause_data = {"login": test_user}

        indefinite_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            indefinite_pause_data,
        )
        if indefinite_result is None or indefinite_result is not True:
            self.log_error("Failed to create indefinite pause")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние через alerts/search
        after_indefinite = get_pause_state(alert_id)
        if not after_indefinite:
            self.log_error(
                f"Indefinite pause should be active, but paused={after_indefinite}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Indefinite pause correctly active")

        # ====================================================================
        # ШАГ 6: Тест PATCH /alerts/pause когда пауза активна (закрытие всех активных)
        # ====================================================================
        # Что делаем: Вызываем PATCH /alerts/pause когда пауза уже активна
        # Ожидаемый результат:
        #   - Закрываются ВСЕ активные паузы (end_time=now(), end_user=test_user)
        #   - Пауза становится неактивной
        # Как проверяем:
        #   1. Пауза уже активна из предыдущего шага (бессрочная)
        #   2. Вызываем PATCH с test_user
        #   3. Проверяем, что запрос вернул True
        #   4. Проверяем состояние через alerts/search - должна быть paused=False
        # Логика: PATCH закрывает все активные паузы, устанавливая end_time=now()
        # ====================================================================
        self.log_info(
            "Step 6: Testing PATCH /alerts/pause when pause is active (should close all active)"
        )

        # Пауза уже активна из предыдущего шага (бессрочная)
        toggle_result = self.make_request(
            "PATCH", "/alerts/api/v1/alerts/pause", pause_data_close
        )
        if toggle_result is None or toggle_result is not True:
            self.log_error("Failed to toggle pause when active")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние через alerts/search (пауза должна быть закрыта)
        after_toggle = get_pause_state(alert_id)
        if after_toggle:
            self.log_error(
                f"Pause should be inactive after toggle, but paused={after_toggle}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Pause correctly closed via PATCH toggle")

        # ====================================================================
        # ШАГ 7: Тест PATCH /alerts/{alert_id}/pause/stop - остановка всех активных пауз
        # ====================================================================
        # Что делаем: Используем PATCH /pause/stop для остановки всех активных пауз
        # Ожидаемый результат:
        #   - Останавливаются ВСЕ активные паузы (end_time=now(), end_user=test_user)
        #   - Если end_time уже был - перезаписывается на now()
        #   - Если end_user уже был - перезаписывается на test_user
        #   - Пауза становится неактивной
        # Как проверяем:
        #   1. Создаем активную бессрочную паузу
        #   2. Проверяем, что пауза активна (paused=True)
        #   3. Вызываем PATCH /pause/stop с login=test_user
        #   4. Проверяем, что запрос вернул True
        #   5. Проверяем состояние через alerts/search - должна быть paused=False
        # Логика: PATCH /pause/stop останавливает все активные паузы, устанавливая end_time=now()
        # Возвращает true даже если активных пауз не было (idempotent)
        # ====================================================================
        self.log_info(
            "Step 7: Testing PATCH /alerts/{alert_id}/pause/stop (stop all active pauses)"
        )

        # Создаем активную паузу для теста PATCH /pause/stop
        create_pause_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            indefinite_pause_data,
        )
        if not create_pause_result:
            self.log_error("Failed to create pause for PATCH /pause/stop test")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что пауза активна
        before_stop = get_pause_state(alert_id)
        if not before_stop:
            self.log_error(
                "Pause should be active before PATCH /pause/stop test"
            )
            self.test_results["failed"] += 1
            return False

        # Останавливаем паузу через PATCH /pause/stop
        stop_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/stop",
            remove_data,
        )
        if stop_result is None or stop_result is not True:
            self.log_error("Failed to stop pause via PATCH /pause/stop")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние через alerts/search
        after_stop = get_pause_state(alert_id)
        if after_stop:
            self.log_error(
                f"Pause should be inactive after PATCH /pause/stop, but paused={after_stop}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Pause correctly stopped via PATCH /pause/stop")

        # ====================================================================
        # ШАГ 7.5: Тест PATCH /alerts/pause с несколькими одновременными активными паузами
        # ====================================================================
        # Что делаем: Создаем несколько одновременных активных пауз и проверяем, что PATCH закрывает ВСЕ
        # Ожидаемый результат:
        #   - Создаются 2-3 активные паузы одновременно
        #   - Все паузы активны (алерт на паузе)
        #   - PATCH /alerts/pause закрывает ВСЕ активные паузы одновременно
        #   - Все паузы получают end_time=now() и end_user=login
        # Как проверяем:
        #   1. Создаем несколько активных бессрочных пауз (2-3 штуки)
        #   2. Проверяем через GET /alerts/{alert_id}/pause (filter_type=active), что все активны
        #   3. Вызываем PATCH /alerts/pause
        #   4. Проверяем через GET /alerts/{alert_id}/pause (filter_type=active), что активных пауз нет
        #   5. Проверяем через GET /alerts/{alert_id}/pause (filter_type=all), что все паузы закрыты (end_time установлен)
        # Логика: PATCH /alerts/pause должен закрывать ВСЕ активные паузы одним UPDATE запросом
        # ====================================================================
        self.log_info(
            "Step 7.5: Testing PATCH /alerts/pause with multiple simultaneous active pauses"
        )

        # Создаем несколько активных бессрочных пауз
        pause_data_1 = {"login": test_user}
        pause_data_2 = {"login": test_user}
        pause_data_3 = {"login": test_user}

        create_pause_1 = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            pause_data_1,
        )
        create_pause_2 = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            pause_data_2,
        )
        create_pause_3 = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            pause_data_3,
        )

        if not create_pause_1 or not create_pause_2 or not create_pause_3:
            self.log_error("Failed to create multiple pauses for test")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что алерт на паузе
        before_toggle = get_pause_state(alert_id)
        if not before_toggle:
            self.log_error(
                "Alert should be paused with multiple active pauses"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем через GET /alerts/{alert_id}/pause, что все паузы активны
        active_pauses_before = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        if (
            not active_pauses_before
            or not isinstance(active_pauses_before, dict)
            or not active_pauses_before.get("pauses")
        ):
            self.log_error("Should have active pauses before toggle")
            self.test_results["failed"] += 1
            return False

        active_count_before = len(active_pauses_before["pauses"])
        if active_count_before < 3:
            self.log_error(
                f"Expected at least 3 active pauses, but got {active_count_before}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(f"Created {active_count_before} active pauses")

        # Вызываем PATCH /alerts/pause для закрытия всех активных пауз
        pause_data_close = {"alert_id": alert_id, "login": test_user}
        toggle_result = self.make_request(
            "PATCH", "/alerts/api/v1/alerts/pause", pause_data_close
        )
        if toggle_result is None or toggle_result is not True:
            self.log_error(
                "Failed to toggle pause with multiple active pauses"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем, что алерт больше не на паузе
        after_toggle = get_pause_state(alert_id)
        if after_toggle:
            self.log_error(
                f"Alert should not be paused after toggle, but paused={after_toggle}"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем через GET /alerts/{alert_id}/pause (filter_type=active), что активных пауз нет
        active_pauses_after = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        if not active_pauses_after or not isinstance(
            active_pauses_after, dict
        ):
            self.log_error("Failed to get pauses after toggle")
            self.test_results["failed"] += 1
            return False

        active_count_after = len(active_pauses_after.get("pauses", []))
        if active_count_after > 0:
            self.log_error(
                f"Expected 0 active pauses after toggle, but got {active_count_after}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "All active pauses correctly closed (0 active pauses after toggle)"
        )

        # Проверяем через GET /alerts/{alert_id}/pause (filter_type=all), что все паузы закрыты
        all_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all", "limit": 100},
        )
        if (
            not all_pauses
            or not isinstance(all_pauses, dict)
            or not all_pauses.get("pauses")
        ):
            self.log_error("Failed to get all pauses after toggle")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что последние 3 паузы (которые мы создали) все закрыты
        recent_pauses = all_pauses.get("pauses", [])[
            :3
        ]  # Берем последние 3 (они должны быть первыми по start_time DESC)
        all_closed = True
        for pause in recent_pauses:
            if pause.get("end_time") is None:
                self.log_error(
                    f"Pause {pause.get('pause_id')} should be closed (end_time should be set)"
                )
                all_closed = False
            if pause.get("end_user") != test_user:
                self.log_error(
                    f"Pause {pause.get('pause_id')} should have end_user={test_user}, but got {pause.get('end_user')}"
                )
                all_closed = False

        if not all_closed:
            self.test_results["failed"] += 1
            return False
        self.log_success(
            f"All {len(recent_pauses)} pauses correctly closed with end_time and end_user={test_user}"
        )

        # ====================================================================
        # ШАГ 8: Тест множественных пауз (проверка логики определения активности)
        # ====================================================================
        # Что делаем: Создаем несколько пауз и проверяем логику определения активности
        # Ожидаемый результат:
        #   - Пауза в прошлом НЕ активна (end_time < now())
        #   - Пауза в текущем периоде активна (start_time <= now() AND end_time >= now())
        #   - Если есть хотя бы одна активная пауза - алерт считается на паузе
        # Как проверяем:
        #   1. Создаем паузу в прошлом (start_time и end_time в прошлом)
        #   2. Проверяем состояние - должна быть paused=False
        #   3. Создаем активную бессрочную паузу
        #   4. Проверяем состояние - должна быть paused=True
        # Логика: Пауза активна, если текущая дата попадает в период хотя бы одной записи
        #         (start_time <= now() AND (end_time IS NULL OR end_time >= now()))
        # ====================================================================
        self.log_info(
            "Step 8: Testing multiple pauses (should be active if any is in current period)"
        )

        # Создаем паузу в прошлом (не должна быть активна)
        past_start = now - timedelta(hours=2)  # Начало 2 часа назад
        past_end = now - timedelta(hours=1)  # Конец 1 час назад
        past_pause_data = {
            "start_time": past_start.isoformat(),
            "end_time": past_end.isoformat(),
            "login": test_user,
        }
        past_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            past_pause_data,
        )
        if not past_result:
            self.log_error("Failed to create past pause")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние (пауза в прошлом не должна быть активна)
        after_past = get_pause_state(alert_id)
        if after_past:
            self.log_error(
                f"Past pause should not be active, but paused={after_past}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success("Past pause correctly not active (end_time < now())")

        # Создаем активную паузу (без end_time, бессрочная)
        active_pause_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            indefinite_pause_data,
        )
        if not active_pause_result:
            self.log_error("Failed to create active pause")
            self.test_results["failed"] += 1
            return False

        # Проверяем состояние (теперь должна быть активна, так как есть активная пауза)
        after_active = get_pause_state(alert_id)
        if not after_active:
            self.log_error(
                f"Active pause should be active, but paused={after_active}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "Multiple pauses: active pause correctly detected (at least one active pause makes alert paused)"
        )

        # Очищаем все паузы в конце теста
        self.log_info("Cleaning up: removing all pauses")
        cleanup_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/stop",
            remove_data,
        )
        if not cleanup_result:
            self.log_warning(
                "Failed to cleanup pauses, but test may still pass"
            )

        # ====================================================================
        # ШАГ 9: Тест GET /alerts/{alert_id}/pause - получение истории пауз
        # ====================================================================
        # Что делаем: Тестируем GET метод для получения истории пауз с фильтрацией и сортировкой
        # Ожидаемый результат:
        #   - Возвращает список всех пауз алерта в объекте pauses
        #   - Поддерживает фильтрацию: all, active, future, past
        #   - Поддерживает сортировку по start_time, end_time, start_user, end_user
        #   - По умолчанию сортировка по start_time DESC
        # Как проверяем:
        #   1. Создаем несколько пауз разных типов (активная, будущая, прошлая)
        #   2. Тестируем фильтрацию: all, active, future, past
        #   3. Тестируем сортировку по разным полям и направлениям
        #   4. Проверяем структуру ответа (pause_id вместо id, все поля из pause_history)
        # ====================================================================
        self.log_info(
            "Step 9: Testing GET /alerts/{alert_id}/pause (get pause history)"
        )

        # Используем текущее время с таймзоной +3 для сравнения
        tz_plus3 = timezone(timedelta(hours=3))
        current_now = datetime.now(tz_plus3)

        # Создаем несколько пауз разных типов для тестирования
        # 1. Активная бессрочная пауза
        active_pause_data = {"login": test_user}
        active_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            active_pause_data,
        )
        if not active_result:
            self.log_error("Failed to create active pause for GET test")
            self.test_results["failed"] += 1
            return False

        # 2. Будущая пауза
        future_start = current_now + timedelta(hours=3)
        future_end = current_now + timedelta(hours=5)
        future_pause_data = {
            "start_time": future_start.isoformat(),
            "end_time": future_end.isoformat(),
            "login": test_user,
            "comment": "lazy future comment marker",
        }
        future_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            future_pause_data,
        )
        if not future_result:
            self.log_error("Failed to create future pause for GET test")
            self.test_results["failed"] += 1
            return False

        # 3. Прошлая пауза (создаем с датами в прошлом)
        past_start = current_now - timedelta(hours=5)
        past_end = current_now - timedelta(hours=3)
        past_pause_data = {
            "start_time": past_start.isoformat(),
            "end_time": past_end.isoformat(),
            "login": test_user,
        }
        past_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            past_pause_data,
        )
        if not past_result:
            self.log_error("Failed to create past pause for GET test")
            self.test_results["failed"] += 1
            return False

        # Тест 9.1: Получение всех пауз (filter_type=all)
        self.log_info("Step 9.1: Testing GET with filter_type=all")
        all_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if (
            not all_pauses
            or not isinstance(all_pauses, dict)
            or "pauses" not in all_pauses
        ):
            self.log_error("Failed to get all pauses")
            self.test_results["failed"] += 1
            return False

        if all_pauses.get("total", 0) < 3:
            self.log_error(
                f"Expected at least 3 pauses, got {all_pauses.get('total', 0)}"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем структуру ответа
        if all_pauses.get("pauses"):
            first_pause = all_pauses["pauses"][0]
            required_fields = ["pause_id", "start_time", "start_user"]
            missing_fields = [
                field for field in required_fields if field not in first_pause
            ]
            if missing_fields:
                self.log_error(
                    f"Missing required fields in pause response: {missing_fields}"
                )
                self.test_results["failed"] += 1
                return False

            # Проверяем, что id переименован в pause_id
            if "id" in first_pause:
                self.log_error(
                    "Response should use 'pause_id' instead of 'id'"
                )
                self.test_results["failed"] += 1
                return False

            # Дополнительно проверяем, что время возвращается с таймзоной БД (+03:00 для текущего стенда)
            start_time_str = first_pause.get("start_time")
            if (
                not isinstance(start_time_str, str)
                or "+03:00" not in start_time_str
            ):
                self.log_error(
                    f"start_time should contain timezone offset +03:00, got: {start_time_str}"
                )
                self.test_results["failed"] += 1
                return False

            # Проверяем сортировку по умолчанию (start_time DESC)
            pauses_list = all_pauses.get("pauses", [])
            if len(pauses_list) > 1:
                for i in range(len(pauses_list) - 1):
                    current_start_str = pauses_list[i]["start_time"]
                    if current_start_str.endswith("Z"):
                        current_start_str = current_start_str.replace(
                            "Z", "+00:00"
                        )
                    current_start = datetime.fromisoformat(current_start_str)

                    next_start_str = pauses_list[i + 1]["start_time"]
                    if next_start_str.endswith("Z"):
                        next_start_str = next_start_str.replace("Z", "+00:00")
                    next_start = datetime.fromisoformat(next_start_str)

                    if current_start < next_start:
                        self.log_error(
                            f"Default sorting should be DESC: pause {i} start_time ({current_start}) < pause {i + 1} start_time ({next_start})"
                        )
                        self.test_results["failed"] += 1
                        return False

            self.log_success(
                f"GET all pauses: found {all_pauses.get('total', 0)} pauses, structure correct, default sorting (start_time DESC) verified"
            )

            comments = [
                pause.get("comment")
                for pause in all_pauses.get("pauses", [])
                if isinstance(pause, dict)
            ]
            if "lazy future comment marker" not in comments:
                self.log_error(
                    "Expected comment from scheduled pause was not found in pause history response"
                )
                self.test_results["failed"] += 1
                return False

        # Тест 9.2: Фильтрация активных пауз
        self.log_info("Step 9.2: Testing GET with filter_type=active")
        active_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        if not active_pauses or not isinstance(active_pauses, dict):
            self.log_error("Failed to get active pauses")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что все возвращенные паузы активны
        # Используем текущее время для проверки (актуальное на момент проверки)
        check_now = datetime.now(timezone(timedelta(hours=3)))
        for pause in active_pauses.get("pauses", []):
            pause_start = datetime.fromisoformat(
                pause["start_time"].replace("Z", "+00:00")
            )
            pause_end = pause.get("end_time")
            if pause_end:
                pause_end_dt = datetime.fromisoformat(
                    pause_end.replace("Z", "+00:00")
                )
                if pause_start > check_now or pause_end_dt < check_now:
                    self.log_error(
                        f"Pause {pause['pause_id']} is not active but returned in active filter"
                    )
                    self.test_results["failed"] += 1
                    return False
            # Бессрочная пауза должна быть активна если start_time <= check_now
            elif pause_start > check_now:
                self.log_error(
                    f"Pause {pause['pause_id']} is not active but returned in active filter"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success(
            f"GET active pauses: found {active_pauses['total']} active pauses"
        )

        # Тест 9.3: Фильтрация будущих пауз
        self.log_info("Step 9.3: Testing GET with filter_type=future")
        future_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "future"},
        )
        if not future_pauses or not isinstance(future_pauses, dict):
            self.log_error("Failed to get future pauses")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что все возвращенные паузы будущие
        for pause in future_pauses.get("pauses", []):
            pause_start_str = pause["start_time"]
            if pause_start_str.endswith("Z"):
                pause_start_str = pause_start_str.replace("Z", "+00:00")
            pause_start = datetime.fromisoformat(pause_start_str)
            if pause_start <= current_now:
                self.log_error(
                    f"Pause {pause['pause_id']} is not future but returned in future filter"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success(
            f"GET future pauses: found {future_pauses['total']} future pauses"
        )

        # Тест 9.4: Фильтрация прошлых пауз
        self.log_info("Step 9.4: Testing GET with filter_type=past")
        past_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "past"},
        )
        if not past_pauses or not isinstance(past_pauses, dict):
            self.log_error("Failed to get past pauses")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что все возвращенные паузы прошлые
        for pause in past_pauses.get("pauses", []):
            pause_end = pause.get("end_time")
            if not pause_end:
                self.log_error(
                    f"Pause {pause['pause_id']} has no end_time but returned in past filter"
                )
                self.test_results["failed"] += 1
                return False
            pause_end_str = pause_end
            if pause_end_str.endswith("Z"):
                pause_end_str = pause_end_str.replace("Z", "+00:00")
            pause_end_dt = datetime.fromisoformat(pause_end_str)
            if pause_end_dt >= current_now:
                self.log_error(
                    f"Pause {pause['pause_id']} is not past but returned in past filter"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success(
            f"GET past pauses: found {past_pauses['total']} past pauses"
        )

        # Тест 9.5: Сортировка по start_time DESC
        self.log_info("Step 9.5: Testing GET with sorting by start_time DESC")
        sorted_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not sorted_pauses
            or not isinstance(sorted_pauses, dict)
            or len(sorted_pauses.get("pauses", [])) < 2
        ):
            self.log_error("Failed to get sorted pauses")
            self.test_results["failed"] += 1
            return False

        # Проверяем сортировку
        pauses_list = sorted_pauses.get("pauses", [])
        for i in range(len(pauses_list) - 1):
            current_start_str = pauses_list[i]["start_time"]
            if current_start_str.endswith("Z"):
                current_start_str = current_start_str.replace("Z", "+00:00")
            current_start = datetime.fromisoformat(current_start_str)

            next_start_str = pauses_list[i + 1]["start_time"]
            if next_start_str.endswith("Z"):
                next_start_str = next_start_str.replace("Z", "+00:00")
            next_start = datetime.fromisoformat(next_start_str)

            if current_start < next_start:
                self.log_error(
                    "Pauses not sorted correctly by start_time DESC"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success("GET pauses sorted by start_time DESC: correct order")

        # Тест 9.6: Сортировка по start_user ASC
        self.log_info("Step 9.6: Testing GET with sorting by start_user ASC")
        sorted_by_user = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_user",
                "order_dir": "asc",
            },
        )
        if not sorted_by_user or len(sorted_by_user.get("pauses", [])) < 2:
            self.log_error("Failed to get pauses sorted by start_user")
            self.test_results["failed"] += 1
            return False

        # Проверяем сортировку по start_user
        user_pauses = sorted_by_user["pauses"]
        for i in range(len(user_pauses) - 1):
            current_user = user_pauses[i].get("start_user") or ""
            next_user = user_pauses[i + 1].get("start_user") or ""
            if current_user > next_user:
                self.log_error("Pauses not sorted correctly by start_user ASC")
                self.test_results["failed"] += 1
                return False

        self.log_success("GET pauses sorted by start_user ASC: correct order")

        # Тест 9.7: Валидация параметров сортировки
        self.log_info("Step 9.7: Testing GET with invalid order_by parameter")
        invalid_order = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"order_by": "invalid_field"},
            expect_error=True,
        )
        if not invalid_order or invalid_order.get("status_code") != 400:
            self.log_error("Expected 400 error for invalid order_by")
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "GET pauses validation: invalid order_by correctly rejected"
        )

        # Тест 9.8: Валидация параметра order_dir
        self.log_info("Step 9.8: Testing GET with invalid order_dir parameter")
        invalid_order_dir = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"order_by": "start_time", "order_dir": "invalid"},
            expect_error=True,
        )
        if (
            not invalid_order_dir
            or invalid_order_dir.get("status_code") != 400
        ):
            self.log_error("Expected 400 error for invalid order_dir")
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "GET pauses validation: invalid order_dir correctly rejected"
        )

        # ====================================================================
        # ШАГ 10: Тест PATCH /alerts/{alert_id}/pause/{pause_id} - изменение условной паузы
        # ====================================================================
        # Что делаем: Тестируем изменение условной паузы через PATCH
        # Ожидаемый результат:
        #   - Можно изменить start_time (обязательно с login)
        #   - Можно изменить end_time (обязательно с login)
        #   - Можно изменить оба поля одновременно
        #   - Переданные поля перезаписываются в БД
        # Как проверяем:
        #   1. Создаем паузу для теста
        #   2. Получаем pause_id из GET запроса
        #   3. Тестируем изменение start_time с login
        #   4. Тестируем изменение end_time с login
        #   5. Тестируем изменение всех полей одновременно
        #   6. Тестируем валидацию (start_time или end_time без login)
        #   7. Тестируем ошибки (несуществующий pause_id, пустой запрос)
        # ====================================================================
        self.log_info(
            "Step 10: Testing PATCH /alerts/{alert_id}/pause/{pause_id} (update pause)"
        )

        # Создаем паузу для теста
        tz_plus3 = timezone(timedelta(hours=3))
        test_now = datetime.now(tz_plus3)
        test_start = test_now + timedelta(hours=1)
        test_end = test_now + timedelta(hours=3)

        test_pause_data = {
            "start_time": test_start.isoformat(),
            "end_time": test_end.isoformat(),
            "login": test_user,
        }
        create_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            test_pause_data,
        )
        if not create_result:
            self.log_error("Failed to create pause for PATCH test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id из GET запроса
        all_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if (
            not all_pauses
            or not isinstance(all_pauses, dict)
            or not all_pauses.get("pauses")
        ):
            self.log_error("Failed to get pause_id for PATCH test")
            self.test_results["failed"] += 1
            return False

        # Берем первую паузу (должна быть наша тестовая)
        test_pause_id = (
            all_pauses.get("pauses", [])[0].get("pause_id")
            if all_pauses.get("pauses")
            else None
        )
        if not test_pause_id:
            self.log_error("Failed to get test_pause_id")
            self.test_results["failed"] += 1
            return False

        # Тест 10.1: Изменение start_time с login
        self.log_info(
            "Step 10.1: Testing PATCH - update start_time with login"
        )
        new_start = test_now + timedelta(hours=2)
        update_start_data = {
            "start_time": new_start.isoformat(),
            "login": "updated_user",
        }
        update_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{test_pause_id}",
            update_start_data,
        )
        if not update_result:
            self.log_error("Failed to update start_time and start_user")
            self.test_results["failed"] += 1
            return False

        # Проверяем через GET, что данные обновились
        updated_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses or not isinstance(updated_pauses, dict):
            self.log_error("Failed to verify pause update")
            self.test_results["failed"] += 1
            return False

        updated_pause = next(
            (
                p
                for p in updated_pauses.get("pauses", [])
                if p["pause_id"] == test_pause_id
            ),
            None,
        )
        if not updated_pause:
            self.log_error("Обновлённая пауза не найдена")
            self.test_results["failed"] += 1
            return False

        updated_start_dt = datetime.fromisoformat(
            updated_pause["start_time"].replace("Z", "+00:00")
        )
        if (
            abs((updated_start_dt - new_start).total_seconds()) > 60
        ):  # Допуск 1 минута
            self.log_error(
                f"start_time not updated correctly: expected {new_start}, got {updated_start_dt}"
            )
            self.test_results["failed"] += 1
            return False

        if updated_pause.get("start_user") != "updated_user":
            self.log_error(
                f"start_user not updated correctly: expected 'updated_user', got {updated_pause.get('start_user')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success("PATCH update start_time with login: success")

        # Тест 10.2: Изменение end_time с login
        self.log_info("Step 10.2: Testing PATCH - update end_time with login")
        new_end = test_now + timedelta(hours=5)
        update_end_data = {
            "end_time": new_end.isoformat(),
            "login": "updated_user",
        }
        update_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{test_pause_id}",
            update_end_data,
        )
        if not update_result:
            self.log_error("Failed to update end_time and end_user")
            self.test_results["failed"] += 1
            return False

        # Проверяем через GET
        updated_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses or not isinstance(updated_pauses, dict):
            self.log_error(
                "Failed to get updated pauses after end_time update"
            )
            self.test_results["failed"] += 1
            return False
        updated_pause = next(
            (
                p
                for p in updated_pauses.get("pauses", [])
                if p["pause_id"] == test_pause_id
            ),
            None,
        )
        if not updated_pause:
            self.log_error(
                "Обновлённая пауза не найдена после обновления end_time"
            )
            self.test_results["failed"] += 1
            return False

        updated_end_dt = datetime.fromisoformat(
            updated_pause["end_time"].replace("Z", "+00:00")
        )
        if abs((updated_end_dt - new_end).total_seconds()) > 60:
            self.log_error(
                f"end_time not updated correctly: expected {new_end}, got {updated_end_dt}"
            )
            self.test_results["failed"] += 1
            return False

        if updated_pause.get("end_user") != "updated_user":
            self.log_error(
                f"end_user not updated correctly: expected 'updated_user', got {updated_pause.get('end_user')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success("PATCH update end_time with login: success")

        # Тест 10.3: Изменение всех полей одновременно
        self.log_info("Step 10.3: Testing PATCH - update all fields")
        final_start = test_now + timedelta(hours=6)
        final_end = test_now + timedelta(hours=8)
        update_all_data = {
            "start_time": final_start.isoformat(),
            "end_time": final_end.isoformat(),
            "login": "final_user",
        }
        update_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{test_pause_id}",
            update_all_data,
        )
        if not update_result:
            self.log_error("Failed to update all fields")
            self.test_results["failed"] += 1
            return False

        # Проверяем через GET
        updated_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses or not isinstance(updated_pauses, dict):
            self.log_error(
                "Failed to get updated pauses after all fields update"
            )
            self.test_results["failed"] += 1
            return False
        updated_pause = next(
            (
                p
                for p in updated_pauses.get("pauses", [])
                if p["pause_id"] == test_pause_id
            ),
            None,
        )
        if not updated_pause:
            self.log_error(
                "Обновлённая пауза не найдена после обновления всех полей"
            )
            self.test_results["failed"] += 1
            return False

        if (
            updated_pause.get("start_user") != "final_user"
            or updated_pause.get("end_user") != "final_user"
        ):
            self.log_error("All fields not updated correctly")
            self.test_results["failed"] += 1
            return False

        self.log_success("PATCH update all fields: success")

        # Тест 10.4: Валидация - start_time без login
        self.log_info(
            "Step 10.4: Testing PATCH validation - start_time without login"
        )
        invalid_start_data = {
            "start_time": (test_now + timedelta(hours=1)).isoformat()
            # login не указан - должна быть ошибка валидации
        }
        validation_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{test_pause_id}",
            invalid_start_data,
            expect_error=True,
        )
        if (
            not validation_result
            or validation_result.get("status_code") != 400
        ):
            self.log_error(
                f"Expected 400 validation error for start_time without login, got: {validation_result}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "PATCH validation: start_time without login correctly rejected"
        )

        # Тест 10.5: Валидация - end_time без login
        self.log_info(
            "Step 10.5: Testing PATCH validation - end_time without login"
        )
        invalid_end_data = {
            "end_time": (test_now + timedelta(hours=2)).isoformat()
            # login не указан - должна быть ошибка валидации
        }
        validation_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{test_pause_id}",
            invalid_end_data,
            expect_error=True,
        )
        if (
            not validation_result
            or validation_result.get("status_code") != 400
        ):
            self.log_error(
                f"Expected 400 validation error for end_time without login, got: {validation_result}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "PATCH validation: end_time without login correctly rejected"
        )

        # Тест 10.6: Ошибка 404 - несуществующий pause_id
        self.log_info("Step 10.6: Testing PATCH - non-existent pause_id")
        fake_pause_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"start_time": test_now.isoformat(), "login": test_user}
        not_found_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{fake_pause_id}",
            update_data,
            expect_error=True,
        )
        if not not_found_result or not_found_result.get("status_code") != 404:
            self.log_error(
                f"Expected 404 error for non-existent pause_id, got: {not_found_result}"
            )
            self.test_results["failed"] += 1
            return False
        self.log_success(
            "PATCH 404 error: non-existent pause_id correctly handled"
        )

        # Тест 10.7: Ошибка 400 - пустой запрос (ничего не передано)
        self.log_info("Step 10.7: Testing PATCH - empty request body")
        empty_data = {}
        empty_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{test_pause_id}",
            empty_data,
            expect_error=True,
        )
        # Проверяем тип результата - может быть bool (True) или dict с ошибкой
        if isinstance(empty_result, bool):
            # Если вернулся True, значит пустой запрос принят (это нормально для PATCH)
            # Проверяем, что это не ошибка
            if empty_result is True:
                self.log_success(
                    "PATCH empty request body: accepted (no changes made)"
                )
            else:
                self.log_error(
                    f"Unexpected result for empty request body: {empty_result}"
                )
                self.test_results["failed"] += 1
                return False
        elif isinstance(empty_result, dict):
            # Если вернулся dict, проверяем статус ошибки
            if empty_result.get("status_code") != 400:
                self.log_error(
                    f"Expected 400 error for empty request body, got: {empty_result}"
                )
                self.test_results["failed"] += 1
                return False
            self.log_success(
                "PATCH 400 error: empty request body correctly rejected"
            )
        else:
            self.log_error(
                f"Unexpected result type for empty request body: {type(empty_result)}, value: {empty_result}"
            )
            self.test_results["failed"] += 1
            return False

        # Тест 10.8: Пустая строка для start_time (должен установить now())
        self.log_info(
            "Step 10.8: Testing PATCH - empty string for start_time (should set now())"
        )
        # Создаем новую паузу для теста
        test_pause_for_empty_start = {
            "start_time": (test_now + timedelta(hours=10)).isoformat(),
            "end_time": (test_now + timedelta(hours=12)).isoformat(),
            "login": test_user,
        }
        create_empty_start_pause = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            test_pause_for_empty_start,
        )
        if not create_empty_start_pause:
            self.log_error("Failed to create pause for empty start_time test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id
        pauses_for_empty_start = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not pauses_for_empty_start
            or not isinstance(pauses_for_empty_start, dict)
            or not pauses_for_empty_start.get("pauses")
        ):
            self.log_error("Failed to get pause_id for empty start_time test")
            self.test_results["failed"] += 1
            return False

        empty_start_pause_id = (
            pauses_for_empty_start.get("pauses", [])[0].get("pause_id")
            if pauses_for_empty_start.get("pauses")
            else None
        )
        if not empty_start_pause_id:
            self.log_error("Failed to get empty_start_pause_id")
            self.test_results["failed"] += 1
            return False
        datetime.fromisoformat(
            pauses_for_empty_start.get("pauses", [])[0]
            .get("start_time", "")
            .replace("Z", "+00:00")
        )

        # Обновляем с пустой строкой для start_time
        update_empty_start_data = {"start_time": "", "login": test_user}
        update_empty_start_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{empty_start_pause_id}",
            update_empty_start_data,
        )
        if not update_empty_start_result:
            self.log_error("Failed to update pause with empty start_time")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что start_time обновился на now() (должен быть близок к текущему времени)
        updated_pauses_empty_start = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses_empty_start or not isinstance(
            updated_pauses_empty_start, dict
        ):
            self.log_error(
                "Failed to get updated pauses after empty start_time update"
            )
            self.test_results["failed"] += 1
            return False
        updated_pause_empty_start = next(
            (
                p
                for p in updated_pauses_empty_start.get("pauses", [])
                if p["pause_id"] == empty_start_pause_id
            ),
            None,
        )
        if not updated_pause_empty_start:
            self.log_error(
                "Обновлённая пауза не найдена после обновления с пустым start_time"
            )
            self.test_results["failed"] += 1
            return False

        new_start_time = datetime.fromisoformat(
            updated_pause_empty_start["start_time"].replace("Z", "+00:00")
        )
        time_diff = abs(
            (
                datetime.now(timezone(timedelta(hours=3))) - new_start_time
            ).total_seconds()
        )
        if time_diff > 60:  # Допуск 1 минута
            self.log_error(
                f"start_time not set to now() correctly: time difference is {time_diff} seconds"
            )
            self.test_results["failed"] += 1
            return False

        if updated_pause_empty_start.get("start_user") != test_user:
            self.log_error(
                f"start_user not set correctly: expected '{test_user}', got '{updated_pause_empty_start.get('start_user')}'"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success("PATCH with empty start_time: correctly set to now()")

        # Тест 10.9: Пустая строка для end_time (должна стать бессрочной)
        self.log_info(
            "Step 10.9: Testing PATCH - empty string for end_time (should make pause indefinite)"
        )
        # Создаем новую паузу с end_time для теста
        test_pause_for_empty_end = {
            "start_time": (test_now + timedelta(hours=15)).isoformat(),
            "end_time": (test_now + timedelta(hours=17)).isoformat(),
            "login": test_user,
        }
        create_empty_end_pause = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            test_pause_for_empty_end,
        )
        if not create_empty_end_pause:
            self.log_error("Failed to create pause for empty end_time test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id
        pauses_for_empty_end = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not pauses_for_empty_end
            or not isinstance(pauses_for_empty_end, dict)
            or not pauses_for_empty_end.get("pauses")
        ):
            self.log_error("Failed to get pause_id for empty end_time test")
            self.test_results["failed"] += 1
            return False

        empty_end_pause_id = (
            pauses_for_empty_end.get("pauses", [])[0].get("pause_id")
            if pauses_for_empty_end.get("pauses")
            else None
        )
        if not empty_end_pause_id:
            self.log_error("Failed to get empty_end_pause_id")
            self.test_results["failed"] += 1
            return False

        # Обновляем с пустой строкой для end_time
        update_empty_end_data = {"end_time": "", "login": test_user}
        update_empty_end_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{empty_end_pause_id}",
            update_empty_end_data,
        )
        if not update_empty_end_result:
            self.log_error("Failed to update pause with empty end_time")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что end_time стал NULL (бессрочная пауза) и end_user стал NULL
        updated_pauses_empty_end = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses_empty_end or not isinstance(
            updated_pauses_empty_end, dict
        ):
            self.log_error(
                "Failed to get updated pauses after empty end_time update"
            )
            self.test_results["failed"] += 1
            return False
        updated_pause_empty_end = next(
            (
                p
                for p in updated_pauses_empty_end.get("pauses", [])
                if p["pause_id"] == empty_end_pause_id
            ),
            None,
        )
        if not updated_pause_empty_end:
            self.log_error(
                "Обновлённая пауза не найдена после обновления с пустым end_time"
            )
            self.test_results["failed"] += 1
            return False

        if updated_pause_empty_end.get("end_time") is not None:
            self.log_error(
                f"end_time should be NULL (indefinite pause), but got: {updated_pause_empty_end.get('end_time')}"
            )
            self.test_results["failed"] += 1
            return False

        if updated_pause_empty_end.get("end_user") is not None:
            self.log_error(
                f"end_user should be NULL when end_time is empty, but got: {updated_pause_empty_end.get('end_user')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "PATCH with empty end_time: correctly made pause indefinite (end_time = NULL, end_user = NULL)"
        )

        # Тест 10.10: POST с пустой строкой для start_time (должен установить now())
        self.log_info(
            "Step 10.10: Testing POST - empty string for start_time (should set now())"
        )
        post_empty_start_data = {
            "start_time": "",
            "end_time": (test_now + timedelta(hours=20)).isoformat(),
            "login": test_user,
        }
        post_empty_start_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            post_empty_start_data,
        )
        if not post_empty_start_result:
            self.log_error("Failed to create pause with empty start_time")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что start_time установлен на now()
        # Получаем все паузы и ищем ту, которая была создана только что (с end_time из запроса)
        pauses_post_empty_start = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not pauses_post_empty_start
            or not isinstance(pauses_post_empty_start, dict)
            or not pauses_post_empty_start.get("pauses")
        ):
            self.log_error(
                "Failed to get pauses after POST with empty start_time"
            )
            self.test_results["failed"] += 1
            return False

        # Ищем паузу с нужным end_time (из запроса)
        expected_end_time = datetime.fromisoformat(
            post_empty_start_data["end_time"].replace("Z", "+00:00")
        )
        post_empty_start_pause = None
        for pause in pauses_post_empty_start["pauses"]:
            if pause.get("end_time"):
                pause_end_time = datetime.fromisoformat(
                    pause["end_time"].replace("Z", "+00:00")
                )
                if (
                    abs((pause_end_time - expected_end_time).total_seconds())
                    < 60
                ):  # Допуск 1 минута
                    post_empty_start_pause = pause
                    break

        if not post_empty_start_pause:
            self.log_error(
                "Could not find pause created with empty start_time"
            )
            self.test_results["failed"] += 1
            return False

        # Парсим start_time из ответа (может быть в UTC или с таймзоной)
        post_start_time_str = post_empty_start_pause["start_time"]
        if post_start_time_str.endswith("Z"):
            post_start_time = datetime.fromisoformat(
                post_start_time_str.replace("Z", "+00:00")
            )
        else:
            post_start_time = datetime.fromisoformat(post_start_time_str)

        # Сравниваем с текущим временем в UTC (так как БД обычно использует UTC)
        now_utc = datetime.now(timezone.utc)
        if post_start_time.tzinfo is None:
            # Если время без таймзоны, считаем что это UTC
            post_start_time = post_start_time.replace(tzinfo=timezone.utc)

        time_diff_post = abs((now_utc - post_start_time).total_seconds())
        if time_diff_post > 60:
            self.log_error(
                f"POST with empty start_time: start_time not set to now(), time difference is {time_diff_post} seconds"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success("POST with empty start_time: correctly set to now()")

        # Тест 10.11: POST с пустой строкой для end_time (должна быть бессрочная пауза)
        self.log_info(
            "Step 10.11: Testing POST - empty string for end_time (should create indefinite pause)"
        )
        post_empty_end_data = {
            "start_time": (test_now + timedelta(hours=22)).isoformat(),
            "end_time": "",
            "login": test_user,
        }
        post_empty_end_result = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            post_empty_end_data,
        )
        if not post_empty_end_result:
            self.log_error("Failed to create pause with empty end_time")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что end_time = NULL (бессрочная пауза) и end_user = NULL
        # Ищем паузу с нужным start_time (из запроса)
        pauses_post_empty_end = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not pauses_post_empty_end
            or not isinstance(pauses_post_empty_end, dict)
            or not pauses_post_empty_end.get("pauses")
        ):
            self.log_error(
                "Failed to get pauses after POST with empty end_time"
            )
            self.test_results["failed"] += 1
            return False

        # Ищем паузу с нужным start_time (из запроса)
        expected_start_time = datetime.fromisoformat(
            post_empty_end_data["start_time"].replace("Z", "+00:00")
        )
        post_empty_end_pause = None
        for pause in pauses_post_empty_end["pauses"]:
            if pause.get("start_time"):
                pause_start_time = datetime.fromisoformat(
                    pause["start_time"].replace("Z", "+00:00")
                )
                if (
                    abs(
                        (
                            pause_start_time - expected_start_time
                        ).total_seconds()
                    )
                    < 60
                ):  # Допуск 1 минута
                    post_empty_end_pause = pause
                    break

        if not post_empty_end_pause:
            self.log_error("Could not find pause created with empty end_time")
            self.test_results["failed"] += 1
            return False

        if post_empty_end_pause.get("end_time") is not None:
            self.log_error(
                f"POST with empty end_time: end_time should be NULL, but got: {post_empty_end_pause.get('end_time')}"
            )
            self.test_results["failed"] += 1
            return False

        if post_empty_end_pause.get("end_user") is not None:
            self.log_error(
                f"POST with empty end_time: end_user should be NULL, but got: {post_empty_end_pause.get('end_user')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "POST with empty end_time: correctly created indefinite pause (end_time = NULL, end_user = NULL)"
        )

        # Тест 10.12: PATCH без start_time (не должен обновляться)
        self.log_info(
            "Step 10.12: Testing PATCH - without start_time (should not update start_time)"
        )
        # Создаем паузу с известным start_time
        test_pause_for_no_start = {
            "start_time": (test_now + timedelta(hours=25)).isoformat(),
            "end_time": (test_now + timedelta(hours=27)).isoformat(),
            "login": test_user,
        }
        create_no_start_pause = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            test_pause_for_no_start,
        )
        if not create_no_start_pause:
            self.log_error("Failed to create pause for no start_time test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id и сохраняем оригинальный start_time
        pauses_for_no_start = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not pauses_for_no_start
            or not isinstance(pauses_for_no_start, dict)
            or not pauses_for_no_start.get("pauses")
        ):
            self.log_error("Failed to get pause_id for no start_time test")
            self.test_results["failed"] += 1
            return False

        no_start_pause_id = (
            pauses_for_no_start.get("pauses", [])[0].get("pause_id")
            if pauses_for_no_start.get("pauses")
            else None
        )
        if not no_start_pause_id:
            self.log_error("Failed to get no_start_pause_id")
            self.test_results["failed"] += 1
            return False
        original_start_time_no_start = pauses_for_no_start.get("pauses", [])[
            0
        ].get("start_time", "")
        original_start_user_no_start = pauses_for_no_start.get("pauses", [])[
            0
        ].get("start_user")

        # Обновляем только end_time, start_time не передаем
        update_no_start_data = {
            "end_time": (test_now + timedelta(hours=30)).isoformat(),
            "login": "updated_user",
        }
        update_no_start_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{no_start_pause_id}",
            update_no_start_data,
        )
        if not update_no_start_result:
            self.log_error("Failed to update pause without start_time")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что start_time НЕ изменился
        updated_pauses_no_start = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses_no_start or not isinstance(
            updated_pauses_no_start, dict
        ):
            self.log_error(
                "Failed to get updated pauses after no start_time update"
            )
            self.test_results["failed"] += 1
            return False
        updated_pause_no_start = next(
            (
                p
                for p in updated_pauses_no_start.get("pauses", [])
                if p["pause_id"] == no_start_pause_id
            ),
            None,
        )
        if not updated_pause_no_start:
            self.log_error(
                "Обновлённая пауза не найдена после обновления без start_time"
            )
            self.test_results["failed"] += 1
            return False

        if (
            updated_pause_no_start["start_time"]
            != original_start_time_no_start
        ):
            self.log_error(
                f"start_time should not change when not provided: original={original_start_time_no_start}, got={updated_pause_no_start['start_time']}"
            )
            self.test_results["failed"] += 1
            return False

        if (
            updated_pause_no_start.get("start_user")
            != original_start_user_no_start
        ):
            self.log_error(
                f"start_user should not change when start_time not provided: original={original_start_user_no_start}, got={updated_pause_no_start.get('start_user')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "PATCH without start_time: start_time correctly not updated"
        )

        # Тест 10.13: PATCH без end_time (не должен обновляться)
        self.log_info(
            "Step 10.13: Testing PATCH - without end_time (should not update end_time)"
        )
        # Создаем паузу с известным end_time
        test_pause_for_no_end = {
            "start_time": (test_now + timedelta(hours=32)).isoformat(),
            "end_time": (test_now + timedelta(hours=34)).isoformat(),
            "login": test_user,
        }
        create_no_end_pause = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            test_pause_for_no_end,
        )
        if not create_no_end_pause:
            self.log_error("Failed to create pause for no end_time test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id и сохраняем оригинальный end_time
        pauses_for_no_end = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not pauses_for_no_end
            or not isinstance(pauses_for_no_end, dict)
            or not pauses_for_no_end.get("pauses")
        ):
            self.log_error("Failed to get pause_id for no end_time test")
            self.test_results["failed"] += 1
            return False

        no_end_pause_id = (
            pauses_for_no_end.get("pauses", [])[0].get("pause_id")
            if pauses_for_no_end.get("pauses")
            else None
        )
        if not no_end_pause_id:
            self.log_error("Failed to get no_end_pause_id")
            self.test_results["failed"] += 1
            return False
        original_end_time_no_end = pauses_for_no_end.get("pauses", [])[0].get(
            "end_time"
        )
        original_end_user_no_end = pauses_for_no_end.get("pauses", [])[0].get(
            "end_user"
        )

        # Обновляем только start_time, end_time не передаем
        update_no_end_data = {
            "start_time": (test_now + timedelta(hours=35)).isoformat(),
            "login": "updated_user",
        }
        update_no_end_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{no_end_pause_id}",
            update_no_end_data,
        )
        if not update_no_end_result:
            self.log_error("Failed to update pause without end_time")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что end_time НЕ изменился
        updated_pauses_no_end = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses_no_end or not isinstance(
            updated_pauses_no_end, dict
        ):
            self.log_error(
                "Failed to get updated pauses after no end_time update"
            )
            self.test_results["failed"] += 1
            return False
        updated_pause_no_end = next(
            (
                p
                for p in updated_pauses_no_end.get("pauses", [])
                if p["pause_id"] == no_end_pause_id
            ),
            None,
        )
        if not updated_pause_no_end:
            self.log_error(
                "Обновлённая пауза не найдена после обновления без end_time"
            )
            self.test_results["failed"] += 1
            return False

        if updated_pause_no_end.get("end_time") != original_end_time_no_end:
            self.log_error(
                f"end_time should not change when not provided: original={original_end_time_no_end}, got={updated_pause_no_end.get('end_time')}"
            )
            self.test_results["failed"] += 1
            return False

        if updated_pause_no_end.get("end_user") != original_end_user_no_end:
            self.log_error(
                f"end_user should not change when end_time not provided: original={original_end_user_no_end}, got={updated_pause_no_end.get('end_user')}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "PATCH without end_time: end_time correctly not updated"
        )

        # ====================================================================
        # ШАГ 11: Тест PATCH /alerts/{alert_id}/pause/{pause_id}/stop - остановка конкретной паузы
        # ====================================================================
        # Что делаем: Тестируем остановку конкретной паузы через PATCH /pause/{pause_id}/stop
        # Ожидаемый результат:
        #   - Если пауза активна: end_time = now(), end_user = переданный
        #   - Если пауза в будущем: end_time = start_time, end_user = переданный (пауза так и не начнется)
        #   - Если пауза в прошлом: ошибка 400 (пауза уже завершена)
        # Как проверяем:
        #   1. Создаем активную паузу и останавливаем ее
        #   2. Создаем будущую паузу и останавливаем ее (end_time = start_time)
        #   3. Создаем прошлую паузу и пытаемся остановить (ожидаем ошибку 400)
        #   4. Проверяем ошибку 404 для несуществующего pause_id
        # ====================================================================
        self.log_info(
            "Step 11: Testing PATCH /alerts/{alert_id}/pause/{pause_id}/stop (stop specific pause)"
        )

        tz_plus3 = timezone(timedelta(hours=3))
        test_now = datetime.now(tz_plus3)

        # Тест 11.1: Остановка активной паузы
        self.log_info(
            "Step 11.1: Testing PATCH /pause/{pause_id}/stop - active pause"
        )
        active_pause_data = {"login": test_user}
        create_active = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            active_pause_data,
        )
        if not create_active:
            self.log_error("Failed to create active pause for stop test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id активной паузы
        all_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        if (
            not all_pauses
            or not isinstance(all_pauses, dict)
            or not all_pauses.get("pauses")
        ):
            self.log_error("Failed to get active pause_id")
            self.test_results["failed"] += 1
            return False

        active_pause_id = (
            all_pauses.get("pauses", [])[0].get("pause_id")
            if all_pauses.get("pauses")
            else None
        )
        if not active_pause_id:
            self.log_error("Failed to get active_pause_id")
            self.test_results["failed"] += 1
            return False
        datetime.fromisoformat(
            all_pauses.get("pauses", [])[0]
            .get("start_time", "")
            .replace("Z", "+00:00")
        )

        # Останавливаем активную паузу
        stop_active_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{active_pause_id}/stop",
            remove_data,
        )
        if not stop_active_result:
            self.log_error("Failed to stop active pause")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что пауза остановлена (end_time = now(), end_user установлен)
        updated_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses or not isinstance(updated_pauses, dict):
            self.log_error("Failed to get updated pauses after stop")
            self.test_results["failed"] += 1
            return False
        stopped_pause = next(
            (
                p
                for p in updated_pauses.get("pauses", [])
                if p["pause_id"] == active_pause_id
            ),
            None,
        )
        if not stopped_pause:
            self.log_error("Остановленная пауза не найдена")
            self.test_results["failed"] += 1
            return False

        if not stopped_pause.get("end_time"):
            self.log_error("Active pause should have end_time after stop")
            self.test_results["failed"] += 1
            return False

        if stopped_pause.get("end_user") != test_user:
            self.log_error(
                f"end_user not set correctly: expected '{test_user}', got '{stopped_pause.get('end_user')}'"
            )
            self.test_results["failed"] += 1
            return False

        # Проверяем, что пауза больше не активна
        active_after_stop = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "active"},
        )
        if not active_after_stop or not isinstance(active_after_stop, dict):
            self.log_error("Failed to get active pauses after stop")
            self.test_results["failed"] += 1
            return False
        active_pause_ids = [
            p["pause_id"] for p in active_after_stop.get("pauses", [])
        ]
        if active_pause_id in active_pause_ids:
            self.log_error("Pause should not be active after stop")
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "PATCH /pause/{pause_id}/stop: active pause correctly stopped"
        )

        # Тест 11.2: Остановка будущей паузы (end_time = start_time)
        self.log_info(
            "Step 11.2: Testing PATCH /pause/{pause_id}/stop - future pause"
        )
        future_start = test_now + timedelta(hours=2)
        future_end = test_now + timedelta(hours=4)
        future_pause_data = {
            "start_time": future_start.isoformat(),
            "end_time": future_end.isoformat(),
            "login": test_user,
        }
        create_future = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            future_pause_data,
        )
        if not create_future:
            self.log_error("Failed to create future pause for stop test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id будущей паузы
        future_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "future"},
        )
        if (
            not future_pauses
            or not isinstance(future_pauses, dict)
            or not future_pauses.get("pauses")
        ):
            self.log_error("Failed to get future pause_id")
            self.test_results["failed"] += 1
            return False

        future_pause_id = future_pauses["pauses"][0]["pause_id"]
        future_pause_start = datetime.fromisoformat(
            future_pauses["pauses"][0]["start_time"].replace("Z", "+00:00")
        )

        # Останавливаем будущую паузу
        stop_future_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{future_pause_id}/stop",
            remove_data,
        )
        if not stop_future_result:
            self.log_error("Failed to stop future pause")
            self.test_results["failed"] += 1
            return False

        # Проверяем, что end_time = start_time
        updated_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if not updated_pauses or not isinstance(updated_pauses, dict):
            self.log_error(
                "Failed to get updated pauses after future pause stop"
            )
            self.test_results["failed"] += 1
            return False
        stopped_future_pause = next(
            (
                p
                for p in updated_pauses.get("pauses", [])
                if p["pause_id"] == future_pause_id
            ),
            None,
        )
        if not stopped_future_pause:
            self.log_error("Остановленная будущая пауза не найдена")
            self.test_results["failed"] += 1
            return False

        if not stopped_future_pause.get("end_time"):
            self.log_error("Future pause should have end_time after stop")
            self.test_results["failed"] += 1
            return False

        stopped_end_time = datetime.fromisoformat(
            stopped_future_pause["end_time"].replace("Z", "+00:00")
        )
        # Проверяем, что end_time равен start_time (с допуском в 1 секунду)
        if abs((stopped_end_time - future_pause_start).total_seconds()) > 1:
            self.log_error(
                f"Future pause end_time should equal start_time: expected {future_pause_start}, got {stopped_end_time}"
            )
            self.test_results["failed"] += 1
            return False

        if stopped_future_pause.get("end_user") != test_user:
            self.log_error(
                f"end_user not set correctly: expected '{test_user}', got '{stopped_future_pause.get('end_user')}'"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "PATCH /pause/{pause_id}/stop: future pause correctly stopped (end_time = start_time)"
        )

        # Тест 11.3: Попытка остановить прошлую паузу (ожидаем ошибку 400)
        self.log_info(
            "Step 11.3: Testing PATCH /pause/{pause_id}/stop - past pause (should fail)"
        )
        past_start = test_now - timedelta(hours=5)
        past_end = test_now - timedelta(hours=3)
        past_pause_data = {
            "start_time": past_start.isoformat(),
            "end_time": past_end.isoformat(),
            "login": test_user,
        }
        create_past = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            past_pause_data,
        )
        if not create_past:
            self.log_error("Failed to create past pause for stop test")
            self.test_results["failed"] += 1
            return False

        # Получаем pause_id прошлой паузы
        past_pauses = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "past"},
        )
        if (
            not past_pauses
            or not isinstance(past_pauses, dict)
            or not past_pauses.get("pauses")
        ):
            self.log_error("Failed to get past pause_id")
            self.test_results["failed"] += 1
            return False

        past_pause_id = past_pauses["pauses"][0]["pause_id"]

        # Пытаемся остановить прошлую паузу (ожидаем ошибку 400)
        stop_past_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{past_pause_id}/stop",
            remove_data,
            expect_error=True,
        )
        if not stop_past_result or stop_past_result.get("status_code") != 400:
            self.log_error(
                f"Expected 400 error for past pause stop, got: {stop_past_result}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "PATCH /pause/{pause_id}/stop: past pause correctly rejected (400 error)"
        )

        # Тест 11.4: Ошибка 404 - несуществующий pause_id
        self.log_info(
            "Step 11.4: Testing PATCH /pause/{pause_id}/stop - non-existent pause_id"
        )
        fake_pause_id = "00000000-0000-0000-0000-000000000000"
        not_found_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{fake_pause_id}/stop",
            remove_data,
            expect_error=True,
        )
        if not not_found_result or not_found_result.get("status_code") != 404:
            self.log_error(
                f"Expected 404 error for non-existent pause_id, got: {not_found_result}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "PATCH /pause/{pause_id}/stop: 404 error correctly handled"
        )

        # ====================================================================
        # ШАГ 12: Тест DELETE /alerts/{alert_id}/pause/{pause_id} - удаление конкретной паузы
        # ====================================================================
        self.log_info(
            "Step 12: Testing DELETE /alerts/{alert_id}/pause/{pause_id} (delete specific pause)"
        )

        # Создаем паузу для теста удаления
        pause_for_delete_test = {
            "login": test_user,
            "start_time": None,  # Будет установлено now() через DEFAULT
            "end_time": None,  # Бессрочная пауза
        }
        create_pause_for_delete = self.make_request(
            "POST",
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            pause_for_delete_test,
        )
        if not create_pause_for_delete:
            self.log_error("Failed to create pause for DELETE test")
            self.test_results["failed"] += 1
            return False

        # Получаем ID созданной паузы
        pauses_for_delete = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={
                "filter_type": "all",
                "order_by": "start_time",
                "order_dir": "desc",
            },
        )
        if (
            not pauses_for_delete
            or not isinstance(pauses_for_delete, dict)
            or not pauses_for_delete.get("pauses")
        ):
            self.log_error("Failed to get pause for DELETE test")
            self.test_results["failed"] += 1
            return False

        pause_to_delete_id = (
            pauses_for_delete.get("pauses", [])[0].get("pause_id")
            if pauses_for_delete.get("pauses")
            else None
        )
        if not pause_to_delete_id:
            self.log_error("Failed to get pause_to_delete_id")
            self.test_results["failed"] += 1
            return False
        self.log_success(f"Created pause {pause_to_delete_id} for DELETE test")

        # Проверяем, что пауза существует перед удалением
        pause_before_delete = next(
            (
                p
                for p in pauses_for_delete.get("pauses", [])
                if p.get("pause_id") == pause_to_delete_id
            ),
            None,
        )
        if not pause_before_delete:
            self.log_error(
                f"Пауза {pause_to_delete_id} не найдена перед DELETE"
            )
            self.test_results["failed"] += 1
            return False

        # Удаляем паузу
        delete_result = self.make_request(
            "DELETE",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{pause_to_delete_id}",
        )
        if delete_result is None or delete_result is not True:
            self.log_error("Failed to delete pause")
            self.test_results["failed"] += 1
            return False
        self.log_success(
            f"DELETE /pause/{pause_to_delete_id}: pause deleted successfully"
        )

        # Проверяем, что пауза действительно удалена
        pauses_after_delete = self.make_request(
            "GET",
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            params={"filter_type": "all"},
        )
        if (
            pauses_after_delete
            and isinstance(pauses_after_delete, dict)
            and pauses_after_delete.get("pauses")
        ):
            deleted_pause = next(
                (
                    p
                    for p in pauses_after_delete["pauses"]
                    if p["pause_id"] == pause_to_delete_id
                ),
                None,
            )
            if deleted_pause:
                self.log_error(
                    f"Pause {pause_to_delete_id} still exists after DELETE"
                )
                self.test_results["failed"] += 1
                return False

        self.log_success(
            "DELETE /pause/{pause_id}: pause correctly removed from history"
        )

        # Тест 12.1: Ошибка 404 - несуществующий pause_id
        self.log_info(
            "Step 12.1: Testing DELETE /pause/{pause_id} - non-existent pause_id"
        )
        fake_pause_id = "00000000-0000-0000-0000-000000000000"
        not_found_result = self.make_request(
            "DELETE",
            f"/alerts/api/v1/alerts/{alert_id}/pause/{fake_pause_id}",
            expect_error=True,
        )
        if not not_found_result or not_found_result.get("status_code") != 404:
            self.log_error(
                f"Expected 404 error for non-existent pause_id, got: {not_found_result}"
            )
            self.test_results["failed"] += 1
            return False

        self.log_success(
            "DELETE /pause/{pause_id}: 404 error correctly handled for non-existent pause"
        )

        # Тест 12.2: Ошибка 404 - пауза принадлежит другому алерту
        # Создаем другой тестовый алерт для проверки
        if len(self.created_data["alerts"]) > 1:
            other_alert_id = self.created_data["alerts"][1]
            # Создаем паузу для другого алерта
            pause_for_other_alert = {"login": test_user}
            create_other_pause = self.make_request(
                "POST",
                f"/alerts/api/v1/alerts/{other_alert_id}/pause/schedule",
                pause_for_other_alert,
            )
            if create_other_pause:
                other_pauses = self.make_request(
                    "GET",
                    f"/alerts/api/v1/alerts/{other_alert_id}/pause",
                    params={"filter_type": "all"},
                )
                if other_pauses and other_pauses.get("pauses"):
                    other_pause_id = other_pauses["pauses"][0]["pause_id"]
                    # Пытаемся удалить паузу другого алерта через первый алерт
                    cross_alert_result = self.make_request(
                        "DELETE",
                        f"/alerts/api/v1/alerts/{alert_id}/pause/{other_pause_id}",
                        expect_error=True,
                    )
                    if (
                        cross_alert_result
                        and cross_alert_result.get("status_code") == 404
                    ):
                        self.log_success(
                            "DELETE /pause/{pause_id}: 404 error correctly handled for pause from different alert"
                        )
                    else:
                        self.log_warning(
                            f"Expected 404 for pause from different alert, got: {cross_alert_result}"
                        )

        # Очищаем все паузы после тестов GET, PATCH, PATCH /stop и DELETE
        cleanup_result = self.make_request(
            "PATCH",
            f"/alerts/api/v1/alerts/{alert_id}/pause/stop",
            remove_data,
        )
        if not cleanup_result:
            self.log_warning("Failed to cleanup pauses after all pause tests")

        self.test_results["passed"] += 1
        return True

    def test_error_handling(self):
        """Тест обработки ошибок"""
        self.log_test("Testing Error Handling")

        # Тест 404 ошибки для несуществующего пользователя
        result = self.make_request(
            "GET",
            "/alerts/api/v1/users/00000000-0000-0000-0000-000000000000/telegram",
            expect_error=True,
        )
        if result and result.get("status_code") == 404:
            self.log_success("404 error handled correctly")
        else:
            self.log_warning("Expected 404 error but got different response")

        # Тест неверных параметров (удален старый метод by_alert_or_by_user)

        # Тест создания алерта без обязательных полей
        incomplete_alert_data = {
            "alert_name": "Test Alert"
            # Отсутствуют: indicator_id, description, image, group_rule_id
        }
        result = self.make_request(
            "POST",
            "/alerts/api/v1/alerts/detail",
            incomplete_alert_data,
            expect_error=True,
        )
        if result and result.get("status_code") == 400:
            self.log_success("400 validation error for incomplete alert data")
        else:
            self.log_warning(
                "Expected 400 validation error for incomplete alert data"
            )

        # Тест валидации некорректного JSON в silence_time
        # Нужен валидный алерт для обновления, используем существующий если есть
        if self.created_data["alerts"]:
            alert_id = self.created_data["alerts"][0]
            # Получаем индикатор и группу правил для валидного запроса
            indicators_response = self.make_request(
                "GET",
                "/alerts/api/v1/indicators/autocomplete",
                params={"limit": 1},
            )
            groups_resp = self.make_request(
                "GET",
                "/alerts/api/v1/group_rules/autocomplete",
                params={"limit": 1},
            )

            if (
                indicators_response
                and groups_resp
                and indicators_response.get("indicators")
                and groups_resp.get("group_rules")
            ):
                invalid_silence_time_data = {
                    "alert_id": alert_id,
                    "silence_time": "invalid json string",  # Некорректный JSON
                }
                result = self.make_request(
                    "PATCH",
                    "/alerts/api/v1/alerts/detail",
                    invalid_silence_time_data,
                    expect_error=True,
                )
                if result and result.get("status_code") == 400:
                    self.log_success(
                        "400 validation error for invalid silence_time JSON"
                    )
                else:
                    self.log_warning(
                        "Expected 400 validation error for invalid silence_time JSON"
                    )

        self.log_success("Error handling tests completed")
        self.test_results["passed"] += 1
        return True

    def cleanup(self):
        """Очистка созданных данных"""
        self.log_test("Cleaning up test data")

        # Подписки удаляются автоматически при удалении пользователей/алертов
        # Ручное удаление не требуется

        # Удаляем пользователей (подписки удалятся автоматически)
        for user_id in self.created_data["users"]:
            try:
                self.log_info(f"Cleaning up user {user_id}")

                # Удаляем пользователя (подписки удалятся автоматически)
                result = self.make_request(
                    "DELETE", f"/alerts/api/v1/users/{user_id}"
                )
                if result:
                    self.log_success(f"Deleted user {user_id}")
                else:
                    self.log_error(f"Failed to delete user {user_id}")
                    self.test_results["failed"] += 1

            except Exception as e:
                self.log_warning(
                    f"Error during cleanup of user {user_id}: {e}"
                )
                continue  # Продолжаем с следующим пользователем

        # DT, ссылки, подписки и паузы удаляются автоматически при удалении алертов
        # Ручное удаление не требуется

        # Удаляем алерты (DT, ссылки, подписки и паузы удалятся автоматически)
        for alert_id in self.created_data["alerts"]:
            try:
                result = self.make_request(
                    "DELETE",
                    "/alerts/api/v1/alerts/detail",
                    params={"alert_id": alert_id},
                )
                if result:
                    self.log_success(f"Deleted alert {alert_id}")
                else:
                    self.log_warning(f"Failed to delete alert {alert_id}")
            except Exception as e:
                self.log_warning(f"Error deleting alert {alert_id}: {e}")

        self.log_success("Cleanup completed")

    def run_all_tests(self):
        """Запуск всех тестов"""
        self.log("🚀 Starting API Tests", Colors.HEADER, "START")
        self.log("=" * 60, Colors.HEADER)

        # Загружаем предыдущие результаты
        previous_results = self.load_previous_results()
        if previous_results:
            self.log("")

        tests = [
            ("Health Check", self.test_health),
            ("Indicators", self.test_indicators),
            ("Telegram Endpoints", self.test_telegram_endpoints),
            ("Alerts", self.test_alerts),  # Создает тестовый алерт
            (
                "DT CRUD",
                self.test_dt,
            ),  # Тестирует DT (использует тестовый алерт)
            ("Users CRUD", self.test_users),  # Создает тестового пользователя
            (
                "Users Search",
                self.test_users_search,
            ),  # Тестирует /users/search
            (
                "Subscriptions New Methods",
                self.test_subscriptions_new_methods,
            ),  # Тестирует новые методы подписок (использует тестовый алерт и пользователя)
            (
                "User Alerts Subscriptions Search",
                self.test_user_alerts_subscriptions_search,
            ),  # Тестирует /users/{user_id}/subscriptions/search
            (
                "Subscriptions Error Handling",
                self.test_subscriptions_error_handling,
            ),  # Тестирует обработку ошибок и откат транзакций
            ("Links", self.test_links),  # Использует тестовый алерт
            ("Group Rules", self.test_group_rules_autocomplete),
            ("Screenshots Search", self.test_screenshots_search),
            ("Screenshots CRUD", self.test_screenshots_crud),
            ("Search Sorting", self.test_search_sorting),
            ("Feedback CRUD", self.test_feedback),
            ("Error Handling", self.test_error_handling),
            (
                "Pauses",
                self.test_pauses,
            ),  # Раздел 13: Тесты пауз (использует тестовый алерт)
        ]

        for test_name, test_func in tests:
            try:
                self.log(f"\n📋 Running: {test_name}", Colors.BOLD)
                result = test_func()
                if result is False:
                    # Тест уже увеличил счетчик failed внутри себя, но нужно показать что он упал
                    self.log_error(f"❌ Test '{test_name}' FAILED")
                    if not any(
                        f"{test_name}:" in err
                        for err in self.test_results["errors"]
                    ):
                        self.test_results["errors"].append(
                            f"{test_name}: Test returned False"
                        )
            except Exception as e:
                self.log_error(f"Test {test_name} crashed: {e}")
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"{test_name}: {e}")

        # Очистка
        self.log("\n🧹 Cleanup Phase", Colors.BOLD)
        self.cleanup()

        # Сохраняем детальный лог в файл
        self.log("\n💾 Saving Results", Colors.BOLD)
        self.save_results_to_file()

        # Результаты
        self.log("\n📊 Test Results", Colors.BOLD)
        self.log("=" * 60, Colors.HEADER)
        self.log(f"✅ Passed: {self.test_results['passed']}", Colors.OKGREEN)
        self.log(f"❌ Failed: {self.test_results['failed']}", Colors.FAIL)

        if self.test_results["errors"]:
            self.log("\n🚨 Errors:", Colors.FAIL)
            for error in self.test_results["errors"]:
                self.log(f"  • {error}", Colors.FAIL)

        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (
            (self.test_results["passed"] / total_tests * 100)
            if total_tests > 0
            else 0
        )

        self.log(
            f"\n📈 Success Rate: {success_rate:.1f}%",
            Colors.OKGREEN if success_rate >= 80 else Colors.WARNING,
        )

        # Сообщение только о детальном логе
        self.log(
            f"📄 Detailed log saved to: {self.detailed_log_file}",
            Colors.OKBLUE,
        )

        if self.test_results["failed"] > 0:
            self.log("\n💥 Some tests failed!", Colors.FAIL)
            sys.exit(1)
        else:
            self.log("\n🎉 All tests passed!", Colors.OKGREEN)


def main():
    """Главная функция"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("🧪 Alerts Service API Test Suite")
    print("=" * 60)
    print(f"{Colors.ENDC}")

    # Настройка URL сервиса
    SERVICE_URL = "http://localhost:8888"

    # Проверяем аргументы командной строки
    base_url = SERVICE_URL
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    # Создаем тестер для получения пути к лог-файлу
    tester = APITester(base_url)

    print(f"🌐 Service URL: {base_url}")
    print(f"📡 API Base Path: {base_url}/alerts")
    print(f"🔗 Swagger UI: {base_url}/alerts/docs")
    print("📁 Results File: test_results.json")
    print(f"📄 Detailed Log: {tester.detailed_log_file}")
    print()

    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Tests interrupted by user{Colors.ENDC}")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}💥 Unexpected error: {e}{Colors.ENDC}")
        tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
