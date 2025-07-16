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
