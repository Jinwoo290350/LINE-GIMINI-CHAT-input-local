# 🤖 LINE Bot AI Assistant with Context Awareness

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![LINE](https://img.shields.io/badge/LINE-Bot-00C300.svg)](https://developers.line.biz/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini_AI-4285F4.svg)](https://ai.google.dev/)

Advanced LINE Bot powered by **Google Gemini AI** with intelligent **Context Awareness**, **Smart File Retention**, and **Content-Based Intent Detection** capabilities.

## ✨ Features

### 🧠 **Context Awareness**
- **Smart Conversation Memory**: Remembers files and context across messages
- **Continuous File Processing**: Reprocess files without re-uploading
- **Related Intent Detection**: Understands when commands relate to previous files
- **Automatic Context Cleanup**: Intelligent memory management

### 🔍 **Content-Based Intent Detection**
- **Multi-language Support**: Detects intents in Thai and English
- **Smart Suggestions**: Recommends relevant actions based on file content
- **Pattern Recognition**: Identifies commands within file content
- **Confidence Scoring**: Provides reliability metrics for detections

### 📁 **Advanced File Management**
- **Smart Retention**: Keeps files only when needed
- **Multi-format Support**: Images, PDFs, Audio, Video, Documents
- **Automatic Cleanup**: Prevents disk space issues
- **Background Processing**: Non-blocking file operations

### 🎯 **AI Capabilities**
- **Image Analysis**: OCR, object detection, scene description
- **Document Processing**: Summarization, translation, extraction
- **Audio Transcription**: Speech-to-text with content analysis
- **Multi-modal Understanding**: Combined text, image, and audio processing

### 🌐 **Web Interface**
- **Beautiful UI**: Modern, responsive design
- **File Upload**: Drag-and-drop interface
- **Real-time Processing**: Live status updates
- **System Monitoring**: Health checks and statistics

### 📊 **Monitoring & Debug**
- **Context Visualization**: View active conversations
- **System Statistics**: Resource usage monitoring
- **Debug Endpoints**: Comprehensive debugging tools
- **Structured Logging**: Rich, searchable logs

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- LINE Developer Account
- Google AI API Key
- ngrok (for local development)

### Installation

1. **Clone the repository:**
```bash
git clone <your-repository-url>
cd python-line-bot
```

2. **Create virtual environment:**
```bash
python setup.py

# run .env file kub bro
source venv/bin/activate

```

3. **Run the application:**
```bash
python main.py
```

4. **Setup ngrok for local testing:**
```bash
# In another terminal
ngrok http 8000
# Copy the HTTPS URL for LINE webhook
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Google Gemini AI Configuration
GOOGLE_API_KEY=your_google_gemini_api_key

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
SECRET_KEY=your-super-secret-key-here
WEBHOOK_SECRET=your_webhook_secret

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### LINE Developer Console Setup

1. Create a **Messaging API Channel**
2. Set **Webhook URL**: `https://your-ngrok-url.ngrok.io/axons-test/webhook`
3. Enable **Use webhook**
4. Disable **Auto-reply messages**
5. Get your **Channel Access Token** and **Channel Secret**

## 📂 Project Structure

```
python-line-bot/
├── README.md
├── requirements.txt
├── .env
├── .gitignore
├── main.py                    # FastAPI main application
├── config/
│   └── settings.py           # Pydantic settings management
├── models/
│   ├── __init__.py
│   ├── line_models.py        # LINE API models
│   ├── file_models.py        # File handling models
│   └── ai_models.py          # AI response models
├── services/
│   ├── __init__.py
│   ├── line_service.py       # LINE API service
│   ├── gemini_service.py     # Gemini AI service
│   ├── file_service.py       # File management service
│   └── content_analyzer.py   # Content analysis service
├── routers/
│   ├── __init__.py
│   ├── webhook.py            # LINE webhook routes
│   ├── upload.py             # File upload routes
│   └── debug.py              # Debug endpoints
├── middleware/
│   ├── __init__.py
│   └── auth.py               # Authentication middleware
├── utils/
│   ├── __init__.py
│   ├── logger.py             # Logging configuration
│   └── file_helper.py        # File utility functions
├── templates/
│   └── index.html            # Web interface template
├── static/                   # Static files (CSS, JS, images)
├── uploads/                  # Uploaded files directory
└── logs/                     # Application logs
```

## 💬 Usage Examples

### Basic Conversation
```
👤 User: hello
🤖 Bot: สวัสดีครับ! ผมเป็น AI ผู้ช่วยที่เป็นมิตร...

👤 User: help
🤖 Bot: 🤖 สวัสดีครับ! ผมสามารถช่วยคุณได้ดังนี้...
```

### Context-Aware File Processing
```
👤 User: [Sends image]
🤖 Bot: 📎 ได้รับรูปภาพแล้วครับ! คุณต้องการให้ผมทำอะไร?

👤 User: วิเคราะห์รูปนี้
🤖 Bot: ✨ รูปนี้เป็นเมนูอาหารไทย มีจานหลัก 5 จาน...
      💡 คำแนะนำเพิ่มเติม:
      1. แปลข้อความ
      2. สรุปเนื้อหา

👤 User: แปลเป็นภาษาอังกฤษ  # Uses same file!
🤖 Bot: 🔄 กำลังประมวลผลไฟล์เดิมตามคำสั่งใหม่...
      ✨ Thai Menu Translation: • Pad Thai - Stir-fried noodles...
```

### Smart Intent Detection
```
👤 User: [Sends image with text "Please translate this menu"]
🤖 Bot: 📎 ได้รับรูปภาพแล้วครับ!
      🔍 ตรวจพบคำสั่ง: แปลภาษา
      💡 คำแนะนำ: แปลข้อความ, วิเคราะห์เนื้อหา

👤 User: ทำตามที่เขียนไว้
🤖 Bot: ✨ ตามคำสั่งในรูป - แปลเมนูเป็นภาษาอังกฤษ...
```

## 🌐 Web Interface

Access the web interface at: `http://localhost:8000/axons-test/`

### Features:
- **Single File Upload**: Upload and process individual files
- **Multiple File Upload**: Process multiple files simultaneously  
- **File Management**: View and manage uploaded files
- **System Status**: Monitor system health and performance

## 🔧 API Endpoints

### Health Check
```http
GET /axons-test/health
```

### LINE Webhook
```http
POST /axons-test/webhook
```

### File Upload
```http
POST /axons-test/api/upload/single
POST /axons-test/api/upload/multiple
```

### Debug Endpoints
```http
GET /axons-test/debug/contexts          # View all contexts
GET /axons-test/debug/context/{user_id} # View user context
GET /axons-test/debug/system-stats      # System statistics
POST /axons-test/debug/analyze-intent   # Test intent analysis
```

## 🐛 Troubleshooting

### Common Issues

**1. Webhook not working:**
```bash
# Check if app is running
curl http://localhost:8000/axons-test/health

# Check ngrok status
curl https://your-ngrok-url.ngrok.io/axons-test/webhook
```

**2. Bot not responding:**
```bash
# Check logs
tail -f logs/app.log

# Verify LINE credentials in .env
```

**3. Context not working:**
```bash
# View active contexts
curl http://localhost:8000/axons-test/debug/contexts

# Clear contexts if needed
curl -X POST http://localhost:8000/axons-test/debug/cleanup/contexts
```

**4. File processing errors:**
```bash
# Check file permissions
ls -la uploads/

# Check disk space
df -h

# Check supported file types in .env
```

### Debug Commands

```bash
# Real-time logs
tail -f logs/app.log

# System status
curl http://localhost:8000/axons-test/debug/system-stats

# Test intent analysis
curl -X POST "http://localhost:8000/axons-test/debug/analyze-intent?text=แปลข้อความ"

# Clear all contexts
curl -X POST http://localhost:8000/axons-test/debug/cleanup/contexts
```

## 🧪 Testing

### Manual Testing Checklist

**Context Awareness:**
- [ ] Send file → ask for analysis → ask for translation (should reuse file)
- [ ] Send file → wait 10 minutes → ask question (should expire context)
- [ ] Send file → ask unrelated question → send new file (should clean up)

**Intent Detection:**
- [ ] Send image with "translate" text → should suggest translation
- [ ] Send document with "summary" → should suggest summarization
- [ ] Test multilingual intent detection

**File Management:**
- [ ] Upload large files → check size limits
- [ ] Upload unsupported formats → check error handling
- [ ] Check automatic cleanup after timeout

## 📈 Performance Optimization

### Recommended Settings

**For Production:**
```env
DEBUG=False
LOG_LEVEL=WARNING
MAX_FILE_SIZE=5242880  # 5MB
```

**For Development:**
```env
DEBUG=True
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760  # 10MB
```

### Monitoring

- Use `/debug/system-stats` to monitor resource usage
- Check logs regularly for errors
- Monitor context cleanup frequency
- Watch disk space in uploads directory

## 🚀 Deployment

### Local Development
1. Use ngrok for webhook testing
2. Keep DEBUG=True for detailed logs
3. Use smaller file size limits

### Production Deployment
1. Use proper domain with SSL
2. Set DEBUG=False
3. Configure proper logging
4. Set up file cleanup cron jobs
5. Monitor system resources

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write docstrings for all classes and methods
- Add tests for new features
- Update README for new functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits & Acknowledgments

This project was inspired by and builds upon the excellent work from:

**Original Repository:**
- 📎 [LINE-Chatbot-x-Gemini-Multimodal](https://github.com/jirawatee/LINE-Chatbot-x-Gemini-Multimodal) by [@jirawatee](https://github.com/jirawatee)
- 📰 [Medium Article](https://medium.com/@jirawatee/line-chatbot-x-gemini-multimodal-b4e4f31fa9bc) - Comprehensive guide on LINE Bot development

**Key Enhancements Made:**
- 🧠 **Context Awareness System** - Smart conversation memory
- 🔍 **Content-Based Intent Detection** - AI-powered command recognition  
- ⏳ **Smart File Retention** - Intelligent file lifecycle management
- 📊 **Advanced Monitoring** - Comprehensive debugging and analytics
- 🎨 **Modern Web Interface** - Beautiful, responsive UI
- 🏗️ **Production Architecture** - Scalable FastAPI structure

**Technologies Used:**
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation using Python type hints
- [Google Gemini AI](https://ai.google.dev/) - Advanced multimodal AI capabilities
- [LINE Messaging API](https://developers.line.biz/) - LINE Bot platform
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [Structlog](https://www.structlog.org/) - Structured logging

**Special Thanks:**
- Google AI team for the powerful Gemini API
- LINE Corporation for the comprehensive Bot platform
- FastAPI community for the excellent framework
- All contributors and testers who helped improve this project

## 📞 Support

- 📧 **Email**: [your-email@example.com]
- 💬 **Issues**: [GitHub Issues](https://github.com/Jinwoo290350/LINE-GIMINI-CHAT-input-local/issues)
- 📖 **Documentation**: [Wiki](https://github.com/Jinwoo290350/LINE-GIMINI-CHAT-input-local/wiki)
- 🤝 **Discussions**: [GitHub Discussions](https://github.com/Jinwoo290350/LINE-GIMINI-CHAT-input-local/discussions)

## 📊 Project Status

- ✅ **Core Features**: Complete
- ✅ **Context Awareness**: Implemented
- ✅ **Web Interface**: Functional
- ✅ **Documentation**: Comprehensive
- 🔄 **Testing**: In Progress
- 📋 **Future Features**: Planning

---

**Made with ❤️ using Python, FastAPI, and Google Gemini AI**

*If you find this project helpful, please consider giving it a ⭐ star on GitHub!*