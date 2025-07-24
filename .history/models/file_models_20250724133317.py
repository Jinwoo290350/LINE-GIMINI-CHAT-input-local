"""
Pydantic Models สำหรับการจัดการไฟล์
ใช้สำหรับ validation และ metadata ของไฟล์
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
import os


class FileUpload(BaseModel):
    """ข้อมูลไฟล์ที่อัพโหลด"""
    filename: str
    original_filename: str
    content_type: str
    size: int
    upload_time: datetime = Field(default_factory=datetime.now)
    file_path: str
    
    @validator("size")
    def validate_file_size(cls, v):
        """ตรวจสอบขนาดไฟล์"""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f"File size {v} exceeds maximum size {max_size}")
        return v


class FileMetadata(BaseModel):
    """Metadata ของไฟล์"""
    name: str
    size: int
    type: str
    extension: str
    created_at: datetime
    modified_at: datetime
    
    @classmethod
    def from_file_path(cls, file_path: str) -> "FileMetadata":
        """สร้าง metadata จาก file path"""
        stat = os.stat(file_path)
        return cls(
            name=os.path.basename(file_path),
            size=stat.st_size,
            type=cls._get_file_type(file_path),
            extension=os.path.splitext(file_path)[1],
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime)
        )
    
    @staticmethod
    def _get_file_type(file_path: str) -> str:
        """กำหนดประเภทไฟล์จาก extension"""
        ext = os.path.splitext(file_path)[1].lower()
        type_mapping = {
            ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image",
            ".pdf": "document", ".txt": "document",
            ".mp3": "audio", ".wav": "audio", ".m4a": "audio",
            ".mp4": "video", ".mov": "video"
        }
        return type_mapping.get(ext, "unknown")


class PendingFile(BaseModel):
    """ไฟล์ที่รอการประมวลผล"""
    message_id: str
    file_type: Literal["image", "video", "audio", "file"]
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str
    
    @property
    def is_expired(self) -> bool:
        """ตรวจสอบว่าไฟล์หมดอายุหรือไม่ (10 นาที)"""
        return (datetime.now() - self.timestamp).total_seconds() > 600