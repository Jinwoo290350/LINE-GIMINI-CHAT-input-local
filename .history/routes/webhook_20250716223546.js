const express = require('express');
const LineController = require('../controllers/lineController');
const { validateLineSignature } = require('../middleware/auth');

const router = express.Router();

// LINE Webhook endpoint - ปิด validation ชั่วคราว เพื่อทดสอบ
router.post('/', (req, res, next) => {
  console.log('🔔 Webhook received (no validation)');
  console.log('📨 Headers:', JSON.stringify(req.headers, null, 2));
  console.log('📦 Body:', JSON.stringify(req.body, null, 2));
  LineController.handleWebhook(req, res);
});

// Webhook verification (for LINE setup)
router.get('/', (req, res) => {
  res.status(200).json({ 
    status: 'LINE Webhook endpoint is ready',
    timestamp: new Date().toISOString()
  });
});

module.exports = router;