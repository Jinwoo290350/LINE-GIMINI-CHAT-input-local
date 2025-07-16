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