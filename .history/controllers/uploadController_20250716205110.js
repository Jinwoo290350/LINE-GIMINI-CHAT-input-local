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