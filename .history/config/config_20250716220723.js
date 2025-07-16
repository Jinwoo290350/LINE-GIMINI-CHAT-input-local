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