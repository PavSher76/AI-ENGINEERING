#!/bin/bash

# Скрипт инициализации базы данных
echo "Инициализация базы данных AI Engineering Platform..."

# Ожидание готовности PostgreSQL
echo "Ожидание готовности PostgreSQL..."
until docker-compose exec postgres pg_isready -U ai_user -d ai_engineering; do
  echo "PostgreSQL не готов, ожидание..."
  sleep 2
done

echo "PostgreSQL готов!"

# Создание миграций (если необходимо)
echo "Применение миграций..."
docker-compose exec postgres psql -U ai_user -d ai_engineering -c "
-- Дополнительные индексы для полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_documents_title_gin ON documents USING gin(to_tsvector('russian', title));
CREATE INDEX IF NOT EXISTS idx_documents_description_gin ON documents USING gin(to_tsvector('russian', description));
CREATE INDEX IF NOT EXISTS idx_projects_name_gin ON projects USING gin(to_tsvector('russian', name));
CREATE INDEX IF NOT EXISTS idx_projects_description_gin ON projects USING gin(to_tsvector('russian', description));
"

# Создание начальных данных
echo "Создание начальных данных..."
docker-compose exec postgres psql -U ai_user -d ai_engineering -c "
-- Создание системного пользователя
INSERT INTO users (username, email, first_name, last_name) 
VALUES ('system', 'system@ai-engineering.local', 'System', 'User')
ON CONFLICT (username) DO NOTHING;

-- Создание тестового проекта
INSERT INTO projects (name, description, project_code, created_by)
SELECT 'Тестовый проект', 'Проект для тестирования системы', 'TEST-001', id
FROM users WHERE username = 'system'
ON CONFLICT (project_code) DO NOTHING;

-- Создание базовых коллекций документов
INSERT INTO document_collections (name, description, collection_type, project_id, created_by)
SELECT 
    'Нормативные документы',
    'Коллекция нормативно-технической документации',
    'normative',
    p.id,
    u.id
FROM projects p, users u 
WHERE p.project_code = 'TEST-001' AND u.username = 'system'
ON CONFLICT DO NOTHING;

INSERT INTO document_collections (name, description, collection_type, project_id, created_by)
SELECT 
    'Документы чата',
    'Коллекция документов для чата с ИИ',
    'chat',
    p.id,
    u.id
FROM projects p, users u 
WHERE p.project_code = 'TEST-001' AND u.username = 'system'
ON CONFLICT DO NOTHING;

INSERT INTO document_collections (name, description, collection_type, project_id, created_by)
SELECT 
    'Исходные данные проекта',
    'Коллекция исходных данных для проектирования',
    'input_data',
    p.id,
    u.id
FROM projects p, users u 
WHERE p.project_code = 'TEST-001' AND u.username = 'system'
ON CONFLICT DO NOTHING;

INSERT INTO document_collections (name, description, collection_type, project_id, created_by)
SELECT 
    'Документы проекта',
    'Коллекция проектной документации',
    'project',
    p.id,
    u.id
FROM projects p, users u 
WHERE p.project_code = 'TEST-001' AND u.username = 'system'
ON CONFLICT DO NOTHING;

INSERT INTO document_collections (name, description, collection_type, project_id, created_by)
SELECT 
    'Архив и объекты аналоги',
    'Коллекция архивных документов и объектов-аналогов',
    'archive',
    p.id,
    u.id
FROM projects p, users u 
WHERE p.project_code = 'TEST-001' AND u.username = 'system'
ON CONFLICT DO NOTHING;
"

echo "Инициализация базы данных завершена!"
