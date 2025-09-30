"""
Сервис для анализа стиля письма
"""

import re
import nltk
import textstat
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class StyleAnalyzer:
    """Сервис для анализа стиля письма"""
    
    def __init__(self):
        # Загружаем необходимые ресурсы NLTK
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('vader_lexicon', quiet=True)
        except Exception as e:
            logger.warning(f"Не удалось загрузить ресурсы NLTK: {e}")
        
        # Ключевые слова для делового стиля
        self.business_keywords = {
            'ru': [
                'уважаемый', 'уважаемая', 'прошу', 'предлагаю', 'сообщаю',
                'информирую', 'уведомляю', 'направляю', 'представляю',
                'согласно', 'в соответствии', 'в связи с', 'в целях',
                'просим', 'требуем', 'настоятельно', 'необходимо',
                'обязательно', 'срочно', 'немедленно', 'в срок'
            ],
            'en': [
                'dear', 'sir', 'madam', 'please', 'request', 'propose',
                'inform', 'notify', 'submit', 'according', 'pursuant',
                'in accordance', 'in connection', 'in order to',
                'require', 'demand', 'urgent', 'immediate', 'deadline'
            ]
        }
        
        # Слова, снижающие формальность
        self.informal_words = {
            'ru': ['привет', 'пока', 'спасибо', 'пожалуйста', 'извини', 'круто', 'классно'],
            'en': ['hi', 'bye', 'thanks', 'please', 'sorry', 'cool', 'awesome']
        }
    
    async def analyze_style(self, text: str, document_type: str = "letter") -> Dict[str, Any]:
        """
        Анализирует стиль письма
        
        Args:
            text: Текст для анализа
            document_type: Тип документа
            
        Returns:
            Результат анализа стиля
        """
        try:
            # Очищаем текст
            cleaned_text = self._clean_text(text)
            
            # Анализируем читаемость
            readability_score = self._calculate_readability(cleaned_text)
            
            # Анализируем формальность
            formality_score = self._calculate_formality(cleaned_text)
            
            # Анализируем соответствие деловому стилю
            business_style_score = self._calculate_business_style(cleaned_text)
            
            # Анализируем тон
            tone_analysis = self._analyze_tone(cleaned_text)
            
            # Генерируем рекомендации
            recommendations = self._generate_recommendations(
                readability_score, formality_score, business_style_score, tone_analysis
            )
            
            return {
                "readability_score": readability_score,
                "formality_score": formality_score,
                "business_style_score": business_style_score,
                "tone_analysis": tone_analysis,
                "recommendations": recommendations,
                "document_type": document_type
            }
            
        except Exception as e:
            logger.error(f"Ошибка при анализе стиля: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст для анализа"""
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        # Убираем специальные символы, оставляем только буквы и пробелы
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.strip()
    
    def _calculate_readability(self, text: str) -> float:
        """Вычисляет индекс читаемости"""
        try:
            # Используем Flesch Reading Ease для английского
            # Для русского текста используем адаптированную формулу
            
            # Подсчитываем предложения
            sentences = re.split(r'[.!?]+', text)
            sentence_count = len([s for s in sentences if s.strip()])
            
            # Подсчитываем слова
            words = text.split()
            word_count = len(words)
            
            # Подсчитываем слоги (приблизительно)
            syllable_count = sum(self._count_syllables(word) for word in words)
            
            if sentence_count == 0 or word_count == 0:
                return 0.0
            
            # Формула читаемости (адаптированная для русского)
            readability = 206.835 - (1.015 * (word_count / sentence_count)) - (84.6 * (syllable_count / word_count))
            
            # Нормализуем в диапазон 0-100
            return max(0.0, min(100.0, readability))
            
        except Exception as e:
            logger.warning(f"Ошибка при вычислении читаемости: {e}")
            return 50.0  # Среднее значение по умолчанию
    
    def _count_syllables(self, word: str) -> int:
        """Подсчитывает количество слогов в слове"""
        # Простая эвристика для русского языка
        vowels = 'аеёиоуыэюя'
        syllable_count = sum(1 for char in word.lower() if char in vowels)
        return max(1, syllable_count)
    
    def _calculate_formality(self, text: str) -> float:
        """Вычисляет уровень формальности"""
        try:
            words = text.lower().split()
            total_words = len(words)
            
            if total_words == 0:
                return 0.0
            
            # Подсчитываем формальные слова
            formal_count = 0
            informal_count = 0
            
            # Проверяем на формальные слова (деловая лексика)
            for word in words:
                if any(formal_word in word for formal_word in self.business_keywords.get('ru', [])):
                    formal_count += 1
                elif any(formal_word in word for formal_word in self.business_keywords.get('en', [])):
                    formal_count += 1
            
            # Проверяем на неформальные слова
            for word in words:
                if any(informal_word in word for informal_word in self.informal_words.get('ru', [])):
                    informal_count += 1
                elif any(informal_word in word for informal_word in self.informal_words.get('en', [])):
                    informal_count += 1
            
            # Вычисляем формальность
            formality = (formal_count - informal_count) / total_words
            formality = max(0.0, min(1.0, formality + 0.5))  # Нормализуем в 0-1
            
            return round(formality * 100, 2)
            
        except Exception as e:
            logger.warning(f"Ошибка при вычислении формальности: {e}")
            return 50.0
    
    def _calculate_business_style(self, text: str) -> float:
        """Вычисляет соответствие деловому стилю"""
        try:
            words = text.lower().split()
            total_words = len(words)
            
            if total_words == 0:
                return 0.0
            
            business_count = 0
            
            # Подсчитываем деловые слова
            for word in words:
                if any(business_word in word for business_word in self.business_keywords.get('ru', [])):
                    business_count += 1
                elif any(business_word in word for business_word in self.business_keywords.get('en', [])):
                    business_count += 1
            
            # Вычисляем процент деловых слов
            business_ratio = business_count / total_words
            business_score = min(100.0, business_ratio * 200)  # Масштабируем
            
            return round(business_score, 2)
            
        except Exception as e:
            logger.warning(f"Ошибка при вычислении делового стиля: {e}")
            return 50.0
    
    def _analyze_tone(self, text: str) -> Dict[str, Any]:
        """Анализирует тон письма"""
        try:
            # Простой анализ тона на основе ключевых слов
            positive_words = ['спасибо', 'благодарю', 'приятно', 'рад', 'успех', 'достижение']
            negative_words = ['проблема', 'ошибка', 'неудача', 'плохо', 'неправильно', 'отказ']
            neutral_words = ['информация', 'данные', 'документ', 'процедура', 'процесс']
            
            words = text.lower().split()
            
            positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
            negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
            neutral_count = sum(1 for word in words if any(neu in word for neu in neutral_words))
            
            total_sentiment_words = positive_count + negative_count + neutral_count
            
            if total_sentiment_words == 0:
                return {
                    "tone": "neutral",
                    "confidence": 0.5,
                    "positive_score": 0.0,
                    "negative_score": 0.0,
                    "neutral_score": 1.0
                }
            
            positive_score = positive_count / total_sentiment_words
            negative_score = negative_count / total_sentiment_words
            neutral_score = neutral_count / total_sentiment_words
            
            # Определяем основной тон
            if positive_score > negative_score and positive_score > neutral_score:
                tone = "positive"
            elif negative_score > positive_score and negative_score > neutral_score:
                tone = "negative"
            else:
                tone = "neutral"
            
            confidence = max(positive_score, negative_score, neutral_score)
            
            return {
                "tone": tone,
                "confidence": round(confidence, 2),
                "positive_score": round(positive_score, 2),
                "negative_score": round(negative_score, 2),
                "neutral_score": round(neutral_score, 2)
            }
            
        except Exception as e:
            logger.warning(f"Ошибка при анализе тона: {e}")
            return {
                "tone": "neutral",
                "confidence": 0.5,
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0
            }
    
    def _generate_recommendations(self, readability: float, formality: float, 
                                business_style: float, tone_analysis: Dict[str, Any]) -> str:
        """Генерирует рекомендации по улучшению стиля"""
        recommendations = []
        
        # Рекомендации по читаемости
        if readability < 30:
            recommendations.append("Текст слишком сложен для понимания. Упростите предложения и используйте более простые слова.")
        elif readability > 80:
            recommendations.append("Текст может быть слишком простым для делового документа. Добавьте профессиональную терминологию.")
        
        # Рекомендации по формальности
        if formality < 40:
            recommendations.append("Повысьте формальность стиля. Используйте более официальные обращения и конструкции.")
        elif formality > 90:
            recommendations.append("Стиль может быть слишком формальным. Добавьте немного человечности в текст.")
        
        # Рекомендации по деловому стилю
        if business_style < 30:
            recommendations.append("Добавьте больше деловой лексики и официальных формулировок.")
        
        # Рекомендации по тону
        if tone_analysis["tone"] == "negative" and tone_analysis["confidence"] > 0.7:
            recommendations.append("Тон письма слишком негативный. Переформулируйте предложения в более позитивном ключе.")
        
        if not recommendations:
            recommendations.append("Стиль письма соответствует деловым стандартам.")
        
        return " ".join(recommendations)
