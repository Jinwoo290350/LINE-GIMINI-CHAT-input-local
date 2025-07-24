"""
Debug Router สำหรับ Context Management
ใช้สำหรับ debug และ monitoring ระบบ context awareness
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from services.file_service import file_service
from services.content_analyzer import content_analyzer
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/contexts")
async def get_all_contexts():
    """
    ดึงข้อมูล contexts ทั้งหมด (สำหรับ debug)
    """
    try:
        contexts_data = []
        
        for user_id, context in file_service.conversation_contexts.items():
            contexts_data.append({
                "user_id": user_id,
                "file_path": context.file_path,
                "file_type": context.file_type,
                "original_intent": context.original_intent,
                "detected_intents": context.detected_intents,
                "interaction_count": context.interaction_count,
                "last_activity": context.last_activity.isoformat(),
                "should_keep_file": context.should_keep_file,
                "is_expired": context.is_expired,
                "content_preview": context.processed_content[:100] + "..." if context.processed_content else None
            })
        
        return JSONResponse(content={
            "success": True,
            "contexts": contexts_data,
            "total": len(contexts_data),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Debug contexts error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/context/{user_id}")
async def get_user_context(user_id: str):
    """
    ดึงข้อมูล context ของผู้ใช้คนใดคนหนึ่ง
    """
    try:
        context = file_service.get_conversation_context(user_id)
        
        if not context:
            return JSONResponse(content={
                "success": False,
                "message": "No context found for this user"
            })
        
        context_data = {
            "user_id": user_id,
            "file_path": context.file_path,
            "file_type": context.file_type,
            "original_intent": context.original_intent,
            "detected_intents": context.detected_intents,
            "interaction_count": context.interaction_count,
            "last_activity": context.last_activity.isoformat(),
            "should_keep_file": context.should_keep_file,
            "is_expired": context.is_expired,
            "processed_content_preview": context.processed_content[:200] if context.processed_content else None
        }
        
        return JSONResponse(content={
            "success": True,
            "context": context_data
        })
        
    except Exception as e:
        logger.error(f"❌ Debug user context error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.delete("/context/{user_id}")
async def clear_user_context(user_id: str):
    """
    ลบ context ของผู้ใช้ (สำหรับ debug)
    """
    try:
        context = file_service.get_conversation_context(user_id)
        if not context:
            return JSONResponse(content={
                "success": False,
                "message": "No context found for this user"
            })
        
        file_service.remove_conversation_context(user_id)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Context cleared for user: {user_id}"
        })
        
    except Exception as e:
        logger.error(f"❌ Clear context error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.post("/cleanup/contexts")
async def force_cleanup_contexts():
    """
    บังคับทำความสะอาด contexts ที่หมดอายุ
    """
    try:
        # เก็บจำนวนก่อนทำความสะอาด
        before_count = len(file_service.conversation_contexts)
        
        file_service.cleanup_expired_contexts()
        
        # นับหลังทำความสะอาด
        after_count = len(file_service.conversation_contexts)
        cleaned_count = before_count - after_count
        
        return JSONResponse(content={
            "success": True,
            "message": f"Cleaned up {cleaned_count} expired contexts",
            "before_count": before_count,
            "after_count": after_count,
            "cleaned_count": cleaned_count
        })
        
    except Exception as e:
        logger.error(f"❌ Force cleanup error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/pending-files")
async def get_pending_files():
    """
    ดูไฟล์ที่รอการประมวลผล
    """
    try:
        pending_data = []
        
        for user_id, pending_file in file_service.pending_files.items():
            pending_data.append({
                "user_id": user_id,
                "message_id": pending_file.message_id,
                "file_type": pending_file.file_type,
                "timestamp": pending_file.timestamp.isoformat(),
                "is_expired": pending_file.is_expired
            })
        
        return JSONResponse(content={
            "success": True,
            "pending_files": pending_data,
            "total": len(pending_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Get pending files error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.post("/analyze-intent")
async def analyze_intent_debug(text: str):
    """
    ทดสอบการวิเคราะห์ intent จากข้อความ
    """
    try:
        # วิเคราะห์ด้วย content analyzer
        analysis = content_analyzer.analyze_content(text, "text")
        
        # วิเคราะห์ด้วย IntentAnalysis
        from models.ai_models import IntentAnalysis
        intent_analysis = IntentAnalysis.analyze_intent(text)
        
        return JSONResponse(content={
            "success": True,
            "input_text": text,
            "content_analysis": {
                "detected_intents": analysis.detected_intents,
                "key_phrases": analysis.key_phrases,
                "suggested_actions": analysis.suggested_actions,
                "confidence_score": analysis.confidence_score
            },
            "intent_analysis": {
                "intent_type": intent_analysis.intent_type,
                "confidence": intent_analysis.confidence
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Analyze intent error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/system-stats")
async def get_system_stats():
    """
    ดูสถิติระบบโดยรวม
    """
    try:
        import psutil
        import os
        
        # ข้อมูลระบบ
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # ข้อมูล contexts
        total_contexts = len(file_service.conversation_contexts)
        expired_contexts = sum(1 for ctx in file_service.conversation_contexts.values() if ctx.is_expired)
        
        # ข้อมูล pending files
        total_pending = len(file_service.pending_files)
        expired_pending = sum(1 for pf in file_service.pending_files.values() if pf.is_expired)
        
        # ข้อมูลไฟล์ในโฟลเดอร์ uploads
        upload_files = list(Path(file_service.upload_dir).glob("*"))
        upload_files_count = len([f for f in upload_files if f.is_file() and f.name != '.gitkeep'])
        
        return JSONResponse(content={
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "contexts": {
                "total": total_contexts,
                "active": total_contexts - expired_contexts,
                "expired": expired_contexts
            },
            "pending_files": {
                "total": total_pending,
                "active": total_pending - expired_pending,
                "expired": expired_pending
            },
            "upload_files": {
                "count": upload_files_count,
                "directory": str(file_service.upload_dir)
            }
        })
        
    except Exception as e:
        logger.error(f"❌ System stats error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/")
async def debug_index():
    """
    Debug endpoints รายการ
    """
    return {
        "message": "Debug API for Context Management",
        "endpoints": {
            "GET /debug/contexts": "ดูทุก contexts",
            "GET /debug/context/{user_id}": "ดู context ของผู้ใช้",
            "DELETE /debug/context/{user_id}": "ลบ context ของผู้ใช้",
            "POST /debug/cleanup/contexts": "บังคับ cleanup contexts",
            "GET /debug/pending-files": "ดูไฟล์ที่รอประมวลผล",
            "POST /debug/analyze-intent": "ทดสอบ intent analysis",
            "GET /debug/system-stats": "ดูสถิติระบบ"
        }
    }