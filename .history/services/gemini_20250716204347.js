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
