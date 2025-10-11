"""
Сервис для работы с архивами проектов
"""

import os
import zipfile
import json
import hashlib
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
import logging
from datetime import datetime

from minio import Minio
from minio.error import S3Error

from schemas.archive import Manifest, ArchiveUploadRequest, ProcessingStatus
from models.database import Archive, Document, SessionLocal, Project, ProcessingJob
from services.minio_service import MinIOService

logger = logging.getLogger(__name__)


class ArchiveService:
    """Сервис для работы с архивами проектов"""
    
    def __init__(self, minio_service: MinIOService):
        self.minio_service = minio_service
        self.temp_dir = "/tmp/archive_processing"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def upload_archive(self, request: ArchiveUploadRequest) -> str:
        """
        Загружает архив и создает задание на обработку
        
        Args:
            request: Запрос на загрузку архива
            
        Returns:
            ID задания на обработку
        """
        try:
            # Создаем или получаем проект
            project = await self._get_or_create_project(request.manifest)
            
            # Создаем запись архива
            archive = Archive(
                project_id=project.id,
                archive_path=request.archive_path,
                archive_size=request.archive_size,
                archive_hash=request.archive_hash,
                manifest=request.manifest.dict(),
                status=ProcessingStatus.PENDING
            )
            
            # Создаем задание на обработку
            job_id = f"archive_{request.manifest.project_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            job = ProcessingJob(
                job_id=job_id,
                project_id=request.manifest.project_id,
                object_id=request.manifest.object_id,
                job_type="archive_ingest",
                status=ProcessingStatus.PENDING,
                parameters={
                    "archive_path": request.archive_path,
                    "manifest": request.manifest.dict()
                }
            )
            
            logger.info(f"Создано задание на обработку архива: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке архива: {str(e)}")
            raise
    
    async def process_archive(self, job_id: str) -> Dict[str, Any]:
        """
        Обрабатывает архив: извлекает, парсит документы, создает чанки
        
        Args:
            job_id: ID задания на обработку
            
        Returns:
            Результат обработки
        """
        try:
            # Получаем задание
            job = await self._get_processing_job(job_id)
            if not job:
                raise ValueError(f"Задание {job_id} не найдено")
            
            # Обновляем статус
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.utcnow()
            
            # Скачиваем архив из MinIO
            archive_path = job.parameters["archive_path"]
            local_archive_path = await self._download_archive(archive_path)
            
            # Извлекаем архив
            extract_path = await self._extract_archive(local_archive_path)
            
            # Читаем манифест
            manifest = await self._read_manifest(extract_path)
            
            # Обрабатываем документы
            result = await self._process_documents(extract_path, manifest, job)
            
            # Обновляем статус задания
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            
            # Очищаем временные файлы
            await self._cleanup_temp_files(local_archive_path, extract_path)
            
            logger.info(f"Архив {job_id} успешно обработан")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке архива {job_id}: {str(e)}")
            # Обновляем статус на ошибку
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            raise
    
    async def _get_or_create_project(self, manifest: Manifest) -> Project:
        """Создает или получает проект"""
        # Здесь должна быть логика работы с БД
        # Пока возвращаем заглушку
        project = Project(
            project_id=manifest.project_id,
            object_id=manifest.object_id,
            name=f"{manifest.project_id} - {manifest.object_id}",
            phase=manifest.phase.value,
            customer=manifest.customer,
            language=manifest.language,
            confidentiality=manifest.confidentiality.value,
            default_discipline=manifest.default_discipline.value
        )
        return project
    
    async def _download_archive(self, archive_path: str) -> str:
        """Скачивает архив из MinIO во временную папку"""
        local_path = os.path.join(self.temp_dir, f"archive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip")
        
        # Скачиваем файл из MinIO
        await self.minio_service.download_file(archive_path, local_path)
        
        return local_path
    
    async def _extract_archive(self, archive_path: str) -> str:
        """Извлекает архив"""
        extract_path = archive_path.replace('.zip', '_extracted')
        os.makedirs(extract_path, exist_ok=True)
        
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        return extract_path
    
    async def _read_manifest(self, extract_path: str) -> Manifest:
        """Читает манифест из архива"""
        manifest_path = os.path.join(extract_path, "manifest.json")
        
        if not os.path.exists(manifest_path):
            raise ValueError("manifest.json не найден в архиве")
        
        async with aiofiles.open(manifest_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            manifest_data = json.loads(content)
        
        return Manifest(**manifest_data)
    
    async def _process_documents(self, extract_path: str, manifest: Manifest, job: ProcessingJob) -> Dict[str, Any]:
        """Обрабатывает документы в архиве"""
        result = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "documents": []
        }
        
        # Сканируем структуру архива
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file == "manifest.json":
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, extract_path)
                
                result["total_files"] += 1
                
                try:
                    # Определяем тип документа по папке
                    doc_type = self._determine_document_type(relative_path)
                    discipline = self._determine_discipline(relative_path, manifest.default_discipline)
                    
                    # Создаем запись документа
                    document = await self._create_document_record(
                        file_path, relative_path, doc_type, discipline, manifest
                    )
                    
                    # Парсим документ
                    chunks = await self._parse_document(file_path, document)
                    
                    result["processed_files"] += 1
                    result["total_chunks"] += len(chunks)
                    result["documents"].append({
                        "path": relative_path,
                        "type": doc_type,
                        "discipline": discipline,
                        "chunks": len(chunks)
                    })
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {relative_path}: {str(e)}")
                    result["failed_files"] += 1
        
        return result
    
    def _determine_document_type(self, file_path: str) -> str:
        """Определяет тип документа по пути"""
        path_lower = file_path.lower()
        
        if "pfd" in path_lower or "process" in path_lower:
            return "PFD"
        elif "pid" in path_lower or "piping" in path_lower:
            return "P&ID"
        elif "spec" in path_lower:
            return "SPEC"
        elif "bom" in path_lower or "bill_of_materials" in path_lower:
            return "BOM"
        elif "boq" in path_lower or "bill_of_quantities" in path_lower:
            return "BOQ"
        elif "drawing" in path_lower or "dwg" in path_lower or "dxf" in path_lower:
            return "DRAWING"
        elif "ifc" in path_lower:
            return "IFC"
        elif "manual" in path_lower:
            return "MANUAL"
        else:
            return "REPORT"
    
    def _determine_discipline(self, file_path: str, default_discipline: str) -> str:
        """Определяет дисциплину по пути"""
        path_lower = file_path.lower()
        
        if "process" in path_lower:
            return "process"
        elif "piping" in path_lower or "pipe" in path_lower:
            return "piping"
        elif "civil" in path_lower:
            return "civil"
        elif "electrical" in path_lower or "elec" in path_lower:
            return "elec"
        elif "instrument" in path_lower or "instr" in path_lower:
            return "instr"
        elif "hvac" in path_lower:
            return "hvac"
        elif "procurement" in path_lower or "vendor" in path_lower:
            return "procurement"
        else:
            return default_discipline
    
    async def _create_document_record(self, file_path: str, relative_path: str, 
                                    doc_type: str, discipline: str, manifest: Manifest) -> Document:
        """Создает запись документа в БД"""
        # Вычисляем хеш файла
        file_hash = await self._calculate_file_hash(file_path)
        
        # Получаем размер файла
        file_size = os.path.getsize(file_path)
        
        # Определяем MIME тип
        mime_type = self._get_mime_type(file_path)
        
        # Извлекаем номер документа из имени файла
        doc_no = self._extract_doc_number(relative_path)
        
        document = Document(
            project_id=None,  # Будет установлено при сохранении
            archive_id=None,  # Будет установлено при сохранении
            doc_no=doc_no,
            rev="A",  # По умолчанию
            doc_type=doc_type,
            discipline=discipline,
            language=manifest.language[0] if manifest.language else "ru",
            source_path=relative_path,
            source_hash=file_hash,
            file_size=file_size,
            mime_type=mime_type,
            status="pending"
        )
        
        return document
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Вычисляет SHA-256 хеш файла"""
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_mime_type(self, file_path: str) -> str:
        """Определяет MIME тип файла"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.dwg': 'application/dwg',
            '.dxf': 'application/dxf',
            '.ifc': 'application/ifc',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _extract_doc_number(self, file_path: str) -> str:
        """Извлекает номер документа из пути"""
        filename = Path(file_path).stem
        # Простая логика извлечения номера документа
        # В реальном проекте это может быть более сложная логика
        return filename
    
    async def _parse_document(self, file_path: str, document: Document) -> List[Dict[str, Any]]:
        """Парсит документ и создает чанки"""
        # Здесь будет логика парсинга документов
        # Пока возвращаем заглушку
        chunks = []
        
        # В зависимости от типа документа вызываем соответствующий парсер
        if document.mime_type == 'application/pdf':
            chunks = await self._parse_pdf(file_path, document)
        elif document.mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            chunks = await self._parse_docx(file_path, document)
        elif document.mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
            chunks = await self._parse_xlsx(file_path, document)
        elif document.mime_type == 'application/ifc':
            chunks = await self._parse_ifc(file_path, document)
        
        return chunks
    
    async def _parse_pdf(self, file_path: str, document: Document) -> List[Dict[str, Any]]:
        """Парсит PDF документ"""
        # Заглушка - здесь будет реальная логика парсинга PDF
        return [{"chunk_id": f"pdf_chunk_1", "content": "PDF content", "type": "text"}]
    
    async def _parse_docx(self, file_path: str, document: Document) -> List[Dict[str, Any]]:
        """Парсит DOCX документ"""
        # Заглушка - здесь будет реальная логика парсинга DOCX
        return [{"chunk_id": f"docx_chunk_1", "content": "DOCX content", "type": "text"}]
    
    async def _parse_xlsx(self, file_path: str, document: Document) -> List[Dict[str, Any]]:
        """Парсит XLSX документ"""
        # Заглушка - здесь будет реальная логика парсинга XLSX
        return [{"chunk_id": f"xlsx_chunk_1", "content": "XLSX content", "type": "table"}]
    
    async def _parse_ifc(self, file_path: str, document: Document) -> List[Dict[str, Any]]:
        """Парсит IFC документ"""
        # Заглушка - здесь будет реальная логика парсинга IFC
        return [{"chunk_id": f"ifc_chunk_1", "content": "IFC content", "type": "ifc"}]
    
    async def _get_processing_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Получает задание на обработку"""
        # Здесь должна быть логика работы с БД
        # Пока возвращаем заглушку
        return None
    
    async def _cleanup_temp_files(self, *paths: str):
        """Очищает временные файлы"""
        for path in paths:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {path}: {str(e)}")
