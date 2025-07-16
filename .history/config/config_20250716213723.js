// ====== PROJECT STRUCTURE ======
/*
line-bot-project/
├── package.json
├── .env
├── .gitignore
├── server.js
├── config/
│   └── config.js
├── controllers/
│   ├── lineController.js
│   └── uploadController.js
├── services/
│   ├── request.js
│   └── gemini.js
├── middleware/
│   └── auth.js
├── routes/
│   ├── upload.js
│   └── webhook.js
├── utils/
│   └── fileHelper.js
├── uploads/
│   └── .gitkeep
├── public/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── README.md
*/

// ====== package.json ======
{
  "name": "line-bot-local-files",
  "version": "1.0.0",
  "description": "LINE Bot with local file upload support and Gemini AI integration",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [
    "line-bot",
    "gemini-ai",
    "file-upload",
    "express",
    "nodejs"
  ],
  "author": "Your Name",
  "license": "MIT",
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.6.0",
    "@google/generative-ai": "^0.21.0",
    "multer": "^1.4.5-lts.1",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.1.5",
    "moment": "^2.29.4"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  },
  "engines": {
    "node": ">=16.0.0",
    "npm": ">=8.0.0"
  }
}

// ====== .env ======
# LINE Bot Configuration
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
CHANNEL_SECRET=your_line_channel_secret_here

# Google Gemini AI Configuration
API_KEY=your_google_gemini_api_key_here

# Server Configuration
PORT=3000
NODE_ENV=development

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads

# Security
WEBHOOK_SECRET=your_webhook_secret_here

// ====== .gitignore ======
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Uploads
uploads/*
!uploads/.gitkeep

# Logs
logs/
*.log

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode/
.idea/

// ====== config/config.js ======
const dotenv = require('dotenv');
dotenv.config();

module.exports = {
  line: {
    channelAccessToken: process.env.CHANNEL_ACCESS_TOKEN,
    channelSecret: process.env.CHANNEL_SECRET,
    webhookSecret: process.env.WEBHOOK_SECRET
  },
  gemini: {
    apiKey: process.env.API_KEY
  },
  server: {
    port: process.env.PORT || 3000,
    env: process.env.NODE_ENV || 'development',
    basePath: process.env.BASE_PATH || ''
  },
  upload: {
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE) || 10485760, // 10MB
    uploadDir: process.env.UPLOAD_DIR || './uploads',
    allowedMimeTypes: [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'image/gif',
      'audio/wav',
      'audio/mp3',
      'audio/x-m4a',
      'video/mp4',
      'video/mov',
      'text/plain'
    ]
  }
};

// ====== server.js ======
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');

const config = require('./config/config');
const uploadRoutes = require('./routes/upload');
const webhookRoutes = require('./routes/webhook');

const app = express();

// Security middleware
app.use(helmet());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// CORS
app.use(cors({
  origin: ['http://localhost:3000', 'https://your-domain.com'],
  credentials: true
}));

// Body parsing middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Create uploads directory if it doesn't exist
const uploadDir = config.upload.uploadDir;
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Routes
app.use('/api/upload', uploadRoutes);
app.use('/webhook', webhookRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    error: config.server.env === 'development' ? err.message : 'Internal server error'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Start server
const port = config.server.port;
app.listen(port, () => {
  console.log(`🚀 Server running on port ${port}`);
  console.log(`📱 Web interface: http://localhost:${port}`);
  console.log(`🔗 LINE Webhook: http://localhost:${port}/webhook`);
  console.log(`🏥 Health check: http://localhost:${port}/health`);
  console.log(`📁 Upload directory: ${uploadDir}`);
});

// ====== services/request.js ======
const axios = require('axios');
const fs = require('fs');
const config = require('../config/config');

const LINE_HEADER = {
  'Content-Type': 'application/json',
  Authorization: `Bearer ${config.line.channelAccessToken}`
};

class RequestService {
  constructor() {
    this.lineApiBase = 'https://api.line.me/v2/bot';
    this.lineDataApi = 'https://api-data.line.me/v2/bot';
  }

  async getBinary(messageId) {
    try {
      return await axios({
        method: 'get',
        headers: LINE_HEADER,
        url: `${this.lineDataApi}/message/${messageId}/content`,
        responseType: 'arraybuffer'
      });
    } catch (error) {
      throw new Error(`Failed to get binary data: ${error.message}`);
    }
  }

  async reply(replyToken, messages) {
    try {
      return await axios({
        method: 'post',
        url: `${this.lineApiBase}/message/reply`,
        headers: LINE_HEADER,
        data: {
          replyToken,
          messages: Array.isArray(messages) ? messages : [messages]
        }
      });
    } catch (error) {
      throw new Error(`Failed to send reply: ${error.message}`);
    }
  }

  async push(to, messages) {
    try {
      return await axios({
        method: 'post',
        url: `${this.lineApiBase}/message/push`,
        headers: LINE_HEADER,
        data: {
          to,
          messages: Array.isArray(messages) ? messages : [messages]
        }
      });
    } catch (error) {
      throw new Error(`Failed to push message: ${error.message}`);
    }
  }

  async showLoading(chatId) {
    try {
      return await axios({
        method: 'post',
        url: `${this.lineApiBase}/chat/loading/start`,
        headers: LINE_HEADER,
        data: { chatId }
      });
    } catch (error) {
      console.warn(`Failed to show loading: ${error.message}`);
    }
  }

  async getProfile(userId) {
    try {
      return await axios({
        method: 'get',
        url: `${this.lineApiBase}/profile/${userId}`,
        headers: LINE_HEADER
      });
    } catch (error) {
      throw new Error(`Failed to get profile: ${error.message}`);
    }
  }

  readLocalFile(filePath) {
    try {
      return fs.readFileSync(filePath);
    } catch (error) {
      throw new Error(`Cannot read file: ${error.message}`);
    }
  }

  saveFile(buffer, fileName) {
    try {
      const uploadDir = config.upload.uploadDir;
      if (!fs.existsSync(uploadDir)) {
        fs.mkdirSync(uploadDir, { recursive: true });
      }
      
      const filePath = `${uploadDir}/${fileName}`;
      fs.writeFileSync(filePath, buffer);
      return filePath;
    } catch (error) {
      throw new Error(`Failed to save file: ${error.message}`);
    }
  }
}

module.exports = new RequestService();

// ====== services/gemini.js ======
const { GoogleGenerativeAI } = require('@google/generative-ai');
const fs = require('fs');
const path = require('path');
const config = require('../config/config');

class GeminiService {
  constructor() {
    this.genAI = new GoogleGenerativeAI(config.gemini.apiKey);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
  }

  isUrl(str) {
    const urlRegex = /^(http(s)?:\/\/)?(www\.)?[a-z0-9]+([-.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/i;
    return urlRegex.test(str);
  }

  getMimeType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
      '.pdf': 'application/pdf',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif',
      '.wav': 'audio/wav',
      '.mp3': 'audio/mp3',
      '.m4a': 'audio/x-m4a',
      '.mp4': 'video/mp4',
      '.mov': 'video/mov',
      '.txt': 'text/plain'
    };
    return mimeTypes[ext] || 'application/octet-stream';
  }

  isAllowedMimes(mimeType) {
    return config.upload.allowedMimeTypes.includes(mimeType);
  }

  fileToGenerativePart(filePath) {
    try {
      const fileBuffer = fs.readFileSync(filePath);
      const mimeType = this.getMimeType(filePath);
      
      return {
        inlineData: {
          data: fileBuffer.toString('base64'),
          mimeType: mimeType
        }
      };
    } catch (error) {
      throw new Error(`Cannot read file: ${error.message}`);
    }
  }

  async generateContent(prompt) {
    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      return response.text();
    } catch (error) {
      throw new Error(`Gemini API error: ${error.message}`);
    }
  }

  async processLocalFile(filePath, textPrompt = 'อธิบายเนื้อหาของไฟล์นี้') {
    try {
      const mimeType = this.getMimeType(filePath);
      
      if (!this.isAllowedMimes(mimeType)) {
        throw new Error(`Unsupported file type: ${mimeType}`);
      }

      const imagePart = this.fileToGenerativePart(filePath);
      
      const result = await this.model.generateContent([textPrompt, imagePart]);
      const response = await result.response;
      return response.text();
    } catch (error) {
      throw new Error(`Error processing file: ${error.message}`);
    }
  }

  async processMultipleFiles(files, textPrompt = 'อธิบายเนื้อหาของไฟล์เหล่านี้') {
    try {
      const parts = [textPrompt];
      
      for (const filePath of files) {
        const mimeType = this.getMimeType(filePath);
        if (this.isAllowedMimes(mimeType)) {
          parts.push(this.fileToGenerativePart(filePath));
        }
      }

      const result = await this.model.generateContent(parts);
      const response = await result.response;
      return response.text();
    } catch (error) {
      throw new Error(`Error processing multiple files: ${error.message}`);
    }
  }
}

module.exports = new GeminiService();

// ====== utils/fileHelper.js ======
const fs = require('fs');
const path = require('path');
const moment = require('moment');
const config = require('../config/config');

class FileHelper {
  static generateFileName(originalName, extension = null) {
    const timestamp = moment().format('YYYYMMDD_HHmmss');
    const random = Math.random().toString(36).substring(2, 8);
    const ext = extension || path.extname(originalName);
    const name = path.basename(originalName, path.extname(originalName));
    return `${timestamp}_${random}_${name}${ext}`;
  }

  static deleteFile(filePath) {
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        return true;
      }
      return false;
    } catch (error) {
      console.error(`Error deleting file ${filePath}:`, error);
      return false;
    }
  }

  static getFileInfo(filePath) {
    try {
      const stats = fs.statSync(filePath);
      return {
        size: stats.size,
        created: stats.birthtime,
        modified: stats.mtime,
        extension: path.extname(filePath),
        name: path.basename(filePath)
      };
    } catch (error) {
      throw new Error(`Cannot get file info: ${error.message}`);
    }
  }

  static cleanupOldFiles(directory = config.upload.uploadDir, maxAge = 24 * 60 * 60 * 1000) {
    try {
      const files = fs.readdirSync(directory);
      const now = Date.now();
      let deletedCount = 0;

      files.forEach(file => {
        const filePath = path.join(directory, file);
        const stats = fs.statSync(filePath);
        
        if (now - stats.mtime.getTime() > maxAge) {
          this.deleteFile(filePath);
          deletedCount++;
        }
      });

      return deletedCount;
    } catch (error) {
      console.error('Error cleaning up old files:', error);
      return 0;
    }
  }

  static formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
}

module.exports = FileHelper;

// ====== middleware/auth.js ======
const crypto = require('crypto');
const config = require('../config/config');

const validateLineSignature = (req, res, next) => {
  const signature = req.headers['x-line-signature'];
  const body = JSON.stringify(req.body);

  if (!signature) {
    return res.status(401).json({ error: 'Missing LINE signature' });
  }

  const expectedSignature = crypto
    .createHmac('sha256', config.line.channelSecret)
    .update(body)
    .digest('base64');

  if (signature !== `SHA256=${expectedSignature}`) {
    return res.status(401).json({ error: 'Invalid LINE signature' });
  }

  next();
};

const validateApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'] || req.query.apiKey;
  
  if (!apiKey || apiKey !== config.line.webhookSecret) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  next();
};

module.exports = {
  validateLineSignature,
  validateApiKey
};

// ====== controllers/lineController.js ======
const RequestService = require('../services/request');
const GeminiService = require('../services/gemini');
const FileHelper = require('../utils/fileHelper');

class LineController {
  async handleWebhook(req, res) {
    try {
      const events = req.body.events || [];

      for (const event of events) {
        await this.processEvent(event);
      }

      res.status(200).json({ success: true });
    } catch (error) {
      console.error('Webhook error:', error);
      res.status(500).json({ error: error.message });
    }
  }

  async processEvent(event) {
    if (event.type !== 'message') return;

    const { replyToken, message, source } = event;
    const userId = source.userId;

    try {
      // Show loading indicator
      await RequestService.showLoading(userId);

      switch (message.type) {
        case 'text':
          await this.handleTextMessage(replyToken, message, userId);
          break;
        case 'image':
        case 'video':
        case 'audio':
        case 'file':
          await this.handleFileMessage(replyToken, message, userId);
          break;
        default:
          await this.handleUnsupportedMessage(replyToken);
      }
    } catch (error) {
      console.error('Event processing error:', error);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: 'เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง'
      });
    }
  }

  async handleTextMessage(replyToken, message, userId) {
    const text = message.text.toLowerCase();

    if (text.includes('help') || text.includes('ช่วย')) {
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `🤖 LINE Bot ช่วยเหลือ\n\n📎 ส่งไฟล์: รูปภาพ, PDF, เสียง, วิดีโอ\n💬 ส่งข้อความ: สอบถามข้อมูลทั่วไป\n🔍 คำสั่ง: help, status, info\n\nพิมพ์ข้อความพร้อมส่งไฟล์เพื่อให้ AI วิเคราะห์ครับ!`
      });
    } else if (text.includes('status')) {
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `✅ สถานะระบบ: ปกติ\n🚀 เซิร์ฟเวอร์: ออนไลน์\n🤖 AI: พร้อมใช้งาน\n📊 อัพเดต: ${new Date().toLocaleString('th-TH')}`
      });
    } else {
      // Process general text with Gemini
      const response = await GeminiService.generateContent(message.text);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: response
      });
    }
  }

  async handleFileMessage(replyToken, message, userId) {
    try {
      // Download file from LINE
      const response = await RequestService.getBinary(message.id);
      
      // Generate unique filename
      const fileName = FileHelper.generateFileName(`line_${message.id}`, '.bin');
      const filePath = RequestService.saveFile(response.data, fileName);
      
      // Process file with Gemini
      const prompt = 'วิเคราะห์และอธิบายเนื้อหาของไฟล์นี้ให้ละเอียด';
      const aiResponse = await GeminiService.processLocalFile(filePath, prompt);
      
      // Get file info
      const fileInfo = FileHelper.getFileInfo(filePath);
      
      // Reply with analysis
      await RequestService.reply(replyToken, [
        {
          type: 'text',
          text: `📁 ไฟล์: ${fileInfo.name}\n📊 ขนาด: ${FileHelper.formatFileSize(fileInfo.size)}\n\n🔍 การวิเคราะห์:\n${aiResponse}`
        }
      ]);
      
      // Clean up file after processing
      setTimeout(() => {
        FileHelper.deleteFile(filePath);
      }, 5000);
      
    } catch (error) {
      console.error('File processing error:', error);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: 'ไม่สามารถประมวลผลไฟล์ได้ กรุณาตรวจสอบรูปแบบไฟล์และลองใหม่'
      });
    }
  }

  async handleUnsupportedMessage(replyToken) {
    await RequestService.reply(replyToken, {
      type: 'text',
      text: 'ขออภัย ยังไม่รองรับข้อความประเภทนี้ กรุณาส่งข้อความหรือไฟล์ (รูป, เสียง, วิดีโอ, PDF)'
    });
  }
}

module.exports = new LineController();

// ====== controllers/uploadController.js ======
const GeminiService = require('../services/gemini');
const FileHelper = require('../utils/fileHelper');

class UploadController {
  async uploadFile(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({
          success: false,
          error: 'ไม่พบไฟล์ที่อัพโหลด'
        });
      }

      const filePath = req.file.path;
      const prompt = req.body.prompt || 'อธิบายเนื้อหาของไฟล์นี้';

      console.log('Processing file:', filePath);
      console.log('Prompt:', prompt);

      // Get file info
      const fileInfo = FileHelper.getFileInfo(filePath);

      // Process file with Gemini
      const result = await GeminiService.processLocalFile(filePath, prompt);

      res.json({
        success: true,
        response: result,
        fileInfo: {
          name: fileInfo.name,
          size: FileHelper.formatFileSize(fileInfo.size),
          type: fileInfo.extension
        }
      });

    } catch (error) {
      console.error('Upload processing error:', error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  async uploadMultipleFiles(req, res) {
    try {
      if (!req.files || req.files.length === 0) {
        return res.status(400).json({
          success: false,
          error: 'ไม่พบไฟล์ที่อัพโหลด'
        });
      }

      const filePaths = req.files.map(file => file.path);
      const prompt = req.body.prompt || 'อธิบายเนื้อหาของไฟล์เหล่านี้';

      // Process multiple files with Gemini
      const result = await GeminiService.processMultipleFiles(filePaths, prompt);

      // Get files info
      const filesInfo = req.files.map(file => {
        const info = FileHelper.getFileInfo(file.path);
        return {
          name: info.name,
          size: FileHelper.formatFileSize(info.size),
          type: info.extension
        };
      });

      res.json({
        success: true,
        response: result,
        filesInfo: filesInfo
      });

    } catch (error) {
      console.error('Multiple upload processing error:', error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  async getUploadedFiles(req, res) {
    try {
      const fs = require('fs');
      const path = require('path');
      const config = require('../config/config');

      const uploadDir = config.upload.uploadDir;
      const files = fs.readdirSync(uploadDir);

      const fileList = files
        .filter(file => file !== '.gitkeep')
        .map(file => {
          const filePath = path.join(uploadDir, file);
          const info = FileHelper.getFileInfo(filePath);
          return {
            name: info.name,
            size: FileHelper.formatFileSize(info.size),
            created: info.created,
            modified: info.modified
          };
        });

      res.json({
        success: true,
        files: fileList,
        total: fileList.length
      });

    } catch (error) {
      console.error('Get files error:', error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  async cleanupFiles(req, res) {
    try {
      const deletedCount = FileHelper.cleanupOldFiles();
      
      res.json({
        success: true,
        message: `ลบไฟล์เก่า ${deletedCount} ไฟล์เรียบร้อย`
      });

    } catch (error) {
      console.error('Cleanup error:', error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }
}

module.exports = new UploadController();

// ====== routes/upload.js ======
const express = require('express');
const multer = require('multer');
const path = require('path');
const config = require('../config/config');
const UploadController = require('../controllers/uploadController');
const { validateApiKey } = require('../middleware/auth');

const router = express.Router();

// Multer configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, config.upload.uploadDir);
  },
  filename: (req, file, cb) => {
    const FileHelper = require('../utils/fileHelper');
    const fileName = FileHelper.generateFileName(file.originalname);
    cb(null, fileName);
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: config.upload.maxFileSize
  },
  fileFilter: (req, file, cb) => {
    const GeminiService = require('../services/gemini');
    const mimeType = file.mimetype;
    
    if (GeminiService.isAllowedMimes(mimeType)) {
      cb(null, true);
    } else {
      cb(new Error(`ไม่รองรับไฟล์ประเภท ${mimeType}`), false);
    }
  }
});

// Routes
router.post('/single', upload.single('file'), UploadController.uploadFile);
router.post('/multiple', upload.array('files', 5), UploadController.uploadMultipleFiles);
router.get('/files', UploadController.getUploadedFiles);
router.delete('/cleanup', validateApiKey, UploadController.cleanupFiles);

// Error handling for multer
router.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        error: 'ไฟล์มีขนาดใหญ่เกินไป'
      });
    }
  }
  
  res.status(400).json({
    success: false,
    error: error.message
  });
});

module.exports = router;

// ====== routes/webhook.js ======
const express = require('express');
const LineController = require('../controllers/lineController');
const { validateLineSignature } = require('../middleware/auth');

const router = express.Router();

// LINE Webhook endpoint
router.post('/', validateLineSignature, LineController.handleWebhook);

// Webhook verification (for LINE setup)
router.get('/', (req, res) => {
  res.status(200).send('LINE Webhook endpoint is ready');
});

module.exports = router;

// ====== public/index.html ======
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LINE Bot File Upload System</title>
    <link rel="stylesheet" href="css/style.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1><i class="fab fa-line"></i> LINE Bot File Upload System</h1>
            <p>ระบบอัพโหลดไฟล์และประมวลผลด้วย AI</p>
        </header>

        <div class="tabs">
            <button class="tab-button active" onclick="openTab(event, 'upload-tab')">
                <i class="fas fa-upload"></i> อัพโหลดไฟล์
            </button>
            <button class="tab-button" onclick="openTab(event, 'multiple-tab')">
                <i class="fas fa-files"></i> อัพโหลดหลายไฟล์
            </button>
            <button class="tab-button" onclick="openTab(event, 'files-tab')">
                <i class="fas fa-folder"></i> ไฟล์ที่อัพโหลด
            </button>
            <button class="tab-button" onclick="openTab(event, 'status-tab')">
                <i class="fas fa-chart-line"></i> สถานะระบบ
            </button>
        </div>

        <!-- Single File Upload Tab -->
        <div id="upload-tab" class="tab-content active">
            <div class="upload-section">
                <h2><i class="fas fa-file-upload"></i> อัพโหลดไฟล์เดี่ยว</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="file">
                            <i class="fas fa-paperclip"></i> เลือกไฟล์:
                        </label>
                        <input type="file" id="file" name="file" 
                               accept=".pdf,.jpg,.jpeg,.png,.gif,.wav,.mp3,.m4a,.mp4,.mov,.txt" 
                               required>
                        <div class="file-info">
                            รองรับ: PDF, รูปภาพ, เสียง, วิดีโอ, ข้อความ (ขนาดสูงสุด 10MB)
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="prompt">
                            <i class="fas fa-comment-dots"></i> คำสั่งหรือคำถาม:
                        </label>
                        <textarea id="prompt" name="prompt" rows="4" 
                                  placeholder="กรุณาใส่คำถามหรือคำสั่งที่ต้องการให้ AI ประมวลผลไฟล์"></textarea>
                    </div>
                    <button type="submit" class="btn-primary">
                        <i class="fas fa-cogs"></i> อัพโหลดและประมวลผล
                    </button>
                </form>
                <div id="result" class="result" style="display: none;"></div>
            </div>
        </div>

        <!-- Multiple Files Upload Tab -->
        <div id="multiple-tab" class="tab-content">
            <div class="upload-section">
                <h2><i class="fas fa-files"></i> อัพโหลดหลายไฟล์</h2>
                <form id="multipleUploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="files">
                            <i class="fas fa-paperclip"></i> เลือกไฟล์ (สูงสุด 5 ไฟล์):
                        </label>
                        <input type="file" id="files" name="files" multiple 
                               accept=".pdf,.jpg,.jpeg,.png,.gif,.wav,.mp3,.m4a,.mp4,.mov,.txt">
                        <div class="file-info">
                            รองรับหลายไฟล์พร้อมกัน สูงสุด 5 ไฟล์
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="multiplePrompt">
                            <i class="fas fa-comment-dots"></i> คำสั่งหรือคำถาม:
                        </label>
                        <textarea id="multiplePrompt" name="prompt" rows="4" 
                                  placeholder="กรุณาใส่คำถามหรือคำสั่งสำหรับไฟล์ทั้งหมด"></textarea>
                    </div>
                    <button type="submit" class="btn-primary">
                        <i class="fas fa-cogs"></i> อัพโหลดและประมวลผลทั้งหมด
                    </button>
                </form>
                <div id="multipleResult" class="result" style="display: none;"></div>
            </div>
        </div>

        <!-- Files List Tab -->
        <div id="files-tab" class="tab-content">
            <div class="files-section">
                <h2><i class="fas fa-folder-open"></i> ไฟล์ที่อัพโหลด</h2>
                <div class="files-controls">
                    <button onclick="loadFilesList()" class="btn-secondary">
                        <i class="fas fa-sync"></i> รีเฟรช
                    </button>
                    <button onclick="cleanupFiles()" class="btn-danger">
                        <i class="fas fa-trash"></i> ลบไฟล์เก่า
                    </button>
                </div>
                <div id="filesList" class="files-list">
                    <div class="loading">กำลังโหลด...</div>
                </div>
            </div>
        </div>

        <!-- System Status Tab -->
        <div id="status-tab" class="tab-content">
            <div class="status-section">
                <h2><i class="fas fa-server"></i> สถานะระบบ</h2>
                <div class="status-cards">
                    <div class="status-card">
                        <div class="status-icon">
                            <i class="fas fa-server"></i>
                        </div>
                        <div class="status-info">
                            <h3>เซิร์ฟเวอร์</h3>
                            <p id="serverStatus" class="status-value">กำลังตรวจสอบ...</p>
                        </div>
                    </div>
                    <div class="status-card">
                        <div class="status-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="status-info">
                            <h3>Gemini AI</h3>
                            <p id="aiStatus" class="status-value">พร้อมใช้งาน</p>
                        </div>
                    </div>
                    <div class="status-card">
                        <div class="status-icon">
                            <i class="fab fa-line"></i>
                        </div>
                        <div class="status-info">
                            <h3>LINE Bot</h3>
                            <p id="lineStatus" class="status-value">เชื่อมต่อแล้ว</p>
                        </div>
                    </div>
                </div>
                <div class="system-info">
                    <h3><i class="fas fa-info-circle"></i> ข้อมูลระบบ</h3>
                    <div id="systemInfo">
                        <p><strong>เวลาปัจจุบัน:</strong> <span id="currentTime"></span></p>
                        <p><strong>Webhook URL:</strong> <code id="webhookUrl"></code></p>
                        <p><strong>รองรับไฟล์:</strong> PDF, รูปภาพ, เสียง, วิดีโอ</p>
                        <p><strong>ขนาดไฟล์สูงสุด:</strong> 10 MB</p>
                    </div>
                </div>
            </div>
        </div>

        <footer>
            <p>&copy; 2025 LINE Bot File Upload System. สร้างด้วย Express.js และ Gemini AI</p>
        </footer>
    </div>

    <script src="js/main.js"></script>
</body>
</html>

// ====== public/css/style.css ======
/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: rgba(255, 255, 255, 0.95);
    min-height: 100vh;
    box-shadow: 0 0 30px rgba(0, 0, 0, 0.1);
}

/* Header Styles */
header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px 0;
    border-bottom: 2px solid #eee;
}

header h1 {
    color: #2c3e50;
    font-size: 2.5rem;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

header p {
    color: #7f8c8d;
    font-size: 1.1rem;
}

header i {
    color: #00C300;
    margin-right: 10px;
}

/* Tabs Styles */
.tabs {
    display: flex;
    border-bottom: 2px solid #eee;
    margin-bottom: 30px;
    overflow-x: auto;
}

.tab-button {
    flex: 1;
    padding: 15px 20px;
    border: none;
    background: #f8f9fa;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s ease;
    white-space: nowrap;
    min-width: 150px;
}

.tab-button:hover {
    background: #e9ecef;
}

.tab-button.active {
    background: #007bff;
    color: white;
    border-bottom: 3px solid #0056b3;
}

.tab-button i {
    margin-right: 8px;
}

/* Tab Content */
.tab-content {
    display: none;
    animation: fadeIn 0.3s ease-in;
}

.tab-content.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Form Styles */
.upload-section {
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.upload-section h2 {
    color: #2c3e50;
    margin-bottom: 25px;
    font-size: 1.8rem;
}

.form-group {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
    color: #34495e;
    font-size: 1.1rem;
}

input[type="file"] {
    width: 100%;
    padding: 12px;
    border: 2px dashed #bdc3c7;
    border-radius: 8px;
    background: #f8f9fa;
    font-size: 16px;
    transition: border-color 0.3s ease;
}

input[type="file"]:hover {
    border-color: #3498db;
}

textarea {
    width: 100%;
    padding: 12px;
    border: 2px solid #bdc3c7;
    border-radius: 8px;
    font-size: 16px;
    resize: vertical;
    transition: border-color 0.3s ease;
}

textarea:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 5px rgba(52, 152, 219, 0.3);
}

.file-info {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-top: 5px;
    font-style: italic;
}

/* Button Styles */
.btn-primary, .btn-secondary, .btn-danger {
    padding: 12px 25px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
    transition: all 0.3s ease;
    margin-right: 10px;
    margin-bottom: 10px;
}

.btn-primary {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #2980b9, #1f4e79);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
}

.btn-secondary {
    background: linear-gradient(135deg, #95a5a6, #7f8c8d);
    color: white;
}

.btn-secondary:hover {
    background: linear-gradient(135deg, #7f8c8d, #6c7b7d);
    transform: translateY(-2px);
}

.btn-danger {
    background: linear-gradient(135deg, #e74c3c, #c0392b);
    color: white;
}

.btn-danger:hover {
    background: linear-gradient(135deg, #c0392b, #a93226);
    transform: translateY(-2px);
}

/* Result Styles */
.result {
    margin-top: 25px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #3498db;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.result h3 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.result.error {
    border-left-color: #e74c3c;
    background: #fdf2f2;
}

.result.error h3 {
    color: #e74c3c;
}

.result.success {
    border-left-color: #27ae60;
    background: #f0fff4;
}

.result.success h3 {
    color: #27ae60;
}

/* Files Section */
.files-section {
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.files-controls {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.files-list {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 10px;
}

.file-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    border-bottom: 1px solid #eee;
    transition: background-color 0.3s ease;
}

.file-item:hover {
    background: #f8f9fa;
}

.file-item:last-child {
    border-bottom: none;
}

.file-details h4 {
    color: #2c3e50;
    margin-bottom: 5px;
}

.file-details p {
    color: #7f8c8d;
    font-size: 0.9rem;
}

/* Status Section */
.status-section {
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.status-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.status-card {
    display: flex;
    align-items: center;
    padding: 20px;
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    border-radius: 10px;
    border-left: 4px solid #3498db;
    transition: transform 0.3s ease;
}

.status-card:hover {
    transform: translateY(-3px);
}

.status-icon {
    font-size: 2rem;
    color: #3498db;
    margin-right: 15px;
}

.status-info h3 {
    color: #2c3e50;
    margin-bottom: 5px;
}

.status-value {
    color: #27ae60;
    font-weight: bold;
}

.system-info {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.system-info h3 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.system-info p {
    margin-bottom: 8px;
    color: #495057;
}

.system-info code {
    background: #e9ecef;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    color: #e83e8c;
}

/* Loading Animation */
.loading {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
    font-size: 1.1rem;
}

.loading::after {
    content: '';
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid #bdc3c7;
    border-radius: 50%;
    border-top-color: #3498db;
    animation: spin 1s linear infinite;
    margin-left: 10px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Footer */
footer {
    text-align: center;
    margin-top: 40px;
    padding: 20px 0;
    border-top: 1px solid #eee;
    color: #7f8c8d;
}

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    header h1 {
        font-size: 2rem;
    }
    
    .tabs {
        flex-direction: column;
    }
    
    .tab-button {
        flex: none;
        width: 100%;
    }
    
    .upload-section {
        padding: 20px;
    }
    
    .status-cards {
        grid-template-columns: 1fr;
    }
    
    .files-controls {
        flex-direction: column;
    }
    
    .file-item {
        flex-direction: column;
        align-items: flex-start;
    }
}

// ====== public/js/main.js ======
// Global variables
let currentTab = 'upload-tab';

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing application...');
    initializeApp();
    updateCurrentTime();
    checkSystemStatus();
    loadFilesList();
    
    // Update time every second
    setInterval(updateCurrentTime, 1000);
    
    // Debug: Check if tabs are working
    console.log('✅ Application initialized successfully');
});

// Initialize application
function initializeApp() {
    setupEventListeners();
    updateWebhookUrl();
    
    // Make sure the first tab is active
    const firstTab = document.querySelector('.tab-button');
    const firstContent = document.querySelector('.tab-content');
    if (firstTab && firstContent) {
        firstTab.classList.add('active');
        firstContent.classList.add('active');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Single file upload form
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleSingleUpload);
    }
    
    // Multiple files upload form
    const multipleForm = document.getElementById('multipleUploadForm');
    if (multipleForm) {
        multipleForm.addEventListener('submit', handleMultipleUpload);
    }
    
    // File input changes
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    const filesInput = document.getElementById('files');
    if (filesInput) {
        filesInput.addEventListener('change', handleMultipleFileSelect);
    }
}

// Tab functionality - FIXED VERSION
function openTab(evt, tabName) {
    console.log('🔄 Opening tab:', tabName);
    
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }

    // Remove active class from all tab buttons
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }

    // Show selected tab content and mark button as active
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
        console.log('✅ Tab content activated:', tabName);
    } else {
        console.error('❌ Tab not found:', tabName);
    }
    
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add('active');
        console.log('✅ Tab button activated');
    }
    
    currentTab = tabName;
    
    // Load data for specific tabs
    if (tabName === 'files-tab') {
        console.log('📁 Loading files list...');
        loadFilesList();
    } else if (tabName === 'status-tab') {
        console.log('📊 Checking system status...');
        checkSystemStatus();
    }
}

// Handle single file upload
async function handleSingleUpload(e) {
    e.preventDefault();
    console.log('📤 Starting single file upload...');
    
    const formData = new FormData();
    const fileInput = document.getElementById('file');
    const promptInput = document.getElementById('prompt');
    const resultDiv = document.getElementById('result');
    
    if (!fileInput.files[0]) {
        showResult(resultDiv, 'error', 'กรุณาเลือกไฟล์');
        return;
    }
    
    console.log('📁 File selected:', fileInput.files[0].name);
    
    formData.append('file', fileInput.files[0]);
    formData.append('prompt', promptInput.value || 'อธิบายเนื้อหาของไฟล์นี้');
    
    showResult(resultDiv, 'loading', 'กำลังอัพโหลดและประมวลผล...');
    
    try {
        console.log('🚀 Sending request to server...');
        const response = await fetch('/api/upload/single', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('📨 Server response:', result);
        
        if (result.success) {
            const fileInfo = result.fileInfo;
            const content = `
                <h3><i class="fas fa-check-circle"></i> ประมวลผลเสร็จสิ้น</h3>
                <div class="file-details">
                    <p><strong>ไฟล์:</strong> ${fileInfo.name}</p>
                    <p><strong>ขนาด:</strong> ${fileInfo.size}</p>
                    <p><strong>ประเภท:</strong> ${fileInfo.type}</p>
                </div>
                <h4>ผลการวิเคราะห์:</h4>
                <p>${result.response}</p>
            `;
            showResult(resultDiv, 'success', content);
        } else {
            showResult(resultDiv, 'error', result.error);
        }
    } catch (error) {
        console.error('❌ Upload error:', error);
        showResult(resultDiv, 'error', 'เกิดข้อผิดพลาด: ' + error.message);
    }
}

// Handle multiple files upload
async function handleMultipleUpload(e) {
    e.preventDefault();
    console.log('📤 Starting multiple files upload...');
    
    const formData = new FormData();
    const filesInput = document.getElementById('files');
    const promptInput = document.getElementById('multiplePrompt');
    const resultDiv = document.getElementById('multipleResult');
    
    if (!filesInput.files.length) {
        showResult(resultDiv, 'error', 'กรุณาเลือกไฟล์');
        return;
    }
    
    console.log('📁 Files selected:', filesInput.files.length);
    
    // Append all files
    for (let i = 0; i < filesInput.files.length; i++) {
        formData.append('files', filesInput.files[i]);
        console.log(`📄 File ${i + 1}:`, filesInput.files[i].name);
    }
    formData.append('prompt', promptInput.value || 'อธิบายเนื้อหาของไฟล์เหล่านี้');
    
    showResult(resultDiv, 'loading', 'กำลังอัพโหลดและประมวลผลไฟล์ทั้งหมด...');
    
    try {
        const response = await fetch('/api/upload/multiple', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('📨 Server response:', result);
        
        if (result.success) {
            let filesInfoHtml = '';
            result.filesInfo.forEach((file, index) => {
                filesInfoHtml += `
                    <div class="file-item">
                        <p><strong>ไฟล์ ${index + 1}:</strong> ${file.name} (${file.size})</p>
                    </div>
                `;
            });
            
            const content = `
                <h3><i class="fas fa-check-circle"></i> ประมวลผลไฟล์ทั้งหมดเสร็จสิ้น</h3>
                <div class="files-summary">
                    <h4>ไฟล์ที่ประมวลผล (${result.filesInfo.length} ไฟล์):</h4>
                    ${filesInfoHtml}
                </div>
                <h4>ผลการวิเคราะห์:</h4>
                <p>${result.response}</p>
            `;
            showResult(resultDiv, 'success', content);
        } else {
            showResult(resultDiv, 'error', result.error);
        }
    } catch (error) {
        console.error('❌ Multiple upload error:', error);
        showResult(resultDiv, 'error', 'เกิดข้อผิดพลาด: ' + error.message);
    }
}

// Handle file selection display
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        console.log('📁 Selected file:', file.name, 'Size:', formatFileSize(file.size));
    }
}

// Handle multiple files selection display
function handleMultipleFileSelect(e) {
    const files = e.target.files;
    if (files.length) {
        console.log(`📁 Selected ${files.length} files:`);
        for (let i = 0; i < files.length; i++) {
            console.log(`- ${files[i].name} (${formatFileSize(files[i].size)})`);
        }
    }
}

// Show result in specified div
function showResult(div, type, content) {
    if (!div) {
        console.error('❌ Result div not found');
        return;
    }
    
    div.style.display = 'block';
    div.className = `result ${type}`;
    
    if (type === 'loading') {
        div.innerHTML = `<div class="loading">${content}</div>`;
    } else if (type === 'error') {
        div.innerHTML = `<h3><i class="fas fa-exclamation-triangle"></i> เกิดข้อผิดพลาด</h3><p>${content}</p>`;
    } else if (type === 'success') {
        div.innerHTML = content;
    } else {
        div.innerHTML = content;
    }
    
    // Scroll to result
    div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Load files list
async function loadFilesList() {
    const listDiv = document.getElementById('filesList');
    if (!listDiv) {
        console.error('❌ Files list div not found');
        return;
    }
    
    listDiv.innerHTML = '<div class="loading">กำลังโหลดรายการไฟล์...</div>';
    
    try {
        console.log('📂 Loading files list...');
        const response = await fetch('/api/upload/files');
        const result = await response.json();
        console.log('📋 Files list response:', result);
        
        if (result.success) {
            if (result.files.length === 0) {
                listDiv.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">ยังไม่มีไฟล์ที่อัพโหลด</p>';
            } else {
                let filesHtml = `<h4>ไฟล์ทั้งหมด (${result.total} ไฟล์)</h4>`;
                result.files.forEach(file => {
                    filesHtml += `
                        <div class="file-item">
                            <div class="file-details">
                                <h4><i class="fas fa-file"></i> ${file.name}</h4>
                                <p><strong>ขนาด:</strong> ${file.size}</p>
                                <p><strong>อัพโหลด:</strong> ${new Date(file.created).toLocaleString('th-TH')}</p>
                                <p><strong>แก้ไขล่าสุด:</strong> ${new Date(file.modified).toLocaleString('th-TH')}</p>
                            </div>
                        </div>
                    `;
                });
                listDiv.innerHTML = filesHtml;
            }
        } else {
            listDiv.innerHTML = '<p style="color: #e74c3c;">เกิดข้อผิดพลาดในการโหลดรายการไฟล์</p>';
        }
    } catch (error) {
        console.error('❌ Files list error:', error);
        listDiv.innerHTML = '<p style="color: #e74c3c;">เกิดข้อผิดพลาด: ' + error.message + '</p>';
    }
}

// Cleanup old files
async function cleanupFiles() {
    if (!confirm('คุณต้องการลบไฟล์เก่าหรือไม่?')) {
        return;
    }
    
    try {
        console.log('🗑️ Cleaning up old files...');
        const response = await fetch('/api/upload/cleanup?apiKey=your_webhook_secret_here', {
            method: 'DELETE'
        });
        
        const result = await response.json();
        console.log('🧹 Cleanup response:', result);
        
        if (result.success) {
            alert(result.message);
            loadFilesList(); // Reload files list
        } else {
            alert('เกิดข้อผิดพลาด: ' + result.error);
        }
    } catch (error) {
        console.error('❌ Cleanup error:', error);
        alert('เกิดข้อผิดพลาด: ' + error.message);
    }
}

// Check system status
async function checkSystemStatus() {
    try {
        console.log('🔍 Checking system status...');
        const response = await fetch('/health');
        const result = await response.json();
        console.log('💚 Health check response:', result);
        
        const serverStatusEl = document.getElementById('serverStatus');
        if (serverStatusEl) {
            serverStatusEl.textContent = result.status === 'OK' ? 'ออนไลน์' : 'ออฟไลน์';
            serverStatusEl.style.color = result.status === 'OK' ? '#27ae60' : '#e74c3c';
        }
        
    } catch (error) {
        console.error('❌ Health check error:', error);
        const serverStatusEl = document.getElementById('serverStatus');
        if (serverStatusEl) {
            serverStatusEl.textContent = 'ออฟไลน์';
            serverStatusEl.style.color = '#e74c3c';
        }
    }
}

// Update current time
function updateCurrentTime() {
    const now = new Date();
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = now.toLocaleString('th-TH');
    }
}

// Update webhook URL
function updateWebhookUrl() {
    const webhookElement = document.getElementById('webhookUrl');
    if (webhookElement) {
        const baseUrl = window.location.origin;
        webhookElement.textContent = `${baseUrl}/webhook`;
    }
}

// Format file size
function formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

// Utility function for copying text
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        console.log('📋 Copied to clipboard:', text);
        alert('คัดลอกแล้ว: ' + text);
    }).catch(err => {
        console.error('❌ Copy failed:', err);
    });
}

// Make openTab function globally available
window.openTab = openTab;
window.loadFilesList = loadFilesList;
window.cleanupFiles = cleanupFiles;
window.copyToClipboard = copyToClipboard;

console.log('✅ All functions loaded successfully');

// ====== uploads/.gitkeep ======
# This file ensures the uploads directory is tracked by git
# Files uploaded here will be ignored by .gitignore except this file

// ====== README.md ======
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