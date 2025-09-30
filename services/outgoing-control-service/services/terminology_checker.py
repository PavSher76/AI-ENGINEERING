"""
Сервис для проверки правильности использования профессиональной терминологии
"""

import re
from typing import Dict, Any, List, Set
import logging

logger = logging.getLogger(__name__)

class TerminologyChecker:
    """Сервис для проверки терминологии"""
    
    def __init__(self):
        # Словари профессиональной терминологии по областям
        self.terminology_dictionaries = {
            'engineering': {
                'correct_terms': {
                    'ru': {
                        'техническое задание': ['ТЗ', 'техзадание'],
                        'проектная документация': ['ПД', 'проектная документация'],
                        'рабочая документация': ['РД', 'рабочая документация'],
                        'смета': ['сметная стоимость', 'сметный расчет'],
                        'спецификация': ['спецификация оборудования', 'спецификация материалов'],
                        'чертеж': ['чертеж', 'схема', 'план'],
                        'монтаж': ['монтажные работы', 'установка'],
                        'наладка': ['пусконаладочные работы', 'ПНР'],
                        'эксплуатация': ['эксплуатационные характеристики'],
                        'техническое обслуживание': ['ТО', 'техобслуживание'],
                        'ремонт': ['капитальный ремонт', 'текущий ремонт'],
                        'контроль качества': ['ОТК', 'контроль качества'],
                        'сертификация': ['сертификат соответствия'],
                        'лицензирование': ['лицензия', 'разрешение']
                    },
                    'en': {
                        'technical specification': ['TS', 'tech spec'],
                        'project documentation': ['PD', 'project docs'],
                        'working documentation': ['WD', 'working docs'],
                        'estimate': ['cost estimate', 'budget'],
                        'specification': ['equipment spec', 'material spec'],
                        'drawing': ['drawing', 'scheme', 'plan'],
                        'installation': ['installation works', 'mounting'],
                        'commissioning': ['commissioning works', 'startup'],
                        'operation': ['operational characteristics'],
                        'maintenance': ['maintenance', 'servicing'],
                        'repair': ['major repair', 'minor repair'],
                        'quality control': ['QC', 'quality assurance'],
                        'certification': ['certificate of compliance'],
                        'licensing': ['license', 'permit']
                    }
                },
                'incorrect_terms': {
                    'ru': {
                        'техзадание': 'техническое задание',
                        'проектка': 'проектная документация',
                        'рабочка': 'рабочая документация',
                        'сметка': 'смета',
                        'спецификация': 'спецификация оборудования',
                        'чертежик': 'чертеж',
                        'монтажик': 'монтаж',
                        'наладка': 'пусконаладочные работы',
                        'эксплуатация': 'эксплуатационные характеристики',
                        'ремонтик': 'ремонт'
                    },
                    'en': {
                        'tech spec': 'technical specification',
                        'project docs': 'project documentation',
                        'working docs': 'working documentation',
                        'cost est': 'cost estimate',
                        'equipment spec': 'equipment specification',
                        'drawing': 'technical drawing',
                        'install': 'installation',
                        'startup': 'commissioning',
                        'ops': 'operations',
                        'maint': 'maintenance'
                    }
                }
            },
            'legal': {
                'correct_terms': {
                    'ru': {
                        'договор': ['договор', 'соглашение', 'контракт'],
                        'соглашение': ['соглашение', 'договоренность'],
                        'контракт': ['контракт', 'договор'],
                        'лицензия': ['лицензия', 'разрешение'],
                        'патент': ['патент', 'изобретение'],
                        'авторское право': ['копирайт', 'авторские права'],
                        'интеллектуальная собственность': ['ИС', 'интеллектуальная собственность'],
                        'конфиденциальность': ['конфиденциальная информация'],
                        'неразглашение': ['соглашение о неразглашении', 'NDA'],
                        'ответственность': ['материальная ответственность', 'гражданская ответственность'],
                        'страхование': ['страхование ответственности'],
                        'арбитраж': ['арбитражный суд', 'третейский суд'],
                        'медиация': ['медиация', 'посредничество'],
                        'иск': ['исковое заявление', 'судебный иск']
                    },
                    'en': {
                        'contract': ['contract', 'agreement'],
                        'agreement': ['agreement', 'understanding'],
                        'license': ['license', 'permit'],
                        'patent': ['patent', 'invention'],
                        'copyright': ['copyright', 'intellectual property'],
                        'intellectual property': ['IP', 'intellectual property'],
                        'confidentiality': ['confidential information'],
                        'non-disclosure': ['non-disclosure agreement', 'NDA'],
                        'liability': ['material liability', 'civil liability'],
                        'insurance': ['liability insurance'],
                        'arbitration': ['arbitration court', 'arbitral tribunal'],
                        'mediation': ['mediation', 'conciliation'],
                        'lawsuit': ['legal action', 'court case']
                    }
                },
                'incorrect_terms': {
                    'ru': {
                        'договорчик': 'договор',
                        'соглашенье': 'соглашение',
                        'контрактик': 'контракт',
                        'лицензийка': 'лицензия',
                        'патентчик': 'патент',
                        'копирайт': 'авторское право',
                        'ИС': 'интеллектуальная собственность',
                        'конфиденциальность': 'конфиденциальная информация',
                        'NDA': 'соглашение о неразглашении',
                        'ответственность': 'материальная ответственность',
                        'страховка': 'страхование ответственности',
                        'арбитраж': 'арбитражный суд',
                        'медиация': 'медиация',
                        'иск': 'исковое заявление'
                    },
                    'en': {
                        'contract': 'contract agreement',
                        'agreement': 'legal agreement',
                        'license': 'operating license',
                        'patent': 'patent protection',
                        'copyright': 'copyright protection',
                        'IP': 'intellectual property',
                        'confidentiality': 'confidential information',
                        'NDA': 'non-disclosure agreement',
                        'liability': 'legal liability',
                        'insurance': 'liability insurance',
                        'arbitration': 'arbitration proceeding',
                        'mediation': 'mediation process',
                        'lawsuit': 'legal action'
                    }
                }
            },
            'business': {
                'correct_terms': {
                    'ru': {
                        'бизнес-план': ['бизнес-план', 'план развития'],
                        'стратегия': ['стратегия развития', 'корпоративная стратегия'],
                        'бюджет': ['бюджет', 'финансовый план'],
                        'инвестиции': ['инвестиции', 'капиталовложения'],
                        'прибыль': ['прибыль', 'доход'],
                        'убыток': ['убыток', 'потери'],
                        'активы': ['активы', 'имущество'],
                        'пассивы': ['пассивы', 'обязательства'],
                        'ликвидность': ['ликвидность', 'платежеспособность'],
                        'рентабельность': ['рентабельность', 'доходность'],
                        'конкурентоспособность': ['конкурентоспособность', 'конкурентные преимущества'],
                        'маркетинг': ['маркетинг', 'продвижение'],
                        'продажи': ['продажи', 'сбыт'],
                        'клиент': ['клиент', 'заказчик', 'покупатель']
                    },
                    'en': {
                        'business plan': ['business plan', 'development plan'],
                        'strategy': ['development strategy', 'corporate strategy'],
                        'budget': ['budget', 'financial plan'],
                        'investment': ['investment', 'capital investment'],
                        'profit': ['profit', 'revenue'],
                        'loss': ['loss', 'deficit'],
                        'assets': ['assets', 'property'],
                        'liabilities': ['liabilities', 'obligations'],
                        'liquidity': ['liquidity', 'solvency'],
                        'profitability': ['profitability', 'return'],
                        'competitiveness': ['competitiveness', 'competitive advantage'],
                        'marketing': ['marketing', 'promotion'],
                        'sales': ['sales', 'selling'],
                        'client': ['client', 'customer', 'buyer']
                    }
                },
                'incorrect_terms': {
                    'ru': {
                        'бизнес-планик': 'бизнес-план',
                        'стратегийка': 'стратегия',
                        'бюджетик': 'бюджет',
                        'инвестиции': 'капиталовложения',
                        'прибылька': 'прибыль',
                        'убыточек': 'убыток',
                        'активики': 'активы',
                        'пассивики': 'пассивы',
                        'ликвидность': 'платежеспособность',
                        'рентабельность': 'доходность',
                        'конкурентоспособность': 'конкурентные преимущества',
                        'маркетинг': 'продвижение',
                        'продажи': 'сбыт',
                        'клиентик': 'клиент'
                    },
                    'en': {
                        'business plan': 'development plan',
                        'strategy': 'corporate strategy',
                        'budget': 'financial plan',
                        'investment': 'capital investment',
                        'profit': 'revenue',
                        'loss': 'deficit',
                        'assets': 'property',
                        'liabilities': 'obligations',
                        'liquidity': 'solvency',
                        'profitability': 'return',
                        'competitiveness': 'competitive advantage',
                        'marketing': 'promotion',
                        'sales': 'selling',
                        'client': 'customer'
                    }
                }
            }
        }
    
    async def check_terminology(self, text: str, domain: str = "engineering") -> Dict[str, Any]:
        """
        Проверяет правильность использования терминологии
        
        Args:
            text: Текст для проверки
            domain: Область знаний ('engineering', 'legal', 'business')
            
        Returns:
            Результат проверки терминологии
        """
        try:
            # Очищаем текст
            cleaned_text = self._clean_text(text)
            
            # Получаем словарь терминологии для области
            if domain not in self.terminology_dictionaries:
                domain = "engineering"  # По умолчанию
            
            terminology_dict = self.terminology_dictionaries[domain]
            
            # Анализируем использованные термины
            terms_used = await self._extract_terms(cleaned_text, terminology_dict)
            
            # Находим неправильно использованные термины
            incorrect_terms = await self._find_incorrect_terms(cleaned_text, terminology_dict)
            
            # Генерируем предложения по улучшению
            suggestions = await self._generate_suggestions(incorrect_terms, terminology_dict)
            
            # Вычисляем оценку точности
            accuracy_score = self._calculate_accuracy_score(terms_used, incorrect_terms)
            
            return {
                "terms_used": terms_used,
                "incorrect_terms": incorrect_terms,
                "suggestions": suggestions,
                "accuracy_score": accuracy_score,
                "domain": domain
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке терминологии: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст для анализа"""
        # Приводим к нижнему регистру
        text = text.lower()
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        # Убираем знаки препинания для анализа терминов
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.strip()
    
    async def _extract_terms(self, text: str, terminology_dict: Dict[str, Any]) -> List[str]:
        """Извлекает использованные термины из текста"""
        terms_found = []
        
        # Проверяем правильные термины
        for language in ['ru', 'en']:
            if language in terminology_dict.get('correct_terms', {}):
                for term, variants in terminology_dict['correct_terms'][language].items():
                    # Проверяем основной термин
                    if term in text:
                        terms_found.append(term)
                    # Проверяем варианты
                    for variant in variants:
                        if variant in text:
                            terms_found.append(variant)
        
        return list(set(terms_found))  # Убираем дубликаты
    
    async def _find_incorrect_terms(self, text: str, terminology_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Находит неправильно использованные термины"""
        incorrect_terms = []
        
        # Проверяем неправильные термины
        for language in ['ru', 'en']:
            if language in terminology_dict.get('incorrect_terms', {}):
                for incorrect_term, correct_term in terminology_dict['incorrect_terms'][language].items():
                    if incorrect_term in text:
                        incorrect_terms.append({
                            "incorrect_term": incorrect_term,
                            "correct_term": correct_term,
                            "language": language,
                            "severity": "medium"
                        })
        
        return incorrect_terms
    
    async def _generate_suggestions(self, incorrect_terms: List[Dict[str, Any]], 
                                  terminology_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерирует предложения по улучшению терминологии"""
        suggestions = []
        
        for term in incorrect_terms:
            suggestions.append({
                "original": term['incorrect_term'],
                "suggestion": term['correct_term'],
                "reason": f"Используйте профессиональную терминологию",
                "category": "terminology"
            })
        
        return suggestions
    
    def _calculate_accuracy_score(self, terms_used: List[str], incorrect_terms: List[Dict[str, Any]]) -> float:
        """Вычисляет оценку точности терминологии"""
        try:
            total_terms = len(terms_used) + len(incorrect_terms)
            
            if total_terms == 0:
                return 100.0  # Нет терминов для проверки
            
            correct_terms = len(terms_used)
            accuracy = (correct_terms / total_terms) * 100
            
            return round(accuracy, 2)
            
        except Exception as e:
            logger.warning(f"Ошибка при вычислении оценки точности: {e}")
            return 50.0
    
    def get_supported_domains(self) -> List[str]:
        """Возвращает список поддерживаемых областей знаний"""
        return list(self.terminology_dictionaries.keys())
    
    def get_domain_terms(self, domain: str, language: str = "ru") -> Dict[str, List[str]]:
        """Возвращает термины для указанной области и языка"""
        if domain not in self.terminology_dictionaries:
            return {}
        
        terminology_dict = self.terminology_dictionaries[domain]
        return terminology_dict.get('correct_terms', {}).get(language, {})
    
    def add_custom_terms(self, domain: str, language: str, terms: Dict[str, List[str]]):
        """Добавляет пользовательские термины"""
        if domain not in self.terminology_dictionaries:
            self.terminology_dictionaries[domain] = {
                'correct_terms': {},
                'incorrect_terms': {}
            }
        
        if 'correct_terms' not in self.terminology_dictionaries[domain]:
            self.terminology_dictionaries[domain]['correct_terms'] = {}
        
        if language not in self.terminology_dictionaries[domain]['correct_terms']:
            self.terminology_dictionaries[domain]['correct_terms'][language] = {}
        
        self.terminology_dictionaries[domain]['correct_terms'][language].update(terms)
