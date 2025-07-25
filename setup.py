#!/usr/bin/env python3
"""
Setup Script สำหรับ LINE Bot AI Assistant
ช่วยในการติดตั้งและตั้งค่าโปรเจ็กต์
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """ตรวจสอบเวอร์ชัน Python"""
    print("🐍 ตรวจสอบเวอร์ชัน Python...")
    
    if sys.version_info < (3, 9):
        print("❌ โปรเจ็กต์นี้ต้องการ Python 3.9 หรือสูงกว่า")
        print(f"📍 เวอร์ชันปัจจุบัน: Python {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def create_virtual_environment():
    """สร้าง Virtual Environment"""
    print("\n🔧 สร้าง Virtual Environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("⚠️ Virtual Environment มีอยู่แล้ว")
        response = input("ต้องการสร้างใหม่หรือไม่? (y/N): ")
        if response.lower() == 'y':
            print("🗑️ ลบ Virtual Environment เก่า...")
            shutil.rmtree(venv_path)
        else:
            print("⏭️ ข้ามการสร้าง Virtual Environment")
            return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ สร้าง Virtual Environment เรียบร้อย")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ สร้าง Virtual Environment ไม่สำเร็จ: {e}")
        return False


def get_venv_python():
    """หา path ของ Python ใน Virtual Environment"""
    if os.name == 'nt':  # Windows
        return Path("venv/Scripts/python.exe")
    else:  # Unix/Linux/macOS
        return Path("venv/bin/python")


def install_requirements():
    """ติดตั้ง Dependencies"""
    print("\n📦 ติดตั้ง Dependencies...")
    
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ ไม่พบ Virtual Environment")
        return False
    
    try:
        # อัปเกรด pip ก่อน
        subprocess.run([
            str(venv_python), "-m", "pip", "install", "--upgrade", "pip"
        ], check=True)
        
        # ติดตั้ง dependencies
        subprocess.run([
            str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        
        print("✅ ติดตั้ง Dependencies เรียบร้อย")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ติดตั้ง Dependencies ไม่สำเร็จ: {e}")
        return False


def create_env_file():
    """สร้างไฟล์ .env"""
    print("\n⚙️ สร้างไฟล์ .env...")
    
    env_path = Path(".env")
    if env_path.exists():
        print("⚠️ ไฟล์ .env มีอยู่แล้ว")
        response = input("ต้องการสร้างใหม่หรือไม่? (y/N): ")
        if response.lower() != 'y':
            print("⏭️ ข้ามการสร้างไฟล์ .env")
            return True
    
    env_template = '''# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here

# Google Gemini AI Configuration
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Server Configuration
APP_NAME=LINE Bot AI Assistant
APP_VERSION=1.0.0
DEBUG=True
HOST=0.0.0.0
PORT=8000
BASE_PATH=/axons-test

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
WEBHOOK_SECRET=your-webhook-secret-key-change-this

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
'''
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_template)
        
        print("✅ สร้างไฟล์ .env เรียบร้อย")
        print("📝 กรุณาแก้ไขค่า configuration ในไฟล์ .env")
        return True
    except Exception as e:
        print(f"❌ สร้างไฟล์ .env ไม่สำเร็จ: {e}")
        return False


def create_directories():
    """สร้างโฟลเดอร์ที่จำเป็น"""
    print("\n📁 สร้างโฟลเดอร์ที่จำเป็น...")
    
    directories = ["uploads", "logs", "static", "templates"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ สร้างโฟลเดอร์: {directory}")
        else:
            print(f"📁 โฟลเดอร์มีอยู่แล้ว: {directory}")
    
    # สร้างไฟล์ .gitkeep ในโฟลเดอร์ uploads
    gitkeep_path = Path("uploads/.gitkeep")
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print("✅ สร้าง uploads/.gitkeep")
    
    return True


def check_dependencies():
    """ตรวจสอบ Dependencies เพิ่มเติม"""
    print("\n🔍 ตรวจสอบ Dependencies...")
    
    optional_deps = {
        "ngrok": "สำหรับทดสอบ webhook ในเครื่อง",
        "git": "สำหรับ version control"
    }
    
    for dep, description in optional_deps.items():
        if shutil.which(dep):
            print(f"✅ {dep} - {description}")
        else:
            print(f"⚠️ {dep} ไม่พบ - {description}")
    
    return True


def show_next_steps():
    """แสดงขั้นตอนถัดไป"""
    print("\n" + "="*60)
    print("🎉 การติดตั้งเสร็จสิ้น!")
    print("="*60)
    
    print("\n📋 ขั้นตอนถัดไป:")
    print("1. แก้ไขไฟล์ .env และใส่ค่า configuration ที่ถูกต้อง:")
    print("   - LINE_CHANNEL_ACCESS_TOKEN")
    print("   - LINE_CHANNEL_SECRET") 
    print("   - GOOGLE_API_KEY")
    
    print("\n2. เปิดใช้งาน Virtual Environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")
    
    print("\n3. รันแอปพลิเคชัน:")
    print("   python main.py")
    
    print("\n4. สำหรับการทดสอบ webhook:")
    print("   - ติดตั้ง ngrok: https://ngrok.com/")
    print("   - รันคำสั่ง: ngrok http 8000")
    print("   - ใช้ URL ที่ได้ตั้งค่าใน LINE Developer Console")
    
    print("\n🌐 เข้าถึงแอปพลิเคชัน:")
    print("   - Web Interface: http://localhost:8000/axons-test/")
    print("   - Health Check: http://localhost:8000/axons-test/health")
    print("   - API Docs: http://localhost:8000/docs")
    
    print("\n📚 เอกสารประกอบ:")
    print("   - README.md - คู่มือการใช้งานละเอียด")
    print("   - /debug/contexts - ดู context การสนทนา")
    print("   - /debug/system-stats - สถิติระบบ")


def main():
    """ฟังก์ชันหลัก"""
    print("🚀 Setup Script สำหรับ LINE Bot AI Assistant")
    print("="*60)
    
    # ตรวจสอบเวอร์ชัน Python
    if not check_python_version():
        sys.exit(1)
    
    # สร้าง Virtual Environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # ติดตั้ง Dependencies
    if not install_requirements():
        sys.exit(1)
    
    # สร้างไฟล์ .env
    if not create_env_file():
        sys.exit(1)
    
    # สร้างโฟลเดอร์
    if not create_directories():
        sys.exit(1)
    
    # ตรวจสอบ Dependencies เพิ่มเติม
    check_dependencies()
    
    # แสดงขั้นตอนถัดไป
    show_next_steps()


if __name__ == "__main__":
    main()