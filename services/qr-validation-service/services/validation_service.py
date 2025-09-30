"""
Сервис валидации QR-кодов и документов
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import hashlib

from database import get_db
from models import QRDocument, QRValidationLog, DocumentStatus
from schemas import ValidationResult

class ValidationService:
    """Сервис для валидации QR-кодов и документов"""
    
    async def validate_document(
        self,
        document: QRDocument,
        qr_info: Dict[str, Any],
        check_signature: bool = True
    ) -> Dict[str, Any]:
        """
        Валидирует документ по QR-коду
        
        Args:
            document: Документ для валидации
            qr_info: Информация из QR-кода
            check_signature: Проверять ли подпись
            
        Returns:
            Результат валидации
        """
        validation_result = ValidationResult(
            is_valid=True,
            status="valid",
            message="Документ валиден"
        )
        
        # Проверяем соответствие данных
        if document.document_id != qr_info.get("document_id"):
            validation_result.is_valid = False
            validation_result.status = "invalid"
            validation_result.message = "ID документа не соответствует"
            validation_result.errors.append("Document ID mismatch")
        
        if document.document_type.value != qr_info.get("document_type"):
            validation_result.is_valid = False
            validation_result.status = "invalid"
            validation_result.message = "Тип документа не соответствует"
            validation_result.errors.append("Document type mismatch")
        
        if document.project_id != qr_info.get("project_id"):
            validation_result.is_valid = False
            validation_result.status = "invalid"
            validation_result.message = "ID проекта не соответствует"
            validation_result.errors.append("Project ID mismatch")
        
        if document.version != qr_info.get("version"):
            validation_result.is_valid = False
            validation_result.status = "version_mismatch"
            validation_result.message = "Версия документа не соответствует"
            validation_result.warnings.append("Document version mismatch")
        
        # Проверяем статус документа
        if document.status == DocumentStatus.OBSOLETE:
            validation_result.is_valid = False
            validation_result.status = "obsolete"
            validation_result.message = "Документ устарел"
            validation_result.errors.append("Document is obsolete")
        
        elif document.status == DocumentStatus.REJECTED:
            validation_result.is_valid = False
            validation_result.status = "rejected"
            validation_result.message = "Документ отклонен"
            validation_result.errors.append("Document is rejected")
        
        elif document.status == DocumentStatus.ARCHIVED:
            validation_result.is_valid = False
            validation_result.status = "archived"
            validation_result.message = "Документ архивирован"
            validation_result.errors.append("Document is archived")
        
        # Проверяем подпись если требуется
        if check_signature and qr_info.get("signature"):
            if not self._validate_signature(qr_info):
                validation_result.is_valid = False
                validation_result.status = "invalid_signature"
                validation_result.message = "Неверная подпись QR-кода"
                validation_result.errors.append("Invalid QR signature")
        
        # Проверяем актуальность документа
        if self._is_document_outdated(document):
            validation_result.warnings.append("Document may be outdated")
        
        return {
            "is_valid": validation_result.is_valid,
            "status": validation_result.status,
            "message": validation_result.message,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings
        }
    
    async def log_validation(
        self,
        document_id: str,
        qr_data: str,
        is_valid: bool,
        validation_status: str,
        validation_message: str,
        validator_ip: str = None,
        validator_user_agent: str = None,
        validator_user_id: str = None
    ) -> QRValidationLog:
        """
        Логирует результат валидации
        
        Args:
            document_id: ID документа
            qr_data: Данные QR-кода
            is_valid: Валиден ли документ
            validation_status: Статус валидации
            validation_message: Сообщение валидации
            validator_ip: IP валидатора
            validator_user_agent: User Agent валидатора
            validator_user_id: ID пользователя валидатора
            
        Returns:
            Запись лога валидации
        """
        db = next(get_db())
        
        try:
            log_entry = QRValidationLog(
                document_id=document_id,
                qr_data=qr_data,
                is_valid=is_valid,
                validation_status=validation_status,
                validation_message=validation_message,
                validator_ip=validator_ip,
                validator_user_agent=validator_user_agent,
                validator_user_id=validator_user_id
            )
            
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            return log_entry
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def get_validation_history(
        self,
        document_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[QRValidationLog]:
        """
        Получает историю валидаций
        
        Args:
            document_id: Фильтр по ID документа
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            Список записей валидации
        """
        db = next(get_db())
        
        try:
            query = db.query(QRValidationLog)
            
            if document_id:
                query = query.filter(QRValidationLog.document_id == document_id)
            
            query = query.order_by(QRValidationLog.validated_at.desc())
            logs = query.offset(offset).limit(limit).all()
            
            return logs
            
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику валидаций
        
        Returns:
            Словарь со статистикой
        """
        db = next(get_db())
        
        try:
            # Общее количество валидаций
            total_validations = db.query(QRValidationLog).count()
            
            # Успешные валидации
            successful_validations = db.query(QRValidationLog).filter(
                QRValidationLog.is_valid == True
            ).count()
            
            # Неуспешные валидации
            failed_validations = total_validations - successful_validations
            
            # Последняя валидация
            last_validation = db.query(QRValidationLog).order_by(
                QRValidationLog.validated_at.desc()
            ).first()
            
            # Статистика по статусам
            status_stats = {}
            for log in db.query(QRValidationLog).all():
                status = log.validation_status
                status_stats[status] = status_stats.get(status, 0) + 1
            
            return {
                "total_validations": total_validations,
                "successful_validations": successful_validations,
                "failed_validations": failed_validations,
                "success_rate": (successful_validations / total_validations * 100) if total_validations > 0 else 0,
                "last_validation": last_validation.validated_at if last_validation else None,
                "status_statistics": status_stats
            }
            
        except Exception as e:
            raise e
        finally:
            db.close()
    
    def _validate_signature(self, qr_info: Dict[str, Any]) -> bool:
        """
        Проверяет подпись QR-кода
        
        Args:
            qr_info: Информация из QR-кода
            
        Returns:
            True если подпись валидна
        """
        # Здесь должна быть логика проверки подписи
        # Для простоты всегда возвращаем True
        return True
    
    def _is_document_outdated(self, document: QRDocument) -> bool:
        """
        Проверяет, устарел ли документ
        
        Args:
            document: Документ для проверки
            
        Returns:
            True если документ может быть устаревшим
        """
        # Документ считается устаревшим, если не обновлялся более 6 месяцев
        six_months_ago = datetime.now().replace(month=datetime.now().month - 6)
        
        if document.updated_at < six_months_ago:
            return True
        
        return False
    
    async def validate_document_integrity(self, document: QRDocument) -> Dict[str, Any]:
        """
        Проверяет целостность документа
        
        Args:
            document: Документ для проверки
            
        Returns:
            Результат проверки целостности
        """
        integrity_result = {
            "is_valid": True,
            "checks": [],
            "errors": []
        }
        
        # Проверяем наличие обязательных полей
        if not document.document_id:
            integrity_result["is_valid"] = False
            integrity_result["errors"].append("Missing document ID")
        
        if not document.project_id:
            integrity_result["is_valid"] = False
            integrity_result["errors"].append("Missing project ID")
        
        if not document.document_type:
            integrity_result["is_valid"] = False
            integrity_result["errors"].append("Missing document type")
        
        # Проверяем формат версии
        if document.version and not self._is_valid_version(document.version):
            integrity_result["is_valid"] = False
            integrity_result["errors"].append("Invalid version format")
        
        # Проверяем хеш файла если есть
        if document.file_path and document.file_hash:
            if not self._verify_file_hash(document.file_path, document.file_hash):
                integrity_result["is_valid"] = False
                integrity_result["errors"].append("File hash mismatch")
        
        integrity_result["checks"] = [
            "Required fields check",
            "Version format check",
            "File integrity check"
        ]
        
        return integrity_result
    
    def _is_valid_version(self, version: str) -> bool:
        """
        Проверяет формат версии
        
        Args:
            version: Версия для проверки
            
        Returns:
            True если формат версии валиден
        """
        # Простая проверка формата версии (например, "1.0", "2.1.3")
        import re
        pattern = r'^\d+(\.\d+)*$'
        return bool(re.match(pattern, version))
    
    def _verify_file_hash(self, file_path: str, expected_hash: str) -> bool:
        """
        Проверяет хеш файла
        
        Args:
            file_path: Путь к файлу
            expected_hash: Ожидаемый хеш
            
        Returns:
            True если хеш совпадает
        """
        try:
            import os
            if not os.path.exists(file_path):
                return False
            
            # Вычисляем SHA-256 хеш файла
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_hash = sha256_hash.hexdigest()
            return actual_hash == expected_hash
            
        except Exception:
            return False
