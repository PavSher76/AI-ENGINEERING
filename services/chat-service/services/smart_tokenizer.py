"""
Умная система токенизации документов с сохранением контекста
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class TokenChunk:
    """Класс для представления токенизированного фрагмента документа"""
    chunk_id: str
    text: str
    token_count: int
    chunk_type: str  # 'paragraph', 'section', 'table', 'list', 'definition', 'requirement'
    metadata: Dict[str, Any]
    start_position: int
    end_position: int
    parent_section: Optional[str] = None
    importance_score: float = 0.0
    context_keywords: List[str] = None

@dataclass
class DocumentStructure:
    """Структура документа после анализа"""
    title: str
    sections: List[Dict[str, Any]]
    total_tokens: int
    chunk_count: int
    document_type: str
    language: str
    metadata: Dict[str, Any]

class SmartTokenizer:
    """Умная система токенизации с сохранением контекста"""
    
    def __init__(self):
        self.max_chunk_size = 1000  # Максимальное количество токенов в чанке
        self.overlap_size = 200     # Размер перекрытия между чанками
        self.min_chunk_size = 100   # Минимальный размер чанка
        
        # Паттерны для определения структуры документа
        self.section_patterns = [
            r'^(\d+\.?\s+[А-ЯЁ][^.\n]*)',  # Нумерованные разделы
            r'^([А-ЯЁ][^.\n]*\s*:)',       # Заголовки с двоеточием
            r'^(\d+\.\d+\.?\s+[А-ЯЁ][^.\n]*)',  # Подразделы
            r'^(ГЛАВА\s+\d+[^.\n]*)',      # Главы
            r'^(РАЗДЕЛ\s+\d+[^.\n]*)',     # Разделы
            r'^(ПРИЛОЖЕНИЕ\s+[А-Я0-9][^.\n]*)',  # Приложения
        ]
        
        # Паттерны для определения типов контента
        self.content_patterns = {
            'definition': [
                r'([А-ЯЁ][^.\n]*\s*—\s*[^.\n]*)',  # Определения через тире
                r'([А-ЯЁ][^.\n]*\s*:\s*[^.\n]*)',   # Определения через двоеточие
                r'(определение|определяется|означает|под\s+[^.\n]*\s+понимается)',
            ],
            'requirement': [
                r'(должен|должна|должно|должны)',
                r'(обязательно|необходимо|требуется)',
                r'(не\s+допускается|запрещается|не\s+разрешается)',
                r'(следует|рекомендуется)',
            ],
            'table': [
                r'(\|.*\|)',  # Таблицы в markdown формате
                r'(\+.*\+)',  # Таблицы с разделителями
            ],
            'list': [
                r'^(\s*[-•*]\s+[^.\n]*)',  # Маркированные списки
                r'^(\s*\d+\.\s+[^.\n]*)',  # Нумерованные списки
            ],
            'formula': [
                r'(\$.*?\$)',  # LaTeX формулы
                r'(\[.*?\])',  # Математические выражения
            ],
            'reference': [
                r'(ГОСТ\s+\d+(?:\.\d+)*-\d{4})',
                r'(СП\s+\d+(?:\.\d+)*\.\d{4})',
                r'(СНиП\s+\d+(?:\.\d+)*-\d{4})',
                r'(п\.\s*\d+(?:\.\d+)*)',
                r'(раздел\s+\d+(?:\.\d+)*)',
            ]
        }
        
        # Ключевые слова для определения важности
        self.importance_keywords = {
            'high': ['требование', 'обязательно', 'запрещается', 'должен', 'необходимо'],
            'medium': ['рекомендуется', 'следует', 'желательно', 'предпочтительно'],
            'low': ['может', 'возможно', 'допускается', 'разрешается']
        }
        
        # Стоп-слова для фильтрации
        self.stop_words = {
            'ru': ['и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два', 'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между'],
            'en': ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their']
        }
    
    async def tokenize_document(self, text: str, filename: str = None) -> Tuple[List[TokenChunk], DocumentStructure]:
        """
        Основной метод токенизации документа
        
        Args:
            text: Текст документа
            filename: Имя файла (для определения типа документа)
            
        Returns:
            Кортеж из списка токенизированных чанков и структуры документа
        """
        logger.info(f"🔄 Начинаем умную токенизацию документа: {filename}")
        
        try:
            # 1. Предварительная обработка текста
            cleaned_text = self._preprocess_text(text)
            
            # 2. Анализ структуры документа
            document_structure = await self._analyze_document_structure(cleaned_text, filename)
            
            # 3. Определение языка
            language = self._detect_language(cleaned_text)
            
            # 4. Разбиение на семантические блоки
            semantic_blocks = await self._extract_semantic_blocks(cleaned_text, document_structure)
            
            # 5. Токенизация блоков с сохранением контекста
            token_chunks = await self._tokenize_blocks(semantic_blocks, language)
            
            # 6. Обогащение метаданными
            enriched_chunks = await self._enrich_chunks_metadata(token_chunks, document_structure)
            
            # 7. Оптимизация размеров чанков
            optimized_chunks = await self._optimize_chunk_sizes(enriched_chunks)
            
            logger.info(f"✅ Токенизация завершена: {len(optimized_chunks)} чанков, {document_structure.total_tokens} токенов")
            
            return optimized_chunks, document_structure
            
        except Exception as e:
            logger.error(f"❌ Ошибка токенизации документа: {str(e)}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Предварительная обработка текста"""
        # Нормализация пробелов
        text = re.sub(r'\s+', ' ', text)
        
        # Удаление лишних символов
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Нормализация переносов строк
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    async def _analyze_document_structure(self, text: str, filename: str = None) -> DocumentStructure:
        """Анализ структуры документа"""
        sections = []
        current_section = None
        
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Проверяем, является ли строка заголовком раздела
            for pattern in self.section_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = {
                        'title': match.group(1),
                        'start_line': line_num,
                        'end_line': line_num,
                        'level': self._get_section_level(line),
                        'content': []
                    }
                    break
            else:
                if current_section:
                    current_section['content'].append(line)
                    current_section['end_line'] = line_num
        
        # Добавляем последний раздел
        if current_section:
            sections.append(current_section)
        
        # Определяем тип документа
        document_type = self._detect_document_type(text, filename)
        
        return DocumentStructure(
            title=self._extract_title(text, filename),
            sections=sections,
            total_tokens=len(text.split()),
            chunk_count=0,  # Будет обновлено позже
            document_type=document_type,
            language=self._detect_language(text),
            metadata={
                'filename': filename,
                'sections_count': len(sections),
                'analyzed_at': datetime.now().isoformat()
            }
        )
    
    def _get_section_level(self, line: str) -> int:
        """Определение уровня заголовка"""
        if re.match(r'^\d+\.\d+\.\d+', line):
            return 3
        elif re.match(r'^\d+\.\d+', line):
            return 2
        elif re.match(r'^\d+\.', line):
            return 1
        else:
            return 0
    
    def _detect_document_type(self, text: str, filename: str = None) -> str:
        """Определение типа документа"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['гост', 'стандарт', 'стандартизация']):
            return 'standard'
        elif any(keyword in text_lower for keyword in ['снип', 'строительные нормы']):
            return 'building_code'
        elif any(keyword in text_lower for keyword in ['сп', 'свод правил']):
            return 'code_of_practice'
        elif any(keyword in text_lower for keyword in ['техническое задание', 'тз']):
            return 'technical_specification'
        elif any(keyword in text_lower for keyword in ['проект', 'проектирование']):
            return 'project_document'
        else:
            return 'general'
    
    def _extract_title(self, text: str, filename: str = None) -> str:
        """Извлечение заголовка документа"""
        lines = text.split('\n')
        
        # Ищем заголовок в первых строках
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Проверяем, что это не служебная информация
                if not any(keyword in line.lower() for keyword in ['страница', 'page', 'дата', 'date']):
                    return line
        
        # Если заголовок не найден, используем имя файла
        if filename:
            return filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
        
        return "Документ"
    
    def _detect_language(self, text: str) -> str:
        """Определение языка документа"""
        # Простая эвристика на основе кириллических символов
        cyrillic_count = len(re.findall(r'[а-яё]', text.lower()))
        latin_count = len(re.findall(r'[a-z]', text.lower()))
        
        if cyrillic_count > latin_count:
            return 'ru'
        else:
            return 'en'
    
    async def _extract_semantic_blocks(self, text: str, structure: DocumentStructure) -> List[Dict[str, Any]]:
        """Извлечение семантических блоков из текста"""
        blocks = []
        
        # Разбиваем текст на абзацы
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) < 20:  # Пропускаем слишком короткие абзацы
                continue
            
            # Определяем тип контента
            content_type = self._classify_content_type(paragraph)
            
            # Определяем важность
            importance = self._calculate_importance(paragraph)
            
            # Извлекаем ключевые слова
            keywords = self._extract_keywords(paragraph)
            
            # Определяем родительский раздел
            parent_section = self._find_parent_section(paragraph, structure)
            
            blocks.append({
                'text': paragraph,
                'type': content_type,
                'importance': importance,
                'keywords': keywords,
                'parent_section': parent_section,
                'position': i,
                'length': len(paragraph)
            })
        
        return blocks
    
    def _classify_content_type(self, text: str) -> str:
        """Классификация типа контента"""
        text_lower = text.lower()
        
        for content_type, patterns in self.content_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return content_type
        
        # Дополнительная логика для определения типа
        if len(text.split()) < 20:
            return 'short_text'
        elif any(char in text for char in ['•', '-', '*', '1.', '2.']):
            return 'list'
        elif '|' in text or '+' in text:
            return 'table'
        else:
            return 'paragraph'
    
    def _calculate_importance(self, text: str) -> float:
        """Расчет важности текста"""
        text_lower = text.lower()
        importance_score = 0.5  # Базовый уровень
        
        # Проверяем ключевые слова важности
        for level, keywords in self.importance_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if level == 'high':
                        importance_score += 0.3
                    elif level == 'medium':
                        importance_score += 0.1
                    else:
                        importance_score -= 0.1
        
        # Учитываем длину текста
        if len(text) > 500:
            importance_score += 0.1
        elif len(text) < 100:
            importance_score -= 0.1
        
        # Учитываем наличие цифр и специальных символов
        if re.search(r'\d+', text):
            importance_score += 0.1
        
        return max(0.0, min(1.0, importance_score))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Простое извлечение ключевых слов
        words = re.findall(r'\b[а-яё]{3,}\b', text.lower())
        
        # Фильтруем стоп-слова
        stop_words = self.stop_words.get('ru', [])
        keywords = [word for word in words if word not in stop_words]
        
        # Подсчитываем частоту
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Возвращаем наиболее частые слова
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:10]
    
    def _find_parent_section(self, text: str, structure: DocumentStructure) -> Optional[str]:
        """Поиск родительского раздела для текста"""
        # Простая логика - ищем ближайший раздел выше
        for section in reversed(structure.sections):
            if any(keyword in text.lower() for keyword in section['title'].lower().split()):
                return section['title']
        
        return None
    
    async def _tokenize_blocks(self, blocks: List[Dict[str, Any]], language: str) -> List[TokenChunk]:
        """Токенизация блоков с сохранением контекста"""
        chunks = []
        
        for i, block in enumerate(blocks):
            text = block['text']
            
            # Если блок слишком большой, разбиваем его
            if len(text.split()) > self.max_chunk_size:
                sub_chunks = await self._split_large_block(text, block)
                chunks.extend(sub_chunks)
            else:
                # Создаем чанк из блока
                chunk = TokenChunk(
                    chunk_id=f"chunk_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    text=text,
                    token_count=len(text.split()),
                    chunk_type=block['type'],
                    metadata={
                        'importance': block['importance'],
                        'keywords': block['keywords'],
                        'parent_section': block['parent_section'],
                        'position': block['position'],
                        'language': language
                    },
                    start_position=0,  # Будет обновлено позже
                    end_position=len(text),
                    parent_section=block['parent_section'],
                    importance_score=block['importance'],
                    context_keywords=block['keywords']
                )
                chunks.append(chunk)
        
        return chunks
    
    async def _split_large_block(self, text: str, block: Dict[str, Any]) -> List[TokenChunk]:
        """Разбиение большого блока на меньшие чанки"""
        chunks = []
        sentences = re.split(r'[.!?]+', text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = len(sentence.split())
            
            # Если добавление предложения превысит лимит, создаем новый чанк
            if current_tokens + sentence_tokens > self.max_chunk_size and current_chunk:
                chunk = TokenChunk(
                    chunk_id=f"chunk_{block['position']}_{chunk_index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    text=current_chunk.strip(),
                    token_count=current_tokens,
                    chunk_type=block['type'],
                    metadata={
                        'importance': block['importance'],
                        'keywords': block['keywords'],
                        'parent_section': block['parent_section'],
                        'position': block['position'],
                        'chunk_index': chunk_index,
                        'is_split': True
                    },
                    start_position=0,
                    end_position=len(current_chunk),
                    parent_section=block['parent_section'],
                    importance_score=block['importance'],
                    context_keywords=block['keywords']
                )
                chunks.append(chunk)
                
                # Начинаем новый чанк с перекрытием
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence
                current_tokens = len(current_chunk.split())
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        # Добавляем последний чанк
        if current_chunk:
            chunk = TokenChunk(
                chunk_id=f"chunk_{block['position']}_{chunk_index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                text=current_chunk.strip(),
                token_count=current_tokens,
                chunk_type=block['type'],
                metadata={
                    'importance': block['importance'],
                    'keywords': block['keywords'],
                    'parent_section': block['parent_section'],
                    'position': block['position'],
                    'chunk_index': chunk_index,
                    'is_split': True
                },
                start_position=0,
                end_position=len(current_chunk),
                parent_section=block['parent_section'],
                importance_score=block['importance'],
                context_keywords=block['keywords']
            )
            chunks.append(chunk)
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Получение текста для перекрытия между чанками"""
        words = text.split()
        if len(words) <= self.overlap_size:
            return text
        
        return " ".join(words[-self.overlap_size:])
    
    async def _enrich_chunks_metadata(self, chunks: List[TokenChunk], structure: DocumentStructure) -> List[TokenChunk]:
        """Обогащение чанков дополнительными метаданными"""
        for i, chunk in enumerate(chunks):
            # Добавляем информацию о позиции в документе
            chunk.metadata['document_position'] = i
            chunk.metadata['document_type'] = structure.document_type
            chunk.metadata['document_title'] = structure.title
            
            # Добавляем информацию о соседних чанках
            if i > 0:
                chunk.metadata['previous_chunk_id'] = chunks[i-1].chunk_id
            if i < len(chunks) - 1:
                chunk.metadata['next_chunk_id'] = chunks[i+1].chunk_id
            
            # Добавляем временные метки
            chunk.metadata['created_at'] = datetime.now().isoformat()
            
            # Обновляем позиции
            chunk.start_position = sum(len(c.text) for c in chunks[:i])
            chunk.end_position = chunk.start_position + len(chunk.text)
        
        return chunks
    
    async def _optimize_chunk_sizes(self, chunks: List[TokenChunk]) -> List[TokenChunk]:
        """Оптимизация размеров чанков"""
        optimized_chunks = []
        
        for chunk in chunks:
            # Если чанк слишком маленький, пытаемся объединить с соседними
            if chunk.token_count < self.min_chunk_size and len(optimized_chunks) > 0:
                last_chunk = optimized_chunks[-1]
                
                # Проверяем, можно ли объединить
                if (last_chunk.token_count + chunk.token_count <= self.max_chunk_size and
                    last_chunk.chunk_type == chunk.chunk_type and
                    last_chunk.parent_section == chunk.parent_section):
                    
                    # Объединяем чанки
                    last_chunk.text += " " + chunk.text
                    last_chunk.token_count += chunk.token_count
                    last_chunk.end_position = chunk.end_position
                    last_chunk.metadata['merged_chunks'] = last_chunk.metadata.get('merged_chunks', 1) + 1
                    last_chunk.metadata['merged_chunk_ids'] = last_chunk.metadata.get('merged_chunk_ids', [last_chunk.chunk_id]) + [chunk.chunk_id]
                    continue
            
            optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def get_tokenization_stats(self, chunks: List[TokenChunk], structure: DocumentStructure) -> Dict[str, Any]:
        """Получение статистики токенизации"""
        total_tokens = sum(chunk.token_count for chunk in chunks)
        avg_chunk_size = total_tokens / len(chunks) if chunks else 0
        
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        return {
            'total_chunks': len(chunks),
            'total_tokens': total_tokens,
            'average_chunk_size': avg_chunk_size,
            'chunk_types_distribution': chunk_types,
            'document_type': structure.document_type,
            'language': structure.language,
            'sections_count': len(structure.sections),
            'tokenization_time': datetime.now().isoformat()
        }

