"""
Service สำหรับการจัดการไฟล์
จัดการการอัพโหลด บันทึก และลบไฟล์
"""
import os
import aiofiles
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import UploadFile
from config.settings import get_settings
from models.file_models import FileUpload, FileMetadata, PendingFile
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class FileService:
    """
    Service สำหรับการจัดการไฟล์
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.pending_files: Dict[str, PendingFile] = {}
    
    async def save_upload_file(self, file: UploadFile) -> FileUpload:
        """
        บันทึกไฟล์ที่อัพโหลด
        """
        try:
            # สร้างชื่อไฟล์ใหม่
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = os.urandom(4).hex()
            filename = f"{timestamp}_{random_suffix}_{file.filename}"
            file_path = self.upload_dir / filename
            
            # บันทึกไฟล์
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # สร้าง FileUpload object
            file_upload = FileUpload(
                filename=filename,
                original_filename=file.filename,
                content_type=file.content_type,
                size=len(content),
                file_path=str(file_path)
            )
            
            logger.info(f"📁 File saved: {filename} ({file_upload.size} bytes)")
            return file_upload
            
        except Exception as e:
            logger.error(f"❌ File save failed: {str(e)}")
            raise
    
    async def save_binary_content(self, content: bytes, filename: str) -> str:
        """
        บันทึกเนื้อหาไฟล์จาก binary data
        """
        try:
            file_path = self.upload_dir / filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.info(f"📁 Binary content saved: {filename} ({len(content)} bytes)")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Binary save failed: {str(e)}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """
        ลบไฟล์
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ File deleted: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ File deletion failed: {str(e)}")
            return False
    
    def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """
        ดึงข้อมูล metadata ของไฟล์
        """
        try:
            if os.path.exists(file_path):
                return FileMetadata.from_file_path(file_path)
            return None
            
        except Exception as e:
            logger.error(f"❌ Metadata extraction failed: {str(e)}")
            return None
    
    def list_uploaded_files(self) -> List[FileMetadata]:
        """
        ดึงรายการไฟล์ที่อัพโหลด
        """
        try:
            files = []
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file() and file_path.name != '.gitkeep':
                    metadata = self.get_file_metadata(str(file_path))
                    if metadata:
                        files.append(metadata)
            
            # เรียงตามวันที่แก้ไขล่าสุด
            files.sort(key=lambda x: x.modified_at, reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"❌ File listing failed: {str(e)}")
            return []
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        ลบไฟล์เก่า
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            deleted_count = 0
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file() and file_path.name != '.gitkeep':
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_modified < cutoff_time:
                        self.delete_file(str(file_path))
                        deleted_count += 1
            
            logger.info(f"🧹 Cleaned up {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {str(e)}")
            return 0
    
    def add_pending_file(self, user_id: str, message_id: str, file_type: str):
        """
        เพิ่มไฟล์ที่รอการประมวลผล
        """
        pending_file = PendingFile(
            message_id=message_id,
            file_type=file_type,
            user_id=user_id
        )
        self.pending_files[user_id] = pending_file
        logger.info(f"📝 Added pending file for user: {user_id}")
    
    def get_pending_file(self, user_id: str) -> Optional[PendingFile]:
        """
        ดึงไฟล์ที่รอการประมวลผล
        """
        pending_file = self.pending_files.get(user_id)
        if pending_file and pending_file.is_expired:
            # ลบไฟล์ที่หมดอายุ
            del self.pending_files[user_id]
            return None
        return pending_file
    
    def remove_pending_file(self, user_id: str):
        """
        ลบไฟล์ที่รอการประมวลผล
        """
        if user_id in self.pending_files:
            del self.pending_files[user_id]
            logger.info(f"🗑️ Removed pending file for user: {user_id}")
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        แปลงขนาดไฟล์เป็นรูปแบบที่อ่านง่าย
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"


# สร้าง singleton instance
file_service = FileService()