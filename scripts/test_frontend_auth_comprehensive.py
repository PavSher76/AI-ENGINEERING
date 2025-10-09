#!/usr/bin/env python3
"""
Комплексный тест авторизации фронтенда
Проверяет все сценарии авторизации через браузер
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend_auth_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FrontendAuthTester:
    def __init__(self):
        self.base_url = "https://localhost:9300"
        self.keycloak_url = "https://localhost:9080"
        self.driver = None
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
    def setup_driver(self):
        """Настройка Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Отключаем предупреждения о небезопасном контенте
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriver успешно инициализирован")
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации WebDriver: {e}")
            return False
    
    def test_keycloak_availability(self):
        """Тест доступности Keycloak"""
        logger.info("🔍 Тестирование доступности Keycloak...")
        self.test_results["total_tests"] += 1
        
        try:
            response = requests.get(
                f"{self.keycloak_url}/realms/ai-engineering",
                verify=False,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("✅ Keycloak доступен")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ Keycloak недоступен: {response.status_code}")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Keycloak: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Keycloak connection error: {e}")
            return False
    
    def test_frontend_availability(self):
        """Тест доступности фронтенда"""
        logger.info("🔍 Тестирование доступности фронтенда...")
        self.test_results["total_tests"] += 1
        
        try:
            response = requests.get(
                self.base_url,
                verify=False,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("✅ Фронтенд доступен")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ Фронтенд недоступен: {response.status_code}")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к фронтенду: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Frontend connection error: {e}")
            return False
    
    def test_initial_page_load(self):
        """Тест загрузки начальной страницы"""
        logger.info("🔍 Тестирование загрузки начальной страницы...")
        self.test_results["total_tests"] += 1
        
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Проверяем, что страница загрузилась
            if "AI Engineering" in self.driver.title or "React App" in self.driver.title:
                logger.info("✅ Начальная страница загружена")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ Неожиданный заголовок страницы: {self.driver.title}")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки страницы: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Page load error: {e}")
            return False
    
    def test_redirect_to_login(self):
        """Тест перенаправления на страницу входа"""
        logger.info("🔍 Тестирование перенаправления на страницу входа...")
        self.test_results["total_tests"] += 1
        
        try:
            # Переходим на защищенную страницу
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"Текущий URL: {current_url}")
            
            # Проверяем, что произошло перенаправление на Keycloak или страницу входа
            if "keycloak" in current_url.lower() or "login" in current_url.lower() or "auth" in current_url.lower():
                logger.info("✅ Перенаправление на авторизацию работает")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ Перенаправление не произошло. URL: {current_url}")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования перенаправления: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Redirect test error: {e}")
            return False
    
    def test_keycloak_login_form(self):
        """Тест формы входа Keycloak"""
        logger.info("🔍 Тестирование формы входа Keycloak...")
        self.test_results["total_tests"] += 1
        
        try:
            # Ждем появления формы входа
            wait = WebDriverWait(self.driver, 15)
            
            # Ищем поля ввода
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            login_button = self.driver.find_element(By.ID, "kc-login")
            
            if username_field and password_field and login_button:
                logger.info("✅ Форма входа Keycloak найдена")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error("❌ Форма входа Keycloak не найдена")
                self.test_results["failed"] += 1
                return False
        except TimeoutException:
            logger.error("❌ Таймаут при поиске формы входа")
            self.test_results["failed"] += 1
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка поиска формы входа: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Login form error: {e}")
            return False
    
    def test_login_with_test_user(self):
        """Тест входа с тестовым пользователем"""
        logger.info("🔍 Тестирование входа с тестовым пользователем...")
        self.test_results["total_tests"] += 1
        
        try:
            # Вводим данные тестового пользователя
            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            login_button = self.driver.find_element(By.ID, "kc-login")
            
            username_field.clear()
            username_field.send_keys("testuser")
            
            password_field.clear()
            password_field.send_keys("testpassword")
            
            # Нажимаем кнопку входа
            login_button.click()
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"URL после входа: {current_url}")
            
            # Проверяем, что произошло перенаправление обратно в приложение
            if "localhost:9300" in current_url and "keycloak" not in current_url.lower():
                logger.info("✅ Вход выполнен успешно")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ Вход не удался. URL: {current_url}")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка входа: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Login error: {e}")
            return False
    
    def test_authenticated_navigation(self):
        """Тест навигации после авторизации"""
        logger.info("🔍 Тестирование навигации после авторизации...")
        self.test_results["total_tests"] += 1
        
        try:
            # Проверяем доступность различных страниц
            pages_to_test = [
                "/dashboard",
                "/chat",
                "/consultation",
                "/archive",
                "/calculations"
            ]
            
            accessible_pages = 0
            for page in pages_to_test:
                try:
                    self.driver.get(f"{self.base_url}{page}")
                    time.sleep(2)
                    
                    current_url = self.driver.current_url
                    if page in current_url and "keycloak" not in current_url.lower():
                        accessible_pages += 1
                        logger.info(f"✅ Страница {page} доступна")
                    else:
                        logger.warning(f"⚠️ Страница {page} недоступна")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка доступа к {page}: {e}")
            
            if accessible_pages >= len(pages_to_test) * 0.8:  # 80% страниц должны быть доступны
                logger.info(f"✅ Навигация работает ({accessible_pages}/{len(pages_to_test)} страниц)")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ Навигация работает плохо ({accessible_pages}/{len(pages_to_test)} страниц)")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования навигации: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Navigation test error: {e}")
            return False
    
    def test_logout_functionality(self):
        """Тест функционала выхода"""
        logger.info("🔍 Тестирование функционала выхода...")
        self.test_results["total_tests"] += 1
        
        try:
            # Ищем кнопку выхода (может быть в разных местах)
            logout_selectors = [
                "button[data-testid='logout']",
                "button:contains('Выход')",
                "button:contains('Logout')",
                "[data-testid='user-menu'] button:last-child",
                ".logout-button"
            ]
            
            logout_clicked = False
            for selector in logout_selectors:
                try:
                    if ":contains" in selector:
                        # Для селекторов с :contains используем XPath
                        xpath = f"//button[contains(text(), 'Выход') or contains(text(), 'Logout')]"
                        logout_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        logout_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    logout_button.click()
                    logout_clicked = True
                    break
                except NoSuchElementException:
                    continue
            
            if not logout_clicked:
                # Если не нашли кнопку выхода, попробуем через URL
                self.driver.get(f"{self.keycloak_url}/realms/ai-engineering/protocol/openid-connect/logout")
                logout_clicked = True
            
            if logout_clicked:
                time.sleep(3)
                current_url = self.driver.current_url
                
                # Проверяем, что произошел выход
                if "keycloak" in current_url.lower() or "login" in current_url.lower():
                    logger.info("✅ Выход выполнен успешно")
                    self.test_results["passed"] += 1
                    return True
                else:
                    logger.error(f"❌ Выход не выполнен. URL: {current_url}")
                    self.test_results["failed"] += 1
                    return False
            else:
                logger.error("❌ Кнопка выхода не найдена")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования выхода: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Logout test error: {e}")
            return False
    
    def test_protected_routes(self):
        """Тест защищенных маршрутов"""
        logger.info("🔍 Тестирование защищенных маршрутов...")
        self.test_results["total_tests"] += 1
        
        try:
            # Очищаем сессию
            self.driver.delete_all_cookies()
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(3)
            
            current_url = self.driver.current_url
            
            # Проверяем, что произошло перенаправление на авторизацию
            if "keycloak" in current_url.lower() or "login" in current_url.lower():
                logger.info("✅ Защищенные маршруты работают корректно")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ Защищенные маршруты не работают. URL: {current_url}")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования защищенных маршрутов: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Protected routes test error: {e}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Начинаем комплексное тестирование авторизации фронтенда")
        
        if not self.setup_driver():
            logger.error("❌ Не удалось инициализировать WebDriver")
            return False
        
        try:
            # Тесты доступности
            self.test_keycloak_availability()
            self.test_frontend_availability()
            
            # Тесты загрузки и перенаправления
            self.test_initial_page_load()
            self.test_redirect_to_login()
            
            # Тесты авторизации
            self.test_keycloak_login_form()
            self.test_login_with_test_user()
            
            # Тесты после авторизации
            self.test_authenticated_navigation()
            self.test_logout_functionality()
            
            # Тесты защиты
            self.test_protected_routes()
            
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.generate_report()
    
    def generate_report(self):
        """Генерация отчета о тестировании"""
        logger.info("📊 Генерация отчета о тестировании...")
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{success_rate:.1f}%"
            },
            "errors": self.test_results["errors"]
        }
        
        # Сохраняем отчет
        with open("frontend_auth_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Выводим результаты
        logger.info("=" * 60)
        logger.info("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ АВТОРИЗАЦИИ ФРОНТЕНДА")
        logger.info("=" * 60)
        logger.info(f"Всего тестов: {total}")
        logger.info(f"✅ Пройдено: {passed}")
        logger.info(f"❌ Провалено: {failed}")
        logger.info(f"📈 Успешность: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            logger.info("\n🚨 ОШИБКИ:")
            for error in self.test_results["errors"]:
                logger.info(f"  - {error}")
        
        logger.info(f"\n📄 Подробный отчет сохранен в: frontend_auth_test_report.json")
        logger.info("=" * 60)
        
        return success_rate >= 80  # Считаем успешным если 80%+ тестов прошли

def main():
    """Основная функция"""
    tester = FrontendAuthTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("🎉 Тестирование авторизации фронтенда завершено успешно!")
        exit(0)
    else:
        logger.error("💥 Тестирование авторизации фронтенда завершено с ошибками!")
        exit(1)

if __name__ == "__main__":
    main()
