# LINE Bot with Local File Upload System

ระบบ LINE Bot ที่รองรับการอัพโหลดไฟล์และประมวลผลด้วย Google Gemini AI

## ฟีเจอร์หลัก

### 🚀 ระบบหลัก
- **LINE Bot Integration** - เชื่อมต่อกับ LINE Messaging API
- **File Upload System** - รองรับการอัพโหลดไฟล์หลายรูปแบบ
- **AI Processing** - ประมวลผลไฟล์ด้วย Google Gemini AI
- **Web Interface** - หน้าเว็บสำหรับจัดการและทดสอบระบบ

### 📁 รองรับไฟล์
- **รูปภาพ**: JPG, PNG, GIF
- **เอกสาร**: PDF, TXT
- **เสียง**: MP3, WAV, M4A
- **วิดีโอ**: MP4, MOV
- **ขนาดสูงสุด**: 10MB ต่อไฟล์

### 🛠 เทคโนโลยีที่ใช้
- **Backend**: Node.js, Express.js
- **AI**: Google Gemini 2.5 Flash
- **File Upload**: Multer
- **LINE API**: LINE Messaging API
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## การติดตั้งและใช้งาน

### 1. ติดตั้ง Dependencies
```bash
npm install
```

### 2. ตั้งค่า Environment Variables
สร้างไฟล์ `.env` และใส่ค่าต่อไปนี้:

```env
# LINE Bot Configuration
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
CHANNEL_SECRET=your_line_channel_secret

# Google Gemini AI Configuration
API_KEY=your_google_gemini_api_key

# Server Configuration
PORT=3000
NODE_ENV=development

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads

# Security
WEBHOOK_SECRET=your_webhook_secret
```

### 3. เริ่มเซิร์ฟเวอร์
```bash
# Development
npm run dev

# Production
npm start
```

### 4. ตั้งค่า ngrok สำหรับ LINE Webhook
```bash
# ติดตั้ง ngrok
npm install -g ngrok

# เปิด tunnel
ngrok http 3000
```

### 5. ตั้งค่า LINE Developer Console
1. เข้า [LINE Developers Console](https://developers.line.biz/)
2. สร้าง Channel ใหม่หรือเลือก Channel ที่มีอยู่
3. ตั้งค่า Webhook URL: `https://your-ngrok-url.ngrok.io/webhook`
4. เปิดใช้งาน Webhook
5. คัดลอก Channel Access Token และ Channel Secret มาใส่ในไฟล์ `.env`

## โครงสร้างโปรเจค

```
line-bot-project/
├── package.json                 # Dependencies และ scripts
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
├── server.js                   # Main server file
├── config/
│   └── config.js              # Configuration settings
├── controllers/
│   ├── lineController.js      # LINE Bot logic
│   └── uploadController.js    # File upload logic
├── services/
│   ├── request.js            # LINE API service
│   └── gemini.js             # Gemini AI service
├── middleware/
│   └── auth.js               # Authentication middleware
├── routes/
│   ├── upload.js             # Upload routes
│   └── webhook.js            # Webhook routes
├── utils/
│   └── fileHelper.js         # File utility functions
├── uploads/                   # File upload directory
├── public/                   # Static files
│   ├── index.html           # Main web interface
│   ├── css/style.css        # Styles
│   └── js/main.js           # Frontend JavaScript
└── README.md                # This file
```

## API Endpoints

### LINE Webhook
- `POST /webhook` - รับข้อความจาก LINE
- `GET /webhook` - ตรวจสอบสถานะ webhook

### File Upload
- `POST /api/upload/single` - อัพโหลดไฟล์เดี่ยว
- `POST /api/upload/multiple` - อัพโหลดหลายไฟล์
- `GET /api/upload/files` - ดูรายการไฟล์ที่อัพโหลด
- `DELETE /api/upload/cleanup` - ลบไฟล์เก่า

### System
- `GET /health` - ตรวจสอบสถานะระบบ
- `GET /` - หน้าเว็บหลัก

## การใช้งาน

### 1. ผ่าน LINE Bot
1. เพิ่ม Bot เป็นเพื่อนใน LINE
2. ส่งไฟล์หรือข้อความ
3. Bot จะประมวลผลและตอบกลับ

### 2. ผ่าน Web Interface
1. เข้า `http://localhost:3000`
2. เลือกแท็บที่ต้องการ:
   - **อัพโหลดไฟล์**: อัพโหลดไฟล์เดี่ยว
   - **อัพโหลดหลายไฟล์**: อัพโหลดหลายไฟล์พร้อมกัน
   - **ไฟล์ที่อัพโหลด**: ดูรายการไฟล์
   - **สถานะระบบ**: ตรวจสอบสถานะ

## คำสั่ง LINE Bot

### คำสั่งพิเศษ
- `help` หรือ `ช่วย` - แสดงคำแนะนำการใช้งาน
- `status` - แสดงสถานะระบบ
- `info` - แสดงข้อมูลเกี่ยวกับ Bot

### การส่งไฟล์
- ส่งไฟล์ใดๆ ที่รองรับ
- สามารถส่งข้อความพร้อมไฟล์เพื่อให้คำสั่งเฉพาะ
- Bot จะวิเคราะห์และตอบกลับผลลัพธ์

## Security Features

### Authentication
- LINE Signature Validation
- API Key Protection
- Rate Limiting

### File Security
- File Type Validation
- File Size Limits
- Automatic Cleanup
- Secure File Storage

## การปรับแต่ง

### เปลี่ยนขนาดไฟล์สูงสุด
แก้ไขใน `.env`:
```env
MAX_FILE_SIZE=20971520  # 20MB
```

### เปลี่ยนประเภทไฟล์ที่รองรับ
แก้ไขใน `config/config.js`:
```javascript
allowedMimeTypes: [
  'application/pdf',
  'image/jpeg',
  'image/png',
  // เพิ่มประเภทไฟล์ใหม่
]
```

### เปลี่ยน AI Model
แก้ไขใน `services/gemini.js`:
```javascript
this.model = 'gemini-1.5-pro'; // หรือ model อื่นๆ
```

## การแก้ไขปัญหา

### ปัญหาการเชื่อมต่อ LINE
1. ตรวจสอบ Channel Access Token และ Channel Secret
2. ตรวจสอบ Webhook URL ใน LINE Console
3. ตรวจสอบว่า ngrok ทำงานอยู่

### ปัญหาการอัพโหลดไฟล์
1. ตรวจสอบขนาดไฟล์ (ต้องไม่เกิน 10MB)
2. ตรวจสอบประเภทไฟล์ที่รองรับ
3. ตรวจสอบสิทธิ์การเขียนไฟล์ในโฟลเดอร์ uploads

### ปัญหา Gemini AI
1. ตรวจสอบ API Key
2. ตรวจสอบ quota การใช้งาน
3. ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต

## การพัฒนาต่อ

### เพิ่มฟีเจอร์ใหม่
1. Fork หรือ clone โปรเจค
2. สร้าง branch ใหม่
3. เขียนโค้ดและทดสอบ
4. สร้าง pull request

### การปรับปรุงที่แนะนำ
- [ ] Database integration (MongoDB/PostgreSQL)
- [ ] User management system
- [ ] File sharing capabilities
- [ ] Advanced AI conversation
- [ ] Multi-language support
- [ ] Admin dashboard
- [ ] Analytics and logging
- [ ] Cloud storage integration

## License

MIT License - ใช้งานได้อย่างเสรี

## Support

หากมีปัญหาหรือข้อสงสัย:
1. ตรวจสอบ README และ documentation
2. ดู logs ใน console
3. ตรวจสอบ network และ API calls
4. สร้าง issue ใน repository

---

**สร้างด้วย ❤️ โดยใช้ Node.js และ Google Gemini AI**