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