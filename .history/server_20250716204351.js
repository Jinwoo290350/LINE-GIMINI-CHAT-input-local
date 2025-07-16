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