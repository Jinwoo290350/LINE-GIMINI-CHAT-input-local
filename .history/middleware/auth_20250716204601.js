
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