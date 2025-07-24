"""
Router สำหรับการอัพโหลดไฟล์
จัดการการอัพโหลดและประมวลผลไฟล์ผ่าน Web Interface
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
from config.settings import get_settings
from services.file_service import file_service
from services.gemini_service import gemini_service
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/single")
async def upload_single_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: str = Form("อธิบายเนื้อหาของไฟล์นี้")
):
    """
    อัพโหลดและประมวลผลไฟล์เดี่ยว
    """
    try:
        logger.info(f"📤 Processing single file upload: {file.filename}")
        
        # ตรวจสอบประเภทไฟล์
        if not _is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {', '.join(settings.allowed_extensions)}"
            )
        
        # ตรวจสอบขนาดไฟล์
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size too large. Maximum: {settings.max_file_size} bytes"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # บันทึกไฟล์
        file_upload = await file_service.save_upload_file(file)
        
        # ประมวลผลด้วย AI
        ai_response = await gemini_service.process_file(file_upload.file_path, prompt)
        
        # ดึงข้อมูลไฟล์
        file_metadata = file_service.get_file_metadata(file_upload.file_path)
        
        # ลบไฟล์ใน background (หลังจาก 5 วินาที)
        background_tasks.add_task(
            _delayed_file_cleanup,
            file_upload.file_path# 🐍 Python LINE Bot - แยกไฟล์ทีละไฟล์

## 📁 โครงสร้างโปรเจค