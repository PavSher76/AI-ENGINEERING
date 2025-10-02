#!/bin/bash

echo "🔐 Настройка SSL сертификатов для локальной разработки"
echo "======================================================"

# Создаем директорию для SSL, если ее нет
mkdir -p ./ssl

echo "📝 Генерация SSL сертификатов..."
echo "⚠️  ВНИМАНИЕ: Эти сертификаты только для разработки!"

# Генерируем приватный ключ
echo "🔑 Генерация приватного ключа..."
openssl genrsa -out ./ssl/localhost.key 2048

# Генерируем сертификат
echo "📜 Генерация сертификата..."
openssl req -new -x509 -sha256 -key ./ssl/localhost.key -out ./ssl/localhost.crt -days 365 -subj "/CN=localhost" -config <(
  cat <<-EOF
  [req]
  distinguished_name = req_distinguished_name
  x509_extensions = v3_req
  prompt = no
  [req_distinguished_name]
  CN = localhost
  [v3_req]
  keyUsage = critical, digitalSignature, keyEncipherment
  extendedKeyUsage = serverAuth, clientAuth
  subjectAltName = @alt_names
  [alt_names]
  DNS.1 = localhost
  DNS.2 = *.localhost
  IP.1 = 127.0.0.1
  IP.2 = ::1
EOF
)

# Создаем PEM файл (объединяем ключ и сертификат)
echo "🔗 Создание PEM файла..."
cat ./ssl/localhost.key ./ssl/localhost.crt > ./ssl/localhost.pem

# Создаем конфигурационный файл
echo "⚙️  Создание конфигурационного файла..."
cat > ./ssl/localhost.conf << EOF
# SSL Configuration for localhost
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = localhost

[v3_req]
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

echo ""
echo "✅ SSL сертификаты успешно созданы:"
echo "   📄 Сертификат: ./ssl/localhost.crt"
echo "   🔑 Приватный ключ: ./ssl/localhost.key"
echo "   📋 PEM файл: ./ssl/localhost.pem"
echo "   ⚙️  Конфигурация: ./ssl/localhost.conf"
echo ""
echo "🔧 Сертификат действителен для:"
openssl x509 -in ./ssl/localhost.crt -noout -text | grep -A 1 "Subject Alternative Name"

echo ""
echo "⚠️  ВАЖНО:"
echo "   • Эти сертификаты только для разработки!"
echo "   • В браузере появится предупреждение о безопасности"
echo "   • Для продакшена используйте сертификаты от доверенного CA"
echo "   • SSL файлы добавлены в .gitignore и НЕ будут в репозитории"
echo ""
echo "🚀 Теперь можно запустить: docker-compose up -d"
