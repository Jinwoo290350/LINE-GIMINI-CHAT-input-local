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