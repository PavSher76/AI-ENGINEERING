"""
Сервис для работы с MinIO (S3-совместимое хранилище)
"""

import os
import tempfile
from typing import Optional, List
from minio import Minio
from minio.error import S3Error
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class MinIOService:
    """Сервис для работы с MinIO"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.client = None
        self.bucket_name = "archive-documents"
        self._bucket_checked = False
    
    def _get_client(self):
        """Ленивая инициализация клиента MinIO"""
        if self.client is None:
            self.client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
        return self.client
    
    def _ensure_bucket_exists(self):
        """Создает bucket если он не существует"""
        if self._bucket_checked:
            return
            
        try:
            client = self._get_client()
            if not client.bucket_exists(self.bucket_name):
                client.make_bucket(self.bucket_name)
                logger.info(f"Создан bucket: {self.bucket_name}")
            self._bucket_checked = True
        except Exception as e:
            logger.warning(f"Не удалось подключиться к MinIO: {str(e)}")
            # Не поднимаем исключение, чтобы сервис мог работать без MinIO
    
    async def upload_file(self, file_path: str, object_name: str) -> str:
        """
        Загружает файл в MinIO
        
        Args:
            file_path: Путь к локальному файлу
            object_name: Имя объекта в MinIO
            
        Returns:
            Путь к загруженному файлу
        """
        try:
            self._ensure_bucket_exists()
            client = self._get_client()
            client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            logger.info(f"Файл загружен: {object_name}")
            return f"{self.bucket_name}/{object_name}"
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {object_name}: {str(e)}")
            raise
    
    async def download_file(self, object_name: str, local_path: str):
        """
        Скачивает файл из MinIO
        
        Args:
            object_name: Имя объекта в MinIO
            local_path: Локальный путь для сохранения
        """
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            client = self._get_client()
            client.fget_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=local_path
            )
            logger.info(f"Файл скачан: {object_name} -> {local_path}")
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {object_name}: {str(e)}")
            raise
    
    async def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
        """
        Генерирует presigned URL для доступа к файлу
        
        Args:
            object_name: Имя объекта в MinIO
            expires: Время жизни URL
            
        Returns:
            Presigned URL
        """
        try:
            client = self._get_client()
            url = client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except Exception as e:
            logger.error(f"Ошибка при генерации presigned URL для {object_name}: {str(e)}")
            raise
    
    async def list_objects(self, prefix: str = "", recursive: bool = True) -> List[str]:
        """
        Список объектов в bucket
        
        Args:
            prefix: Префикс для фильтрации
            recursive: Рекурсивный поиск
            
        Returns:
            Список имен объектов
        """
        try:
            client = self._get_client()
            objects = client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            return [obj.object_name for obj in objects]
        except Exception as e:
            logger.error(f"Ошибка при получении списка объектов: {str(e)}")
            raise
    
    async def delete_object(self, object_name: str):
        """
        Удаляет объект из MinIO
        
        Args:
            object_name: Имя объекта для удаления
        """
        try:
            client = self._get_client()
            client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"Объект удален: {object_name}")
        except Exception as e:
            logger.error(f"Ошибка при удалении объекта {object_name}: {str(e)}")
            raise
    
    async def object_exists(self, object_name: str) -> bool:
        """
        Проверяет существование объекта
        
        Args:
            object_name: Имя объекта
            
        Returns:
            True если объект существует
        """
        try:
            client = self._get_client()
            client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except Exception:
            return False
    
    async def get_object_info(self, object_name: str) -> Optional[dict]:
        """
        Получает информацию об объекте
        
        Args:
            object_name: Имя объекта
            
        Returns:
            Информация об объекте или None
        """
        try:
            client = self._get_client()
            stat = client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return {
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации об объекте {object_name}: {str(e)}")
            return None
