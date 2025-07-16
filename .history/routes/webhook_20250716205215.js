const express = require('express');
const LineController = require('../controllers/lineController');
const { validateLineSignature } = require('../middleware/auth');

const router = express.Router();

// LINE Webhook endpoint
router.post('/', validateLineSignature, LineController.handleWebhook);

// Webhook verification (for LINE setup)
router.get('/', (req, res) => {
  res.status(200).send('LINE Webhook endpoint is ready');
});

module.exports = router;