"""
Middleware สำหรับการยืนยันตัวตน และความปลอดภัย
จัดการการตรวจสอบลายเซ็น LINE และ API keys
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import hmac
import hashlib
import base64
from config.settings import get_settings
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class LineSignatureMiddleware(BaseHTTPMiddleware):
    """
    Middleware สำหรับตรวจสอบลายเซ็น LINE Webhook
    """
    
    async def dispatch(self, request: Request, call_next):
        # ตรวจสอบเฉพาะ webhook endpoint
        if request.url.path.endswith("/webhook") and request.method == "POST":
            signature = request.headers.get("x-line-signature")
            
            if not signature:
                logger.warning("⚠️ Missing LINE signature")
                # ในการพัฒนา อาจปิดการตรวจสอบไว้ชั่วคราว
                if not settings.debug:
                    raise HTTPException(status_code=401, detail="Missing signature")
            else:
                # อ่าน body สำหรับตรวจสอบลายเซ็น
                body = await request.body()
                
                if not self._verify_signature(body, signature):
                    logger.error("❌ Invalid LINE signature")
                    if not settings.debug:
                        raise HTTPException(status_code=401, detail="Invalid signature")
        
        response = await call_next(request)
        return response
    
    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """
        ตรวจสอบลายเซ็น LINE
        """
        try:
            hash_digest = hmac.new(
                settings.line_channel_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
            expected_signature = base64.b64encode(hash_digest).decode('utf-8')
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"❌ Signature verification error: {str(e)}")
            return False


def verify_api_key(api_key: str) -> bool:
    """
    ตรวจสอบ API key
    """
    return api_key == settings.webhook_secret