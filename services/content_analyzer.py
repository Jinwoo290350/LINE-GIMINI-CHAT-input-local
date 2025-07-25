"""
Content Analysis Service - เวอร์ชันสุดท้าย
ตรวจจับ Intent และวิเคราะห์เนื้อหาในไฟล์ + ตรวจสอบความเกี่ยวข้องอย่างแม่นยำ
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
    วิเคราะห์เนื้อหาในไฟล์เพื่อตรวจจับ Intent (เวอร์ชันสุดท้าย)
    """
    
    def __init__(self):
        # คำสำคัญสำหรับแต่ละ intent
        self.intent_keywords = {
            "translate": [
                # ภาษาไทย
                "แปล", "translate", "แปลภาษา", "เปลี่ยนภาษา", "แปลเป็น",
                # ภาษาอังกฤษ
                "translate this", "translation", "convert to", "in english", "in thai",
                # ชื่อภาษา
                "english", "thai", "chinese", "japanese", "korean", "ภาษาอังกฤษ", "ภาษาไทย"
            ],
            "summarize": [
                "สรุป", "summary", "summarize", "conclude", "overview", 
                "key points", "main points", "executive summary",
                "บทสรุป", "สาระสำคัญ", "ข้อสรุป", "สรุปใจความ"
            ],
            "analyze": [
                "วิเคราะห์", "analyze", "analysis", "examine", "evaluate",
                "assess", "review", "study", "investigate", "ดู", "ดูให้หน่อย",
                "ตรวจสอบ", "ประเมิน", "ศึกษา", "อธิบาย", "explain"
            ],
            "extract_text": [
                "อ่าน", "read", "extract", "OCR", "text recognition",
                "get text", "read text", "extract text", "อ่านข้อความ",
                "ดึงข้อความ", "อ่านข้อความ", "มีอะไรเขียนไว้", "เขียนว่าอะไร"
            ],
            "calculate": [
                "คำนวณ", "calculate", "compute", "math", "formula",
                "equation", "result", "answer", "solve",
                "หาผลลัพธ์", "แก้สมการ", "รวม", "บวก", "ลบ", "คูณ", "หาร"
            ],
            "explain": [
                "อธิบาย", "explain", "describe", "what is", "how to",
                "why", "because", "reason", "meaning", "คืออะไร",
                "หมายความ", "คืออะไร", "ทำไม", "อย่างไร", "นี่คืออะไร"
            ]
        }
        
        # คำที่บ่งบอกว่าไม่เกี่ยวข้องกับไฟล์/รูปภาพ (ปรับปรุงแล้ว)
        self.general_conversation_keywords = [
            # คำทักทาย
            "สวัสดี", "hello", "hi", "hey", "ดี", "หวัดดี",
            # คำถามทั่วไป
            "อย่างไร", "เป็นไง", "ยังไง", "ไหม", "รึเปล่า",
            # คำถามส่วนตัว
            "คุณ", "you", "เธอ", "ตัวเอง", "ของคุณ", "ของเธอ",
            # หัวข้อทั่วไป - อาหาร (เพิ่มเยอะขึ้น)
            "อากาศ", "weather", "ข่าว", "news", "กิน", "eat", "อาหาร", "food",
            "แนะนำอาหาร", "อาหารเช้า", "อาหารกลางวัน", "อาหารเย็น", "ของกิน",
            "เมนู", "menu", "ร้านอาหาร", "restaurant", "สูตรอาหาร", "recipe",
            "หิว", "hungry", "อร่อย", "delicious", "ทาน", "กิน", "ดื่ม", "drink",
            "ชานมไข่มุก", "bubble tea", "น้ำ", "water", "กาแฟ", "coffee",
            "อยากกิน", "อยากดื่ม", "อยากทาน", "want to eat", "want to drink",
            # เวลาและวัน
            "เวลา", "time", "วัน", "day", "คืน", "night", "เช้า", "morning",
            "กลางวัน", "afternoon", "เย็น", "evening",
            # คำสั่งระบบ
            "help", "ช่วย", "status", "สถานะ", "ทำอะไรได้", "สามารถ",
            # คำถามไม่เกี่ยวข้องกับไฟล์
            "เล่า", "tell", "story", "เรื่อง", "ข่าว", "ความรู้",
            "แนะนำ", "recommend", "suggest", "ชอบ", "like",
            # เพลงและบันเทิง (เพิ่มใหม่)
            "เพลง", "song", "music", "เพลงไทย", "เพลงสากล", "ศิลปิน", "นักร้อง",
            "ฟัง", "listen", "ร้อง", "sing", "บท", "lyrics", "ตามหา",
            "ตามหาเพลง", "หาเพลง", "find song", "search song",
            # เทคโนโลยีและไฟล์ (เพิ่มใหม่)
            "ลบไฟล์", "delete file", "ลบข้อมูล", "clear data", "format",
            "คอมพิวเตอร์", "computer", "มือถือ", "phone", "แอป", "app",
            "ลบ", "delete", "clear", "remove", "ไฟล์เก่า", "old file",
            # คำเชื่อมและคำนำหน้า
            "ต่อไป", "next", "แล้ว", "then", "หลังจากนั้น", "after that"
        ]
        
        # คำที่บ่งบอกถึงการอ้างอิงไฟล์/รูป
        self.file_reference_keywords = [
            # การอ้างอิงไฟล์/รูป
            "รูป", "ภาพ", "image", "picture", "photo", "pic", "ไฟล์", "file",
            "นี่", "this", "นั้น", "that", "เดิม", "เก่า", "ที่ส่งมา", "ที่ส่งไป",
            "ข้างบน", "above", "ข้างล่าง", "below", "ในรูป", "in the image",
            # คำสรรพนาม
            "มัน", "it", "ตัวนี้", "อันนี้", "เจ้านี้", "เจ้านั้น"
        ]
        
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
        ตรวจสอบว่าคำสั่งปัจจุบันเกี่ยวข้องกับไฟล์เดิมหรือไม่ (ปรับปรุงแล้ว)
        """
        if not previous_context:
            return False
        
        # ตรวจสอบ current_intent เป็น string หรือไม่
        if isinstance(current_intent, str):
            user_message = current_intent
        else:
            user_message = str(current_intent)
        
        logger.info(f"🔍 Checking if related - Message: '{user_message}', Previous file: {previous_context.file_type}")
        
        # ถ้าข้อความมีการอ้างอิงไฟล์/รูปชัดเจน → เกี่ยวข้อง
        is_file_reference = self._contains_file_reference(user_message)
        if is_file_reference:
            logger.info("✅ Contains file reference - related")
            return True
        
        # ถ้าข้อความเป็นการสนทนาทั่วไป → ไม่เกี่ยวข้อง
        is_general_conversation = self._is_general_conversation(user_message)
        if is_general_conversation:
            logger.info("❌ General conversation detected - not related")
            return False
        
        # ตรวจสอบ intent ที่เกี่ยวข้องกับการประมวลผลไฟล์
        file_processing_intents = ["translate", "summarize", "analyze", "extract_text", "transcribe"]
        current_intent_type = self._detect_primary_intent(user_message)
        
        if current_intent_type in file_processing_intents:
            # ถ้าเป็น intent ที่เกี่ยวข้องกับไฟล์ และไม่มีการอ้างอิงไฟล์ใหม่
            # ให้ถือว่าเกี่ยวข้องกับไฟล์เดิม
            logger.info(f"✅ File processing intent '{current_intent_type}' - related")
            return True
        
        # ตรวจสอบว่ามีคำสำคัญที่เกี่ยวข้องกับไฟล์เดิมหรือไม่
        previous_intent = previous_context.original_intent
        if current_intent_type == previous_intent:
            logger.info(f"✅ Same intent '{current_intent_type}' - related")
            return True
        
        # ตรวจสอบ related intents
        related_intents = {
            "analyze": ["summarize", "explain", "extract_text"],
            "summarize": ["analyze", "explain"],
            "translate": ["extract_text", "explain"],
            "extract_text": ["translate", "analyze"]
        }
        
        if current_intent_type in related_intents.get(previous_intent, []):
            logger.info(f"✅ Related intent '{current_intent_type}' to '{previous_intent}' - related")
            return True
        
        logger.info(f"❌ No relationship found - not related")
        return False
    
    def _contains_file_reference(self, message: str) -> bool:
        """
        ตรวจสอบว่าข้อความมีการอ้างอิงไฟล์/รูปหรือไม่
        """
        message_lower = message.lower()
        
        for keyword in self.file_reference_keywords:
            if keyword.lower() in message_lower:
                return True
        
        return False
    
    def _is_general_conversation(self, message: str) -> bool:
        """
        ตรวจสอบว่าเป็นการสนทนาทั่วไปหรือไม่
        """
        message_lower = message.lower().strip()
        
        # ตรวจสอบคำทักทายและคำถามทั่วไป
        for keyword in self.general_conversation_keywords:
            if keyword.lower() in message_lower:
                return True
        
        # ตรวจสอบรูปแบบคำถามทั่วไป (ปรับปรุงแล้ว)
        general_patterns = [
            r'^(สวัสดี|hello|hi|hey)',
            r'^(อย่างไร|เป็นไง|ยังไง)',
            r'(อากาศ|weather)',
            r'(ข่าว|news)',
            r'(เวลา|time)',
            r'^(คุณ|you)\s+',
            r'(แนะนำ|recommend)',
            r'(ชอบ|like)\s+อะไร',
            r'^(help|ช่วย)$',
            r'^(status|สถานะ)$',
            # เพิ่ม pattern สำหรับอาหาร
            r'(แนะนำ.*อาหาร|อาหาร.*แนะนำ)',
            r'(อยาก.*กิน|อยาก.*ทาน|อยาก.*ดื่ม)',
            r'(หิว|hungry)',
            r'(เมนู|menu)',
            r'(ร้านอาหาร|restaurant)',
            # เพิ่ม pattern สำหรับเพลง
            r'(เพลง|song|music)',
            r'(ร้อง|sing|ฟัง|listen)',
            r'(ตามหา.*เพลง|หา.*เพลง)',
            # เพิ่ม pattern สำหรับไฟล์ระบบ
            r'(ลบไฟล์|delete.*file)',
            r'(ลบข้อมูล|clear.*data)',
            # เพิ่ม pattern ทั่วไป
            r'^(ต่อไป)',
            r'(บอก|tell).*หน่อย',
            r'(ช่วย|help).*หน่อย'
        ]
        
        for pattern in general_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _detect_primary_intent(self, message: str) -> str:
        """
        ตรวจจับ intent หลักจากข้อความ
        """
        message_lower = message.lower()
        
        # นับคำสำคัญของแต่ละ intent
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    score += 1
            intent_scores[intent] = score
        
        # หา intent ที่มีคะแนนสูงสุด
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])
            if primary_intent[1] > 0:
                return primary_intent[0]
        
        return "general"
    
    def should_clear_context(self, message: str, previous_context) -> bool:
        """
        ตรวจสอบว่าควรลบ context หรือไม่
        """
        if not previous_context:
            return False
        
        # ถ้าเป็นการสนทนาทั่วไป → ลบ context
        if self._is_general_conversation(message):
            logger.info("🗑️ General conversation detected - should clear context")
            return True
        
        # ถ้าไม่เกี่ยวข้องกับไฟล์เดิม → ลบ context
        if not self.is_related_to_previous(message, previous_context):
            logger.info("🗑️ Not related to previous file - should clear context")
            return True
        
        # ถ้า context หมดอายุ → ลบ context
        if previous_context.is_expired:
            logger.info("🗑️ Context expired - should clear context")
            return True
        
        return False


# Singleton instance
content_analyzer = ContentAnalyzer()