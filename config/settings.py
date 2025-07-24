"""
Pydantic Settings สำหรับการจัดการ Configuration
รวมการตั้งค่าทั้งหมดของแอปพลิเคชัน (Compatible กับ Pydantic v2)
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """
    การตั้งค่าหลักของแอปพลิเคชัน
    ใช้ Pydantic BaseSettings สำหรับ validation
    """
    
    # === ข้อมูลแอปพลิเคชัน ===
    app_name: str = Field("LINE Bot AI Assistant", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # === การตั้งค่าเซิร์ฟเวอร์ ===
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    base_path: str = Field("", env="BASE_PATH")
    
    # === LINE Bot Configuration ===
    line_channel_access_token: str = Field(..., env="LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret: str = Field(..., env="LINE_CHANNEL_SECRET")
    
    # === Google Gemini AI ===
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    
    # === File Upload Settings ===
    max_file_size: int = Field(10485760, env="MAX_FILE_SIZE")  # 10MB
    upload_dir: str = Field("./uploads", env="UPLOAD_DIR")
    
    # === Security ===
    secret_key: str = Field(..., env="SECRET_KEY")
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")
    
    # === Logging ===
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("./logs/app.log", env="LOG_FILE")
    
    @field_validator("upload_dir", mode="after")
    @classmethod
    def create_upload_dir(cls, v: str) -> str:
        """สร้างโฟลเดอร์ upload หากไม่มี"""
        os.makedirs(v, exist_ok=True)
        return v
    
    @field_validator("log_file", mode="after")
    @classmethod
    def create_log_dir(cls, v: str) -> str:
        """สร้างโฟลเดอร์ logs หากไม่มี"""
        log_dir = os.path.dirname(v)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # เพิ่ม field ที่ต้องการ ignore จาก env
        env_ignore_empty=True
    )
    
    # === ตั้งค่า allowed_extensions แยกต่างหาก ===
    @property
    def allowed_extensions(self) -> List[str]:
        """ส่วนขยายไฟล์ที่อนุญาต - ไม่อ่านจาก env"""
        return [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".mp3", ".wav", ".m4a", ".mp4", ".mov"]


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton pattern สำหรับ settings
    ใช้ lru_cache เพื่อไม่ให้โหลดซ้ำ
    """
    return Settings()