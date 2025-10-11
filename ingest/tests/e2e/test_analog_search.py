#!/usr/bin/env python3
"""
E2E тесты для поиска аналогов оборудования
"""

import asyncio
import pytest
import json
import os
from typing import Dict, List, Any
from pathlib import Path

# Импорты для тестирования
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from rag.service.hybrid_search import HybridSearchService
from pipeline.vectorizer import DocumentVectorizer
from pipeline.parser import DocumentParser


class TestAnalogSearch:
    """Тесты для поиска аналогов оборудования"""
    
    @pytest.fixture
    async def search_service(self):
        """Инициализация сервиса поиска"""
        service = HybridSearchService()
        return service
    
    @pytest.fixture
    async def vectorizer(self):
        """Инициализация векторизатора"""
        vectorizer = DocumentVectorizer()
        await vectorizer.ensure_collections_exist()
        return vectorizer
    
    @pytest.fixture
    async def parser(self):
        """Инициализация парсера"""
        return DocumentParser()
    
    @pytest.fixture
    def sample_equipment_data(self):
        """Тестовые данные оборудования"""
        return [
            {
                "chunk_id": "pump_001",
                "content": "Центробежный насос для перекачки аммиака. Производительность 1000 м3/ч, напор 50 м. Материал корпуса - нержавеющая сталь 316L.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "chunk_type": "text",
                "tags": ["pump", "centrifugal", "ammonia", "stainless_steel"],
                "numeric": {
                    "flow_rate": {"value": 1000, "unit": "m3/h"},
                    "head": {"value": 50, "unit": "m"},
                    "material": "316L"
                }
            },
            {
                "chunk_id": "heat_exchanger_001",
                "content": "Кожухотрубный теплообменник TEMA E. Тепловая нагрузка 5000 кВт. Рабочее давление 25 бар, температура 200°C.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-SPEC-100",
                "rev": "A",
                "chunk_type": "text",
                "tags": ["heat_exchanger", "shell_tube", "TEMA"],
                "numeric": {
                    "heat_duty": {"value": 5000, "unit": "kW"},
                    "pressure": {"value": 25, "unit": "bar"},
                    "temperature": {"value": 200, "unit": "°C"}
                }
            },
            {
                "chunk_id": "compressor_001",
                "content": "Центробежный компрессор для сжатия синтез-газа. Производительность 50000 м3/ч, степень сжатия 3.5.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-SPEC-200",
                "rev": "A",
                "chunk_type": "text",
                "tags": ["compressor", "centrifugal", "synthesis_gas"],
                "numeric": {
                    "flow_rate": {"value": 50000, "unit": "m3/h"},
                    "compression_ratio": {"value": 3.5, "unit": ""}
                }
            },
            {
                "chunk_id": "valve_001",
                "content": "Шаровой кран DN 200, PN 40. Материал корпуса - углеродистая сталь, уплотнения - PTFE.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "piping",
                "doc_no": "AI-ENG-PID-002",
                "rev": "A",
                "chunk_type": "text",
                "tags": ["valve", "ball_valve", "carbon_steel"],
                "numeric": {
                    "diameter": {"value": 200, "unit": "mm"},
                    "pressure": {"value": 40, "unit": "bar"}
                }
            }
        ]
    
    async def test_centrifugal_pump_search(self, search_service, vectorizer, sample_equipment_data):
        """Тест поиска центробежных насосов"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_equipment_data, "ae_text_m3")
        
        # Поиск центробежных насосов
        results = await search_service.search_analogs(
            equipment_description="центробежный насос",
            equipment_type="pump",
            parameters={"flow_rate": 1000, "head": 50},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти хотя бы один насос"
        
        # Проверяем, что найден насос
        pump_found = False
        for result in results:
            content = result["content"].lower()
            if "насос" in content or "pump" in content:
                pump_found = True
                break
        
        assert pump_found, "Должен найти насос в результатах"
        
        # Проверяем релевантность
        top_result = results[0]
        assert top_result["relevance_score"] > 0.1, "Релевантность должна быть выше 0.1"
    
    async def test_heat_exchanger_search(self, search_service, vectorizer, sample_equipment_data):
        """Тест поиска теплообменников"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_equipment_data, "ae_text_m3")
        
        # Поиск теплообменников
        results = await search_service.search_analogs(
            equipment_description="теплообменник кожухотрубный",
            equipment_type="heat_exchanger",
            parameters={"heat_duty": 5000, "pressure": 25},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти хотя бы один теплообменник"
        
        # Проверяем, что найден теплообменник
        heat_exchanger_found = False
        for result in results:
            content = result["content"].lower()
            if "теплообменник" in content or "heat exchanger" in content:
                heat_exchanger_found = True
                break
        
        assert heat_exchanger_found, "Должен найти теплообменник в результатах"
    
    async def test_compressor_search(self, search_service, vectorizer, sample_equipment_data):
        """Тест поиска компрессоров"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_equipment_data, "ae_text_m3")
        
        # Поиск компрессоров
        results = await search_service.search_analogs(
            equipment_description="центробежный компрессор",
            equipment_type="compressor",
            parameters={"flow_rate": 50000, "compression_ratio": 3.5},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти хотя бы один компрессор"
        
        # Проверяем, что найден компрессор
        compressor_found = False
        for result in results:
            content = result["content"].lower()
            if "компрессор" in content or "compressor" in content:
                compressor_found = True
                break
        
        assert compressor_found, "Должен найти компрессор в результатах"
    
    async def test_valve_search(self, search_service, vectorizer, sample_equipment_data):
        """Тест поиска арматуры"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_equipment_data, "ae_text_m3")
        
        # Поиск арматуры
        results = await search_service.search_analogs(
            equipment_description="шаровой кран",
            equipment_type="valve",
            parameters={"diameter": 200, "pressure": 40},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти хотя бы один кран"
        
        # Проверяем, что найден кран
        valve_found = False
        for result in results:
            content = result["content"].lower()
            if "кран" in content or "valve" in content:
                valve_found = True
                break
        
        assert valve_found, "Должен найти кран в результатах"
    
    async def test_hybrid_search_weights(self, search_service, vectorizer, sample_equipment_data):
        """Тест весов гибридного поиска"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_equipment_data, "ae_text_m3")
        
        # Выполняем гибридный поиск
        results = await search_service.hybrid_search(
            query="насос аммиак",
            limit=5
        )
        
        assert len(results) > 0, "Должен найти результаты"
        
        # Проверяем структуру результатов
        for result in results:
            assert "combined_score" in result, "Должен содержать combined_score"
            assert "search_types" in result, "Должен содержать search_types"
            assert "content" in result, "Должен содержать content"
            assert "metadata" in result, "Должен содержать metadata"
    
    async def test_search_with_filters(self, search_service, vectorizer, sample_equipment_data):
        """Тест поиска с фильтрами"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_equipment_data, "ae_text_m3")
        
        # Поиск с фильтром по дисциплине
        results = await search_service.hybrid_search(
            query="оборудование",
            filters={"discipline": "process"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти результаты"
        
        # Проверяем, что все результаты соответствуют фильтру
        for result in results:
            discipline = result["metadata"].get("discipline")
            assert discipline == "process", f"Дисциплина должна быть 'process', получена: {discipline}"
    
    async def test_search_relevance_scoring(self, search_service, vectorizer, sample_equipment_data):
        """Тест скоринга релевантности"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_equipment_data, "ae_text_m3")
        
        # Поиск с разными запросами
        queries = [
            "центробежный насос аммиак",
            "насос",
            "оборудование",
            "нерелевантный запрос xyz"
        ]
        
        for query in queries:
            results = await search_service.hybrid_search(
                query=query,
                limit=3
            )
            
            # Проверяем, что результаты отсортированы по убыванию релевантности
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i]["combined_score"] >= results[i + 1]["combined_score"], \
                        "Результаты должны быть отсортированы по убыванию релевантности"
    
    async def test_empty_search_results(self, search_service):
        """Тест пустых результатов поиска"""
        # Поиск несуществующего оборудования
        results = await search_service.search_analogs(
            equipment_description="несуществующее оборудование xyz123",
            limit=5
        )
        
        # Может вернуть пустой список или результаты с низкой релевантностью
        if len(results) > 0:
            # Если есть результаты, они должны иметь низкую релевантность
            for result in results:
                assert result["relevance_score"] < 0.5, "Релевантность должна быть низкой для несуществующего оборудования"


# Запуск тестов
async def run_tests():
    """Запуск всех тестов"""
    test_instance = TestAnalogSearch()
    
    # Создаем фикстуры
    search_service = await test_instance.search_service()
    vectorizer = await test_instance.vectorizer()
    parser = await test_instance.parser()
    sample_data = test_instance.sample_equipment_data()
    
    print("Запуск E2E тестов для поиска аналогов...")
    
    try:
        # Тест 1: Поиск центробежных насосов
        print("Тест 1: Поиск центробежных насосов")
        await test_instance.test_centrifugal_pump_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 2: Поиск теплообменников
        print("Тест 2: Поиск теплообменников")
        await test_instance.test_heat_exchanger_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 3: Поиск компрессоров
        print("Тест 3: Поиск компрессоров")
        await test_instance.test_compressor_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 4: Поиск арматуры
        print("Тест 4: Поиск арматуры")
        await test_instance.test_valve_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 5: Веса гибридного поиска
        print("Тест 5: Веса гибридного поиска")
        await test_instance.test_hybrid_search_weights(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 6: Поиск с фильтрами
        print("Тест 6: Поиск с фильтрами")
        await test_instance.test_search_with_filters(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 7: Скоринг релевантности
        print("Тест 7: Скоринг релевантности")
        await test_instance.test_search_relevance_scoring(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 8: Пустые результаты
        print("Тест 8: Пустые результаты")
        await test_instance.test_empty_search_results(search_service)
        print("✓ Пройден")
        
        print("\n🎉 Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"\n❌ Тест провален: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_tests())
