const crypto = require('crypto');
const config = require('../config/config');

const validateLineSignature = (req, res, next) => {
  try {
    const signature = req.headers['x-line-signature'];
    
    // ถ้าไม่มี signature ให้ผ่านไปก่อน (สำหรับทดสอบ)
    if (!signature) {
      console.log('⚠️  No signature found, allowing request for testing');
      return next();
    }

    // ถ้าไม่มี channel secret ให้ผ่านไปก่อน
    if (!config.line.channelSecret) {
      console.log('⚠️  No channel secret configured, allowing request');
      return next();
    }

    const body = JSON.stringify(req.body);
    console.log('🔐 Validating signature for body:', body.substring(0, 100) + '...');

    const expectedSignature = crypto
      .createHmac('sha256', config.line.channelSecret)
      .update(body)
      .digest('base64');

    const fullExpectedSignature = `SHA256=${expectedSignature}`;
    
    console.log('📝 Expected signature:', fullExpectedSignature);
    console.log('📝 Received signature:', signature);

    if (signature !== fullExpectedSignature) {
      console.log('❌ Signature validation failed');
      return res.status(401).json({ error: 'Invalid LINE signature' });
    }

    console.log('✅ Signature validation passed');
    next();
  } catch (error) {
    console.error('❌ Signature validation error:', error);
    // ในกรณีมี error ให้ผ่านไปก่อน (สำหรับทดสอบ)
    next();
  }
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
