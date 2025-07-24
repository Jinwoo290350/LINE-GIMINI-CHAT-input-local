"""
Service สำหรับการเชื่อมต่อกับ LINE API
จัดการการส่งข้อความและดาวน์โหลดไฟล์
"""
import httpx
from typing import List, Optional
from config.settings import get_settings
from models.line_models import LineReplyMessage
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class LineService:
    """
    Service สำหรับการติดต่อกับ LINE API
    """
    
    def __init__(self):
        self.channel_access_token = settings.line_channel_access_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        self.api_base = "https://api.line.me/v2/bot"
        self.data_api_base = "https://api-data.line.me/v2/bot"
    
    async def reply_message(self, reply_token: str, messages: List[LineReplyMessage]) -> bool:
        """
        ตอบกลับข้อความใน LINE
        """
        try:
            logger.info(f"📤 Sending reply with token: {reply_token[:10]}...")
            
            messages_data = [msg.dict(exclude_none=True) for msg in messages]
            
            payload = {
                "replyToken": reply_token,
                "messages": messages_data
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_base}/message/reply",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info("✅ Reply sent successfully")
                    return True
                else:
                    logger.error(f"❌ Reply failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Reply error: {str(e)}")
            return False
    
    async def push_message(self, user_id: str, messages: List[LineReplyMessage]) -> bool:
        """
        ส่งข้อความแบบ Push ไปยังผู้ใช้
        """
        try:
            logger.info(f"📤 Pushing message to user: {user_id[:10]}...")
            
            messages_data = [msg.dict(exclude_none=True) for msg in messages]
            
            payload = {
                "to": user_id,
                "messages": messages_data
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_base}/message/push",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info("✅ Push message sent successfully")
                    return True
                else:
                    logger.error(f"❌ Push failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Push error: {str(e)}")
            return False
    
    async def show_loading(self, user_id: str) -> bool:
        """
        แสดง loading indicator ใน LINE
        """
        try:
            payload = {"chatId": user_id}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/loading/start",
                    headers=self.headers,
                    json=payload
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.warning(f"⚠️ Loading indicator failed: {str(e)}")
            return False
    
    async def get_message_content(self, message_id: str) -> Optional[bytes]:
        """
        ดาวน์โหลดเนื้อหาของข้อความ (ไฟล์)
        """
        try:
            logger.info(f"📥 Downloading content for message: {message_id}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.data_api_base}/message/{message_id}/content",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    logger.info("✅ Content downloaded successfully")
                    return response.content
                else:
                    logger.error(f"❌ Download failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Download error: {str(e)}")
            return None


# สร้าง singleton instance
line_service = LineService()