# Улучшенная RAG-система для консультаций по НТД

## Обзор

Реализована комплексная RAG-система для консультаций по нормативно-техническим документам с интеграцией API "Техэксперт". Система обеспечивает высокое качество ответов через гибридный поиск, переформулировку запросов, re-ranking и grounded QA.

## Архитектура

### Компоненты системы

1. **TechExpert Connector** - сервис интеграции с API "Техэксперт"
2. **Enhanced RAG Service** - улучшенная RAG-система с гибридным поиском
3. **Qdrant Vector Database** - векторная база данных для документов
4. **Redis Cache** - кэширование запросов и результатов
5. **Circuit Breaker** - защита от сбоев внешних сервисов

### Схема данных

#### Коллекция normative_documents в Qdrant

```json
{
  "doc_id": "gost-21.201-2011",
  "doc_title": "ГОСТ 21.201-2011",
  "doc_family": "ГОСТ",
  "discipline": ["АП", "КИПиА"],
  "edition_year": 2011,
  "is_current": true,
  "effective_from": "2012-01-01",
  "canceled_by": null,
  "section": "4",
  "clause": "4.2",
  "clause_title": "Область применения",
  "breadcrumbs": "ГОСТ 21.201-2011 > 4 > 4.2",
  "page_from": 12,
  "page_to": 13,
  "source_url": "pte-ntd://gost-21.201-2011#4.2",
  "checksum": "abc123...",
  "ingest_ts": "2025-09-30T09:00:00Z"
}
```

## Ключевые возможности

### 1. Переформулировка запросов (Query Rewrite)

- **Синонимическое расширение**: автоматическое добавление синонимов технических терминов
- **Нормализация**: приведение к стандартному виду (ГОСТ, СП, ФНП и т.д.)
- **Контекстное расширение**: добавление связанных терминов и понятий

**Пример:**
```
Исходный запрос: "область применения АСУТП"
Переформулировки:
- "сфера действия автоматизированных систем управления технологическими процессами"
- "распространяется на АСУТП"
- "применяется к автоматизированным системам"
```

### 2. Классификация намерений (Intent Classification)

Система автоматически определяет тип запроса:

- **definition** - поиск определений терминов
- **scope** - область применения документов
- **requirement** - требования и нормы
- **reference** - ссылки на конкретные документы/пункты
- **comparison** - сравнение документов
- **relevance** - актуальность и версии
- **general** - общий поиск

### 3. Гибридный поиск (Hybrid Retrieval)

Комбинация векторного и BM25 поиска:

```python
final_score = 0.6 * vector_score + 0.4 * bm25_score
```

**Преимущества:**
- Векторный поиск: семантическое понимание
- BM25: точное совпадение терминов
- Адаптивные веса в зависимости от типа запроса

### 4. Re-ranking с Cross-Encoder

Использование модели `cross-encoder/ms-marco-MiniLM-L-6-v2` для улучшения релевантности:

```python
rerank_score = cross_encoder.predict([query, document_text])
final_score = 0.3 * original_score + 0.7 * rerank_score
```

### 5. Grounded QA с цитатами

Все ответы основаны на найденных документах с обязательными ссылками:

```
**Ответ:** Согласно ГОСТ 21.201-2011, п. 4.2, автоматизированные системы управления технологическими процессами применяются для...

**Источники:**
• ГОСТ 21.201-2011, раздел 4, пункт 4.2
• СП 131.13330.2020, раздел 5, пункт 5.1.3
```

### 6. Интеграция с API "Техэксперт"

**Online-first подход:**
1. Попытка получения данных из API "Техэксперт"
2. Fallback на локальный индекс при недоступности
3. Автоматическая синхронизация актуальности

**Возможности:**
- Поиск документов по тексту
- Получение метаданных и содержимого
- Проверка актуальности редакций
- Получение ссылок на документы

## API Endpoints

### TechExpert Connector (порт 8014)

#### Аутентификация
```http
POST /auth/token
Content-Type: application/json

{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "scope": "read"
}
```

#### Поиск документов
```http
POST /documents/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "область применения АСУТП",
  "filters": {
    "doc_family": ["ГОСТ", "СП"],
    "is_current": true
  },
  "limit": 20
}
```

#### Получение метаданных
```http
GET /documents/{doc_id}/meta
Authorization: Bearer <token>
```

#### Проверка актуальности
```http
GET /documents/{doc_id}/latest
Authorization: Bearer <token>
```

### Enhanced RAG Service

#### Обработка запроса
```http
POST /rag/query
Content-Type: application/json

{
  "query": "Что такое АСУТП?",
  "user_context": {
    "discipline": "АП",
    "experience_level": "expert"
  },
  "max_sources": 5,
  "min_confidence": 0.7
}
```

## Конфигурация

### Настройки поиска

```python
search_config = {
    "hybrid_weights": {"vector": 0.6, "bm25": 0.4},
    "rerank_top_k": 50,
    "final_top_k": 10,
    "similarity_threshold": 0.7,
    "max_query_rewrites": 3,
    "enable_reranking": True,
    "enable_query_rewrite": True
}
```

### Настройки кэширования

```python
cache_config = {
    "enable_query_cache": True,
    "enable_result_cache": True,
    "query_cache_ttl": 3600,  # 1 час
    "result_cache_ttl": 1800,  # 30 минут
    "max_cache_size": 10000
}
```

## Тестирование

### Golden Dataset

Создан набор из 100+ тестовых вопросов по категориям:

- **Определения** (20 вопросов)
- **Область применения** (15 вопросов)
- **Требования** (25 вопросов)
- **Ссылки на документы** (15 вопросов)
- **Сравнение** (10 вопросов)
- **Актуальность** (10 вопросов)
- **Сложные запросы** (15 вопросов)

### Метрики качества

- **Answerable@K** - доля отвечаемых вопросов в топ-K
- **Precision@K** - точность результатов в топ-K
- **Faithfulness** - соответствие ответа контексту
- **Citation Coverage** - покрытие цитатами
- **Response Time** - время ответа
- **Intent Classification Accuracy** - точность классификации

### Целевые показатели

| Метрика | Минимум | Production | Отлично |
|---------|---------|------------|---------|
| Answerable@5 | 70% | 85% | 95% |
| Precision@5 | 65% | 80% | 90% |
| Faithfulness | 80% | 90% | 95% |
| Citation Coverage | 85% | 95% | 98% |
| Response Time | 5s | 3s | 2s |

## Мониторинг и логирование

### Структурированные логи

```json
{
  "timestamp": "2025-10-01T10:30:00Z",
  "level": "INFO",
  "service": "techexpert-connector",
  "request_id": "req_20251001_103000_123456",
  "method": "POST",
  "path": "/documents/search",
  "query": "область применения АСУТП",
  "processing_time_ms": 1250,
  "results_count": 15,
  "cache_hit": false
}
```

### Метрики Prometheus

- `techexpert_requests_total` - общее количество запросов
- `techexpert_request_duration_seconds` - время обработки запросов
- `techexpert_errors_total` - количество ошибок
- `techexpert_cache_hits_total` - попадания в кэш
- `techexpert_circuit_breaker_state` - состояние circuit breaker

### Health Checks

```http
GET /health
```

```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T10:30:00Z",
  "services": {
    "techexpert_api": {
      "status": "up",
      "response_time_ms": 150
    },
    "local_index": {
      "status": "up",
      "documents_count": 15420
    }
  },
  "version": "1.0.0"
}
```

## Развертывание

### Docker Compose

```yaml
services:
  techexpert-connector:
    build: ./services/techexpert-connector
    ports:
      - "8014:8014"
    environment:
      - TECHEXPERT_API_URL=https://api.techexpert.ru/v1
      - TECHEXPERT_CLIENT_ID=${TECHEXPERT_CLIENT_ID}
      - TECHEXPERT_CLIENT_SECRET=${TECHEXPERT_CLIENT_SECRET}
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - redis
      - qdrant
```

### Переменные окружения

```bash
# TechExpert API
TECHEXPERT_API_URL=https://api.techexpert.ru/v1
TECHEXPERT_CLIENT_ID=your_client_id
TECHEXPERT_CLIENT_SECRET=your_client_secret

# Базы данных
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
DATABASE_URL=postgresql://user:pass@postgres:5432/db

# Настройки
LOG_LEVEL=INFO
CACHE_TTL=3600
CIRCUIT_BREAKER_THRESHOLD=5
```

## Безопасность

### Аутентификация

- OAuth2 с client credentials flow
- JWT токены с ограниченным временем жизни
- Scope-based авторизация

### Защита данных

- Шифрование данных в транзите (HTTPS)
- Безопасное хранение секретов
- Логирование доступа к данным

### Rate Limiting

- Ограничение запросов к API "Техэксперт"
- Circuit breaker для защиты от сбоев
- Graceful degradation при недоступности

## Производительность

### Оптимизации

- **Кэширование**: Redis для запросов и результатов
- **Параллельная обработка**: асинхронные запросы
- **Индексация**: оптимизированные индексы в Qdrant
- **Batch processing**: группировка запросов

### Масштабирование

- Горизонтальное масштабирование сервисов
- Load balancing через Nginx
- Автоматическое масштабирование на основе метрик

## Roadmap

### Краткосрочные улучшения (2-4 недели)

1. **Неделя 1**: Гибридный поиск + re-ranking, расширенный payload
2. **Неделя 2**: Connector к "Техэксперту", online-first + fallback
3. **Неделя 3**: Golden-сет, метрики, авто-сверка актуальности
4. **Неделя 4**: Intent-routing, справочная страница, журнал соответствия

### Долгосрочные планы

- Интеграция с другими источниками НТД
- Многоязычная поддержка
- Машинное обучение для улучшения качества
- Мобильное приложение
- API для внешних интеграций

## Поддержка

### Документация

- [OpenAPI спецификация](schemas/techexpert_connector_openapi.yaml)
- [Схема Qdrant](schemas/qdrant_normative_documents.json)
- [Golden dataset](tests/golden_questions_rag.json)

### Контакты

- Email: support@ai-engineering.ru
- Документация: [docs/](docs/)
- Issues: GitHub Issues

---

*Документация обновлена: 2025-10-01*
*Версия системы: 1.0.0*
