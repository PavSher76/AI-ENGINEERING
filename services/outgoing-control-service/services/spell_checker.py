"""
Сервис для проверки орфографии
"""

import re
from typing import List, Dict, Any, Optional
import language_tool_python
from spellchecker import SpellChecker
import logging

logger = logging.getLogger(__name__)

class SpellCheckService:
    """Сервис для проверки орфографии и грамматики"""
    
    def __init__(self):
        self.language_tool = None
        self.spell_checker_ru = SpellChecker(language='ru')
        self.spell_checker_en = SpellChecker(language='en')
        
        # Инициализация LanguageTool
        try:
            self.language_tool = language_tool_python.LanguageTool('ru-RU')
        except Exception as e:
            logger.warning(f"Не удалось инициализировать LanguageTool: {e}")
    
    async def check_spelling(self, text: str, language: str = "ru") -> Dict[str, Any]:
        """
        Проверяет орфографию и грамматику текста
        
        Args:
            text: Текст для проверки
            language: Язык текста ('ru' или 'en')
            
        Returns:
            Результат проверки
        """
        try:
            # Очищаем текст
            cleaned_text = self._clean_text(text)
            
            # Разбиваем на слова
            words = self._extract_words(cleaned_text)
            
            # Проверяем орфографию
            spelling_errors = await self._check_spelling_errors(words, language)
            
            # Проверяем грамматику (если доступен LanguageTool)
            grammar_errors = []
            if self.language_tool and language == "ru":
                grammar_errors = await self._check_grammar_errors(text)
            
            # Объединяем результаты
            all_errors = spelling_errors + grammar_errors
            
            # Создаем исправленный текст
            corrected_text = self._create_corrected_text(text, all_errors)
            
            # Вычисляем оценку качества
            confidence_score = self._calculate_confidence_score(len(words), len(all_errors))
            
            return {
                "total_words": len(words),
                "errors_found": len(all_errors),
                "suggestions": all_errors,
                "corrected_text": corrected_text,
                "confidence_score": confidence_score,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке орфографии: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст от лишних символов"""
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        # Убираем специальные символы, оставляем только буквы, цифры и знаки препинания
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        return text.strip()
    
    def _extract_words(self, text: str) -> List[str]:
        """Извлекает слова из текста"""
        # Разбиваем на слова, сохраняя знаки препинания
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    async def _check_spelling_errors(self, words: List[str], language: str) -> List[Dict[str, Any]]:
        """Проверяет орфографические ошибки"""
        errors = []
        
        # Выбираем подходящий spell checker
        spell_checker = self.spell_checker_ru if language == "ru" else self.spell_checker_en
        
        for word in words:
            if not spell_checker.known([word]):
                # Слово не найдено в словаре
                candidates = spell_checker.candidates(word)
                suggestions = list(candidates)[:5] if candidates else []
                
                errors.append({
                    "type": "spelling",
                    "word": word,
                    "position": 0,  # TODO: Вычислить позицию в тексте
                    "suggestions": suggestions,
                    "severity": "medium"
                })
        
        return errors
    
    async def _check_grammar_errors(self, text: str) -> List[Dict[str, Any]]:
        """Проверяет грамматические ошибки с помощью LanguageTool"""
        errors = []
        
        try:
            if self.language_tool:
                matches = self.language_tool.check(text)
                
                for match in matches:
                    errors.append({
                        "type": "grammar",
                        "message": match.message,
                        "position": match.offset,
                        "length": match.errorLength,
                        "suggestions": match.replacements[:5],
                        "severity": "low" if match.ruleId.startswith('WHITESPACE') else "medium"
                    })
        except Exception as e:
            logger.warning(f"Ошибка при проверке грамматики: {e}")
        
        return errors
    
    def _create_corrected_text(self, original_text: str, errors: List[Dict[str, Any]]) -> str:
        """Создает исправленный текст"""
        corrected_text = original_text
        
        # Сортируем ошибки по позиции (от конца к началу, чтобы не сбить позиции)
        errors_sorted = sorted(errors, key=lambda x: x.get('position', 0), reverse=True)
        
        for error in errors_sorted:
            if error.get('suggestions') and len(error['suggestions']) > 0:
                # Берем первое предложение
                suggestion = error['suggestions'][0]
                word = error.get('word', '')
                
                # Заменяем слово в тексте
                if word:
                    corrected_text = corrected_text.replace(word, suggestion)
        
        return corrected_text
    
    def _calculate_confidence_score(self, total_words: int, errors_found: int) -> float:
        """Вычисляет оценку уверенности"""
        if total_words == 0:
            return 0.0
        
        error_rate = errors_found / total_words
        confidence = max(0.0, 1.0 - error_rate)
        return round(confidence * 100, 2)
    
    def get_supported_languages(self) -> List[str]:
        """Возвращает список поддерживаемых языков"""
        return ["ru", "en"]
    
    def is_language_supported(self, language: str) -> bool:
        """Проверяет, поддерживается ли язык"""
        return language in self.get_supported_languages()
