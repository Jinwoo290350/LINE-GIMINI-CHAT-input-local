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
            file_upload.file_path,
            5
        )
        
        return JSONResponse(content={
            "success": True,
            "response": ai_response.text,
            "fileInfo": {
                "name": file_metadata.name if file_metadata else file_upload.filename,
                "size": file_service.format_file_size(file_upload.size),
                "type": file_metadata.extension if file_metadata else "unknown"
            },
            "processingTime": ai_response.processing_time
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Single upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiple")
async def upload_multiple_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    prompt: str = Form("อธิบายเนื้อหาของไฟล์เหล่านี้")
):
    """
    อัพโหลดและประมวลผลหลายไฟล์
    """
    try:
        logger.info(f"📤 Processing multiple files upload: {len(files)} files")
        
        if len(files) > 5:
            raise HTTPException(
                status_code=400,
                detail="Too many files. Maximum 5 files allowed"
            )
        
        uploaded_files = []
        files_info = []
        
        # อัพโหลดแต่ละไฟล์
        for file in files:
            # ตรวจสอบไฟล์
            if not _is_allowed_file(file.filename):
                continue  # ข้ามไฟล์ที่ไม่รองรับ
            
            content = await file.read()
            if len(content) > settings.max_file_size:
                continue  # ข้ามไฟล์ที่ใหญ่เกินไป
            
            await file.seek(0)
            
            # บันทึกไฟล์
            file_upload = await file_service.save_upload_file(file)
            uploaded_files.append(file_upload.file_path)
            
            # เก็บข้อมูลไฟล์
            file_metadata = file_service.get_file_metadata(file_upload.file_path)
            files_info.append({
                "name": file_metadata.name if file_metadata else file_upload.filename,
                "size": file_service.format_file_size(file_upload.size),
                "type": file_metadata.extension if file_metadata else "unknown"
            })
        
        if not uploaded_files:
            raise HTTPException(
                status_code=400,
                detail="No valid files to process"
            )
        
        # ประมวลผลไฟล์แรก (สำหรับการ demo)
        ai_response = await gemini_service.process_file(uploaded_files[0], prompt)
        
        # ลบไฟล์ทั้งหมดใน background
        for file_path in uploaded_files:
            background_tasks.add_task(_delayed_file_cleanup, file_path, 5)
        
        return JSONResponse(content={
            "success": True,
            "response": ai_response.text,
            "filesInfo": files_info,
            "processingTime": ai_response.processing_time
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Multiple upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def get_uploaded_files():
    """
    ดึงรายการไฟล์ที่อัพโหลด
    """
    try:
        files = file_service.list_uploaded_files()
        
        files_data = []
        for file_metadata in files:
            files_data.append({
                "name": file_metadata.name,
                "size": file_service.format_file_size(file_metadata.size),
                "type": file_metadata.type,
                "created": file_metadata.created_at.isoformat(),
                "modified": file_metadata.modified_at.isoformat()
            })
        
        return JSONResponse(content={
            "success": True,
            "files": files_data,
            "total": len(files_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Files list error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_files(api_key: str = None):
    """
    ลบไฟล์เก่า
    """
    try:
        # ตรวจสอบ API key
        if api_key != settings.webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        deleted_count = file_service.cleanup_old_files()
        
        return JSONResponse(content={
            "success": True,
            "message": f"ลบไฟล์เก่า {deleted_count} ไฟล์เรียบร้อย",
            "deletedCount": deleted_count
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _is_allowed_file(filename: str) -> bool:
    """
    ตรวจสอบว่าไฟล์ได้รับอนุญาตหรือไม่
    """
    if not filename:
        return False
    
    import os
    extension = os.path.splitext(filename)[1].lower()
    return extension in settings.allowed_extensions


async def _delayed_file_cleanup(file_path: str, delay_seconds: int):
    """
    ลบไฟล์หลังจากหน่วงเวลา
    """
    import asyncio
    await asyncio.sleep(delay_seconds)
    file_service.delete_file(file_path)