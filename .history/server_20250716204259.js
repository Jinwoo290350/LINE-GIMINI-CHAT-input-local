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
const { GoogleGenAI } = require('@google/genai');
const fs = require('fs');
const path = require('path');
const config = require('../config/config');

class GeminiService {
  constructor() {
    this.ai = new GoogleGenAI({ apiKey: config.gemini.apiKey });
    this.model = 'gemini-2.5-flash';
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

  fileToBase64(filePath) {
    try {
      const fileBuffer = fs.readFileSync(filePath);
      return fileBuffer.toString('base64');
    } catch (error) {
      throw new Error(`Cannot read file: ${error.message}`);
    }
  }

  createFileObject(filePath) {
    const mimeType = this.getMimeType(filePath);
    const base64Data = this.fileToBase64(filePath);
    
    return {
      inlineData: {
        mimeType: mimeType,
        data: base64Data
      }
    };
  }

  async generateContent(prompt) {
    try {
      const response = await this.ai.models.generateContent({
        model: this.model,
        contents: [{ role: 'user', parts: [{ text: prompt }] }]
      });
      return response.response.text();
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

      const fileObject = this.createFileObject(filePath);
      
      const contents = [{
        role: 'user',
        parts: [
          { text: textPrompt },
          fileObject
        ]
      }];

      const response = await this.ai.models.generateContent({
        model: this.model,
        contents: contents
      });

      return response.response.text();
    } catch (error) {
      throw new Error(`Error processing file: ${error.message}`);
    }
  }

  async processMultipleFiles(files, textPrompt = 'อธิบายเนื้อหาของไฟล์เหล่านี้') {
    try {
      const parts = [{ text: textPrompt }];
      
      for (const filePath of files) {
        const mimeType = this.getMimeType(filePath);
        if (this.isAllowedMimes(mimeType)) {
          parts.push(this.createFileObject(filePath));
        }
      }

      const contents = [{ role: 'user', parts }];

      const response = await this.ai.models.generateContent({
        model: this.model,
        contents: contents
      });

      return response.response.text();
    } catch (error) {
      throw new Error(`Error processing multiple files: ${error.message}`);
    }
  }
}

module.exports = new GeminiService();
