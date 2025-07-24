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
                self.model