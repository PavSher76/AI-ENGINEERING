/**
 * Типы для настроек модуля "Выходной контроль исходящей переписки"
 */

export enum CheckType {
  SPELL_CHECK = "spell_check",
  STYLE_ANALYSIS = "style_analysis", 
  ETHICS_CHECK = "ethics_check",
  TERMINOLOGY_CHECK = "terminology_check",
  FINAL_REVIEW = "final_review"
}

export enum ReportFormat {
  PDF = "pdf",
  DOCX = "docx",
  TXT = "txt",
  HTML = "html"
}

export enum LLMProvider {
  OLLAMA = "ollama",
  OPENAI = "openai",
  ANTHROPIC = "anthropic"
}

export interface OutgoingControlSettings {
  // Настройки LLM
  llm_provider: LLMProvider;
  llm_model: string;
  llm_temperature: number;
  llm_max_tokens: number;
  llm_timeout: number;
  
  // Промпты для проверок
  spell_check_prompt: string;
  style_analysis_prompt: string;
  ethics_check_prompt: string;
  terminology_check_prompt: string;
  final_review_prompt: string;
  
  // Настройки отчетов
  default_report_format: ReportFormat;
  include_detailed_analysis: boolean;
  include_suggestions: boolean;
  include_statistics: boolean;
  
  // Настройки проверок
  enabled_checks: CheckType[];
  auto_process_on_upload: boolean;
  require_manual_approval: boolean;
  
  // Настройки качества
  min_confidence_threshold: number;
  max_processing_time: number;
  
  // Настройки уведомлений
  send_notifications: boolean;
  notification_email?: string;
  
  // Настройки интеграции
  enable_api_access: boolean;
  api_rate_limit: number;
  
  // Настройки безопасности
  require_authentication: boolean;
  allowed_file_types: string[];
  max_file_size_mb: number;
}

export interface SettingsUpdateRequest {
  settings: Partial<OutgoingControlSettings>;
}

export interface SettingsResponse {
  success: boolean;
  settings: OutgoingControlSettings;
  message?: string;
}

export interface SettingsValidationResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface PromptsResponse {
  spell_check_prompt: string;
  style_analysis_prompt: string;
  ethics_check_prompt: string;
  terminology_check_prompt: string;
  final_review_prompt: string;
}

export interface LLMConfigResponse {
  provider: LLMProvider;
  model: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
}
