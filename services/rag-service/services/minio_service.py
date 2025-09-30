"""
Сервис для работы с MinIO (объектное хранилище)
"""

import logging
from typing import Optional, BinaryIO
import os
from minio import Minio
from minio.error import S3Error
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import aiofiles
import tempfile
import mimetypes
from pathlib import Path

# Импорты для извлечения текста
import PyPDF2
from docx import Document as DocxDocument
import json

load_dotenv()

logger = logging.getLogger(__name__)

class MinIOService:
    """Сервис для работы с MinIO"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        self.bucket_name = os.getenv("MINIO_BUCKET", "ai-engineering")
        self.client = None
        
    async def initialize(self):
        """Инициализация MinIO клиента"""
        try:
            logger.info(f"Подключение к MinIO: {self.endpoint}")
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            
            # Создание bucket если не существует
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Создан bucket: {self.bucket_name}")
            
            logger.info("MinIO клиент успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации MinIO: {e}")
            raise
    
    async def upload_file(self, file, folder: str = "documents") -> str:
        """Загрузка файла в MinIO"""
        try:
            if not self.client:
                await self.initialize()
            
            # Генерация уникального имени файла
            file_extension = Path(file.filename).suffix if file.filename else ""
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            object_name = f"{folder}/{datetime.now().strftime('%Y/%m/%d')}/{unique_filename}"
            
            # Определение MIME типа
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            
            # Чтение содержимого файла
            file_content = await file.read()
            
            # Загрузка в MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=BinaryIO(file_content),
                length=len(file_content),
                content_type=content_type
            )
            
            logger.info(f"Файл загружен: {object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"Ошибка загрузки файла: {e}")
            raise
    
    async def download_file(self, object_name: str) -> bytes:
        """Скачивание файла из MinIO"""
        try:
            if not self.client:
                await self.initialize()
            
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            return data
            
        except S3Error as e:
            logger.error(f"Ошибка скачивания файла {object_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при скачивании файла: {e}")
            raise
    
    async def delete_file(self, object_name: str):
        """Удаление файла из MinIO"""
        try:
            if not self.client:
                await self.initialize()
            
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Файл удален: {object_name}")
            
        except S3Error as e:
            logger.error(f"Ошибка удаления файла {object_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при удалении файла: {e}")
            raise
    
    async def get_file_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
        """Получение временной ссылки на файл"""
        try:
            if not self.client:
                await self.initialize()
            
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Ошибка получения URL файла: {e}")
            raise
    
    async def extract_text(self, object_name: str) -> str:
        """Извлечение текста из файла"""
        try:
            # Скачивание файла
            file_data = await self.download_file(object_name)
            
            # Определение типа файла по расширению
            file_extension = Path(object_name).suffix.lower()
            
            if file_extension == '.pdf':
                return await self._extract_text_from_pdf(file_data)
            elif file_extension in ['.docx', '.doc']:
                return await self._extract_text_from_docx(file_data)
            elif file_extension == '.txt':
                return file_data.decode('utf-8', errors='ignore')
            elif file_extension == '.json':
                return await self._extract_text_from_json(file_data)
            else:
                # Для неизвестных типов пытаемся декодировать как текст
                try:
                    return file_data.decode('utf-8', errors='ignore')
                except:
                    return ""
                    
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из {object_name}: {e}")
            return ""
    
    async def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """Извлечение текста из PDF"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_data)
                temp_file.flush()
                
                with open(temp_file.name, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                
                # Удаление временного файла
                os.unlink(temp_file.name)
                
                return text
                
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из PDF: {e}")
            return ""
    
    async def _extract_text_from_docx(self, file_data: bytes) -> str:
        """Извлечение текста из DOCX"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file.write(file_data)
                temp_file.flush()
                
                doc = DocxDocument(temp_file.name)
                text = ""
                
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                
                # Удаление временного файла
                os.unlink(temp_file.name)
                
                return text
                
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из DOCX: {e}")
            return ""
    
    async def _extract_text_from_json(self, file_data: bytes) -> str:
        """Извлечение текста из JSON"""
        try:
            data = json.loads(file_data.decode('utf-8'))
            
            # Рекурсивное извлечение текстовых полей
            def extract_text_recursive(obj):
                if isinstance(obj, dict):
                    return " ".join([extract_text_recursive(v) for v in obj.values()])
                elif isinstance(obj, list):
                    return " ".join([extract_text_recursive(item) for item in obj])
                elif isinstance(obj, str):
                    return obj
                else:
                    return str(obj)
            
            return extract_text_recursive(data)
            
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из JSON: {e}")
            return ""
    
    async def list_files(self, prefix: str = "", recursive: bool = True) -> list:
        """Получение списка файлов"""
        try:
            if not self.client:
                await self.initialize()
            
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            
            files = []
            for obj in objects:
                files.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Ошибка получения списка файлов: {e}")
            return []
    
    async def get_file_info(self, object_name: str) -> dict:
        """Получение информации о файле"""
        try:
            if not self.client:
                await self.initialize()
            
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            return {
                'name': object_name,
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type
            }
            
        except S3Error as e:
            logger.error(f"Ошибка получения информации о файле {object_name}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении информации о файле: {e}")
            return {}
