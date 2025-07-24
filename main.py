"""
FastAPI Main Application
จุดเริ่มต้นของแอปพลิเคชัน LINE Bot AI Assistant + Context Awareness
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
from routers import webhook, upload
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
    logger.info("🚀 Starting LINE Bot AI Assistant with Context Awareness")
    logger.info(f"📱 App: {settings.app_name} v{settings.app_version}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    
    # ทำความสะอาดไฟล์เก่าเมื่อเริ่มต้น
    deleted_count = file_service.cleanup_old_files()
    logger.info(f"🧹 Cleaned up {deleted_count} old files")
    
    # เริ่ม background task สำหรับ context cleanup
    cleanup_task = asyncio.create_task(cleanup_expired_contexts())
    logger.info("🔄 Started context cleanup background task")
    
    yield
    
    # Shutdown
    logger.info("📴 Shutting down LINE Bot AI Assistant")
    
    # ยกเลิก background task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("🛑 Context cleanup task cancelled")
    
    # ทำความสะอาด contexts ที่เหลือ
    file_service.cleanup_expired_contexts()
    logger.info("🧹 Final context cleanup completed")


# สร้าง FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="LINE Bot AI Assistant with Google Gemini AI integration and Context Awareness",
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
else:
    app.include_router(webhook.router)
    app.include_router(upload.router)


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
    Health Check Endpoint
    ตรวจสอบสถานะแอปพลิเคชันและ services ต่างๆ
    """
    try:
        # ตรวจสอบสถานะระบบ
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # ข้อมูล context management
        active_contexts = len(file_service.conversation_contexts)
        pending_files = len(file_service.pending_files)
        
        return {
            "status": "OK",
            "timestamp": datetime.now().isoformat(),
            "app": {
                "name": settings.app_name,
                "version": settings.app_version,
                "debug": settings.debug
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
                "content_analyzer": "ready"
            },
            "context_management": {
                "active_contexts": active_contexts,
                "pending_files": pending_files
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


@app.get("/debug/contexts")
@app.get(f"{settings.base_path}/debug/contexts")
async def debug_contexts():
    """
    Debug endpoint สำหรับดู contexts ทั้งหมด
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
                "is_expired": context.is_expired
            })
        
        return {
            "success": True,
            "contexts": contexts_data,
            "total": len(contexts_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Debug contexts error: {str(e)}")
        return {"success": False, "error": str(e)}


# รันแอปพลิเคชัน
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )