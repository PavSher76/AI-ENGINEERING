"""
Сервис для управления настройками LLM
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class LLMSettings(BaseModel):
    """Настройки LLM"""
    model: str = Field(default="llama3.1:8b", description="Модель LLM")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Максимальное количество токенов")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p параметр")
    top_k: int = Field(default=40, ge=1, le=100, description="Top-k параметр")
    repeat_penalty: float = Field(default=1.1, ge=0.0, le=2.0, description="Штраф за повторения")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Штраф за частоту")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Штраф за присутствие")
    stop_sequences: list = Field(default=[], description="Последовательности остановки")
    system_prompt: str = Field(default="", description="Системный промпт")
    context_length: int = Field(default=4096, ge=512, le=32768, description="Длина контекста")
    enable_memory: bool = Field(default=True, description="Включить память чата")
    memory_limit: int = Field(default=10, ge=1, le=100, description="Лимит сообщений в памяти")
    timeout: float = Field(default=300.0, ge=30.0, le=1800.0, description="Таймаут запроса к LLM в секундах")

class ChatSettings(BaseModel):
    """Настройки чата"""
    auto_save: bool = Field(default=True, description="Автосохранение чата")
    show_timestamps: bool = Field(default=True, description="Показывать временные метки")
    enable_file_upload: bool = Field(default=True, description="Разрешить загрузку файлов")
    max_file_size_mb: int = Field(default=100, ge=1, le=500, description="Максимальный размер файла в MB")
    allowed_file_types: list = Field(
        default=["pdf", "docx", "xls", "xlsx", "txt", "md"], 
        description="Разрешенные типы файлов"
    )
    enable_ocr: bool = Field(default=True, description="Включить OCR для PDF")
    ocr_language: str = Field(default="rus+eng", description="Язык OCR")
    export_format: str = Field(default="docx", description="Формат экспорта по умолчанию")

class SystemSettings(BaseModel):
    """Системные настройки"""
    debug_mode: bool = Field(default=False, description="Режим отладки")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    cache_enabled: bool = Field(default=True, description="Включить кэширование")
    cache_ttl: int = Field(default=3600, ge=60, le=86400, description="TTL кэша в секундах")
    rate_limit: int = Field(default=100, ge=1, le=1000, description="Лимит запросов в минуту")
    timeout: int = Field(default=30, ge=5, le=300, description="Таймаут запроса в секундах")

class SettingsService:
    """Сервис для управления настройками"""
    
    def __init__(self, settings_file: str = "chat_settings.json"):
        self.settings_file = settings_file
        self.llm_settings = LLMSettings()
        self.chat_settings = ChatSettings()
        self.system_settings = SystemSettings()
        self.load_settings()
    
    def load_settings(self):
        """Загружает настройки из файла"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Загружаем настройки LLM
                if 'llm' in data:
                    self.llm_settings = LLMSettings(**data['llm'])
                
                # Загружаем настройки чата
                if 'chat' in data:
                    self.chat_settings = ChatSettings(**data['chat'])
                
                # Загружаем системные настройки
                if 'system' in data:
                    self.system_settings = SystemSettings(**data['system'])
                    
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            # Используем настройки по умолчанию
    
    def save_settings(self):
        """Сохраняет настройки в файл"""
        try:
            data = {
                'llm': self.llm_settings.model_dump(),
                'chat': self.chat_settings.model_dump(),
                'system': self.system_settings.model_dump(),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    def get_llm_settings(self) -> Dict[str, Any]:
        """Возвращает настройки LLM"""
        return self.llm_settings.model_dump()
    
    def update_llm_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет настройки LLM"""
        try:
            # Валидируем и обновляем настройки
            updated_settings = self.llm_settings.model_validate(settings)
            self.llm_settings = updated_settings
            self.save_settings()
            
            return {
                "success": True,
                "message": "Настройки LLM обновлены",
                "settings": self.llm_settings.model_dump()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка обновления настроек LLM: {str(e)}"
            }
    
    def get_chat_settings(self) -> Dict[str, Any]:
        """Возвращает настройки чата"""
        return self.chat_settings.model_dump()
    
    def update_chat_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет настройки чата"""
        try:
            # Валидируем и обновляем настройки
            updated_settings = self.chat_settings.model_validate(settings)
            self.chat_settings = updated_settings
            self.save_settings()
            
            return {
                "success": True,
                "message": "Настройки чата обновлены",
                "settings": self.chat_settings.model_dump()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка обновления настроек чата: {str(e)}"
            }
    
    def get_system_settings(self) -> Dict[str, Any]:
        """Возвращает системные настройки"""
        return self.system_settings.model_dump()
    
    def update_system_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет системные настройки"""
        try:
            # Валидируем и обновляем настройки
            updated_settings = self.system_settings.model_validate(settings)
            self.system_settings = updated_settings
            self.save_settings()
            
            return {
                "success": True,
                "message": "Системные настройки обновлены",
                "settings": self.system_settings.model_dump()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка обновления системных настроек: {str(e)}"
            }
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Возвращает все настройки"""
        return {
            "llm": self.get_llm_settings(),
            "chat": self.get_chat_settings(),
            "system": self.get_system_settings(),
            "last_updated": datetime.now().isoformat()
        }
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """Сбрасывает настройки к значениям по умолчанию"""
        try:
            self.llm_settings = LLMSettings()
            self.chat_settings = ChatSettings()
            self.system_settings = SystemSettings()
            self.save_settings()
            
            return {
                "success": True,
                "message": "Настройки сброшены к значениям по умолчанию",
                "settings": self.get_all_settings()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка сброса настроек: {str(e)}"
            }
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует настройки"""
        try:
            # Пытаемся создать объекты настроек
            if 'llm' in settings:
                LLMSettings(**settings['llm'])
            
            if 'chat' in settings:
                ChatSettings(**settings['chat'])
            
            if 'system' in settings:
                SystemSettings(**settings['system'])
            
            return {
                "valid": True,
                "message": "Настройки валидны"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Ошибка валидации настроек: {str(e)}"
            }
    
    async def get_available_models(self) -> list:
        """Возвращает список доступных моделей из LLMService"""
        from services.llm_service import LLMService
        
        llm_service = LLMService()
        try:
            models = await llm_service.get_available_models()
            return models if models else [
                "llama3.1:8b",
                "llama2:latest",
                "gpt-oss-optimized:latest",
                "gpt-oss:latest",
                "bge-m3:latest"
            ]
        except Exception:
            # Fallback к статическому списку в случае ошибки
            return [
                "llama3.1:8b",
                "llama2:latest",
                "gpt-oss-optimized:latest",
                "gpt-oss:latest",
                "bge-m3:latest"
            ]
    
    def get_available_languages(self) -> list:
        """Возвращает список доступных языков для OCR"""
        return [
            "rus",
            "eng", 
            "rus+eng",
            "fra",
            "deu",
            "spa",
            "ita",
            "por",
            "chi_sim",
            "chi_tra"
        ]
    
    def get_available_export_formats(self) -> list:
        """Возвращает список доступных форматов экспорта"""
        return ["docx", "pdf", "txt", "md"]
    
    async def get_available_models(self) -> list:
        """Возвращает список доступных моделей LLM"""
        # Импортируем здесь, чтобы избежать циклических импортов
        from services.llm_service import LLMService
        
        llm_service = LLMService()
        try:
            models = await llm_service.get_available_models()
            return models if models else [
                "llama3.1:8b",
                "llama3.1:70b", 
                "llama2:7b",
                "llama2:13b",
                "llama2:70b",
                "mistral:7b",
                "mistral:13b",
                "codellama:7b",
                "codellama:13b",
                "codellama:34b"
            ]
        except Exception:
            # Возвращаем список по умолчанию в случае ошибки
            return [
                "llama3.1:8b",
                "llama3.1:70b", 
                "llama2:7b",
                "llama2:13b",
                "llama2:70b",
                "mistral:7b",
                "mistral:13b",
                "codellama:7b",
                "codellama:13b",
                "codellama:34b"
            ]
