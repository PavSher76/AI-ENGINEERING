#!/bin/bash

# Скрипт для генерации SSL сертификатов для разработки
# Использует самоподписанные сертификаты для localhost

SSL_DIR="./ssl"
CERT_FILE="$SSL_DIR/localhost.crt"
KEY_FILE="$SSL_DIR/localhost.key"
PEM_FILE="$SSL_DIR/localhost.pem"

echo "🔐 Генерация SSL сертификатов для разработки"
echo "=============================================="

# Создаем директорию если не существует
mkdir -p "$SSL_DIR"

# Генерируем приватный ключ
echo "📝 Генерация приватного ключа..."
openssl genrsa -out "$KEY_FILE" 2048

# Создаем конфигурационный файл для сертификата
cat > "$SSL_DIR/localhost.conf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=RU
ST=Moscow
L=Moscow
O=AI Engineering Platform
OU=Development
CN=localhost

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Генерируем сертификат
echo "📜 Генерация сертификата..."
openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days 365 -config "$SSL_DIR/localhost.conf" -extensions v3_req

# Создаем PEM файл (комбинация сертификата и ключа)
echo "🔗 Создание PEM файла..."
cat "$CERT_FILE" "$KEY_FILE" > "$PEM_FILE"

# Устанавливаем правильные права доступа
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"
chmod 644 "$PEM_FILE"

echo ""
echo "✅ SSL сертификаты успешно созданы:"
echo "   📄 Сертификат: $CERT_FILE"
echo "   🔑 Приватный ключ: $KEY_FILE"
echo "   📋 PEM файл: $PEM_FILE"
echo ""
echo "🔧 Сертификат действителен для:"
echo "   • localhost"
echo "   • *.localhost"
echo "   • 127.0.0.1"
echo "   • ::1"
echo ""
echo "⚠️  ВНИМАНИЕ: Это самоподписанные сертификаты для разработки!"
echo "   В браузере появится предупреждение о безопасности."
echo "   Для продакшена используйте сертификаты от доверенного CA."
echo ""
echo "🚀 Теперь можно настроить Nginx и Keycloak для работы с HTTPS."
