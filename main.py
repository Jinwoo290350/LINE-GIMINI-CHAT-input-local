"""
FastAPI Main Application
จุดเริ่มต้นของแอปพลิเคชัน LINE Bot AI Assistant + AI Context Awareness
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from pathlib import Path
from datetime import datetime
import psutil

# Import configurations และ services
from config.settings import get_settings
from routers import webhook, upload, debug
from utils.logger import get_logger, setup_logging
from services.file_service import file_service

# ตั้งค่า logging และ settings
setup_logging()
settings = get_settings()
logger = get_logger(__name__)


async def cleanup_expired_contexts():
    """
    Background task สำหรับ cleanup contexts ที่หมดอายุ
    """
    while True:
        try:
            file_service.cleanup_expired_contexts()
            await asyncio.sleep(300)  # ทำทุก 5 นาที
        except Exception as e:
            logger.error(f"❌ Context cleanup error: {str(e)}")
            await asyncio.sleep(60)  # รอ 1 นาทีแล้วลองใหม่


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    จัดการ lifecycle ของแอปพลิเคชัน
    ทำงานเมื่อเริ่มต้นและปิดแอปพลิเคชัน
    """
    # Startup
    logger.info("🚀 Starting LINE Bot AI Assistant with AI Context Awareness")
    logger.info(f"📱 App: {settings.app_name} v{settings.app_version}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info("🤖 AI Features: Context Analysis, Conversation History, Smart File Management")
    
    # ทำความสะอาดไฟล์เก่าเมื่อเริ่มต้น
    deleted_count = file_service.cleanup_old_files()
    logger.info(f"🧹 Cleaned up {deleted_count} old files")
    
    # เริ่ม background task สำหรับ context cleanup
    cleanup_task = asyncio.create_task(cleanup_expired_contexts())
    logger.info("🔄 Started AI context cleanup background task")
    
    # แสดงสถิติเริ่มต้น
    stats = file_service.get_system_statistics()
    logger.info(f"📊 Initial stats: {stats}")
    
    yield
    
    # Shutdown
    logger.info("📴 Shutting down LINE Bot AI Assistant")
    
    # ยกเลิก background task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("🛑 AI context cleanup task cancelled")
    
    # ทำความสะอาด contexts ที่เหลือ
    file_service.cleanup_expired_contexts()
    logger.info("🧹 Final AI context cleanup completed")


# สร้าง FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="LINE Bot AI Assistant with Google Gemini AI integration and Advanced AI Context Awareness",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตั้งค่า static files และ templates
static_dir = Path("static")
templates_dir = Path("templates")

# สร้างโฟลเดอร์หากไม่มี
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# เพิ่ม routers พร้อม base path
if settings.base_path:
    app.include_router(webhook.router, prefix=settings.base_path)
    app.include_router(upload.router, prefix=settings.base_path)
    app.include_router(debug.router, prefix=settings.base_path)
else:
    app.include_router(webhook.router)
    app.include_router(upload.router)
    app.include_router(debug.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get(f"{settings.base_path}/", response_class=HTMLResponse, include_in_schema=False)
async def web_interface(request: Request):
    """
    หน้าเว็บหลักสำหรับ File Upload Interface
    """
    base_url = str(request.base_url).rstrip('/')
    api_base_path = f"{base_url}{settings.base_path}"
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "base_path": settings.base_path,
        "api_base_path": api_base_path,
        "max_file_size": settings.max_file_size,
        "allowed_extensions": ", ".join(settings.allowed_extensions),
        "webhook_secret": settings.webhook_secret
    })


@app.get("/health")
@app.get(f"{settings.base_path}/health")
async def health_check():
    """
    Health Check Endpoint - เพิ่มข้อมูล AI Context Management
    ตรวจสอบสถานะแอปพลิเคชันและ services ต่างๆ
    """
    try:
        # ตรวจสอบสถานะระบบ
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # ข้อมูล AI context management
        stats = file_service.get_system_statistics()
        
        return {
            "status": "OK",
            "timestamp": datetime.now().isoformat(),
            "app": {
                "name": settings.app_name,
                "version": settings.app_version,
                "debug": settings.debug,
                "features": [
                    "AI Context Awareness",
                    "Conversation History",
                    "Smart File Management",
                    "Multi-modal AI Processing"
                ]
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            },
            "services": {
                "gemini_ai": "ready",
                "line_api": "ready",
                "file_service": "ready",
                "ai_context_analyzer": "ready"
            },
            "ai_context_management": {
                "active_contexts": stats.get('contexts', {}).get('active', 0),
                "total_contexts": stats.get('contexts', {}).get('total', 0),
                "active_histories": stats.get('histories', {}).get('active', 0),
                "pending_files": stats.get('pending_files', {}).get('active', 0),
                "upload_files": stats.get('upload_files', {}).get('count', 0)
            },
            "base_path": settings.base_path or "/",
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/debug/ai-features")
@app.get(f"{settings.base_path}/debug/ai-features")
async def debug_ai_features():
    """
    Debug endpoint สำหรับ AI features
    """
    try:
        stats = file_service.get_system_statistics()
        
        # ดึงข้อมูล contexts ที่มี AI analysis
        ai_contexts = []
        for user_id, context in file_service.conversation_contexts.items():
            ai_contexts.append({
                "user_id": user_id,
                "file_type": context.file_type,
                "ai_confidence": context.ai_confidence,
                "ai_reasoning": context.ai_reasoning,
                "conversation_summary": context.conversation_summary,
                "interaction_count": context.interaction_count,
                "last_activity": context.last_activity.isoformat(),
                "is_expired": context.is_expired
            })
        
        # ดึงข้อมูล conversation histories
        conversation_stats = []
        for user_id, history in file_service.conversation_histories.items():
            conversation_stats.append({
                "user_id": user_id,
                "message_count": len(history.messages),
                "last_updated": history.last_updated.isoformat(),
                "is_expired": history.is_expired,
                "recent_messages": [
                    {
                        "role": msg.role,
                        "type": msg.message_type,
                        "content_preview": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in history.get_recent_messages(3)
                ]
            })
        
        return {
            "success": True,
            "ai_features": {
                "context_awareness": "enabled",
                "conversation_history": "enabled",
                "ai_analysis": "enabled",
                "smart_file_management": "enabled"
            },
            "statistics": stats,
            "ai_contexts": ai_contexts,
            "conversation_histories": conversation_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ AI features debug error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/debug/contexts")
@app.get(f"{settings.base_path}/debug/contexts")
async def debug_contexts():
    """
    Debug endpoint สำหรับดู contexts ทั้งหมด - เวอร์ชันขยาย
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
                # AI features
                "ai_confidence": context.ai_confidence,
                "ai_reasoning": context.ai_reasoning,
                "conversation_summary": context.conversation_summary,
                "content_preview": context.processed_content[:200] + "..." if context.processed_content else None
            })
        
        return {
            "success": True,
            "contexts": contexts_data,
            "total": len(contexts_data),
            "ai_powered": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Debug contexts error: {str(e)}")
        return {"success": False, "error": str(e)}


# รันแอปพลิเคชัน
if __name__ == "__main__":
    logger.info("🚀 Starting FastAPI server with AI Context Awareness...")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )