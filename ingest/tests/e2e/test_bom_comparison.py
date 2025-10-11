#!/usr/bin/env python3
"""
E2E тесты для сравнения BoM (Bill of Materials)
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


class TestBOMComparison:
    """Тесты для сравнения BoM"""
    
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
    def sample_bom_data(self):
        """Тестовые данные BoM"""
        return [
            {
                "chunk_id": "bom_pump_001",
                "content": "Насос центробежный API 610, тип OH2. Материал корпуса: нержавеющая сталь 316L, материал рабочего колеса: нержавеющая сталь 316L. Производительность: 1000 м3/ч, напор: 50 м, мощность: 75 кВт. Поставщик: Sulzer.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-BOM-001",
                "rev": "A",
                "chunk_type": "table",
                "page": 1,
                "section": "Pump Equipment",
                "tags": ["pump", "centrifugal", "API610", "stainless_steel", "Sulzer"],
                "numeric": {
                    "flow_rate": {"value": 1000, "unit": "m3/h"},
                    "head": {"value": 50, "unit": "m"},
                    "power": {"value": 75, "unit": "kW"},
                    "quantity": {"value": 2, "unit": "pcs"}
                },
                "row_data": [
                    ["Tag", "Description", "Material", "Qty", "Unit", "Vendor"],
                    ["P-101", "Centrifugal Pump API 610", "SS 316L", "2", "pcs", "Sulzer"],
                    ["P-102", "Centrifugal Pump API 610", "SS 316L", "1", "pcs", "Sulzer"]
                ]
            },
            {
                "chunk_id": "bom_heat_exchanger_001",
                "content": "Теплообменник кожухотрубный TEMA E. Материал кожуха: углеродистая сталь A106, материал труб: нержавеющая сталь 316L. Тепловая нагрузка: 5000 кВт, площадь поверхности: 200 м2. Поставщик: Alfa Laval.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-BOM-001",
                "rev": "A",
                "chunk_type": "table",
                "page": 2,
                "section": "Heat Exchanger Equipment",
                "tags": ["heat_exchanger", "shell_tube", "TEMA", "carbon_steel", "Alfa_Laval"],
                "numeric": {
                    "heat_duty": {"value": 5000, "unit": "kW"},
                    "surface_area": {"value": 200, "unit": "m2"},
                    "quantity": {"value": 1, "unit": "pcs"}
                },
                "row_data": [
                    ["Tag", "Description", "Material", "Qty", "Unit", "Vendor"],
                    ["E-101", "Shell & Tube Heat Exchanger TEMA E", "CS A106/SS 316L", "1", "pcs", "Alfa Laval"]
                ]
            },
            {
                "chunk_id": "bom_compressor_001",
                "content": "Компрессор центробежный API 617. Материал корпуса: углеродистая сталь A516, материал ротора: нержавеющая сталь 410. Производительность: 10000 м3/ч, степень сжатия: 2.5, мощность: 2000 кВт. Поставщик: Atlas Copco.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "process",
                "doc_no": "AI-ENG-BOM-001",
                "rev": "A",
                "chunk_type": "table",
                "page": 3,
                "section": "Compressor Equipment",
                "tags": ["compressor", "centrifugal", "API617", "carbon_steel", "Atlas_Copco"],
                "numeric": {
                    "flow_rate": {"value": 10000, "unit": "m3/h"},
                    "compression_ratio": {"value": 2.5, "unit": ""},
                    "power": {"value": 2000, "unit": "kW"},
                    "quantity": {"value": 1, "unit": "pcs"}
                },
                "row_data": [
                    ["Tag", "Description", "Material", "Qty", "Unit", "Vendor"],
                    ["C-101", "Centrifugal Compressor API 617", "CS A516/SS 410", "1", "pcs", "Atlas Copco"]
                ]
            },
            {
                "chunk_id": "bom_valve_001",
                "content": "Задвижка клиновая API 600. Материал корпуса: углеродистая сталь A216 WCB, материал клина: нержавеющая сталь 316L. Диаметр: 300 мм, давление: 40 бар. Поставщик: Velan.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "piping",
                "doc_no": "AI-ENG-BOM-002",
                "rev": "A",
                "chunk_type": "table",
                "page": 1,
                "section": "Valve Equipment",
                "tags": ["gate_valve", "API600", "carbon_steel", "Velan"],
                "numeric": {
                    "diameter": {"value": 300, "unit": "mm"},
                    "pressure": {"value": 40, "unit": "bar"},
                    "quantity": {"value": 10, "unit": "pcs"}
                },
                "row_data": [
                    ["Tag", "Description", "Material", "Qty", "Unit", "Vendor"],
                    ["GV-101", "Gate Valve API 600", "CS A216 WCB/SS 316L", "10", "pcs", "Velan"]
                ]
            },
            {
                "chunk_id": "bom_instrument_001",
                "content": "Датчик давления PT-101. Тип: мембранный, диапазон: 0-100 бар, точность: ±0.1%. Материал мембраны: нержавеющая сталь 316L. Поставщик: Emerson.",
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "discipline": "instrumentation",
                "doc_no": "AI-ENG-BOM-003",
                "rev": "A",
                "chunk_type": "table",
                "page": 1,
                "section": "Instrumentation Equipment",
                "tags": ["pressure_transmitter", "membrane", "accuracy", "Emerson"],
                "numeric": {
                    "measurement_range": {"value": 100, "unit": "bar"},
                    "accuracy": {"value": 0.1, "unit": "%"},
                    "quantity": {"value": 5, "unit": "pcs"}
                },
                "row_data": [
                    ["Tag", "Description", "Material", "Qty", "Unit", "Vendor"],
                    ["PT-101", "Pressure Transmitter", "SS 316L", "5", "pcs", "Emerson"]
                ]
            }
        ]
    
    async def test_pump_bom_search(self, search_service, vectorizer, sample_bom_data):
        """Тест поиска насосов в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск насосов в BoM
        results = await search_service.hybrid_search(
            query="насос центробежный API 610 Sulzer",
            filters={"discipline": "process", "chunk_type": "table"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти насосы в BoM"
        
        # Проверяем, что найден насос
        pump_found = False
        for result in results:
            content = result["content"].lower()
            if "насос" in content and "api 610" in content and "sulzer" in content:
                pump_found = True
                break
        
        assert pump_found, "Должен найти насос API 610 от Sulzer"
        
        # Проверяем метаданные
        top_result = results[0]
        assert top_result["metadata"]["chunk_type"] == "table", "Должен быть табличный чанк"
        assert top_result["metadata"]["section"] == "Pump Equipment", "Должен быть из секции Pump Equipment"
    
    async def test_heat_exchanger_bom_search(self, search_service, vectorizer, sample_bom_data):
        """Тест поиска теплообменников в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск теплообменников в BoM
        results = await search_service.hybrid_search(
            query="теплообменник кожухотрубный TEMA Alfa Laval",
            filters={"discipline": "process", "chunk_type": "table"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти теплообменники в BoM"
        
        # Проверяем, что найден теплообменник
        heat_exchanger_found = False
        for result in results:
            content = result["content"].lower()
            if "теплообменник" in content and "tema" in content and "alfa laval" in content:
                heat_exchanger_found = True
                break
        
        assert heat_exchanger_found, "Должен найти теплообменник TEMA от Alfa Laval"
    
    async def test_compressor_bom_search(self, search_service, vectorizer, sample_bom_data):
        """Тест поиска компрессоров в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск компрессоров в BoM
        results = await search_service.hybrid_search(
            query="компрессор центробежный API 617 Atlas Copco",
            filters={"discipline": "process", "chunk_type": "table"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти компрессоры в BoM"
        
        # Проверяем, что найден компрессор
        compressor_found = False
        for result in results:
            content = result["content"].lower()
            if "компрессор" in content and "api 617" in content and "atlas copco" in content:
                compressor_found = True
                break
        
        assert compressor_found, "Должен найти компрессор API 617 от Atlas Copco"
    
    async def test_valve_bom_search(self, search_service, vectorizer, sample_bom_data):
        """Тест поиска арматуры в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск арматуры в BoM
        results = await search_service.hybrid_search(
            query="задвижка клиновая API 600 Velan",
            filters={"discipline": "piping", "chunk_type": "table"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти арматуру в BoM"
        
        # Проверяем, что найдена задвижка
        valve_found = False
        for result in results:
            content = result["content"].lower()
            if "задвижка" in content and "api 600" in content and "velan" in content:
                valve_found = True
                break
        
        assert valve_found, "Должен найти задвижку API 600 от Velan"
    
    async def test_instrumentation_bom_search(self, search_service, vectorizer, sample_bom_data):
        """Тест поиска приборов КИПиА в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск приборов КИПиА в BoM
        results = await search_service.hybrid_search(
            query="датчик давления Emerson точность",
            filters={"discipline": "instrumentation", "chunk_type": "table"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти приборы КИПиА в BoM"
        
        # Проверяем, что найден датчик
        instrument_found = False
        for result in results:
            content = result["content"].lower()
            if "датчик" in content and "emerson" in content and "точность" in content:
                instrument_found = True
                break
        
        assert instrument_found, "Должен найти датчик давления от Emerson"
    
    async def test_material_comparison(self, search_service, vectorizer, sample_bom_data):
        """Тест сравнения материалов в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск оборудования из нержавеющей стали
        results = await search_service.hybrid_search(
            query="нержавеющая сталь 316L материал корпус",
            filters={"chunk_type": "table"},
            limit=10
        )
        
        assert len(results) > 0, "Должен найти оборудование из нержавеющей стали"
        
        # Проверяем, что найдено оборудование из нержавеющей стали
        stainless_steel_found = False
        for result in results:
            content = result["content"].lower()
            if "нержавеющая сталь" in content and "316l" in content:
                stainless_steel_found = True
                break
        
        assert stainless_steel_found, "Должен найти оборудование из нержавеющей стали 316L"
    
    async def test_vendor_comparison(self, search_service, vectorizer, sample_bom_data):
        """Тест сравнения поставщиков в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск оборудования от конкретного поставщика
        vendors = ["Sulzer", "Alfa Laval", "Atlas Copco", "Velan", "Emerson"]
        
        for vendor in vendors:
            results = await search_service.hybrid_search(
                query=vendor,
                filters={"chunk_type": "table"},
                limit=5
            )
            
            assert len(results) > 0, f"Должен найти оборудование от поставщика {vendor}"
            
            # Проверяем, что найден поставщик
            vendor_found = False
            for result in results:
                content = result["content"].lower()
                if vendor.lower() in content:
                    vendor_found = True
                    break
            
            assert vendor_found, f"Должен найти поставщика {vendor} в результатах"
    
    async def test_quantity_comparison(self, search_service, vectorizer, sample_bom_data):
        """Тест сравнения количеств в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск оборудования с определенным количеством
        results = await search_service.hybrid_search(
            query="количество 2 штуки насос",
            filters={"chunk_type": "table"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти оборудование с количеством 2"
        
        # Проверяем, что найдено оборудование с количеством 2
        quantity_found = False
        for result in results:
            content = result["content"].lower()
            if "2" in content and ("штук" in content or "pcs" in content):
                quantity_found = True
                break
        
        assert quantity_found, "Должен найти оборудование с количеством 2"
    
    async def test_standard_comparison(self, search_service, vectorizer, sample_bom_data):
        """Тест сравнения стандартов в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск оборудования по стандартам
        standards = ["API 610", "API 617", "API 600", "TEMA"]
        
        for standard in standards:
            results = await search_service.hybrid_search(
                query=standard,
                filters={"chunk_type": "table"},
                limit=5
            )
            
            assert len(results) > 0, f"Должен найти оборудование по стандарту {standard}"
            
            # Проверяем, что найден стандарт
            standard_found = False
            for result in results:
                content = result["content"].lower()
                if standard.lower() in content:
                    standard_found = True
                    break
            
            assert standard_found, f"Должен найти стандарт {standard} в результатах"
    
    async def test_parameter_comparison(self, search_service, vectorizer, sample_bom_data):
        """Тест сравнения параметров в BoM"""
        # Векторизуем тестовые данные
        await vectorizer.vectorize_chunks(sample_bom_data, "ae_tables")
        
        # Поиск оборудования с определенными параметрами
        results = await search_service.hybrid_search(
            query="производительность 1000 м3/ч напор 50 м",
            filters={"chunk_type": "table"},
            limit=5
        )
        
        assert len(results) > 0, "Должен найти оборудование с указанными параметрами"
        
        # Проверяем, что найдено оборудование с указанными параметрами
        parameters_found = False
        for result in results:
            content = result["content"].lower()
            if "1000" in content and "м3/ч" in content and "50" in content and "м" in content:
                parameters_found = True
                break
        
        assert parameters_found, "Должен найти оборудование с указанными параметрами"


# Запуск тестов
async def run_tests():
    """Запуск всех тестов"""
    test_instance = TestBOMComparison()
    
    # Создаем фикстуры
    search_service = await test_instance.search_service()
    vectorizer = await test_instance.vectorizer()
    sample_data = test_instance.sample_bom_data()
    
    print("Запуск E2E тестов для сравнения BoM...")
    
    try:
        # Тест 1: Поиск насосов в BoM
        print("Тест 1: Поиск насосов в BoM")
        await test_instance.test_pump_bom_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 2: Поиск теплообменников в BoM
        print("Тест 2: Поиск теплообменников в BoM")
        await test_instance.test_heat_exchanger_bom_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 3: Поиск компрессоров в BoM
        print("Тест 3: Поиск компрессоров в BoM")
        await test_instance.test_compressor_bom_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 4: Поиск арматуры в BoM
        print("Тест 4: Поиск арматуры в BoM")
        await test_instance.test_valve_bom_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 5: Поиск приборов КИПиА в BoM
        print("Тест 5: Поиск приборов КИПиА в BoM")
        await test_instance.test_instrumentation_bom_search(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 6: Сравнение материалов
        print("Тест 6: Сравнение материалов")
        await test_instance.test_material_comparison(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 7: Сравнение поставщиков
        print("Тест 7: Сравнение поставщиков")
        await test_instance.test_vendor_comparison(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 8: Сравнение количеств
        print("Тест 8: Сравнение количеств")
        await test_instance.test_quantity_comparison(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 9: Сравнение стандартов
        print("Тест 9: Сравнение стандартов")
        await test_instance.test_standard_comparison(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        # Тест 10: Сравнение параметров
        print("Тест 10: Сравнение параметров")
        await test_instance.test_parameter_comparison(search_service, vectorizer, sample_data)
        print("✓ Пройден")
        
        print("\n🎉 Все тесты BoM пройдены успешно!")
        
    except Exception as e:
        print(f"\n❌ Тест провален: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_tests())
