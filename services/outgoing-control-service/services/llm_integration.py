"""
Сервис для интеграции с LLM (Ollama/OpenAI) для финальной проверки
"""

import httpx
import json
from typing import Dict, Any, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

class LLMIntegration:
    """Сервис для интеграции с LLM"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Промпты для различных типов проверок
        self.prompts = {
            "final_review": """
Ты - эксперт по деловой переписке и документообороту. Проанализируй следующий документ и дай заключение о возможности его отправки.

Документ:
{text}

Результаты предыдущих проверок:
- Орфография: {spell_check_result}
- Стиль: {style_analysis_result}
- Этичность: {ethics_check_result}
- Терминология: {terminology_check_result}

Дай заключение в следующем формате:
1. ОБЩАЯ ОЦЕНКА (0-100): [число]
2. МОЖНО ОТПРАВЛЯТЬ: [да/нет]
3. КРИТИЧЕСКИЕ ПРОБЛЕМЫ: [список проблем, если есть]
4. МЕЛКИЕ ПРОБЛЕМЫ: [список проблем, если есть]
5. РЕКОМЕНДАЦИИ: [конкретные рекомендации по улучшению]
6. ЗАКЛЮЧЕНИЕ: [краткое резюме]

Учитывай:
- Деловой стиль и этикет
- Логичность и последовательность
- Правильность профессиональных терминов
- Соответствие корпоративным стандартам
- Возможные риски при отправке
""",
            
            "style_improvement": """
Ты - эксперт по деловому стилю. Улучши следующий текст, сохранив его смысл:

Оригинальный текст:
{text}

Требования:
- Деловой стиль
- Вежливость и профессионализм
- Четкость и ясность
- Соответствие этическим нормам

Предоставь улучшенную версию текста.
""",
            
            "terminology_check": """
Ты - эксперт по профессиональной терминологии в области {domain}. Проверь правильность использования терминов в тексте:

Текст:
{text}

Область: {domain}

Найди:
1. Неправильно использованные термины
2. Неточные формулировки
3. Предложения по улучшению

Дай рекомендации по исправлению терминологии.
""",
            
            "ethics_review": """
Ты - эксперт по корпоративной этике. Проверь этичность следующего документа:

Документ:
{text}

Контекст: {context}

Проверь на:
- Дискриминацию
- Нарушение конфиденциальности
- Конфликт интересов
- Неподходящий тон
- Этические нарушения

Дай заключение об этичности документа.
"""
        }
    
    async def perform_final_review(self, text: str, check_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполняет финальную проверку документа с помощью LLM
        
        Args:
            text: Текст документа
            check_results: Результаты предыдущих проверок
            
        Returns:
            Финальное заключение
        """
        try:
            # Формируем промпт
            prompt = self.prompts["final_review"].format(
                text=text,
                spell_check_result=check_results.get("spell_check", {}),
                style_analysis_result=check_results.get("style_analysis", {}),
                ethics_check_result=check_results.get("ethics_check", {}),
                terminology_check_result=check_results.get("terminology_check", {})
            )
            
            # Отправляем запрос к LLM
            response = await self._call_llm(prompt)
            
            # Парсим ответ
            parsed_response = self._parse_final_review_response(response)
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Ошибка при финальной проверке: {str(e)}")
            raise
    
    async def improve_style(self, text: str) -> str:
        """
        Улучшает стиль текста с помощью LLM
        
        Args:
            text: Исходный текст
            
        Returns:
            Улучшенный текст
        """
        try:
            prompt = self.prompts["style_improvement"].format(text=text)
            response = await self._call_llm(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при улучшении стиля: {str(e)}")
            return text  # Возвращаем исходный текст в случае ошибки
    
    async def check_terminology_with_llm(self, text: str, domain: str) -> Dict[str, Any]:
        """
        Проверяет терминологию с помощью LLM
        
        Args:
            text: Текст для проверки
            domain: Область знаний
            
        Returns:
            Результат проверки терминологии
        """
        try:
            prompt = self.prompts["terminology_check"].format(text=text, domain=domain)
            response = await self._call_llm(prompt)
            
            return {
                "llm_analysis": response,
                "domain": domain
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке терминологии: {str(e)}")
            raise
    
    async def review_ethics_with_llm(self, text: str, context: str = None) -> Dict[str, Any]:
        """
        Проверяет этичность с помощью LLM
        
        Args:
            text: Текст для проверки
            context: Контекст документа
            
        Returns:
            Результат проверки этики
        """
        try:
            prompt = self.prompts["ethics_review"].format(text=text, context=context or "")
            response = await self._call_llm(prompt)
            
            return {
                "llm_analysis": response,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке этики: {str(e)}")
            raise
    
    async def _call_llm(self, prompt: str, model: str = "llama2") -> str:
        """
        Вызывает LLM (Ollama или OpenAI)
        
        Args:
            prompt: Промпт для LLM
            model: Модель для использования
            
        Returns:
            Ответ от LLM
        """
        try:
            # Пробуем сначала Ollama
            if await self._is_ollama_available():
                return await self._call_ollama(prompt, model)
            
            # Если Ollama недоступен, пробуем OpenAI
            if self.openai_api_key:
                return await self._call_openai(prompt, model)
            
            # Если ничего не доступно, возвращаем заглушку
            logger.warning("LLM недоступен, возвращаем заглушку")
            return "LLM недоступен. Проверьте подключение к Ollama или настройте OpenAI API."
            
        except Exception as e:
            logger.error(f"Ошибка при вызове LLM: {str(e)}")
            raise
    
    async def _is_ollama_available(self) -> bool:
        """Проверяет доступность Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def _call_ollama(self, prompt: str, model: str) -> str:
        """Вызывает Ollama API"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    raise Exception(f"Ollama API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка при вызове Ollama: {str(e)}")
            raise
    
    async def _call_openai(self, prompt: str, model: str) -> str:
        """Вызывает OpenAI API"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"OpenAI API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI: {str(e)}")
            raise
    
    def _parse_final_review_response(self, response: str) -> Dict[str, Any]:
        """Парсит ответ от LLM для финальной проверки"""
        try:
            # Простой парсинг ответа
            lines = response.split('\n')
            
            result = {
                "overall_score": 50.0,
                "can_send": False,
                "critical_issues": [],
                "minor_issues": [],
                "recommendations": "",
                "conclusion": ""
            }
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("1. ОБЩАЯ ОЦЕНКА"):
                    try:
                        score = float(line.split(":")[1].strip().split()[0])
                        result["overall_score"] = score
                    except:
                        pass
                
                elif line.startswith("2. МОЖНО ОТПРАВЛЯТЬ"):
                    can_send = line.split(":")[1].strip().lower()
                    result["can_send"] = "да" in can_send or "yes" in can_send
                
                elif line.startswith("3. КРИТИЧЕСКИЕ ПРОБЛЕМЫ"):
                    issues = line.split(":")[1].strip()
                    if issues and issues != "нет" and issues != "none":
                        result["critical_issues"] = [issues]
                
                elif line.startswith("4. МЕЛКИЕ ПРОБЛЕМЫ"):
                    issues = line.split(":")[1].strip()
                    if issues and issues != "нет" and issues != "none":
                        result["minor_issues"] = [issues]
                
                elif line.startswith("5. РЕКОМЕНДАЦИИ"):
                    result["recommendations"] = line.split(":")[1].strip()
                
                elif line.startswith("6. ЗАКЛЮЧЕНИЕ"):
                    result["conclusion"] = line.split(":")[1].strip()
            
            return result
            
        except Exception as e:
            logger.warning(f"Ошибка при парсинге ответа LLM: {e}")
            return {
                "overall_score": 50.0,
                "can_send": False,
                "critical_issues": ["Ошибка при анализе LLM"],
                "minor_issues": [],
                "recommendations": "Проверьте документ вручную",
                "conclusion": "Требуется дополнительная проверка"
            }
    
    def get_available_models(self) -> List[str]:
        """Возвращает список доступных моделей"""
        return ["llama2", "codellama", "mistral", "gpt-3.5-turbo", "gpt-4"]
