"""
Основной файл сервиса выходного контроля исходящей переписки
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import tempfile
import logging

from database import get_db, engine
from models import Base, OutgoingDocument, DocumentCheck, SpellCheckResult, StyleAnalysisResult, EthicsCheckResult, TerminologyCheckResult, FinalReview
from schemas import (
    DocumentCreate, Document, DocumentUpdate, CheckResult, SpellCheckRequest, SpellCheckResponse,
    StyleAnalysisRequest, StyleAnalysisResponse, EthicsCheckRequest, EthicsCheckResponse,
    TerminologyCheckRequest, TerminologyCheckResponse, FinalReviewRequest, FinalReviewResponse,
    FileUploadResponse, DocumentProcessingRequest, DocumentProcessingResponse, ServiceStats
)
from services.document_processor import DocumentProcessor
from services.spell_checker import SpellCheckService
from services.style_analyzer import StyleAnalyzer
from services.ethics_checker import EthicsChecker
from services.terminology_checker import TerminologyChecker
from services.llm_integration import LLMIntegration
from services.settings_service import OutgoingControlSettingsService
from settings import (
    OutgoingControlSettings, 
    SettingsUpdateRequest, 
    SettingsResponse,
    SettingsValidationResponse
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI
app = FastAPI(
    title="Outgoing Control Service",
    description="Сервис выходного контроля исходящей переписки",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация сервисов
document_processor = DocumentProcessor()
spell_checker = SpellCheckService()
style_analyzer = StyleAnalyzer()
ethics_checker = EthicsChecker()
terminology_checker = TerminologyChecker()
llm_integration = LLMIntegration()
settings_service = OutgoingControlSettingsService()

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Outgoing Control Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Сервис выходного контроля исходящей переписки"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "outgoing-control-service"}

# === УПРАВЛЕНИЕ ДОКУМЕНТАМИ ===

@app.post("/documents/", response_model=Document)
async def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    """Создает новый документ для проверки"""
    try:
        db_document = OutgoingDocument(
            title=document.title,
            document_type=document.document_type,
            project_id=document.project_id,
            status="pending"
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        logger.info(f"Создан документ {db_document.id}")
        return db_document
        
    except Exception as e:
        logger.error(f"Ошибка при создании документа: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/", response_model=List[Document])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получает список документов"""
    try:
        documents = db.query(OutgoingDocument).offset(skip).limit(limit).all()
        return documents
        
    except Exception as e:
        logger.error(f"Ошибка при получении документов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Получает документ по ID"""
    try:
        document = db.query(OutgoingDocument).filter(OutgoingDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении документа: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/documents/{document_id}", response_model=Document)
async def update_document(
    document_id: uuid.UUID,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """Обновляет документ"""
    try:
        document = db.query(OutgoingDocument).filter(OutgoingDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Обновляем поля
        for field, value in document_update.dict(exclude_unset=True).items():
            setattr(document, field, value)
        
        db.commit()
        db.refresh(document)
        
        logger.info(f"Обновлен документ {document_id}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении документа: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === ЗАГРУЗКА ФАЙЛОВ ===

@app.post("/documents/{document_id}/upload", response_model=FileUploadResponse)
async def upload_document(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Загружает файл документа"""
    try:
        # Проверяем существование документа
        document = db.query(OutgoingDocument).filter(OutgoingDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Извлекаем текст из файла
            extraction_result = await document_processor.extract_text(
                temp_file_path, 
                file.content_type
            )
            
            # Обновляем документ
            document.file_path = temp_file_path
            document.file_size = len(content)
            document.mime_type = file.content_type
            document.extracted_text = extraction_result["text"]
            document.status = "processing"
            
            db.commit()
            db.refresh(document)
            
            logger.info(f"Загружен файл для документа {document_id}")
            
            # Автоматическая обработка если включена
            settings_service = OutgoingControlSettingsService()
            settings = settings_service.get_settings()
            
            if settings.auto_process_on_upload:
                logger.info(f"Запуск автоматической обработки для документа {document_id}")
                try:
                    # Выполняем все включенные проверки
                    completed_checks = []
                    overall_score = 0.0
                    can_send = True
                    
                    for check_type in settings.enabled_checks:
                        try:
                            if check_type == "spell_check":
                                result = await spell_checker.check_spelling(document.extracted_text)
                                score = result["confidence_score"]
                                
                            elif check_type == "style_analysis":
                                result = await style_analyzer.analyze_style(document.extracted_text, document.document_type)
                                score = (result["readability_score"] + result["formality_score"] + result["business_style_score"]) / 3
                                
                            elif check_type == "ethics_check":
                                result = await ethics_checker.check_ethics(document.extracted_text)
                                score = result["ethics_score"]
                                if not result["is_approved"]:
                                    can_send = False
                                    
                            elif check_type == "terminology_check":
                                result = await terminology_checker.check_terminology(document.extracted_text, "engineering")
                                score = result["accuracy_score"]
                                
                            else:
                                continue
                            
                            completed_checks.append(check_type)
                            overall_score += score
                            
                        except Exception as e:
                            logger.warning(f"Ошибка при выполнении проверки {check_type}: {str(e)}")
                            continue
                    
                    # Вычисляем среднюю оценку
                    if completed_checks:
                        overall_score = overall_score / len(completed_checks)
                    
                    # Обновляем статус документа и сохраняем результаты
                    if can_send and overall_score >= 70:
                        document.status = "approved"
                    elif overall_score >= 50:
                        document.status = "needs_revision"
                    else:
                        document.status = "rejected"
                    
                    # Сохраняем результаты обработки
                    document.overall_score = overall_score
                    document.can_send = can_send
                    document.recommendations = "Автоматическая обработка завершена. Проверьте результаты всех проверок для получения детальных рекомендаций."
                    
                    db.commit()
                    
                    logger.info(f"Автоматическая обработка завершена для документа {document_id}, выполнено проверок: {len(completed_checks)}, общая оценка: {overall_score}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при автоматической обработке документа {document_id}: {str(e)}")
                    document.status = "processing"
                    db.commit()
            
            return FileUploadResponse(
                file_id=str(document_id),
                filename=file.filename,
                size=len(content),
                mime_type=file.content_type,
                extracted_text=extraction_result["text"]
            )
            
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === ПРОВЕРКА ОРФОГРАФИИ ===

@app.post("/spell-check", response_model=SpellCheckResponse)
async def check_spelling(request: SpellCheckRequest):
    """Проверяет орфографию текста"""
    try:
        result = await spell_checker.check_spelling(request.text, request.language)
        
        return SpellCheckResponse(
            total_words=result["total_words"],
            errors_found=result["errors_found"],
            suggestions=result["suggestions"],
            corrected_text=result["corrected_text"],
            confidence_score=result["confidence_score"]
        )
        
    except Exception as e:
        logger.error(f"Ошибка при проверке орфографии: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === АНАЛИЗ СТИЛЯ ===

@app.post("/style-analysis", response_model=StyleAnalysisResponse)
async def analyze_style(request: StyleAnalysisRequest):
    """Анализирует стиль письма"""
    try:
        result = await style_analyzer.analyze_style(request.text, request.document_type)
        
        return StyleAnalysisResponse(
            readability_score=result["readability_score"],
            formality_score=result["formality_score"],
            business_style_score=result["business_style_score"],
            tone_analysis=result["tone_analysis"],
            recommendations=result["recommendations"]
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе стиля: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === ПРОВЕРКА ЭТИКИ ===

@app.post("/ethics-check", response_model=EthicsCheckResponse)
async def check_ethics(request: EthicsCheckRequest):
    """Проверяет этичность содержания"""
    try:
        result = await ethics_checker.check_ethics(request.text, request.context)
        
        return EthicsCheckResponse(
            ethics_score=result["ethics_score"],
            violations_found=result["violations_found"],
            recommendations=result["recommendations"],
            is_approved=result["is_approved"]
        )
        
    except Exception as e:
        logger.error(f"Ошибка при проверке этики: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === ПРОВЕРКА ТЕРМИНОЛОГИИ ===

@app.post("/terminology-check", response_model=TerminologyCheckResponse)
async def check_terminology(request: TerminologyCheckRequest):
    """Проверяет правильность терминологии"""
    try:
        result = await terminology_checker.check_terminology(request.text, request.domain)
        
        return TerminologyCheckResponse(
            terms_used=result["terms_used"],
            incorrect_terms=result["incorrect_terms"],
            suggestions=result["suggestions"],
            accuracy_score=result["accuracy_score"]
        )
        
    except Exception as e:
        logger.error(f"Ошибка при проверке терминологии: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === ФИНАЛЬНАЯ ПРОВЕРКА ===

@app.post("/final-review", response_model=FinalReviewResponse)
async def perform_final_review(
    request: FinalReviewRequest,
    db: Session = Depends(get_db)
):
    """Выполняет финальную проверку документа"""
    try:
        # Получаем документ
        document = db.query(OutgoingDocument).filter(OutgoingDocument.id == request.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        if not document.extracted_text:
            raise HTTPException(status_code=400, detail="Документ не содержит текста для проверки")
        
        # Выполняем все проверки
        check_results = {}
        
        if request.include_all_checks:
            # Проверка орфографии
            spell_result = await spell_checker.check_spelling(document.extracted_text)
            check_results["spell_check"] = spell_result
            
            # Анализ стиля
            style_result = await style_analyzer.analyze_style(document.extracted_text, document.document_type)
            check_results["style_analysis"] = style_result
            
            # Проверка этики
            ethics_result = await ethics_checker.check_ethics(document.extracted_text)
            check_results["ethics_check"] = ethics_result
            
            # Проверка терминологии
            terminology_result = await terminology_checker.check_terminology(document.extracted_text, "engineering")
            check_results["terminology_check"] = terminology_result
        
        # Финальная проверка с LLM
        final_result = await llm_integration.perform_final_review(
            document.extracted_text, 
            check_results
        )
        
        # Сохраняем результат
        final_review = FinalReview(
            document_id=document.id,
            overall_score=final_result["overall_score"],
            can_send=final_result["can_send"],
            critical_issues=final_result["critical_issues"],
            minor_issues=final_result["minor_issues"],
            recommendations=final_result["recommendations"]
        )
        
        db.add(final_review)
        
        # Обновляем статус документа
        if final_result["can_send"]:
            document.status = "approved"
        else:
            document.status = "needs_revision"
        
        db.commit()
        
        logger.info(f"Выполнена финальная проверка документа {request.document_id}")
        
        return FinalReviewResponse(
            overall_score=final_result["overall_score"],
            can_send=final_result["can_send"],
            critical_issues=final_result["critical_issues"],
            minor_issues=final_result["minor_issues"],
            recommendations=final_result["recommendations"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при финальной проверке: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === ОБРАБОТКА ДОКУМЕНТА ===

@app.post("/documents/{document_id}/process", response_model=DocumentProcessingResponse)
async def process_document(
    document_id: uuid.UUID,
    request: DocumentProcessingRequest,
    db: Session = Depends(get_db)
):
    """Обрабатывает документ всеми проверками"""
    try:
        # Получаем документ
        document = db.query(OutgoingDocument).filter(OutgoingDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        if not document.extracted_text:
            raise HTTPException(status_code=400, detail="Документ не содержит текста для проверки")
        
        # Выполняем запрошенные проверки
        completed_checks = []
        overall_score = 0.0
        can_send = True
        
        for check_type in request.checks_to_perform:
            try:
                if check_type == "spell_check":
                    result = await spell_checker.check_spelling(document.extracted_text)
                    score = result["confidence_score"]
                    
                elif check_type == "style_check":
                    result = await style_analyzer.analyze_style(document.extracted_text, document.document_type)
                    score = (result["readability_score"] + result["formality_score"] + result["business_style_score"]) / 3
                    
                elif check_type == "ethics_check":
                    result = await ethics_checker.check_ethics(document.extracted_text)
                    score = result["ethics_score"]
                    if not result["is_approved"]:
                        can_send = False
                        
                elif check_type == "terminology_check":
                    result = await terminology_checker.check_terminology(document.extracted_text, "engineering")
                    score = result["accuracy_score"]
                    
                else:
                    continue
                
                completed_checks.append(check_type)
                overall_score += score
                
            except Exception as e:
                logger.warning(f"Ошибка при выполнении проверки {check_type}: {str(e)}")
                continue
        
        # Вычисляем среднюю оценку
        if completed_checks:
            overall_score = overall_score / len(completed_checks)
        
        # Обновляем статус документа и сохраняем результаты
        if can_send and overall_score >= 70:
            document.status = "approved"
        elif overall_score >= 50:
            document.status = "needs_revision"
        else:
            document.status = "rejected"
        
        # Сохраняем результаты обработки
        document.overall_score = overall_score
        document.can_send = can_send
        document.recommendations = "Проверьте результаты всех проверок для получения детальных рекомендаций"
        
        db.commit()
        
        logger.info(f"Обработан документ {document_id}, выполнено проверок: {len(completed_checks)}")
        
        return DocumentProcessingResponse(
            document_id=document_id,
            status=document.status,
            checks_completed=completed_checks,
            overall_score=overall_score,
            can_send=can_send,
            recommendations="Проверьте результаты всех проверок для получения детальных рекомендаций"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке документа: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === СТАТИСТИКА ===

@app.get("/stats", response_model=ServiceStats)
async def get_service_stats(db: Session = Depends(get_db)):
    """Получает статистику сервиса"""
    try:
        total_documents = db.query(OutgoingDocument).count()
        approved_documents = db.query(OutgoingDocument).filter(OutgoingDocument.status == "approved").count()
        rejected_documents = db.query(OutgoingDocument).filter(OutgoingDocument.status == "rejected").count()
        needs_revision = db.query(OutgoingDocument).filter(OutgoingDocument.status == "needs_revision").count()
        
        return ServiceStats(
            total_documents_processed=total_documents,
            documents_approved=approved_documents,
            documents_rejected=rejected_documents,
            documents_needing_revision=needs_revision,
            average_processing_time=0.0,  # TODO: Реализовать подсчет времени
            most_common_issues=[]  # TODO: Реализовать анализ проблем
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== НАСТРОЙКИ МОДУЛЯ ====================

@app.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Получить настройки модуля выходного контроля"""
    try:
        settings = settings_service.get_settings()
        return SettingsResponse(
            success=True,
            settings=settings,
            message="Настройки успешно получены"
        )
    except Exception as e:
        logger.error(f"Ошибка при получении настроек: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest):
    """Обновить настройки модуля выходного контроля"""
    try:
        response = settings_service.update_settings(request.settings)
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        return response
    except Exception as e:
        logger.error(f"Ошибка при обновлении настроек: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings/validate", response_model=SettingsValidationResponse)
async def validate_settings(request: SettingsUpdateRequest):
    """Валидировать настройки модуля выходного контроля"""
    try:
        return settings_service.validate_settings(request.settings)
    except Exception as e:
        logger.error(f"Ошибка при валидации настроек: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings/reset", response_model=SettingsResponse)
async def reset_settings():
    """Сбросить настройки к значениям по умолчанию"""
    try:
        return settings_service.reset_to_defaults()
    except Exception as e:
        logger.error(f"Ошибка при сбросе настроек: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings/prompts")
async def get_prompts():
    """Получить все промпты для проверок"""
    try:
        settings = settings_service.get_settings()
        return {
            "spell_check_prompt": settings.spell_check_prompt,
            "style_analysis_prompt": settings.style_analysis_prompt,
            "ethics_check_prompt": settings.ethics_check_prompt,
            "terminology_check_prompt": settings.terminology_check_prompt,
            "final_review_prompt": settings.final_review_prompt
        }
    except Exception as e:
        logger.error(f"Ошибка при получении промптов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings/llm-config")
async def get_llm_config():
    """Получить конфигурацию LLM"""
    try:
        return settings_service.get_llm_config()
    except Exception as e:
        logger.error(f"Ошибка при получении конфигурации LLM: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
