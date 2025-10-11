#!/usr/bin/env python3
"""
E2E тесты для поиска узлов P&ID
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


class TestPIDSearch:
    """Тесты для поиска узлов P&ID"""
    
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
    def sample_pid_data(self):
        """Тестовые данные P&ID"""
        return [
            {
                "chunk_id": "pid_reactor_001",
                "content": "Реактор синтеза аммиака R-101. Температура 450°C, давление 200 бар. Вход: синтез-газ, выход: аммиак. Управление температурой через теплообменник E-101.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "chunk_type": "text",
                "page": 1,
                "section": "Reactor Section",
                "tags": ["reactor", "ammonia", "synthesis", "temperature_control"],
                "numeric": {
                    "temperature": {"value": 450, "unit": "°C"},
                    "pressure": {"value": 200, "unit": "bar"},
                    "equipment_tag": "R-101"
                }
            },
            {
                "chunk_id": "pid_heat_exchanger_001",
                "content": "Теплообменник E-101 для охлаждения реактора R-101. Тепловая нагрузка 10000 кВт. Хладагент: вода, температура на входе 25°C, на выходе 80°C.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "chunk_type": "text",
                "page": 1,
                "section": "Reactor Section",
                "tags": ["heat_exchanger", "cooling", "water", "temperature_control"],
                "numeric": {
                    "heat_duty": {"value": 10000, "unit": "kW"},
                    "inlet_temp": {"value": 25, "unit": "°C"},
                    "outlet_temp": {"value": 80, "unit": "°C"},
                    "equipment_tag": "E-101"
                }
            },
            {
                "chunk_id": "pid_pump_001",
                "content": "Насос P-101 для циркуляции хладагента в контуре охлаждения реактора. Производительность 500 м3/ч, напор 30 м. Управление через частотный преобразователь.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "chunk_type": "text",
                "page": 2,
                "section": "Cooling System",
                "tags": ["pump", "circulation", "cooling", "vfd_control"],
                "numeric": {
                    "flow_rate": {"value": 500, "unit": "m3/h"},
                    "head": {"value": 30, "unit": "m"},
                    "equipment_tag": "P-101"
                }
            },
            {
                "chunk_id": "pid_compressor_001",
                "content": "Компрессор C-101 для сжатия синтез-газа перед реактором. Производительность 10000 м3/ч, степень сжатия 2.5. Антисуржая защита через байпас.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "chunk_type": "text",
                "page": 1,
                "section": "Feed Gas Compression",
                "tags": ["compressor", "synthesis_gas", "compression", "surge_protection"],
                "numeric": {
                    "flow_rate": {"value": 10000, "unit": "m3/h"},
                    "compression_ratio": {"value": 2.5, "unit": ""},
                    "equipment_tag": "C-101"
                }
            },
            {
                "chunk_id": "pid_valve_001",
                "content": "Регулирующий клапан FV-101 на линии подачи синтез-газа в реактор. Диаметр 300 мм, PN 250. Позиционер с HART протоколом.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "chunk_type": "text",
                "page": 1,
                "section": "Feed Gas Control",
                "tags": ["control_valve", "flow_control", "HART", "positioner"],
                "numeric": {
                    "diameter": {"value": 300, "unit": "mm"},
                    "pressure": {"value": 250, "unit": "bar"},
                    "equipment_tag": "FV-101"
                }
            },
            {
                "chunk_id": "pid_instrument_001",
                "content": "Датчик температуры TT-101 на выходе реактора R-101. Диапазон измерения 0-600°C, точность ±1°C. Передача сигнала 4-20 мА.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "instrumentation",
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "chunk_type": "text",
                "page": 1,
                "section": "Instrumentation",
                "tags": ["temperature_transmitter", "measurement", "4-20mA", "accuracy"],
                "numeric": {
                    "measurement_range": {"value": 600, "unit": "°C"},
                    "accuracy": {"value": 1, "unit": "°C"},
                    "signal": "4-20mA",
                    "equipment_tag": "TT-101"
                }
            }
        ]
    
    async def test_reactor_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска реактора"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск реактора
        results = await search_service.hybrid_search(
            query="реактор синтеза аммиака R-101",
            filters={"discipline": "process"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти реактор"
        
        # Проверяем, что найден реактор
        reactor_found = False
        for result in results:
            content = result["content"].lower()
            if "реактор" in content and "r-101" in content.lower():
                reactor_found = True
                break
        
        assert reactor_found, "Должен найти реактор R-101"
        
        # Проверяем метаданные
        top_result = results[0]
        assert top_result["metadata"]["equipment_tag"] == "R-101", "Должен содержать тег оборудования R-101"
        assert top_result["metadata"]["section"] == "Reactor Section", "Должен быть из секции Reactor Section"
    
    async def test_heat_exchanger_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска теплообменника"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск теплообменника
        results = await search_service.hybrid_search(
            query="теплообменник E-101 охлаждение",
            filters={"discipline": "process"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти теплообменник"
        
        # Проверяем, что найден теплообменник
        heat_exchanger_found = False
        for result in results:
            content = result["content"].lower()
            if "теплообменник" in content and "e-101" in content.lower():
                heat_exchanger_found = True
                break
        
        assert heat_exchanger_found, "Должен найти теплообменник E-101"
    
    async def test_pump_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска насоса"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск насоса
        results = await search_service.hybrid_search(
            query="насос P-101 циркуляция хладагент",
            filters={"discipline": "process"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти насос"
        
        # Проверяем, что найден насос
        pump_found = False
        for result in results:
            content = result["content"].lower()
            if "насос" in content and "p-101" in content.lower():
                pump_found = True
                break
        
        assert pump_found, "Должен найти насос P-101"
    
    async def test_compressor_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска компрессора"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск компрессора
        results = await search_service.hybrid_search(
            query="компрессор C-101 синтез-газ сжатие",
            filters={"discipline": "process"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти компрессор"
        
        # Проверяем, что найден компрессор
        compressor_found = False
        for result in results:
            content = result["content"].lower()
            if "компрессор" in content and "c-101" in content.lower():
                compressor_found = True
                break
        
        assert compressor_found, "Должен найти компрессор C-101"
    
    async def test_control_valve_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска регулирующего клапана"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск регулирующего клапана
        results = await search_service.hybrid_search(
            query="регулирующий клапан FV-101 HART позиционер",
            filters={"discipline": "process"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти регулирующий клапан"
        
        # Проверяем, что найден клапан
        valve_found = False
        for result in results:
            content = result["content"].lower()
            if "клапан" in content and "fv-101" in content.lower():
                valve_found = True
                break
        
        assert valve_found, "Должен найти клапан FV-101"
    
    async def test_instrumentation_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска приборов КИПиА"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск датчика температуры
        results = await search_service.hybrid_search(
            query="датчик температуры TT-101 4-20мА",
            filters={"discipline": "instrumentation"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти датчик температуры"
        
        # Проверяем, что найден датчик
        transmitter_found = False
        for result in results:
            content = result["content"].lower()
            if "датчик" in content and "tt-101" in content.lower():
                transmitter_found = True
                break
        
        assert transmitter_found, "Должен найти датчик TT-101"
    
    async def test_equipment_tag_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска по тегам оборудования"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск по тегу оборудования
        equipment_tags = ["R-101", "E-101", "P-101", "C-101", "FV-101", "TT-101"]
        
        for tag in equipment_tags:
            results = await search_service.hybrid_search(
                query=tag,
                limit=3
            )
            
            assert len(results) > 0, f"Должен найти оборудование с тегом {tag}"
            
            # Проверяем, что найден правильный тег
            tag_found = False
            for result in results:
                content = result["content"].lower()
                if tag.lower() in content:
                    tag_found = True
                    break
            
            assert tag_found, f"Должен найти тег {tag} в результатах"
    
    async def test_process_flow_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска по технологическому потоку"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск по технологическому потоку
        results = await search_service.hybrid_search(
            query="синтез-газ реактор аммиак выход",
            filters={"discipline": "process"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти оборудование по технологическому потоку"
        
        # Проверяем релевантность
        relevant_results = 0
        for result in results:
            content = result["content"].lower()
            if any(keyword in content for keyword in ["синтез-газ", "реактор", "аммиак"]):
                relevant_results += 1
        
        assert relevant_results > 0, "Должен найти релевантные результаты по технологическому потоку"
    
    async def test_temperature_control_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска по системе управления температурой"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск по управлению температурой
        results = await search_service.hybrid_search(
            query="управление температурой охлаждение теплообменник",
            limit=5
        )
        
        assert len(results) > 0, "Должен найти оборудование системы управления температурой"
        
        # Проверяем, что найдены релевантные компоненты
        temperature_control_found = False
        for result in results:
            content = result["content"].lower()
            if any(keyword in content for keyword in ["температур", "охлажден", "теплообменник"]):
                temperature_control_found = True
                break
        
        assert temperature_control_found, "Должен найти компоненты системы управления температурой"
    
    async def test_pressure_control_search(self, search_service, vectorizer, sample_pid_data):
        """Тест поиска по системе управления давлением"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_pid_data, "ae_text_m3")
        
        # Поиск по управлению давлением
        results = await search_service.hybrid_search(
            query="давление 200 бар компрессор сжатие",
            limit=5
        )
        
        assert len(results) > 0, "Должен найти оборудование системы управления давлением"
        
        # Проверяем, что найдены релевантные компоненты
        pressure_control_found = False
        for result in results:
            content = result["content"].lower()
            if any(keyword in content for keyword in ["давлен", "бар", "компрессор", "сжатие"]):
                pressure_control_found = True
                break
        
        assert pressure_control_found, "Должен найти компоненты системы управления давлением"


# Запуск тестов
async def run_tests():
    """Запуск всех тестов"""
    test_instance = TestPIDSearch()
    
    # Создаем фикстуры
    search_service = await test_instance.search_service()
    vectorizer = await test_instance.vectorizer()
    sample_data = test_instance.sample_pid_data()
    
    print("Запуск E2E тестов для поиска узлов P&ID...")
    
    try:
        # Тест 1: Поиск реактора
        print("Тест 1: Поиск реактора")
        await test_instance.test_reactor_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 2: Поиск теплообменника
        print("Тест 2: Поиск теплообменника")
        await test_instance.test_heat_exchanger_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 3: Поиск насоса
        print("Тест 3: Поиск насоса")
        await test_instance.test_pump_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 4: Поиск компрессора
        print("Тест 4: Поиск компрессора")
        await test_instance.test_compressor_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 5: Поиск регулирующего клапана
        print("Тест 5: Поиск регулирующего клапана")
        await test_instance.test_control_valve_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 6: Поиск приборов КИПиА
        print("Тест 6: Поиск приборов КИПиА")
        await test_instance.test_instrumentation_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 7: Поиск по тегам оборудования
        print("Тест 7: Поиск по тегам оборудования")
        await test_instance.test_equipment_tag_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 8: Поиск по технологическому потоку
        print("Тест 8: Поиск по технологическому потоку")
        await test_instance.test_process_flow_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 9: Поиск по системе управления температурой
        print("Тест 9: Поиск по системе управления температурой")
        await test_instance.test_temperature_control_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 10: Поиск по системе управления давлением
        print("Тест 10: Поиск по системе управления давлением")
        await test_instance.test_pressure_control_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        print("\n🎉 Все тесты P&ID пройдены успешно!")
        
    except Exception as e:
        print(f"\n❌ Тест провален: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_tests())
