"""
Сервис для обработки документов
"""

import os
import aiofiles
from typing import Optional, Dict, Any
import PyPDF2
from docx import Document as DocxDocument
import io
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Класс для извлечения текста из различных форматов документов"""
    
    def __init__(self):
        self.supported_formats = {
            'application/pdf': self._extract_from_pdf,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._extract_from_docx,
            'application/msword': self._extract_from_docx,
            'text/plain': self._extract_from_txt
        }
    
    async def extract_text(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Извлекает текст из документа
        
        Args:
            file_path: Путь к файлу
            mime_type: MIME тип файла
            
        Returns:
            Словарь с извлеченным текстом и метаданными
        """
        try:
            if mime_type not in self.supported_formats:
                raise ValueError(f"Неподдерживаемый формат файла: {mime_type}")
            
            extractor = self.supported_formats[mime_type]
            result = await extractor(file_path)
            
            logger.info(f"Успешно извлечен текст из {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из {file_path}: {str(e)}")
            raise
    
    async def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Извлекает текст из PDF файла"""
        try:
            text = ""
            tables = []
            
            async with aiofiles.open(file_path, 'rb') as file:
                content = await file.read()
                
                # Создаем объект PDF
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                
                # Извлекаем текст из всех страниц
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- Страница {page_num + 1} ---\n"
                    text += page_text
                
                # TODO: Добавить извлечение таблиц из PDF
                # Это требует более сложной обработки с использованием библиотек типа pdfplumber
                
            return {
                "text": text.strip(),
                "tables": tables,
                "page_count": len(pdf_reader.pages),
                "extraction_method": "pypdf2"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF {file_path}: {str(e)}")
            raise
    
    async def _extract_from_docx(self, file_path: str) -> Dict[str, Any]:
        """Извлекает текст из DOCX файла"""
        try:
            text = ""
            tables = []
            
            # Загружаем документ
            doc = DocxDocument(file_path)
            
            # Извлекаем текст из параграфов
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            
            # Извлекаем таблицы
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        row_data.append(cell.text.strip())
                    table_data.append(row_data)
                tables.append(table_data)
            
            return {
                "text": text.strip(),
                "tables": tables,
                "table_count": len(tables),
                "extraction_method": "python-docx"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке DOCX {file_path}: {str(e)}")
            raise
    
    async def _extract_from_txt(self, file_path: str) -> Dict[str, Any]:
        """Извлекает текст из текстового файла"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                text = await file.read()
            
            return {
                "text": text.strip(),
                "tables": [],
                "extraction_method": "plain_text"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке TXT {file_path}: {str(e)}")
            raise
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Получает информацию о файле"""
        try:
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о файле {file_path}: {str(e)}")
            return {}
