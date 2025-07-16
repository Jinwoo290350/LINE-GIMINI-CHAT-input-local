const express = require('express');
const LineController = require('../controllers/lineController');
const { validateLineSignature } = require('../middleware/auth');

const router = express.Router();

// LINE Webhook endpoint with signature validation
router.post('/', validateLineSignature, LineController.handleWebhook);

// Webhook verification (for LINE setup)
router.get('/', (req, res) => {
  res.status(200).json({ 
    status: 'LINE Webhook endpoint is ready',
    timestamp: new Date().toISOString()
  });
});

module.exports = router;