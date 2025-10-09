# 🔐 Keycloak Setup для AI Engineering Platform

## 📁 Файлы инструкций

### 📖 Документация
- **`keycloak_setup_guide.md`** - Подробная инструкция по настройке Keycloak
- **`keycloak_quick_setup.md`** - Быстрая настройка за 5 минут
- **`KEYCLOAK_README.md`** - Этот файл (обзор всех инструкций)

### 🛠️ Скрипты
- **`setup_keycloak.sh`** - Автоматический скрипт настройки

## 🚀 Быстрый старт

### Вариант 1: Автоматическая настройка (рекомендуется)
```bash
./setup_keycloak.sh
```

### Вариант 2: Ручная настройка
1. Откройте [keycloak_quick_setup.md](keycloak_quick_setup.md)
2. Следуйте инструкциям

### Вариант 3: Подробная настройка
1. Откройте [keycloak_setup_guide.md](keycloak_setup_guide.md)
2. Следуйте пошаговым инструкциям

## 🌐 URL для доступа

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| **Frontend** | https://localhost:9300 | admin | admin123 |
| **Keycloak Admin** | https://localhost:9080/admin | admin | admin |
| **Main App** | https://localhost:9443 | - | - |

## 🔧 Основные настройки

### Realm
- **Name**: `ai-engineering`
- **Display Name**: `AI Engineering Platform`
- **Frontend URL**: `https://localhost:9443`
- **SSL Required**: `None` (для разработки)

### Client
- **Client ID**: `ai-frontend`
- **Client Type**: `OpenID Connect`
- **Client Authentication**: `OFF` (публичный)
- **Redirect URIs**: `https://localhost:9300/*`
- **Web Origins**: `https://localhost:9300`

### User
- **Username**: `admin`
- **Email**: `admin@ai-engineering.local`
- **Password**: `admin123`

## 🚨 Устранение неполадок

### Проблема: "HTTPS required"
```bash
# Проверьте настройки realm
curl -k -s -X GET "https://localhost:9080/admin/realms/ai-engineering" \
  -H "Authorization: Bearer $(curl -k -s -X POST "https://localhost:9080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" | jq -r '.access_token')" \
  | jq '.sslRequired'
```

### Проблема: "Invalid redirect URI"
Проверьте настройки клиента в Keycloak Admin:
- Valid redirect URIs: `https://localhost:9300/*`
- Web origins: `https://localhost:9300`

### Проблема: "Client not found"
```bash
# Проверьте существование клиента
curl -k -s -X GET "https://localhost:9080/admin/realms/ai-engineering/clients" \
  -H "Authorization: Bearer $(curl -k -s -X POST "https://localhost:9080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" | jq -r '.access_token')" \
  | jq '.[] | select(.clientId=="ai-frontend")'
```

### Проблема: "User not found"
```bash
# Проверьте существование пользователя
curl -k -s -X GET "https://localhost:9080/admin/realms/ai-engineering/users" \
  -H "Authorization: Bearer $(curl -k -s -X POST "https://localhost:9080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" | jq -r '.access_token')" \
  | jq '.[] | select(.username=="admin")'
```

## 📊 Проверка статуса

### Проверка сервисов
```bash
docker-compose ps
```

### Проверка логов
```bash
# Keycloak
docker logs ai-engineering-keycloak-1 --tail 20

# Nginx
docker logs ai-engineering-nginx-1 --tail 20

# Frontend
docker logs ai-engineering-frontend-1 --tail 20
```

### Проверка доступности
```bash
# Frontend
curl -k -s -o /dev/null -w "%{http_code}" https://localhost:9300

# Keycloak Admin
curl -k -s -o /dev/null -w "%{http_code}" https://localhost:9080/admin

# Main App
curl -k -s -o /dev/null -w "%{http_code}" https://localhost:9443
```

## 🔒 Безопасность

### Для разработки
- SSL Required: `None`
- Самоподписанные сертификаты
- Простые пароли

### Для продакшена
- SSL Required: `External`
- Валидные SSL сертификаты
- Сложные пароли
- Ограничение доступа к админ-панели
- Мониторинг и логирование

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи**: `docker logs ai-engineering-keycloak-1`
2. **Проверьте статус**: `docker-compose ps`
3. **Проверьте доступность**: Откройте https://localhost:9300
4. **Очистите кэш браузера**
5. **Попробуйте режим инкогнито**

## 📚 Дополнительные ресурсы

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect](https://openid.net/connect/)
- [OAuth 2.0](https://oauth.net/2/)

---

**Примечание**: Данные инструкции предназначены для среды разработки. Для продакшена требуются дополнительные настройки безопасности.
