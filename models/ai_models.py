"""
Pydantic Models สำหรับ AI และการประมวลผล
ใช้สำหรับ request/response ของ AI services
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """คำขอไปยัง AI"""
    prompt: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    intent: Optional[str] = None


class AIResponse(BaseModel):
    """ผลตอบกลับจาก AI"""
    text: str
    success: bool = True
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


class IntentAnalysis(BaseModel):
    """การวิเคราะห์ความตั้งใจของผู้ใช้"""
    intent_type: Literal["translate", "summarize", "analyze", "extract_text", "transcribe", "general"]
    confidence: float = Field(ge=0.0, le=1.0)
    parameters: dict = Field(default_factory=dict)
    
    @classmethod
    def analyze_intent(cls, text: str) -> "IntentAnalysis":
        """วิเคราะห์ความตั้งใจจากข้อความ"""
        text_lower = text.lower()
        
        # การวิเคราะห์ความตั้งใจแบบง่าย
        if any(word in text_lower for word in ["แปล", "translate"]):
            return cls(intent_type="translate", confidence=0.9)
        elif any(word in text_lower for word in ["สรุป", "summarize"]):
            return cls(intent_type="summarize", confidence=0.9)
        elif any(word in text_lower for word in ["วิเคราะห์", "analyze"]):
            return cls(intent_type="analyze", confidence=0.9)
        elif any(word in text_lower for word in ["อ่าน", "ข้อความ", "extract", "text"]):
            return cls(intent_type="extract_text", confidence=0.8)
        elif any(word in text_lower for word in ["เสียง", "transcribe"]):
            return cls(intent_type="transcribe", confidence=0.8)
        else:
            return cls(intent_type="general", confidence=0.5)