"""
Сервис для создания эмбеддингов текста
"""

import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Сервис для создания эмбеддингов"""
    
    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.model = None
        self.dimensions = 384  # Размерность для выбранной модели
        
    async def initialize(self):
        """Инициализация модели эмбеддингов"""
        try:
            logger.info(f"Загрузка модели эмбеддингов: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Модель эмбеддингов успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели эмбеддингов: {e}")
            raise
    
    async def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для одного текста"""
        if not self.model:
            await self.initialize()
        
        try:
            # Очистка и нормализация текста
            cleaned_text = self._clean_text(text)
            
            # Создание эмбеддинга
            embedding = self.model.encode(cleaned_text, convert_to_tensor=False)
            
            # Конвертация в список
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга: {e}")
            raise
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Создание эмбеддингов для списка текстов"""
        if not self.model:
            await self.initialize()
        
        try:
            # Очистка текстов
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # Создание эмбеддингов
            embeddings = self.model.encode(cleaned_texts, convert_to_tensor=False)
            
            # Конвертация в список списков
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддингов: {e}")
            raise
    
    async def create_chunk_embeddings(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[dict]:
        """Создание эмбеддингов для чанков текста"""
        if not self.model:
            await self.initialize()
        
        try:
            # Разбиение текста на чанки
            chunks = self._split_text_into_chunks(text, chunk_size, overlap)
            
            # Создание эмбеддингов для каждого чанка
            chunk_embeddings = []
            for i, chunk in enumerate(chunks):
                embedding = await self.create_embedding(chunk)
                chunk_embeddings.append({
                    'chunk_id': f"chunk_{i}",
                    'text': chunk,
                    'embedding': embedding,
                    'chunk_index': i
                })
            
            return chunk_embeddings
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддингов чанков: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Очистка и нормализация текста"""
        if not text:
            return ""
        
        # Удаление лишних пробелов и переносов строк
        cleaned = " ".join(text.split())
        
        # Ограничение длины текста (максимум 512 токенов для большинства моделей)
        if len(cleaned) > 2000:  # Примерно 512 токенов
            cleaned = cleaned[:2000]
        
        return cleaned
    
    def _split_text_into_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Разбиение текста на чанки с перекрытием"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Если это не последний чанк, ищем хорошее место для разрыва
            if end < len(text):
                # Ищем ближайший пробел или знак препинания
                for i in range(end, max(start + chunk_size - 100, start), -1):
                    if text[i] in ' \n\t.,;:!?':
                        end = i
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Следующий чанк начинается с учетом перекрытия
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def get_model_info(self) -> dict:
        """Получение информации о модели"""
        return {
            'model_name': self.model_name,
            'dimensions': self.dimensions,
            'max_tokens': 512,
            'languages': ['ru', 'en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'pl', 'tr', 'ar', 'zh', 'ja', 'ko']
        }
