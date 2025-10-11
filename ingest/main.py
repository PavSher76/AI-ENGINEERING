#!/usr/bin/env python3
"""
Главный модуль для запуска ingest системы
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем пути для импортов
sys.path.append(str(Path(__file__).parent))

from pipeline.parser import DocumentParser
from pipeline.vectorizer import DocumentVectorizer
from rag.service.hybrid_search import HybridSearchService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция для демонстрации работы ingest системы"""
    
    logger.info("🚀 Запуск ingest системы...")
    
    try:
        # Инициализация компонентов
        logger.info("Инициализация компонентов...")
        
        parser = DocumentParser()
        vectorizer = DocumentVectorizer()
        search_service = HybridSearchService()
        
        # Создание коллекций в Qdrant
        logger.info("Создание коллекций в Qdrant...")
        await vectorizer.ensure_collections_exist()
        
        # Тестовые данные для демонстрации
        test_documents = [
            {
                "file_path": "test_pump_spec.pdf",
                "content": "Центробежный насос API 610 для перекачки аммиака. Производительность 1000 м3/ч, напор 50 м, мощность 75 кВт. Материал корпуса - нержавеющая сталь 316L. Поставщик: Sulzer.",
                "metadata": {
                    "project_id": "EC-Karat-2021",
                    "object_id": "NH3-ATR-3500tpd",
                    "discipline": "process",
                    "doc_no": "AI-ENG-SPEC-001",
                    "rev": "A",
                    "chunk_type": "text"
                }
            },
            {
                "file_path": "test_heat_exchanger_spec.pdf", 
                "content": "Теплообменник кожухотрубный TEMA E. Тепловая нагрузка 5000 кВт, площадь поверхности 200 м2. Материал кожуха - углеродистая сталь A106, труб - нержавеющая сталь 316L. Поставщик: Alfa Laval.",
                "metadata": {
                    "project_id": "EC-Karat-2021",
                    "object_id": "NH3-ATR-3500tpd",
                    "discipline": "process",
                    "doc_no": "AI-ENG-SPEC-002",
                    "rev": "A",
                    "chunk_type": "text"
                }
            }
        ]
        
        # Парсинг документов
        logger.info("Парсинг документов...")
        parsed_documents = []
        
        for doc in test_documents:
            result = await parser.parse_document(doc["file_path"], doc["metadata"])
            result["content"] = doc["content"]  # Используем тестовый контент
            parsed_documents.append(result)
            logger.info(f"Обработан документ: {doc['file_path']}")
        
        # Векторизация
        logger.info("Векторизация документов...")
        for doc in parsed_documents:
            chunks = [{
                "chunk_id": f"chunk_{doc['file_path']}",
                "content": doc["content"],
                **doc["metadata"]
            }]
            
            await vectorizer.vectorize_chunks(chunks, "ae_text_m3")
            logger.info(f"Векторизован документ: {doc['file_path']}")
        
        # Тестирование поиска
        logger.info("Тестирование гибридного поиска...")
        
        # Поиск насосов
        pump_results = await search_service.hybrid_search(
            query="центробежный насос аммиак",
            limit=5
        )
        
        logger.info(f"Найдено насосов: {len(pump_results)}")
        for i, result in enumerate(pump_results):
            logger.info(f"  {i+1}. Score: {result['combined_score']:.3f}")
            logger.info(f"     Content: {result['content'][:100]}...")
        
        # Поиск теплообменников
        heat_exchanger_results = await search_service.hybrid_search(
            query="теплообменник кожухотрубный TEMA",
            limit=5
        )
        
        logger.info(f"Найдено теплообменников: {len(heat_exchanger_results)}")
        for i, result in enumerate(heat_exchanger_results):
            logger.info(f"  {i+1}. Score: {result['combined_score']:.3f}")
            logger.info(f"     Content: {result['content'][:100]}...")
        
        # Поиск аналогов оборудования
        logger.info("Поиск аналогов оборудования...")
        
        analog_results = await search_service.search_analogs(
            equipment_description="центробежный насос",
            equipment_type="pump",
            parameters={"flow_rate": 1000, "head": 50},
            limit=3
        )
        
        logger.info(f"Найдено аналогов: {len(analog_results)}")
        for i, result in enumerate(analog_results):
            logger.info(f"  {i+1}. Relevance: {result['relevance_score']:.3f}")
            logger.info(f"     Equipment: {result['content'][:100]}...")
        
        logger.info("✅ Ingest система успешно протестирована!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в ingest системе: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
