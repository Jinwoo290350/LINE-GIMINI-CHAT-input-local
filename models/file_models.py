"""
Pydantic Models สำหรับการจัดการไฟล์
ใช้สำหรับ validation และ metadata ของไฟล์ + Conversation History
"""
from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, Field, field_validator
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
    
    @field_validator("size")
    @classmethod
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


class ConversationMessage(BaseModel):
    """ข้อความในการสนทนา"""
    timestamp: datetime = Field(default_factory=datetime.now)
    role: Literal["user", "assistant"] = "user"
    content: str
    message_type: Literal["text", "file_upload", "file_analysis"] = "text"
    file_reference: Optional[str] = None


class ConversationHistory(BaseModel):
    """ประวัติการสนทนาทั้งหมด"""
    user_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, message_type: str = "text", file_reference: str = None):
        """เพิ่มข้อความใหม่"""
        message = ConversationMessage(
            role=role,
            content=content,
            message_type=message_type,
            file_reference=file_reference
        )
        self.messages.append(message)
        self.last_updated = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """ดึงข้อความล่าสุด"""
        return self.messages[-limit:] if limit > 0 else self.messages
    
    def clear_history(self):
        """ลบประวัติทั้งหมด"""
        self.messages.clear()
        self.last_updated = datetime.now()
    
    @property
    def is_expired(self) -> bool:
        """หมดอายุหลังจาก 20 นาที"""
        return (datetime.now() - self.last_updated).total_seconds() > 1200


class ConversationContext(BaseModel):
    """บริบทการสนทนาต่อเนื่อง - เวอร์ชันใหม่ที่ใช้ AI"""
    user_id: str
    file_path: str
    file_type: str
    original_intent: str
    processed_content: Optional[str] = None
    detected_intents: List[str] = Field(default_factory=list)
    last_activity: datetime = Field(default_factory=datetime.now)
    interaction_count: int = 0
    
    # ใหม่: AI-powered features
    conversation_summary: Optional[str] = None
    ai_confidence: float = 0.5  # ความมั่นใจของ AI ในการเก็บ context
    ai_reasoning: str = ""  # เหตุผลของ AI
    
    @property
    def is_expired(self) -> bool:
        """หมดอายุหลังจาก 15 นาที (เพิ่มขึ้นจาก 10)"""
        return (datetime.now() - self.last_activity).total_seconds() > 900
    
    @property
    def should_keep_file(self) -> bool:
        """ควรเก็บไฟล์ไว้หรือไม่ - ใช้ AI confidence"""
        return (
            self.ai_confidence > 0.7 or  # AI มั่นใจว่าควรเก็บ
            len(self.detected_intents) > 1 or
            self.interaction_count < 3 or
            not self.is_expired
        )
    
    def update_ai_analysis(self, confidence: float, reasoning: str):
        """อัพเดตผลการวิเคราะห์จาก AI"""
        self.ai_confidence = max(0.0, min(1.0, confidence))  # clamp between 0-1
        self.ai_reasoning = reasoning
        self.last_activity = datetime.now()


class FileContentAnalysis(BaseModel):
    """ผลการวิเคราะห์เนื้อหาไฟล์"""
    detected_intents: List[str] = Field(default_factory=list)
    key_phrases: List[str] = Field(default_factory=list)
    content_summary: str = ""
    suggested_actions: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    
    # ใหม่: AI-based analysis
    ai_analysis: Optional[Dict] = None
    is_related_to_previous: bool = False
    should_clear_context: bool = False


class AIContextAnalysis(BaseModel):
    """ผลการวิเคราะห์บริบทด้วย AI"""
    is_related: bool = False
    confidence: float = 0.0
    reasoning: str = ""
    action: Literal["keep_context", "clear_context", "partial_clear"] = "clear_context"
    related_aspects: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @property
    def should_keep_context(self) -> bool:
        """ควรเก็บ context ไว้หรือไม่"""
        return self.is_related and self.confidence > 0.6
    
    def to_dict(self) -> Dict:
        """แปลงเป็น dictionary"""
        return {
            "is_related": self.is_related,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "action": self.action,
            "related_aspects": self.related_aspects
        }