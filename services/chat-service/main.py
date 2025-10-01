"""
Расширенный Chat Service с поддержкой файлов, OCR, настроек и экспорта
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import io
import logging
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sys

from services.file_processor import FileProcessor
from services.document_exporter import DocumentExporter
from services.settings_service import SettingsService
from services.llm_service import LLMService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Добавляем файловый хендлер если директория существует
try:
    os.makedirs('/app/logs', exist_ok=True)
    file_handler = logging.FileHandler('/app/logs/chat-service.log', mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
except Exception as e:
    print(f"Не удалось создать файловый логгер: {e}")

logger = logging.getLogger(__name__)

# Инициализация сервисов
file_processor = FileProcessor()
document_exporter = DocumentExporter()
settings_service = SettingsService()
llm_service = LLMService()

# Инициализация базы данных при запуске
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Chat Service запущен с расширенным функционалом")
    logger.info("📁 Поддерживаемые форматы: DOCX, PDF, XLS, MD, TXT")
    logger.info("🔍 OCR включен для растровых PDF")
    logger.info("⚙️ Управление настройками LLM доступно")
    logger.info("📄 Экспорт в DOCX/PDF с кириллицей")
    yield
    # Shutdown
    logger.info("🛑 Chat Service остановлен")

app = FastAPI(
    title="Chat Service - Расширенный",
    description="Сервис чата с ИИ с поддержкой файлов, OCR, настроек и экспорта",
    version="2.0.0",
    lifespan=lifespan,
    # Настройки для больших файлов
    max_request_size=100 * 1024 * 1024,  # 100MB
)

# Middleware для логирования запросов и обработки больших запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"📥 Входящий запрос: {request.method} {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")
    
    # Логируем размер контента если есть
    content_length = request.headers.get("content-length")
    if content_length:
        size_mb = int(content_length) / (1024 * 1024)
        logger.info(f"📊 Размер запроса: {size_mb:.2f} MB")
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"📤 Ответ отправлен: {response.status_code} за {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Ошибка обработки запроса: {str(e)} за {process_time:.3f}s")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:80",
        "http://127.0.0.1",
        "*"  # Разрешаем все origins для разработки
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Глобальное хранилище чатов (в production использовать Redis/DB)
chat_sessions = {}

@app.get("/")
async def root():
    logger.info("🏠 Запрос к корневому эндпоинту")
    try:
        response = {
            "message": "Chat Service - Расширенный",
            "version": "2.0.0",
            "features": [
                "Загрузка файлов до 100MB",
                "OCR для растровых PDF",
                "Управление настройками LLM",
                "Экспорт в DOCX/PDF с кириллицей"
            ]
        }
        logger.info("✅ Корневой эндпоинт успешно обработан")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка в корневом эндпоинте: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/health")
async def health():
    logger.info("🏥 Запрос к health check")
    try:
        # Проверяем состояние сервисов
        services_status = {
            "file_processor": "ok",
            "document_exporter": "ok", 
            "settings_service": "ok"
        }
        
        response = {
            "status": "healthy",
            "service": "chat-service",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "features_enabled": {
                "file_upload": True,
                "ocr": True,
                "settings": True,
                "export": True
            },
            "services": services_status
        }
        logger.info("✅ Health check успешно выполнен")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка в health check: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Сервис недоступен")

# === УПРАВЛЕНИЕ НАСТРОЙКАМИ ===

@app.get("/settings")
async def get_all_settings():
    """Получить все настройки"""
    return settings_service.get_all_settings()

@app.get("/settings/llm")
async def get_llm_settings():
    """Получить настройки LLM"""
    return settings_service.get_llm_settings()

@app.put("/settings/llm")
async def update_llm_settings(settings: Dict[str, Any]):
    """Обновить настройки LLM"""
    return settings_service.update_llm_settings(settings)

@app.get("/settings/chat")
async def get_chat_settings():
    """Получить настройки чата"""
    return settings_service.get_chat_settings()

@app.put("/settings/chat")
async def update_chat_settings(settings: Dict[str, Any]):
    """Обновить настройки чата"""
    return settings_service.update_chat_settings(settings)

@app.get("/settings/system")
async def get_system_settings():
    """Получить системные настройки"""
    return settings_service.get_system_settings()

@app.put("/settings/system")
async def update_system_settings(settings: Dict[str, Any]):
    """Обновить системные настройки"""
    return settings_service.update_system_settings(settings)

@app.post("/settings/reset")
async def reset_settings():
    """Сбросить настройки к значениям по умолчанию"""
    return settings_service.reset_to_defaults()

@app.get("/settings/available")
async def get_available_options():
    """Получить доступные опции для настроек"""
    models = await settings_service.get_available_models()
    return {
        "models": models,
        "languages": settings_service.get_available_languages(),
        "export_formats": settings_service.get_available_export_formats()
    }

# === ЗАГРУЗКА И ОБРАБОТКА ФАЙЛОВ ===

@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузить и обработать файл"""
    logger.info(f"📁 Загрузка файла: {file.filename} ({file.content_type})")
    
    try:
        # Проверяем размер файла
        file_content = await file.read()
        file_size = len(file_content)
        logger.info(f"📊 Размер файла: {file_size} байт ({file_size / (1024*1024):.2f} MB)")

        max_size = file_processor.get_max_file_size()
        if file_size > max_size:
            logger.warning(f"⚠️ Файл слишком большой: {file_size} > {max_size}")
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой. Максимальный размер: {max_size / (1024*1024):.0f}MB"
            )

        # Обрабатываем файл
        logger.info(f"🔄 Начинаем обработку файла: {file.filename}")
        result = await file_processor.process_file(file_content, file.filename)

        if not result["success"]:
            logger.error(f"❌ Ошибка обработки файла: {result.get('error', 'Неизвестная ошибка')}")
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(f"✅ Файл успешно обработан: {file.filename}")
        logger.debug(f"Результат обработки: {result}")
        return result

    except HTTPException as he:
        logger.error(f"❌ HTTP ошибка при загрузке файла: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при загрузке файла: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")

@app.get("/files/supported")
async def get_supported_formats():
    """Получить список поддерживаемых форматов файлов"""
    return {
        "supported_formats": file_processor.get_supported_formats(),
        "max_file_size": file_processor.get_max_file_size(),
        "max_file_size_mb": file_processor.get_max_file_size() / (1024 * 1024)
    }

# === ЧАТ С ИИ ===

@app.post("/chat")
async def chat_with_ai(
    message: str = Form(...),
    session_id: str = Form(default="default"),
    files: List[UploadFile] = File(default=[])
):
    """Отправить сообщение в чат с ИИ"""
    logger.info(f"💬 Новое сообщение в чат. Сессия: {session_id}, Файлов: {len(files)}")
    logger.debug(f"Сообщение: {message[:100]}...")
    
    try:
        # Инициализируем сессию если не существует
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "messages": [],
                "files": [],
                "created_at": datetime.now().isoformat()
            }
        
        session = chat_sessions[session_id]
        
        # Обрабатываем загруженные файлы
        processed_files = []
        for file in files:
            file_content = await file.read()
            result = await file_processor.process_file(file_content, file.filename)
            if result["success"]:
                processed_files.append(result)
                session["files"].append(result)
        
        # Добавляем сообщение пользователя
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "files": processed_files
        }
        session["messages"].append(user_message)
        
        # Получаем настройки LLM
        llm_settings = settings_service.get_llm_settings()
        
        # Формируем контекст для LLM
        context = _build_llm_context(session, llm_settings)
        
        # Получаем ответ от LLM
        ai_response = await llm_service.generate_response(
            prompt=context,
            model=llm_settings.get('model', 'llama3.1:8b'),
            temperature=llm_settings.get('temperature', 0.7),
            max_tokens=llm_settings.get('max_tokens', 2048),
            top_p=llm_settings.get('top_p', 0.9),
            top_k=llm_settings.get('top_k', 40),
            repeat_penalty=llm_settings.get('repeat_penalty', 1.1),
            system_prompt=llm_settings.get('system_prompt', ''),
            timeout=llm_settings.get('timeout', 300.0)
        )
        
        # Добавляем ответ ИИ
        ai_message = {
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        session["messages"].append(ai_message)
        
        return {
            "success": True,
            "response": ai_response,
            "session_id": session_id,
            "files_processed": len(processed_files),
            "message_count": len(session["messages"])
        }
        
    except HTTPException as he:
        logger.error(f"❌ HTTP ошибка в чате: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка в чате: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ошибка чата: {str(e)}")

@app.post("/chat/stream")
async def chat_with_ai_streaming(
    message: str = Form(...),
    session_id: str = Form(default="default"),
    files: List[UploadFile] = File(default=[])
):
    """Отправить сообщение в чат с ИИ (потоковый ответ)"""
    logger.info(f"🌊 Потоковый чат. Сессия: {session_id}, Файлов: {len(files)}")
    
    try:
        # Инициализируем сессию если не существует
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "messages": [],
                "files": [],
                "created_at": datetime.now().isoformat()
            }
        
        session = chat_sessions[session_id]
        
        # Обрабатываем загруженные файлы
        processed_files = []
        for file in files:
            file_content = await file.read()
            result = await file_processor.process_file(file_content, file.filename)
            if result["success"]:
                processed_files.append(result)
                session["files"].append(result)
        
        # Добавляем сообщение пользователя
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "files": processed_files
        }
        session["messages"].append(user_message)
        
        # Получаем настройки LLM
        llm_settings = settings_service.get_llm_settings()
        
        # Формируем контекст для LLM
        context = _build_llm_context(session, llm_settings)
        
        # Создаем потоковый ответ
        async def generate_stream():
            full_response = ""
            async for chunk in llm_service.generate_streaming_response(
                prompt=context,
                model=llm_settings.get('model', 'llama3.1:8b'),
                temperature=llm_settings.get('temperature', 0.7),
                max_tokens=llm_settings.get('max_tokens', 2048),
                top_p=llm_settings.get('top_p', 0.9),
                top_k=llm_settings.get('top_k', 40),
                repeat_penalty=llm_settings.get('repeat_penalty', 1.1),
                system_prompt=llm_settings.get('system_prompt', ''),
                timeout=llm_settings.get('timeout', 300.0)
            ):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk, 'session_id': session_id})}\n\n"
            
            # Добавляем полный ответ в сессию
            ai_message = {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            }
            session["messages"].append(ai_message)
            
            # Отправляем финальное сообщение
            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'full_response': full_response})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка потокового чата: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка потокового чата: {str(e)}")

@app.get("/chat/sessions")
async def get_chat_sessions():
    """Получить список сессий чата"""
    return {
        "sessions": list(chat_sessions.keys()),
        "total_sessions": len(chat_sessions)
    }

@app.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Получить конкретную сессию чата"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    return chat_sessions[session_id]

@app.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Удалить сессию чата"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    del chat_sessions[session_id]
    return {"success": True, "message": "Сессия удалена"}

# === ЭКСПОРТ ДОКУМЕНТОВ ===

@app.post("/export/docx")
async def export_to_docx(
    session_id: str = Form(...),
    filename: Optional[str] = Form(default=None)
):
    """Экспортировать чат в DOCX"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Сессия не найдена")
        
        session = chat_sessions[session_id]
        llm_settings = settings_service.get_llm_settings()
        
        # Подготавливаем данные для экспорта
        export_data = {
            "topic": f"Чат {session_id}",
            "messages": session["messages"],
            "files": session["files"],
            "llm_settings": llm_settings,
            "exported_at": datetime.now().isoformat()
        }
        
        # Экспортируем в DOCX
        docx_bytes = await document_exporter.export_to_docx(export_data, filename)
        
        # Возвращаем файл
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename or f'chat_{session_id}.docx'}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта в DOCX: {str(e)}")

@app.post("/export/pdf")
async def export_to_pdf(
    session_id: str = Form(...),
    filename: Optional[str] = Form(default=None)
):
    """Экспортировать чат в PDF"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Сессия не найдена")
        
        session = chat_sessions[session_id]
        llm_settings = settings_service.get_llm_settings()
        
        # Подготавливаем данные для экспорта
        export_data = {
            "topic": f"Чат {session_id}",
            "messages": session["messages"],
            "files": session["files"],
            "llm_settings": llm_settings,
            "exported_at": datetime.now().isoformat()
        }
        
        # Экспортируем в PDF
        pdf_bytes = await document_exporter.export_to_pdf(export_data, filename)
        
        # Возвращаем файл
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename or f'chat_{session_id}.pdf'}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта в PDF: {str(e)}")

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def _build_llm_context(session: Dict[str, Any], llm_settings: Dict[str, Any]) -> str:
    """Строит контекст для LLM"""
    context = ""
    
    # Добавляем системный промпт
    if llm_settings.get("system_prompt"):
        context += f"Система: {llm_settings['system_prompt']}\n\n"
    
    # Добавляем историю сообщений
    for message in session["messages"][-10:]:  # Последние 10 сообщений
        role = "Пользователь" if message["role"] == "user" else "ИИ"
        context += f"{role}: {message['content']}\n"
        
        # Добавляем информацию о файлах
        if message.get("files"):
            context += f"Прикрепленные файлы: {[f['filename'] for f in message['files']]}\n"
    
    return context


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8003,
        # Настройки для больших файлов
        limit_max_requests=1000,
        limit_concurrency=100,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=30,
        # Дополнительные настройки для больших запросов
        limit_request_line=8192,
        limit_request_fields=100,
        limit_request_field_size=8192
    )
