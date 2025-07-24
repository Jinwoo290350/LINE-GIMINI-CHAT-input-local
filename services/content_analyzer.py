"""
Content Analysis Service
ตรวจจับ Intent และวิเคราะห์เนื้อหาในไฟล์
"""
import re
from typing import List, Dict, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class FileContentAnalysis:
    """ผลการวิเคราะห์เนื้อหาไฟล์"""
    def __init__(self):
        self.detected_intents: List[str] = []
        self.key_phrases: List[str] = []
        self.content_summary: str = ""
        self.suggested_actions: List[str] = []
        self.confidence_score: float = 0.0


class ContentAnalyzer:
    """
    วิเคราะห์เนื้อหาในไฟล์เพื่อตรวจจับ Intent
    """
    
    def __init__(self):
        # คำสำคัญสำหรับแต่ละ intent
        self.intent_keywords = {
            "translate": [
                # ภาษาไทย
                "แปล", "translate", "แปลภาษา", "เปลี่ยนภาษา",
                # ภาษาอังกฤษ
                "translate this", "translation", "convert to", "in english", "in thai",
                # ชื่อภาษา
                "english", "thai", "chinese", "japanese", "korean"
            ],
            "summarize": [
                "สรุป", "summary", "summarize", "conclude", "overview", 
                "key points", "main points", "executive summary",
                "บทสรุป", "สาระสำคัญ", "ข้อสรุป"
            ],
            "analyze": [
                "วิเคราะห์", "analyze", "analysis", "examine", "evaluate",
                "assess", "review", "study", "investigate",
                "ตรวจสอบ", "ประเมิน", "ศึกษา"
            ],
            "extract_text": [
                "อ่าน", "read", "extract", "OCR", "text recognition",
                "get text", "read text", "extract text",
                "ดึงข้อความ", "อ่านข้อความ"
            ],
            "calculate": [
                "คำนวณ", "calculate", "compute", "math", "formula",
                "equation", "result", "answer", "solve",
                "หาผลลัพธ์", "แก้สมการ"
            ],
            "explain": [
                "อธิบาย", "explain", "describe", "what is", "how to",
                "why", "because", "reason", "meaning",
                "หมายความ", "คืออะไร", "ทำไม"
            ]
        }
        
        # Pattern สำหรับตรวจจับคำสั่งในรูปแบบต่างๆ
        self.command_patterns = [
            r"please\s+(.*)",
            r"can\s+you\s+(.*)",
            r"กรุณา(.*)",
            r"ช่วย(.*)",
            r"ต้องการ(.*)",
            r"(.*)\s*please",
            r"(.*)\s*ครับ",
            r"(.*)\s*ค่ะ"
        ]
    
    def analyze_content(self, content: str, file_type: str) -> FileContentAnalysis:
        """
        วิเคราะห์เนื้อหาหลักของไฟล์
        """
        try:
            logger.info(f"🔍 Analyzing content for file type: {file_type}")
            
            analysis = FileContentAnalysis()
            analysis.detected_intents = self._detect_intents(content)
            analysis.key_phrases = self._extract_key_phrases(content)
            analysis.suggested_actions = self._suggest_actions(analysis.detected_intents, analysis.key_phrases, file_type)
            analysis.confidence_score = self._calculate_confidence(analysis.detected_intents, analysis.key_phrases)
            analysis.content_summary = self._create_summary(content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Content analysis failed: {str(e)}")
            return FileContentAnalysis()
    
    def _detect_intents(self, content: str) -> List[str]:
        """
        ตรวจจับ Intent จากเนื้อหา
        """
        content_lower = content.lower()
        detected_intents = []
        
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    if intent not in detected_intents:
                        detected_intents.append(intent)
                    break
        
        return detected_intents
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        """
        ดึงวลีสำคัญจากเนื้อหา
        """
        # ลบ special characters และแบ่งเป็นประโยค
        sentences = re.split(r'[.!?]+', content)
        key_phrases = []
        
        for sentence in sentences[:5]:  # เอาแค่ 5 ประโยคแรก
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 100:
                key_phrases.append(sentence)
        
        return key_phrases
    
    def _suggest_actions(self, intents: List[str], phrases: List[str], file_type: str) -> List[str]:
        """
        แนะนำ actions ที่เหมาะสม
        """
        suggestions = []
        
        # แนะนำตาม detected intents
        for intent in intents:
            if intent == "translate":
                suggestions.append("แปลข้อความ")
            elif intent == "summarize":
                suggestions.append("สรุปเนื้อหา")
            elif intent == "analyze":
                suggestions.append("วิเคราะห์รายละเอียด")
            elif intent == "calculate":
                suggestions.append("คำนวณผลลัพธ์")
            elif intent == "explain":
                suggestions.append("อธิบายความหมาย")
        
        # แนะนำตาม file type
        if file_type == "image":
            suggestions.extend(["อ่านข้อความในรูป", "อธิบายรูปภาพ"])
        elif file_type == "audio":
            suggestions.extend(["แปลงเสียงเป็นข้อความ", "สรุปเนื้อหาเสียง"])
        elif file_type == "document":
            suggestions.extend(["สรุปเอกสาร", "ดึงข้อมูลสำคัญ"])
        
        return list(set(suggestions))  # ลบข้อมูลซ้ำ
    
    def _calculate_confidence(self, intents: List[str], phrases: List[str]) -> float:
        """
        คำนวณความมั่นใจในการวิเคราะห์
        """
        confidence = 0.0
        
        # คะแนนจาก detected intents
        confidence += len(intents) * 0.2
        
        # คะแนนจาก key phrases
        confidence += min(len(phrases) * 0.1, 0.5)
        
        # คะแนนพื้นฐาน
        confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _create_summary(self, content: str) -> str:
        """
        สร้างสรุปย่อของเนื้อหา
        """
        # ตัดเนื้อหาแค่ 200 ตัวอักษรแรก
        summary = content[:200].strip()
        if len(content) > 200:
            summary += "..."
        
        return summary
    
    def is_related_to_previous(self, current_intent: str, previous_context) -> bool:
        """
        ตรวจสอบว่าคำสั่งปัจจุบันเกี่ยวข้องกับเดิมหรือไม่
        """
        if not previous_context:
            return False
        
        # ถ้าเป็น intent เดียวกัน
        if current_intent == previous_context.original_intent:
            return True
        
        # ถ้าเป็น intent ที่เกี่ยวข้องกัน
        related_intents = {
            "analyze": ["summarize", "explain", "extract_text"],
            "summarize": ["analyze", "explain"],
            "translate": ["extract_text", "explain"],
            "extract_text": ["translate", "analyze"]
        }
        
        previous_intent = previous_context.original_intent
        if current_intent in related_intents.get(previous_intent, []):
            return True
        
        return False


# Singleton instance
content_analyzer = ContentAnalyzer()