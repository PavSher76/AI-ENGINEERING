# Модуль "Объекты-аналоги и Архив"

## Обзор

Модуль предназначен для пакетной загрузки, обработки и индексации инженерной документации с поддержкой гибридного поиска (BM25 + dense векторы + реранкинг).

## Архитектура

### Компоненты
- **MinIO** - объектное хранилище для исходных файлов
- **Qdrant** - векторная база данных для dense поиска
- **Meilisearch** - полнотекстовый поиск (BM25)
- **RabbitMQ** - очереди для обработки документов
- **PostgreSQL** - метаданные и связи
- **Keycloak** - аутентификация и авторизация

### Конвейер обработки
1. **Загрузка** - архивы проектов в MinIO
2. **Парсинг** - извлечение текста, таблиц, чертежей
3. **Чанкинг** - разбивка на семантические блоки
4. **Векторизация** - создание эмбеддингов
5. **Индексация** - загрузка в Qdrant и Meilisearch
6. **Поиск** - гибридный поиск с реранкингом

## Структура архива

### Требования к архиву
- Формат: ZIP архив
- Корневой файл: `manifest.json`
- Структура папок по дисциплинам
- Соглашения по именованию файлов

### manifest.json
```json
{
  "project_id": "EC-Karat-2021",
  "object_id": "NH3-ATR-3500tpd", 
  "phase": "PD",
  "customer": "EuroChem",
  "language": ["ru", "en"],
  "confidentiality": "internal",
  "default_discipline": "process",
  "ingest_time": "2025-01-11T10:00:00Z",
  "total_files": 1250,
  "archive_size_mb": 2450
}
```

## Соглашения по именованию

### Документы
- **P&ID**: `{PROJECT}-PID-{NUMBER}-{REV}.pdf`
- **PFD**: `{PROJECT}-PFD-{NUMBER}-{REV}.pdf`
- **Спецификации**: `{PROJECT}-SPEC-{NUMBER}-{REV}.pdf`
- **BoM**: `{PROJECT}-BOM-{NUMBER}-{REV}.xlsx`
- **Чертежи**: `{PROJECT}-DWG-{NUMBER}-{REV}.dwg`

### Папки по дисциплинам
- `01_process/` - технологические схемы
- `02_piping/` - трубопроводы
- `03_civil/` - строительная часть
- `04_electrical/` - электрооборудование
- `05_instrumentation/` - КИПиА
- `06_hvac/` - вентиляция
- `07_procurement/` - закупки

## Типы контента

### Текстовые блоки
- Заголовки и описания
- Технические характеристики
- Примечания и комментарии

### Таблицы
- BoM (Bill of Materials)
- BoQ (Bill of Quantities)
- Спецификации оборудования
- Ведомости

### Чертежи
- P&ID схемы
- Планы и разрезы
- Деталировки
- 3D модели (IFC)

## Коллекции Qdrant

### ae_text_m3
- **Модель**: BGE-M3 (1024 dim)
- **Контент**: Текстовые блоки ПД/РД
- **Payload**: doc_no, discipline, page, section

### ae_tables
- **Модель**: BGE-M3 (1024 dim)  
- **Контент**: Строки таблиц BoM/BoQ
- **Payload**: table_type, row_data, equipment_type

### ae_drawings_clip
- **Модель**: CLIP (768 dim)
- **Контент**: Изображения чертежей
- **Payload**: drawing_type, equipment_tags, coordinates

### ae_ifc
- **Модель**: BGE-M3 (1024 dim)
- **Контент**: Объекты IFC моделей
- **Payload**: ifc_type, properties, spatial_info

## Индексы Meilisearch

### documents
- **Поля**: title, content, doc_no, discipline, equipment_type
- **Фильтры**: project_id, phase, confidentiality
- **Сортировка**: relevance, created_at, doc_no

### equipment
- **Поля**: name, description, specifications, materials
- **Фильтры**: category, subcategory, standard
- **Сортировка**: relevance, category, name

## Гибридный поиск

### Алгоритм
1. **BM25 поиск** в Meilisearch (top-k=100)
2. **Dense поиск** в Qdrant (top-k=100)  
3. **Объединение** результатов по document_id
4. **Реранкинг** с помощью bge-reranker-v2-m3
5. **Фильтрация** по релевантности (score > threshold)

### Веса
- BM25: 0.3
- Dense: 0.4  
- Rerank: 0.3

## API эндпоинты

### Поиск
- `POST /search/hybrid` - гибридный поиск
- `POST /search/analogs` - поиск аналогов оборудования
- `POST /search/similar` - поиск похожих документов

### Управление
- `POST /archives/upload` - загрузка архива
- `GET /archives/{id}/status` - статус обработки
- `GET /collections` - список коллекций

## Мониторинг

### Метрики
- Время обработки документов
- Качество извлечения текста
- Точность векторизации
- Производительность поиска

### Логирование
- Структурированные логи (JSON)
- Трассировка запросов
- Ошибки обработки

## Безопасность

### Доступ
- RBAC через Keycloak
- Шифрование данных
- Аудит операций

### Конфиденциальность
- Уровни доступа
- Маскирование данных
- Сроки хранения
