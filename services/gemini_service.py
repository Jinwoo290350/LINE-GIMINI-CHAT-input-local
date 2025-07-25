"""
Service สำหรับการเชื่อมต่อกับ Google Gemini AI
จัดการการประมวลผลไฟล์และการสนทนา (แก้ไข File Detection)
"""
import google.generativeai as genai
import asyncio
import time
import base64
import mimetypes
from typing import Optional, Tuple
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
    Service สำหรับการติดต่อกับ Google Gemini AI (แก้ไข File Detection)
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # MIME types ที่ Gemini รองรับ
        self.supported_mime_types = {
            # Images
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            # Audio
            'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/mp4',
            # Video  
            'video/mp4', 'video/mpeg', 'video/quicktime', 'video/avi', 'video/x-msvideo',
            # Documents
            'application/pdf', 'text/plain', 'text/html', 'text/css', 'text/javascript',
            'application/json', 'text/csv'
        }
        
        # File signatures สำหรับตรวจสอบประเภทไฟล์ (ปรับปรุงแล้ว)
        self.file_signatures = {
            # Images
            b'\xFF\xD8\xFF': ('image/jpeg', 'image', 'JPEG image'),
            b'\x89PNG\r\n\x1a\n': ('image/png', 'image', 'PNG image'),
            b'GIF87a': ('image/gif', 'image', 'GIF image'),
            b'GIF89a': ('image/gif', 'image', 'GIF image'),
            b'RIFF': ('image/webp', 'image', 'WebP image'),
            b'BM': ('image/bmp', 'image', 'BMP image'),
            
            # Audio - ปรับปรุงการตรวจจับ MP3
            b'ID3': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'\xFF\xFB': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'\xFF\xF3': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'\xFF\xF2': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'\xFF\xE2': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'\xFF\xE3': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'\xFF\xFA': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'\xFF\xF1': ('audio/mpeg', 'audio', 'MP3 audio'),
            b'fLaC': ('audio/flac', 'audio', 'FLAC audio'),
            b'OggS': ('audio/ogg', 'audio', 'OGG audio'),
            
            # Video
            b'\x00\x00\x00\x18ftypmp4': ('video/mp4', 'video', 'MP4 video'),
            b'\x00\x00\x00\x20ftypmp4': ('video/mp4', 'video', 'MP4 video'),
            b'\x00\x00\x00\x1cftypmp4': ('video/mp4', 'video', 'MP4 video'),
            b'ftypqt': ('video/quicktime', 'video', 'QuickTime video'),
            
            # Documents
            b'%PDF': ('application/pdf', 'document', 'PDF document'),
        }
    
    async def generate_text(self, prompt: str) -> AIResponse:
        """
        สร้างข้อความตอบกลับจาก AI
        """
        start_time = time.time()
        
        try:
            logger.info(f"🤖 Generating text for prompt: {prompt[:50]}...")
            
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
            
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # ตรวจสอบประเภทไฟล์ (ปรับปรุงแล้ว)
            file_info = await self._detect_file_type(file_path)
            logger.info(f"📋 File detected: {file_info['type']} - {file_info['mime_type']}")
            
            # ประมวลผลตามประเภทไฟล์
            response_text = await self._process_file_by_type(file_path, prompt, file_info)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ File processed in {processing_time:.2f}s")
            
            return AIResponse(
                text=response_text,
                success=True,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ File processing failed: {str(e)}")
            
            return AIResponse(
                text=f"ขออภัยครับ ไม่สามารถประมวลผลไฟล์ได้\n\n❌ Error: {str(e)}",
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    async def _detect_file_type(self, file_path: str) -> dict:
        """
        ตรวจสอบประเภทไฟล์จาก file signature (ปรับปรุงแล้ว)
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(128)  # อ่านเพิ่มขึ้นเป็น 128 bytes
            
            logger.info(f"🔍 File header: {header[:32].hex()}")
            
            # ตรวจสอบ MP3 แบบพิเศษก่อน (เพิ่มการตรวจสอบ)
            mp3_result = self._detect_mp3_file(header)
            if mp3_result:
                return mp3_result
            
            # ตรวจสอบ file signature ทั่วไป
            for signature, (mime_type, file_type, description) in self.file_signatures.items():
                if header.startswith(signature):
                    # ตรวจสอบพิเศษสำหรับ RIFF files
                    if signature == b'RIFF' and len(header) >= 12:
                        riff_type = header[8:12]
                        if riff_type == b'WAVE':
                            mime_type, file_type = 'audio/wav', 'audio'
                            description = 'WAV audio'
                        elif riff_type == b'WEBP':
                            mime_type, file_type = 'image/webp', 'image'
                            description = 'WebP image'
                        elif riff_type == b'AVI ':
                            mime_type, file_type = 'video/avi', 'video'
                            description = 'AVI video'
                    
                    return {
                        'mime_type': mime_type,
                        'type': file_type,
                        'description': description,
                        'size': Path(file_path).stat().st_size,
                        'supported': mime_type in self.supported_mime_types
                    }
            
            # ตรวจสอบว่าเป็น text file หรือไม่
            text_info = await self._check_if_text_file(file_path, header)
            if text_info:
                return text_info
            
            # ถ้าไม่พบ signature ที่รู้จัก
            return {
                'mime_type': 'application/octet-stream',
                'type': 'unknown',
                'description': 'Unknown binary file',
                'size': Path(file_path).stat().st_size,
                'supported': False
            }
            
        except Exception as e:
            logger.error(f"❌ File detection failed: {str(e)}")
            
            # ใช้ mimetypes เป็น fallback
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                file_type = self._get_type_from_mime(mime_type)
                return {
                    'mime_type': mime_type,
                    'type': file_type,
                    'description': f'{file_type.title()} file (guessed)',
                    'size': Path(file_path).stat().st_size,
                    'supported': mime_type in self.supported_mime_types
                }
            
            raise
    
    def _detect_mp3_file(self, header: bytes) -> Optional[dict]:
        """
        ตรวจจับไฟล์ MP3 แบบละเอียด (เพิ่มใหม่)
        """
        try:
            # ตรวจสอบ ID3 tag (MP3 with metadata)
            if header.startswith(b'ID3'):
                logger.info("🎵 Detected MP3 with ID3 tag")
                return {
                    'mime_type': 'audio/mpeg',
                    'type': 'audio',
                    'description': 'MP3 audio with ID3 tag',
                    'size': 0,  # จะถูกอัพเดตภายหลัง
                    'supported': True
                }
            
            # ตรวจสอบ MPEG audio frame header
            for i in range(min(64, len(header) - 1)):  # ตรวจสอบ 64 bytes แรก
                if i + 1 < len(header):
                    byte1 = header[i]
                    byte2 = header[i + 1]
                    
                    # MPEG audio frame sync (11 bits = 0xFF + 3 bits)
                    if byte1 == 0xFF and (byte2 & 0xE0) == 0xE0:
                        # ตรวจสอบ MPEG version และ layer
                        version = (byte2 & 0x18) >> 3
                        layer = (byte2 & 0x06) >> 1
                        
                        if version != 1 and layer == 1:  # Layer III (MP3)
                            logger.info(f"🎵 Detected MP3 frame at offset {i}")
                            return {
                                'mime_type': 'audio/mpeg',
                                'type': 'audio',
                                'description': 'MP3 audio',
                                'size': 0,  # จะถูกอัพเดตภายหลัง
                                'supported': True
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ MP3 detection failed: {str(e)}")
            return None
    
    async def _check_if_text_file(self, file_path: str, header: bytes) -> Optional[dict]:
        """
        ตรวจสอบว่าเป็นไฟล์ text หรือไม่
        """
        try:
            # ตรวจสอบว่า header มี non-printable characters มากไหม
            printable_chars = sum(1 for b in header[:512] if 32 <= b <= 126 or b in [9, 10, 13])
            total_chars = len(header[:512])
            
            if total_chars > 0 and printable_chars / total_chars > 0.8:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_sample = f.read(1024)
                    
                    return {
                        'mime_type': 'text/plain',
                        'type': 'text',
                        'description': 'Text file',
                        'size': Path(file_path).stat().st_size,
                        'supported': True
                    }
                except UnicodeDecodeError:
                    pass
            
            return None
            
        except Exception:
            return None
    
    def _get_type_from_mime(self, mime_type: str) -> str:
        """
        แปลง MIME type เป็น category
        """
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type in ['application/pdf'] or mime_type.startswith('text/'):
            return 'document'
        else:
            return 'unknown'
    
    async def _process_file_by_type(self, file_path: str, prompt: str, file_info: dict) -> str:
        """
        ประมวลผลไฟล์ตามประเภท
        """
        mime_type = file_info['mime_type']
        file_type = file_info['type']
        
        # อัพเดตขนาดไฟล์
        file_info['size'] = Path(file_path).stat().st_size
        
        logger.info(f"🔄 Processing {file_type} file with MIME type: {mime_type}")
        
        if not file_info['supported']:
            return await self._handle_unsupported_file(file_path, file_info)
        
        try:
            # สำหรับไฟล์ text
            if file_type == 'text' or file_type == 'document':
                return await self._process_text_file(file_path, prompt)
            
            # สำหรับไฟล์อื่นๆ ใช้ base64
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            if len(file_data) > 20 * 1024 * 1024:  # 20MB
                raise Exception("ไฟล์ขนาดใหญ่เกินไป (เกิน 20MB)")
            
            # สำหรับรูปภาพ ลองใช้ PIL ก่อน
            if file_type == 'image':
                pil_result = await self._try_pil_processing(file_path, prompt)
                if pil_result:
                    return pil_result
            
            # ใช้ base64 method
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            content = [
                prompt,
                {
                    "mime_type": mime_type,
                    "data": file_base64
                }
            ]
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                content
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ File processing by type failed: {str(e)}")
            return await self._handle_processing_error(file_path, file_info, str(e))
    
    async def _process_text_file(self, file_path: str, prompt: str) -> str:
        """
        ประมวลผลไฟล์ text
        """
        try:
            encodings = ['utf-8', 'utf-8-sig', 'cp874', 'cp1252', 'iso-8859-1']
            
            content = None
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise Exception("ไม่สามารถอ่านไฟล์ text ได้")
            
            if len(content) > 50000:
                content = content[:50000] + "\n\n[เนื้อหาถูกตัดทอน...]"
            
            combined_prompt = f"""{prompt}

เนื้อหาไฟล์:
{content}"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                combined_prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Text file processing failed: {str(e)}")
            raise
    
    async def _try_pil_processing(self, file_path: str, prompt: str) -> Optional[str]:
        """
        ลองประมวลผลรูปภาพด้วย PIL
        """
        try:
            import PIL.Image
            
            loop = asyncio.get_event_loop()
            
            image = await loop.run_in_executor(None, PIL.Image.open, file_path)
            
            if image.size[0] * image.size[1] > 10000000:  # 10M pixels
                image = await loop.run_in_executor(None, self._resize_image, image)
            
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                [prompt, image]
            )
            
            logger.info("✅ PIL processing successful")
            return response.text
            
        except ImportError:
            logger.info("ℹ️ PIL not available, using base64 method")
            return None
        except Exception as e:
            logger.warning(f"⚠️ PIL processing failed: {str(e)}, using base64 method")
            return None
    
    def _resize_image(self, image):
        """
        ย่อขนาดรูปภาพ
        """
        from PIL import Image
        max_size = (2048, 2048)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image
    
    async def _handle_unsupported_file(self, file_path: str, file_info: dict) -> str:
        """
        จัดการไฟล์ที่ไม่รองรับ
        """
        file_name = Path(file_path).name
        file_size = self._format_file_size(file_info['size'])
        
        return f"""❌ **ไฟล์ไม่รองรับ**

📄 **ข้อมูลไฟล์:**
- ชื่อ: {file_name}
- ประเภท: {file_info['type']} ({file_info['mime_type']})
- ขนาด: {file_size}

💡 **ไฟล์ที่รองรับ:**
🖼️ รูปภาพ: JPG, PNG, GIF, WebP, BMP
🎵 เสียง: MP3, WAV, FLAC, OGG
🎥 วิดีโอ: MP4, MOV, AVI
📄 เอกสาร: PDF, TXT, HTML, CSV

💡 ลองแปลงไฟล์เป็นรูปแบบที่รองรับแล้วส่งมาใหม่ครับ"""
    
    async def _handle_processing_error(self, file_path: str, file_info: dict, error: str) -> str:
        """
        จัดการ error ในการประมวลผล
        """
        file_name = Path(file_path).name
        file_size = self._format_file_size(file_info['size'])
        
        return f"""⚠️ **เกิดข้อผิดพลาดในการประมวลผล**

📄 **ข้อมูลไฟล์:**
- ชื่อ: {file_name}
- ประเภท: {file_info['type']}
- ขนาด: {file_size}

❌ **ข้อผิดพลาด:** {error}

🔧 **วิธีแก้ไข:**
- ตรวจสอบว่าไฟล์ไม่เสียหาย
- ลดขนาดไฟล์หากใหญ่เกินไป
- แปลงเป็นรูปแบบมาตรฐาน
- ลองส่งไฟล์ใหม่อีกครั้ง"""
    
    def _format_file_size(self, size_bytes: int) -> str:
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
    
    def create_prompt_from_intent(self, intent: str, file_type: str) -> str:
        """
        สร้าง prompt ตามความตั้งใจของผู้ใช้
        """
        intent_analysis = IntentAnalysis.analyze_intent(intent)
        
        if intent_analysis.intent_type == "translate":
            return "แปลข้อความทั้งหมดในไฟล์นี้เป็นภาษาไทย หากมีข้อความหลายภาษาให้แปลทั้งหมด รวมถึงข้อความในรูปภาพด้วย"
        elif intent_analysis.intent_type == "summarize":
            return "สรุปเนื้อหาสำคัญของไฟล์นี้ให้กระชับและเข้าใจง่าย อธิบายสิ่งที่เห็นหรือได้ยินในไฟล์"
        elif intent_analysis.intent_type == "analyze":
            return "วิเคราะห์และอธิบายเนื้อหาของไฟล์นี้อย่างละเอียด รวมถึงรายละเอียดที่สำคัญทั้งหมด"
        elif intent_analysis.intent_type == "extract_text":
            if file_type == "image":
                return "อ่านข้อความทั้งหมดที่มีในรูปภาพนี้ และจัดรูปแบบให้อ่านง่าย แม้ข้อความจะเล็กหรือเบลอก็ให้พยายามอ่าน"
            else:
                return "อ่านและแสดงเนื้อหาทั้งหมดในไฟล์นี้"
        elif intent_analysis.intent_type == "transcribe" and file_type == "audio":
            return "แปลงเสียงเป็นข้อความและสรุปเนื้อหาที่พูด พร้อมระบุผู้พูดหากมีหลายคน"
        else:
            return f"""ต่อไปนี้คือความต้องการของผู้ใช้: "{intent}"

กรุณาประมวลผลไฟล์นี้ตามความต้องการที่ระบุ โดย:
1. อธิบายสิ่งที่เห็น ได้ยิน หรืออ่านได้ในไฟล์
2. ดำเนินการตามคำสั่งที่ผู้ใช้ระบุ
3. ให้รายละเอียดที่ครบถ้วนและเป็นประโยชน์
4. หากไม่สามารถทำได้ ให้อธิบายเหตุผลและแนะนำทางเลือกอื่น"""
    
    def get_file_type_text(self, file_type: str) -> str:
        """
        แปลงประเภทไฟล์เป็นข้อความภาษาไทย
        """
        type_mapping = {
            "image": "รูปภาพ 🖼️",
            "video": "วิดีโอ 🎥", 
            "audio": "ไฟล์เสียง 🎵",
            "file": "เอกสาร 📄",
            "document": "เอกสาร 📄",
            "text": "ไฟล์ข้อความ 📝"
        }
        return type_mapping.get(file_type, "ไฟล์")


# สร้าง singleton instance
gemini_service = GeminiService()