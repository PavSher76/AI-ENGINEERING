"""
Схемы настроек для модуля "Выходной контроль исходящей переписки"
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum

class CheckType(str, Enum):
    """Типы проверок"""
    SPELL_CHECK = "spell_check"
    STYLE_ANALYSIS = "style_analysis"
    ETHICS_CHECK = "ethics_check"
    TERMINOLOGY_CHECK = "terminology_check"
    FINAL_REVIEW = "final_review"

class ReportFormat(str, Enum):
    """Форматы отчетов"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"

class LLMProvider(str, Enum):
    """Провайдеры LLM"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class OutgoingControlSettings(BaseModel):
    """Настройки модуля выходного контроля"""
    
    # Настройки LLM
    llm_provider: LLMProvider = Field(default=LLMProvider.OLLAMA, description="Провайдер LLM")
    llm_model: str = Field(default="llama3.1:8b", description="Модель LLM")
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Температура генерации")
    llm_max_tokens: int = Field(default=1024, ge=100, le=4096, description="Максимальное количество токенов")
    llm_timeout: int = Field(default=60, ge=10, le=300, description="Таймаут запроса в секундах")
    
    # Промпты для проверок
    spell_check_prompt: str = Field(
        default="Проверь орфографию и грамматику в следующем тексте. Найди ошибки и предложи исправления:",
        description="Промпт для проверки орфографии"
    )
    style_analysis_prompt: str = Field(
        default="Проанализируй стиль следующего текста. Оцени читаемость, формальность и соответствие деловому стилю:",
        description="Промпт для анализа стиля"
    )
    ethics_check_prompt: str = Field(
        default="Проверь текст на соответствие этическим нормам и корпоративным стандартам. Найди потенциальные нарушения:",
        description="Промпт для проверки этики"
    )
    terminology_check_prompt: str = Field(
        default="Проверь использование терминологии в тексте. Найди неточности и предложи правильные термины:",
        description="Промпт для проверки терминологии"
    )
    final_review_prompt: str = Field(
        default="Проведи финальную проверку документа. Оцени готовность к отправке и дай рекомендации:",
        description="Промпт для финальной проверки"
    )
    
    # Настройки отчетов
    default_report_format: ReportFormat = Field(default=ReportFormat.PDF, description="Формат отчета по умолчанию")
    include_detailed_analysis: bool = Field(default=True, description="Включать детальный анализ в отчет")
    include_suggestions: bool = Field(default=True, description="Включать предложения по улучшению")
    include_statistics: bool = Field(default=True, description="Включать статистику проверок")
    
    # Настройки проверок
    enabled_checks: List[CheckType] = Field(
        default=[CheckType.SPELL_CHECK, CheckType.STYLE_ANALYSIS, CheckType.ETHICS_CHECK, CheckType.TERMINOLOGY_CHECK],
        description="Включенные типы проверок"
    )
    auto_process_on_upload: bool = Field(default=False, description="Автоматически обрабатывать при загрузке")
    require_manual_approval: bool = Field(default=True, description="Требовать ручного одобрения")
    
    # Настройки качества
    min_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Минимальный порог уверенности")
    max_processing_time: int = Field(default=300, ge=30, le=1800, description="Максимальное время обработки в секундах")
    
    # Настройки уведомлений
    send_notifications: bool = Field(default=True, description="Отправлять уведомления")
    notification_email: Optional[str] = Field(default=None, description="Email для уведомлений")
    
    # Настройки интеграции
    enable_api_access: bool = Field(default=True, description="Включить API доступ")
    api_rate_limit: int = Field(default=100, ge=1, le=1000, description="Лимит запросов в час")
    
    # Настройки безопасности
    require_authentication: bool = Field(default=True, description="Требовать аутентификацию")
    allowed_file_types: List[str] = Field(
        default=["pdf", "docx", "txt"],
        description="Разрешенные типы файлов"
    )
    max_file_size_mb: int = Field(default=50, ge=1, le=500, description="Максимальный размер файла в МБ")

class SettingsUpdateRequest(BaseModel):
    """Запрос на обновление настроек"""
    settings: Dict[str, Any] = Field(..., description="Настройки для обновления")

class SettingsResponse(BaseModel):
    """Ответ с настройками"""
    success: bool = Field(..., description="Успешность операции")
    settings: OutgoingControlSettings = Field(..., description="Текущие настройки")
    message: Optional[str] = Field(default=None, description="Сообщение")

class SettingsValidationResponse(BaseModel):
    """Ответ валидации настроек"""
    valid: bool = Field(..., description="Валидность настроек")
    errors: List[str] = Field(default=[], description="Список ошибок")
    warnings: List[str] = Field(default=[], description="Список предупреждений")
