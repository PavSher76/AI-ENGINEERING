#!/usr/bin/env python3
"""
Тест консоли фронтенда для проверки JavaScript ошибок
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend_console_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FrontendConsoleTester:
    def __init__(self):
        self.base_url = "https://localhost:9300"
        self.driver = None
        
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
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Включаем логирование консоли
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("✅ Chrome WebDriver успешно инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации WebDriver: {e}")
            return False
    
    def test_console_errors(self):
        """Тест ошибок в консоли"""
        logger.info("🔍 Тестирование ошибок в консоли...")
        
        try:
            # Переходим на главную страницу
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # Получаем логи консоли
            logs = self.driver.get_log('browser')
            
            logger.info(f"📋 Найдено {len(logs)} записей в консоли")
            
            errors = []
            warnings = []
            info = []
            
            for log in logs:
                if log['level'] == 'SEVERE':
                    errors.append(log)
                elif log['level'] == 'WARNING':
                    warnings.append(log)
                else:
                    info.append(log)
            
            # Выводим ошибки
            if errors:
                logger.error(f"🚨 Найдено {len(errors)} ошибок в консоли:")
                for error in errors:
                    logger.error(f"   {error['timestamp']}: {error['message']}")
            else:
                logger.info("✅ Ошибок в консоли не найдено")
            
            # Выводим предупреждения
            if warnings:
                logger.warning(f"⚠️ Найдено {len(warnings)} предупреждений в консоли:")
                for warning in warnings:
                    logger.warning(f"   {warning['timestamp']}: {warning['message']}")
            else:
                logger.info("✅ Предупреждений в консоли не найдено")
            
            # Выводим информацию
            if info:
                logger.info(f"ℹ️ Найдено {len(info)} информационных сообщений в консоли:")
                for msg in info:
                    logger.info(f"   {msg['timestamp']}: {msg['message']}")
            
            return len(errors) == 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования консоли: {e}")
            return False
    
    def test_network_requests(self):
        """Тест сетевых запросов"""
        logger.info("🔍 Тестирование сетевых запросов...")
        
        try:
            # Переходим на защищенную страницу
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(5)
            
            # Получаем логи производительности
            logs = self.driver.get_log('performance')
            
            logger.info(f"📋 Найдено {len(logs)} записей производительности")
            
            network_requests = []
            for log in logs:
                message = log['message']
                if 'Network.requestWillBeSent' in message or 'Network.responseReceived' in message:
                    network_requests.append(log)
            
            logger.info(f"🌐 Найдено {len(network_requests)} сетевых запросов")
            
            # Ищем запросы к Keycloak
            keycloak_requests = []
            for log in network_requests:
                message = log['message']
                if 'keycloak' in message.lower() or 'auth' in message.lower():
                    keycloak_requests.append(log)
            
            if keycloak_requests:
                logger.info(f"🔐 Найдено {len(keycloak_requests)} запросов к Keycloak:")
                for req in keycloak_requests:
                    logger.info(f"   {req['timestamp']}: {req['message']}")
            else:
                logger.warning("⚠️ Запросов к Keycloak не найдено")
            
            return len(keycloak_requests) > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования сетевых запросов: {e}")
            return False
    
    def test_javascript_variables(self):
        """Тест JavaScript переменных"""
        logger.info("🔍 Тестирование JavaScript переменных...")
        
        try:
            # Переходим на главную страницу
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # Проверяем переменные окружения
            env_vars = [
                'process.env.REACT_APP_KEYCLOAK_URL',
                'process.env.REACT_APP_KEYCLOAK_REALM',
                'process.env.REACT_APP_KEYCLOAK_CLIENT_ID',
                'process.env.REACT_APP_ENABLE_KEYCLOAK'
            ]
            
            results = {}
            for var in env_vars:
                try:
                    value = self.driver.execute_script(f"return {var};")
                    results[var] = value
                    logger.info(f"✅ {var} = {value}")
                except Exception as e:
                    results[var] = None
                    logger.warning(f"⚠️ {var} не определена: {e}")
            
            # Проверяем наличие Keycloak объектов
            keycloak_objects = [
                'window.keycloak',
                'window.ReactKeycloakProvider',
                'window.AuthContext'
            ]
            
            for obj in keycloak_objects:
                try:
                    value = self.driver.execute_script(f"return typeof {obj};")
                    if value != 'undefined':
                        logger.info(f"✅ {obj} определен: {value}")
                    else:
                        logger.warning(f"⚠️ {obj} не определен")
                except Exception as e:
                    logger.warning(f"⚠️ {obj} ошибка: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования JavaScript переменных: {e}")
            return {}
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Начинаем тестирование консоли фронтенда")
        
        if not self.setup_driver():
            logger.error("❌ Не удалось инициализировать WebDriver")
            return False
        
        try:
            # Тестируем консоль
            console_ok = self.test_console_errors()
            
            # Тестируем сетевые запросы
            network_ok = self.test_network_requests()
            
            # Тестируем JavaScript переменные
            js_vars = self.test_javascript_variables()
            
            # Генерируем отчет
            self.generate_report(console_ok, network_ok, js_vars)
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def generate_report(self, console_ok, network_ok, js_vars):
        """Генерация отчета"""
        logger.info("📊 Генерация отчета о тестировании консоли...")
        
        logger.info("=" * 60)
        logger.info("📋 ОТЧЕТ О ТЕСТИРОВАНИИ КОНСОЛИ ФРОНТЕНДА")
        logger.info("=" * 60)
        logger.info(f"🔍 Ошибки в консоли: {'✅ НЕТ' if console_ok else '❌ ЕСТЬ'}")
        logger.info(f"🌐 Сетевые запросы к Keycloak: {'✅ ЕСТЬ' if network_ok else '❌ НЕТ'}")
        
        if js_vars:
            logger.info("⚙️ JavaScript переменные:")
            for var, value in js_vars.items():
                status = "✅" if value is not None else "❌"
                logger.info(f"   {status} {var} = {value}")
        
        logger.info("=" * 60)

def main():
    """Основная функция"""
    tester = FrontendConsoleTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
