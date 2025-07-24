"""
ตั้งค่า Logging สำหรับแอปพลิเคชัน
ใช้ structlog และ rich สำหรับ logging ที่สวยงาม
"""
import logging
import sys
from pathlib import Path
import structlog
from rich.logging import RichHandler
from rich.console import Console
from config.settings import get_settings

settings = get_settings()

# สร้าง console สำหรับ rich
console = Console(color_system="auto")


def setup_logging():
    """
    ตั้งค่า logging configuration
    """
    # สร้างโฟลเดอร์ logs หากไม่มี
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # กำหนดระดับ logging
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # ตั้งค่า standard logging
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True
            )
        ]
    )
    
    # ตั้งค่า structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.debug 
            else structlog.dev.ConsoleRenderer(colors=True)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # เพิ่ม file handler สำหรับบันทึกลง log file
    file_handler = logging.FileHandler(settings.log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # เพิ่ม file handler ให้กับ root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # ปิด logging ของ libraries ที่มีเสียงดังเกินไป
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    ดึง logger instance
    """
    return structlog.get_logger(name)


# ตั้งค่า logging เมื่อ import module นี้
setup_logging()