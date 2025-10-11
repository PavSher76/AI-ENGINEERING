"""
Сервис для работы с QR-кодами
"""

import qrcode
import qrcode.image.svg
from PIL import Image
import io
import base64
import json
import hashlib
import hmac
import os
from datetime import datetime
from typing import Optional, Dict, Any
# import cv2  # Временно отключено
# import numpy as np  # Временно отключено
from pyzbar import pyzbar
# import fitz  # PyMuPDF для работы с PDF - временно отключено

from models import QRDocument
from schemas import QRData

class QRService:
    """Сервис для генерации и обработки QR-кодов"""
    
    def __init__(self):
        self.qr_storage_path = "/app/qr_codes"
        self.secret_key = os.getenv("QR_SECRET_KEY", "default_secret_key")
        self.ensure_storage_directory()
    
    def ensure_storage_directory(self):
        """Создает директорию для хранения QR-кодов"""
        os.makedirs(self.qr_storage_path, exist_ok=True)
    
    def generate_qr_data(self, document: QRDocument) -> str:
        """
        Генерирует данные для QR-кода
        
        Args:
            document: Документ РД
            
        Returns:
            JSON строка с данными QR-кода
        """
        qr_data = QRData(
            document_id=document.document_id,
            document_type=document.document_type.value,
            project_id=document.project_id,
            version=document.version,
            timestamp=datetime.now(),
            metadata=document.document_metadata or {}
        )
        
        # Создаем подпись для проверки целостности
        data_json = qr_data.json(exclude={'signature'})
        signature = self._create_signature(data_json)
        qr_data.signature = signature
        
        return qr_data.json()
    
    def generate_qr_image(self, qr_data: str, size: int = 300) -> Image.Image:
        """
        Генерирует изображение QR-кода
        
        Args:
            qr_data: Данные для QR-кода
            size: Размер изображения в пикселях
            
        Returns:
            PIL Image объект
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Изменяем размер
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        return img
    
    async def save_qr_code(
        self, 
        document_id: str, 
        qr_image: Image.Image, 
        version: str = "1.0"
    ) -> str:
        """
        Сохраняет QR-код в файл
        
        Args:
            document_id: ID документа
            qr_image: Изображение QR-кода
            version: Версия документа
            
        Returns:
            Путь к сохраненному файлу
        """
        filename = f"qr_{document_id}_{version}.png"
        filepath = os.path.join(self.qr_storage_path, filename)
        
        # Сохраняем изображение
        qr_image.save(filepath, "PNG")
        
        return filepath
    
    async def get_qr_code_path(self, document_id: str, version: Optional[str] = None) -> Optional[str]:
        """
        Получает путь к QR-коду документа
        
        Args:
            document_id: ID документа
            version: Версия документа (если None, ищет последнюю)
            
        Returns:
            Путь к файлу QR-кода или None
        """
        if version:
            filename = f"qr_{document_id}_{version}.png"
            filepath = os.path.join(self.qr_storage_path, filename)
            return filepath if os.path.exists(filepath) else None
        
        # Ищем последнюю версию
        pattern = f"qr_{document_id}_"
        for filename in os.listdir(self.qr_storage_path):
            if filename.startswith(pattern) and filename.endswith(".png"):
                return os.path.join(self.qr_storage_path, filename)
        
        return None
    
    def parse_qr_data(self, qr_data: str) -> Dict[str, Any]:
        """
        Парсит данные QR-кода
        
        Args:
            qr_data: JSON строка с данными QR-кода
            
        Returns:
            Словарь с данными
        """
        try:
            data = json.loads(qr_data)
            return data
        except json.JSONDecodeError:
            raise ValueError("Некорректные данные QR-кода")
    
    def extract_qr_from_image(self, image_data: bytes) -> Optional[str]:
        """
        Извлекает QR-код из изображения
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Данные QR-кода или None
        """
        try:
            # Используем PIL для работы с изображением
            from PIL import Image
            import io
            
            # Открываем изображение через PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Ищем QR-коды
            qr_codes = pyzbar.decode(image)
            
            if qr_codes:
                # Возвращаем данные первого найденного QR-кода
                return qr_codes[0].data.decode('utf-8')
            
            return None
            
        except Exception as e:
            print(f"Ошибка извлечения QR-кода: {e}")
            return None
    
    def extract_qr_from_pdf(self, pdf_data: bytes) -> Optional[str]:
        """
        Извлекает QR-код из PDF файла
        
        Args:
            pdf_data: Байты PDF файла
            
        Returns:
            Данные QR-кода или None
        """
        try:
            # Временно отключено из-за отсутствия PyMuPDF
            print("Извлечение QR-кода из PDF временно отключено")
            return None
            
        except Exception as e:
            print(f"Ошибка извлечения QR-кода из PDF: {e}")
            return None
    
    def extract_qr_from_file(self, file_data: bytes, file_type: str) -> Optional[str]:
        """
        Извлекает QR-код из файла (изображение или PDF)
        
        Args:
            file_data: Байты файла
            file_type: MIME тип файла
            
        Returns:
            Данные QR-кода или None
        """
        if file_type.startswith('image/'):
            return self.extract_qr_from_image(file_data)
        elif file_type == 'application/pdf':
            return self.extract_qr_from_pdf(file_data)
        else:
            print(f"Неподдерживаемый тип файла: {file_type}")
            return None
    
    def validate_qr_signature(self, qr_data: str) -> bool:
        """
        Проверяет подпись QR-кода
        
        Args:
            qr_data: JSON строка с данными QR-кода
            
        Returns:
            True если подпись валидна
        """
        try:
            data = json.loads(qr_data)
            
            if 'signature' not in data:
                return False
            
            signature = data.pop('signature')
            data_json = json.dumps(data, sort_keys=True)
            
            expected_signature = self._create_signature(data_json)
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception:
            return False
    
    def _create_signature(self, data: str) -> str:
        """
        Создает HMAC подпись для данных
        
        Args:
            data: Данные для подписи
            
        Returns:
            Hex строка подписи
        """
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def generate_qr_with_logo(
        self, 
        qr_data: str, 
        logo_path: Optional[str] = None,
        size: int = 300
    ) -> Image.Image:
        """
        Генерирует QR-код с логотипом
        
        Args:
            qr_data: Данные для QR-кода
            logo_path: Путь к логотипу
            size: Размер изображения
            
        Returns:
            PIL Image объект
        """
        # Генерируем базовый QR-код
        qr_image = self.generate_qr_image(qr_data, size)
        
        if logo_path and os.path.exists(logo_path):
            try:
                # Загружаем логотип
                logo = Image.open(logo_path)
                
                # Вычисляем размер логотипа (20% от размера QR-кода)
                logo_size = int(size * 0.2)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Вычисляем позицию для логотипа (центр)
                logo_pos = ((size - logo_size) // 2, (size - logo_size) // 2)
                
                # Вставляем логотип
                qr_image.paste(logo, logo_pos)
                
            except Exception as e:
                print(f"Ошибка добавления логотипа: {e}")
        
        return qr_image
    
    def generate_qr_svg(self, qr_data: str) -> str:
        """
        Генерирует QR-код в формате SVG
        
        Args:
            qr_data: Данные для QR-кода
            
        Returns:
            SVG строка
        """
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            image_factory=factory
        )
        
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image()
        return img.to_string().decode('utf-8')
    
    def get_qr_info(self, qr_data: str) -> Dict[str, Any]:
        """
        Получает информацию о QR-коде
        
        Args:
            qr_data: Данные QR-кода
            
        Returns:
            Словарь с информацией
        """
        try:
            data = json.loads(qr_data)
            
            return {
                "document_id": data.get("document_id"),
                "document_type": data.get("document_type"),
                "project_id": data.get("project_id"),
                "version": data.get("version"),
                "timestamp": data.get("timestamp"),
                "has_signature": "signature" in data,
                "signature_valid": self.validate_qr_signature(qr_data) if "signature" in data else False
            }
            
        except Exception as e:
            return {"error": str(e)}
