"""
Helper functions สำหรับการจัดการไฟล์
รวม utility functions สำหรับการทำงานกับไฟล์
"""
import os
import mimetypes
from typing import Tuple
from pathlib import Path
from datetime import datetime


class FileHelper:
    """
    Helper class สำหรับการจัดการไฟล์
    """
    
    @staticmethod
    def generate_filename(original_name: str, extension: str = None) -> str:
        """
        สร้างชื่อไฟล์ใหม่ที่ไม่ซ้ำ
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        
        if extension:
            ext = extension
        else:
            ext = os.path.splitext(original_name)[1]
        
        name = os.path.splitext(original_name)[0]
        return f"{timestamp}_{random_suffix}_{name}{ext}"
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """
        ดึงประเภทไฟล์จาก path
        """
        ext = os.path.splitext(file_path)[1].lower()
        type_mapping = {
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
            '.pdf': 'document', '.txt': 'document',
            '.mp3': 'audio', '.wav': 'audio', '.m4a': 'audio',
            '.mp4': 'video', '.mov': 'video'
        }
        return type_mapping.get(ext, 'unknown')
    
    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """
        ดึง MIME type ของไฟล์
        """
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or 'application/octet-stream'
        except:
            return 'application/octet-stream'
    
    @staticmethod
    def validate_file_size(file_path: str, max_size: int) -> bool:
        """
        ตรวจสอบขนาดไฟล์
        """
        try:
            file_size = os.path.getsize(file_path)
            return file_size <= max_size
        except:
            return False
    
    @staticmethod
    def is_safe_path(file_path: str, base_dir: str) -> bool:
        """
        ตรวจสอบว่า path ปลอดภัยหรือไม่ (ป้องกัน path traversal)
        """
        try:
            resolved_path = os.path.realpath(file_path)
            resolved_base = os.path.realpath(base_dir)
            return resolved_path.startswith(resolved_base)
        except:
            return False
    
    @staticmethod
    def create_directory_if_not_exists(dir_path: str) -> bool:
        """
        สร้างโฟลเดอร์หากไม่มี
        """
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except:
            return False