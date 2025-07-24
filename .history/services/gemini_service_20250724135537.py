"""
Service สำหรับการเชื่อมต่อกับ Google Gemini AI
จัดการการประมวลผลไฟล์และการสนทนา
"""
import google.generativeai as genai
import asyncio
import time
from typing import Optional
from pathlib import Path
from config.settings import get_settings
from models.ai_models import AIResponse, IntentAnalysis
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# กำหนดค่า Gemini API
genai.configure(api_key=settings.google_api_key)


class GeminiService:
    """
    Service สำหรับการติดต่อกับ Google Gemini AI
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def generate_text(self, prompt: str) -> AIResponse:
        """
        สร้างข้อความตอบกลับจาก AI
        """
        start_time = time.time()
        
        try:
            logger.info(f"🤖 Generating text for prompt: {prompt[:50]}...")
            
            # รัน generation ใน thread pool เพื่อไม่ให้ block async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.model.generate_content, 
                prompt
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Text generated in {processing_time:.2f}s")
            
            return AIResponse(
                text=response.text,
                success=True,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Text generation failed: {str(e)}")
            
            return AIResponse(
                text="ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผล",
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    async def process_file(self, file_path: str, prompt: str) -> AIResponse:
        """
        ประมวลผลไฟล์ด้วย AI
        """
        start_time = time.time()
        
        try:
            logger.info(f"📁 Processing file: {file_path}")
            
            # ตรวจสอบไฟล์
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # อัพโหลดไฟล์ไปยัง Gemini
            loop = asyncio.get_event_loop()
            file_part = await loop.run_in_executor(
                None,
                genai.upload_file,
                file_path
            )
            
            # รอให้ไฟล์ประมวลผลเสร็จ
            await self._wait_for_file_processing(file_part)
            
            # สร้างคำตอบ
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                [prompt, file_part]
            )
            
            # ลบไฟล์จาก Gemini
            await loop.run_in_executor(
                None,
                genai.delete_file,
                file_part.name
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ File processed in {processing_time:.2f}s")
            
            return AIResponse(
                text=response.text,
                success=True,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ File processing failed: {str(e)}")
            
            return AIResponse(
                text="ขออภัยครับ ไม่สามารถประมวลผลไฟล์ได้",
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    async def _wait_for_file_processing(self, file_part, max_wait: int = 30):
        """
        รอให้ไฟล์ประมวลผลเสร็จ
        """
        wait_time = 0
        while file_part.state.name == "PROCESSING" and wait_time < max_wait:
            await asyncio.sleep(1)
            wait_time += 1
            
            # รีเฟรชสถานะไฟล์
            loop = asyncio.get_event_loop()
            file_part = await loop.run_in_executor(
                None,
                genai.get_file,
                file_part.name
            )
        
        if file_part.state.name != "ACTIVE":
            raise Exception(f"File processing failed: {file_part.state.name}")
    
    def create_prompt_from_intent(self, intent: str, file_type: str) -> str:
        """
        สร้าง prompt ตามความตั้งใจของผู้ใช้
        """
        intent_analysis = IntentAnalysis.analyze_intent(intent)
        
        if intent_analysis.intent_type == "translate":
            return "แปลข้อความทั้งหมดในไฟล์นี้เป็นภาษาไทย หากมีข้อความหลายภาษาให้แปลทั้งหมด"
        elif intent_analysis.intent_type == "summarize":
            return "สรุปเนื้อหาสำคัญของไฟล์นี้ให้กระชับและเข้าใจง่าย"
        elif intent_analysis.intent_type == "analyze":
            return "วิเคราะห์และอธิบายเนื้อหาของไฟล์นี้อย่างละเอียด"
        elif intent_analysis.intent_type == "extract_text":
            if file_type == "image":
                return "อ่านข้อความทั้งหมดที่มีในรูปภาพนี้ และจัดรูปแบบให้อ่านง่าย"
            else:
                return "อ่านและแสดงเนื้อหาทั้งหมดในไฟล์นี้"
        elif intent_analysis.intent_type == "transcribe" and file_type == "audio":
            return "แปลงเสียงเป็นข้อความและสรุปเนื้อหาที่พูด"
        else:
            return f"ต่อไปนี้คือความต้องการของผู้ใช้: \"{intent}\"\n\nกรุณาประมวลผลไฟล์นี้ตามความต้องการที่ระบุ หากไม่สามารถทำได้ให้อธิบายเหตุผลและแนะนำทางเลือกอื่น"
    
    def get_file_type_text(self, file_type: str) -> str:
        """
        แปลงประเภทไฟล์เป็นข้อความภาษาไทย
        """
        type_mapping = {
            "image": "รูปภาพ 🖼️",
            "video": "วิดีโอ 🎥", 
            "audio": "ไฟล์เสียง 🎵",
            "file": "เอกสาร 📄",
            "document": "เอกสาร 📄"
        }
        return type_mapping.get(file_type, "ไฟล์")


# สร้าง singleton instance
gemini_service = GeminiService()