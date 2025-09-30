"""
Сервис для проверки этики и соответствия корпоративным стандартам
"""

import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class EthicsChecker:
    """Сервис для проверки этичности содержания"""
    
    def __init__(self):
        # Слова и фразы, нарушающие этику
        self.unethical_patterns = {
            'discrimination': [
                r'\b(дискриминация|дискриминировать)\b',
                r'\b(расизм|расист)\b',
                r'\b(сексизм|сексист)\b',
                r'\b(гомофобия|гомофоб)\b',
                r'\b(нацизм|нацист)\b'
            ],
            'harassment': [
                r'\b(домогательство|приставание)\b',
                r'\b(угроза|угрожать)\b',
                r'\b(запугивание|запугивать)\b',
                r'\b(буллинг|травля)\b'
            ],
            'inappropriate_language': [
                r'\b(мат|ругательство|нецензурщина)\b',
                r'\b(оскорбление|оскорблять)\b',
                r'\b(унижение|унижать)\b'
            ],
            'confidentiality': [
                r'\b(конфиденциально|секретно|не разглашать)\b',
                r'\b(коммерческая тайна)\b',
                r'\b(персональные данные)\b'
            ],
            'conflict_of_interest': [
                r'\b(конфликт интересов)\b',
                r'\b(взятка|взяткодатель)\b',
                r'\b(откат|откатывать)\b'
            ]
        }
        
        # Положительные этические индикаторы
        self.ethical_patterns = {
            'respect': [
                r'\b(уважение|уважать|уважаемый)\b',
                r'\b(вежливость|вежливый)\b',
                r'\b(учтивость|учтивый)\b'
            ],
            'professionalism': [
                r'\b(профессионализм|профессиональный)\b',
                r'\b(компетентность|компетентный)\b',
                r'\b(ответственность|ответственный)\b'
            ],
            'integrity': [
                r'\b(честность|честный)\b',
                r'\b(порядочность|порядочный)\b',
                r'\b(справедливость|справедливый)\b'
            ]
        }
        
        # Корпоративные стандарты
        self.corporate_standards = {
            'inclusive_language': [
                r'\b(все сотрудники|каждый сотрудник)\b',
                r'\b(команда|коллектив)\b',
                r'\b(партнерство|сотрудничество)\b'
            ],
            'transparency': [
                r'\b(открытость|прозрачность)\b',
                r'\b(информирование|информировать)\b',
                r'\b(объяснение|объяснять)\b'
            ]
        }
    
    async def check_ethics(self, text: str, context: str = None) -> Dict[str, Any]:
        """
        Проверяет этичность содержания
        
        Args:
            text: Текст для проверки
            context: Контекст документа
            
        Returns:
            Результат проверки этики
        """
        try:
            # Очищаем текст
            cleaned_text = self._clean_text(text)
            
            # Проверяем на нарушения этики
            violations = await self._find_violations(cleaned_text)
            
            # Проверяем положительные этические индикаторы
            positive_indicators = await self._find_positive_indicators(cleaned_text)
            
            # Проверяем соответствие корпоративным стандартам
            corporate_compliance = await self._check_corporate_standards(cleaned_text)
            
            # Вычисляем общую оценку этичности
            ethics_score = self._calculate_ethics_score(violations, positive_indicators, corporate_compliance)
            
            # Определяем, можно ли одобрить документ
            is_approved = self._can_approve_document(violations, ethics_score)
            
            # Генерируем рекомендации
            recommendations = self._generate_recommendations(violations, positive_indicators, corporate_compliance)
            
            return {
                "ethics_score": ethics_score,
                "violations_found": violations,
                "positive_indicators": positive_indicators,
                "corporate_compliance": corporate_compliance,
                "recommendations": recommendations,
                "is_approved": is_approved,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке этики: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст для анализа"""
        # Приводим к нижнему регистру
        text = text.lower()
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    async def _find_violations(self, text: str) -> List[Dict[str, Any]]:
        """Находит нарушения этики в тексте"""
        violations = []
        
        for category, patterns in self.unethical_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    violations.append({
                        "category": category,
                        "pattern": pattern,
                        "text": match.group(),
                        "position": match.start(),
                        "severity": self._get_severity(category)
                    })
        
        return violations
    
    async def _find_positive_indicators(self, text: str) -> List[Dict[str, Any]]:
        """Находит положительные этические индикаторы"""
        indicators = []
        
        for category, patterns in self.ethical_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    indicators.append({
                        "category": category,
                        "pattern": pattern,
                        "text": match.group(),
                        "position": match.start()
                    })
        
        return indicators
    
    async def _check_corporate_standards(self, text: str) -> Dict[str, Any]:
        """Проверяет соответствие корпоративным стандартам"""
        compliance = {}
        
        for standard, patterns in self.corporate_standards.items():
            matches = []
            for pattern in patterns:
                pattern_matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in pattern_matches:
                    matches.append({
                        "text": match.group(),
                        "position": match.start()
                    })
            
            compliance[standard] = {
                "found": len(matches) > 0,
                "matches": matches,
                "score": min(1.0, len(matches) / 3)  # Нормализуем
            }
        
        return compliance
    
    def _get_severity(self, category: str) -> str:
        """Определяет серьезность нарушения"""
        severity_map = {
            'discrimination': 'high',
            'harassment': 'high',
            'inappropriate_language': 'medium',
            'confidentiality': 'high',
            'conflict_of_interest': 'high'
        }
        return severity_map.get(category, 'medium')
    
    def _calculate_ethics_score(self, violations: List[Dict[str, Any]], 
                              positive_indicators: List[Dict[str, Any]], 
                              corporate_compliance: Dict[str, Any]) -> float:
        """Вычисляет общую оценку этичности"""
        try:
            # Базовый балл
            base_score = 100.0
            
            # Штрафы за нарушения
            for violation in violations:
                severity = violation.get('severity', 'medium')
                if severity == 'high':
                    base_score -= 20
                elif severity == 'medium':
                    base_score -= 10
                else:
                    base_score -= 5
            
            # Бонусы за положительные индикаторы
            positive_bonus = min(20, len(positive_indicators) * 2)
            base_score += positive_bonus
            
            # Бонусы за соответствие корпоративным стандартам
            corporate_bonus = 0
            for standard, compliance in corporate_compliance.items():
                if compliance['found']:
                    corporate_bonus += 5
            
            base_score += corporate_bonus
            
            # Нормализуем в диапазон 0-100
            final_score = max(0.0, min(100.0, base_score))
            
            return round(final_score, 2)
            
        except Exception as e:
            logger.warning(f"Ошибка при вычислении оценки этичности: {e}")
            return 50.0
    
    def _can_approve_document(self, violations: List[Dict[str, Any]], ethics_score: float) -> bool:
        """Определяет, можно ли одобрить документ"""
        # Нельзя одобрить, если есть критические нарушения
        critical_violations = [v for v in violations if v.get('severity') == 'high']
        if critical_violations:
            return False
        
        # Нельзя одобрить, если оценка слишком низкая
        if ethics_score < 60:
            return False
        
        return True
    
    def _generate_recommendations(self, violations: List[Dict[str, Any]], 
                                positive_indicators: List[Dict[str, Any]], 
                                corporate_compliance: Dict[str, Any]) -> str:
        """Генерирует рекомендации по улучшению этичности"""
        recommendations = []
        
        # Рекомендации по нарушениям
        if violations:
            high_severity = [v for v in violations if v.get('severity') == 'high']
            if high_severity:
                recommendations.append("КРИТИЧНО: Удалите или переформулируйте фразы, нарушающие этические нормы.")
            
            medium_severity = [v for v in violations if v.get('severity') == 'medium']
            if medium_severity:
                recommendations.append("Исправьте неподходящие формулировки для повышения профессионального тона.")
        
        # Рекомендации по корпоративным стандартам
        missing_standards = [std for std, comp in corporate_compliance.items() if not comp['found']]
        if missing_standards:
            recommendations.append("Добавьте формулировки, соответствующие корпоративным стандартам.")
        
        # Рекомендации по положительным индикаторам
        if not positive_indicators:
            recommendations.append("Добавьте вежливые обращения и профессиональные формулировки.")
        
        if not recommendations:
            recommendations.append("Документ соответствует этическим стандартам.")
        
        return " ".join(recommendations)
    
    def get_ethics_guidelines(self) -> Dict[str, str]:
        """Возвращает руководящие принципы этики"""
        return {
            "respect": "Проявляйте уважение ко всем участникам коммуникации",
            "professionalism": "Поддерживайте профессиональный тон и стиль",
            "inclusivity": "Используйте инклюзивный язык",
            "transparency": "Будьте открытыми и честными",
            "confidentiality": "Соблюдайте конфиденциальность информации",
            "integrity": "Действуйте с честностью и порядочностью"
        }
