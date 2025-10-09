#!/usr/bin/env python3
"""
Тест статуса авторизации фронтенда
Проверяет, включена ли авторизация и как она работает
"""

import requests
import json
import logging
import time
from urllib.parse import urljoin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth_status_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuthStatusTester:
    def __init__(self):
        self.base_url = "https://localhost:9300"
        self.keycloak_url = "https://localhost:9080"
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = 10
        
        # Отключаем предупреждения о SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def test_frontend_auth_config(self):
        """Тест конфигурации авторизации фронтенда"""
        logger.info("🔍 Тестирование конфигурации авторизации фронтенда...")
        
        try:
            # Получаем главную страницу
            response = self.session.get(self.base_url)
            
            if response.status_code == 200:
                content = response.text
                
                # Проверяем наличие ключевых элементов авторизации
                auth_indicators = {
                    "Keycloak Provider": "ReactKeycloakProvider" in content or "keycloak" in content.lower(),
                    "Auth Context": "AuthContext" in content or "useAuth" in content,
                    "Protected Routes": "ProtectedRoute" in content,
                    "Login Component": "Login" in content,
                    "Auth Utils": "keycloakUtils" in content or "authUtils" in content
                }
                
                logger.info("📋 Результаты проверки конфигурации авторизации:")
                for indicator, found in auth_indicators.items():
                    status = "✅" if found else "❌"
                    logger.info(f"   {status} {indicator}")
                
                # Проверяем переменные окружения
                env_indicators = {
                    "Keycloak URL": "KEYCLOAK_URL" in content or "keycloak" in content.lower(),
                    "Realm": "ai-engineering" in content,
                    "Client ID": "ai-frontend" in content
                }
                
                logger.info("📋 Результаты проверки переменных окружения:")
                for indicator, found in env_indicators.items():
                    status = "✅" if found else "❌"
                    logger.info(f"   {status} {indicator}")
                
                return auth_indicators, env_indicators
            else:
                logger.error(f"❌ Не удалось загрузить фронтенд: {response.status_code}")
                return None, None
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования конфигурации: {e}")
            return None, None
    
    def test_protected_routes(self):
        """Тест защищенных маршрутов"""
        logger.info("🔍 Тестирование защищенных маршрутов...")
        
        protected_routes = [
            "/dashboard",
            "/chat",
            "/consultation",
            "/archive",
            "/calculations",
            "/validation",
            "/documents",
            "/analytics",
            "/integration",
            "/outgoing-control",
            "/qr-validation",
            "/settings"
        ]
        
        results = {}
        
        for route in protected_routes:
            try:
                url = f"{self.base_url}{route}"
                response = self.session.get(url, allow_redirects=False)
                
                results[route] = {
                    "status_code": response.status_code,
                    "redirect": response.headers.get('Location', ''),
                    "content_length": len(response.content)
                }
                
                if response.status_code == 200:
                    logger.info(f"✅ {route} - доступен без авторизации (200)")
                elif response.status_code in [301, 302, 307, 308]:
                    redirect_url = response.headers.get('Location', '')
                    if 'keycloak' in redirect_url.lower() or 'auth' in redirect_url.lower():
                        logger.info(f"✅ {route} - перенаправляет на авторизацию")
                    else:
                        logger.warning(f"⚠️ {route} - перенаправляет на {redirect_url}")
                else:
                    logger.warning(f"⚠️ {route} - статус {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ {route} - ошибка: {e}")
                results[route] = {"error": str(e)}
        
        return results
    
    def test_keycloak_integration(self):
        """Тест интеграции с Keycloak"""
        logger.info("🔍 Тестирование интеграции с Keycloak...")
        
        try:
            # Проверяем доступность Keycloak
            realm_url = f"{self.keycloak_url}/realms/ai-engineering"
            response = self.session.get(realm_url)
            
            if response.status_code == 200:
                realm_data = response.json()
                logger.info("✅ Keycloak realm доступен")
                logger.info(f"   - Realm: {realm_data.get('realm', 'N/A')}")
                logger.info(f"   - Enabled: {realm_data.get('enabled', 'N/A')}")
                
                # Проверяем клиента
                client_url = f"{realm_url}/clients"
                client_response = self.session.get(client_url)
                
                if client_response.status_code == 200:
                    clients = client_response.json()
                    ai_frontend_client = None
                    for client in clients:
                        if client.get('clientId') == 'ai-frontend':
                            ai_frontend_client = client
                            break
                    
                    if ai_frontend_client:
                        logger.info("✅ Клиент 'ai-frontend' найден")
                        logger.info(f"   - Enabled: {ai_frontend_client.get('enabled', 'N/A')}")
                        logger.info(f"   - Public Client: {ai_frontend_client.get('publicClient', 'N/A')}")
                        logger.info(f"   - Standard Flow Enabled: {ai_frontend_client.get('standardFlowEnabled', 'N/A')}")
                        
                        # Проверяем redirect URIs
                        redirect_uris = ai_frontend_client.get('redirectUris', [])
                        logger.info(f"   - Redirect URIs: {redirect_uris}")
                        
                        return True
                    else:
                        logger.error("❌ Клиент 'ai-frontend' не найден")
                        return False
                else:
                    logger.error(f"❌ Не удалось получить список клиентов: {client_response.status_code}")
                    return False
            else:
                logger.error(f"❌ Keycloak realm недоступен: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования Keycloak: {e}")
            return False
    
    def test_auth_flow(self):
        """Тест потока авторизации"""
        logger.info("🔍 Тестирование потока авторизации...")
        
        try:
            # Пытаемся получить токен через client credentials flow
            token_url = f"{self.keycloak_url}/realms/ai-engineering/protocol/openid-connect/token"
            
            # Проверяем, что endpoint доступен
            response = self.session.get(token_url)
            if response.status_code == 405:  # Method Not Allowed - нормально для GET запроса к token endpoint
                logger.info("✅ Token endpoint доступен")
            else:
                logger.warning(f"⚠️ Token endpoint отвечает с кодом {response.status_code}")
            
            # Проверяем authorization endpoint
            auth_url = f"{self.keycloak_url}/realms/ai-engineering/protocol/openid-connect/auth"
            auth_response = self.session.get(auth_url)
            
            if auth_response.status_code in [200, 400]:  # 400 нормально без параметров
                logger.info("✅ Authorization endpoint доступен")
            else:
                logger.warning(f"⚠️ Authorization endpoint отвечает с кодом {auth_response.status_code}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования потока авторизации: {e}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Начинаем тестирование статуса авторизации")
        
        # Тестируем конфигурацию фронтенда
        auth_config, env_config = self.test_frontend_auth_config()
        
        # Тестируем защищенные маршруты
        protected_results = self.test_protected_routes()
        
        # Тестируем интеграцию с Keycloak
        keycloak_ok = self.test_keycloak_integration()
        
        # Тестируем поток авторизации
        auth_flow_ok = self.test_auth_flow()
        
        # Генерируем отчет
        self.generate_report(auth_config, env_config, protected_results, keycloak_ok, auth_flow_ok)
    
    def generate_report(self, auth_config, env_config, protected_results, keycloak_ok, auth_flow_ok):
        """Генерация отчета"""
        logger.info("📊 Генерация отчета о статусе авторизации...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "auth_status_test",
            "frontend_auth_config": auth_config,
            "environment_config": env_config,
            "protected_routes": protected_results,
            "keycloak_integration": keycloak_ok,
            "auth_flow": auth_flow_ok,
            "recommendations": self.get_recommendations(auth_config, env_config, protected_results, keycloak_ok)
        }
        
        # Сохраняем отчет
        with open("auth_status_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Выводим результаты
        logger.info("=" * 60)
        logger.info("📋 ОТЧЕТ О СТАТУСЕ АВТОРИЗАЦИИ ФРОНТЕНДА")
        logger.info("=" * 60)
        
        if auth_config:
            auth_enabled = sum(auth_config.values()) >= len(auth_config) * 0.6
            logger.info(f"🔐 Авторизация фронтенда: {'✅ ВКЛЮЧЕНА' if auth_enabled else '❌ ОТКЛЮЧЕНА'}")
        
        if env_config:
            env_ok = sum(env_config.values()) >= len(env_config) * 0.6
            logger.info(f"⚙️ Переменные окружения: {'✅ НАСТРОЕНЫ' if env_ok else '❌ НЕ НАСТРОЕНЫ'}")
        
        logger.info(f"🔗 Интеграция с Keycloak: {'✅ РАБОТАЕТ' if keycloak_ok else '❌ НЕ РАБОТАЕТ'}")
        logger.info(f"🔄 Поток авторизации: {'✅ ДОСТУПЕН' if auth_flow_ok else '❌ НЕ ДОСТУПЕН'}")
        
        # Анализируем защищенные маршруты
        if protected_results:
            accessible_routes = sum(1 for r in protected_results.values() if r.get('status_code') == 200)
            total_routes = len(protected_results)
            logger.info(f"🛡️ Защищенные маршруты: {accessible_routes}/{total_routes} доступны без авторизации")
        
        recommendations = self.get_recommendations(auth_config, env_config, protected_results, keycloak_ok)
        if recommendations:
            logger.info("\n💡 РЕКОМЕНДАЦИИ:")
            for rec in recommendations:
                logger.info(f"  - {rec}")
        
        logger.info(f"\n📄 Подробный отчет сохранен в: auth_status_test_report.json")
        logger.info("=" * 60)
    
    def get_recommendations(self, auth_config, env_config, protected_results, keycloak_ok):
        """Получение рекомендаций"""
        recommendations = []
        
        if auth_config and sum(auth_config.values()) < len(auth_config) * 0.6:
            recommendations.append("Включите авторизацию в коде фронтенда")
            recommendations.append("Проверьте импорты ReactKeycloakProvider и AuthContext")
        
        if env_config and sum(env_config.values()) < len(env_config) * 0.6:
            recommendations.append("Настройте переменные окружения для Keycloak")
            recommendations.append("Убедитесь, что REACT_APP_KEYCLOAK_URL, REACT_APP_KEYCLOAK_REALM, REACT_APP_KEYCLOAK_CLIENT_ID установлены")
        
        if not keycloak_ok:
            recommendations.append("Проверьте настройки Keycloak")
            recommendations.append("Убедитесь, что realm 'ai-engineering' и клиент 'ai-frontend' созданы")
        
        if protected_results:
            accessible_routes = sum(1 for r in protected_results.values() if r.get('status_code') == 200)
            if accessible_routes > len(protected_results) * 0.5:
                recommendations.append("Большинство маршрутов доступны без авторизации - проверьте ProtectedRoute компоненты")
        
        if not recommendations:
            recommendations.append("Система авторизации настроена корректно!")
        
        return recommendations

def main():
    """Основная функция"""
    tester = AuthStatusTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
