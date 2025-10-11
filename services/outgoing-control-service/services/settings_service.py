"""
Сервис для управления настройками модуля "Выходной контроль исходящей переписки"
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from settings import (
    OutgoingControlSettings, 
    SettingsUpdateRequest, 
    SettingsResponse,
    SettingsValidationResponse,
    CheckType,
    ReportFormat,
    LLMProvider
)

logger = logging.getLogger(__name__)

class OutgoingControlSettingsService:
    """Сервис для управления настройками выходного контроля"""
    
    def __init__(self, settings_file: str = "outgoing_control_settings.json"):
        self.settings_file = settings_file
        self.settings = OutgoingControlSettings()
        self.load_settings()
    
    def load_settings(self) -> None:
        """Загружает настройки из файла"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Обновляем настройки из файла
                self.settings = OutgoingControlSettings(**data)
                logger.info("Настройки загружены из файла")
            else:
                # Создаем файл с настройками по умолчанию
                self.save_settings()
                logger.info("Создан файл настроек с значениями по умолчанию")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            # Используем настройки по умолчанию
            self.settings = OutgoingControlSettings()
    
    def save_settings(self) -> None:
        """Сохраняет настройки в файл"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.dict(), f, indent=2, ensure_ascii=False)
            logger.info("Настройки сохранены в файл")
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            raise
    
    def get_settings(self) -> OutgoingControlSettings:
        """Получает текущие настройки"""
        return self.settings
    
    def update_settings(self, updates: Dict[str, Any]) -> SettingsResponse:
        """Обновляет настройки"""
        try:
            # Валидируем обновления
            validation = self.validate_settings(updates)
            if not validation.valid:
                return SettingsResponse(
                    success=False,
                    settings=self.settings,
                    message=f"Ошибки валидации: {', '.join(validation.errors)}"
                )
            
            # Обновляем настройки
            current_dict = self.settings.dict()
            current_dict.update(updates)
            
            # Создаем новый объект настроек
            self.settings = OutgoingControlSettings(**current_dict)
            
            # Сохраняем в файл
            self.save_settings()
            
            logger.info("Настройки успешно обновлены")
            return SettingsResponse(
                success=True,
                settings=self.settings,
                message="Настройки успешно обновлены"
            )
            
        except Exception as e:
            logger.error(f"Ошибка обновления настроек: {e}")
            return SettingsResponse(
                success=False,
                settings=self.settings,
                message=f"Ошибка обновления настроек: {str(e)}"
            )
    
    def validate_settings(self, settings: Dict[str, Any]) -> SettingsValidationResponse:
        """Валидирует настройки"""
        errors = []
        warnings = []
        
        try:
            # Проверяем LLM настройки
            if 'llm_temperature' in settings:
                temp = settings['llm_temperature']
                if not isinstance(temp, (int, float)) or temp < 0.0 or temp > 2.0:
                    errors.append("llm_temperature должен быть числом от 0.0 до 2.0")
            
            if 'llm_max_tokens' in settings:
                tokens = settings['llm_max_tokens']
                if not isinstance(tokens, int) or tokens < 100 or tokens > 4096:
                    errors.append("llm_max_tokens должен быть целым числом от 100 до 4096")
            
            if 'llm_timeout' in settings:
                timeout = settings['llm_timeout']
                if not isinstance(timeout, int) or timeout < 10 or timeout > 300:
                    errors.append("llm_timeout должен быть целым числом от 10 до 300")
            
            # Проверяем провайдера LLM
            if 'llm_provider' in settings:
                provider = settings['llm_provider']
                if provider not in [p.value for p in LLMProvider]:
                    errors.append(f"llm_provider должен быть одним из: {[p.value for p in LLMProvider]}")
            
            # Проверяем формат отчета
            if 'default_report_format' in settings:
                format_val = settings['default_report_format']
                if format_val not in [f.value for f in ReportFormat]:
                    errors.append(f"default_report_format должен быть одним из: {[f.value for f in ReportFormat]}")
            
            # Проверяем включенные проверки
            if 'enabled_checks' in settings:
                checks = settings['enabled_checks']
                if not isinstance(checks, list):
                    errors.append("enabled_checks должен быть списком")
                else:
                    valid_checks = [c.value for c in CheckType]
                    for check in checks:
                        if check not in valid_checks:
                            errors.append(f"Неизвестный тип проверки: {check}")
            
            # Проверяем размер файла
            if 'max_file_size_mb' in settings:
                size = settings['max_file_size_mb']
                if not isinstance(size, int) or size < 1 or size > 500:
                    errors.append("max_file_size_mb должен быть целым числом от 1 до 500")
            
            # Проверяем порог уверенности
            if 'min_confidence_threshold' in settings:
                threshold = settings['min_confidence_threshold']
                if not isinstance(threshold, (int, float)) or threshold < 0.0 or threshold > 1.0:
                    errors.append("min_confidence_threshold должен быть числом от 0.0 до 1.0")
            
            # Проверяем email
            if 'notification_email' in settings and settings['notification_email']:
                email = settings['notification_email']
                if '@' not in email or '.' not in email:
                    errors.append("notification_email должен быть валидным email адресом")
            
            # Проверяем типы файлов
            if 'allowed_file_types' in settings:
                file_types = settings['allowed_file_types']
                if not isinstance(file_types, list):
                    errors.append("allowed_file_types должен быть списком")
                else:
                    valid_types = ['pdf', 'docx', 'txt', 'rtf', 'odt']
                    for file_type in file_types:
                        if file_type not in valid_types:
                            warnings.append(f"Неподдерживаемый тип файла: {file_type}")
            
            # Проверяем промпты
            prompt_fields = [
                'spell_check_prompt', 'style_analysis_prompt', 'ethics_check_prompt',
                'terminology_check_prompt', 'final_review_prompt'
            ]
            
            for field in prompt_fields:
                if field in settings:
                    prompt = settings[field]
                    if not isinstance(prompt, str) or len(prompt.strip()) < 10:
                        warnings.append(f"{field} должен содержать минимум 10 символов")
            
            return SettingsValidationResponse(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Ошибка валидации настроек: {e}")
            return SettingsValidationResponse(
                valid=False,
                errors=[f"Ошибка валидации: {str(e)}"],
                warnings=[]
            )
    
    def reset_to_defaults(self) -> SettingsResponse:
        """Сбрасывает настройки к значениям по умолчанию"""
        try:
            self.settings = OutgoingControlSettings()
            self.save_settings()
            
            logger.info("Настройки сброшены к значениям по умолчанию")
            return SettingsResponse(
                success=True,
                settings=self.settings,
                message="Настройки сброшены к значениям по умолчанию"
            )
            
        except Exception as e:
            logger.error(f"Ошибка сброса настроек: {e}")
            return SettingsResponse(
                success=False,
                settings=self.settings,
                message=f"Ошибка сброса настроек: {str(e)}"
            )
    
    def get_prompt_for_check(self, check_type: CheckType) -> str:
        """Получает промпт для конкретного типа проверки"""
        prompts = {
            CheckType.SPELL_CHECK: self.settings.spell_check_prompt,
            CheckType.STYLE_ANALYSIS: self.settings.style_analysis_prompt,
            CheckType.ETHICS_CHECK: self.settings.ethics_check_prompt,
            CheckType.TERMINOLOGY_CHECK: self.settings.terminology_check_prompt,
            CheckType.FINAL_REVIEW: self.settings.final_review_prompt
        }
        return prompts.get(check_type, "")
    
    def is_check_enabled(self, check_type: CheckType) -> bool:
        """Проверяет, включена ли конкретная проверка"""
        return check_type in self.settings.enabled_checks
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Получает конфигурацию LLM"""
        return {
            "provider": self.settings.llm_provider,
            "model": self.settings.llm_model,
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_tokens,
            "timeout": self.settings.llm_timeout
        }
