const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');

const config = require('./config/config');
const uploadRoutes = require('./routes/upload');
const webhookRoutes = require('./routes/webhook');

const app = express();

// Security middleware
app.use(helmet());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// CORS
app.use(cors({
  origin: ['http://localhost:3000', 'https://your-domain.com', 'https://api.yourdomain.com'],
  credentials: true
}));

// Body parsing middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Create uploads directory if it doesn't exist
const uploadDir = config.upload.uploadDir;
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Base path support
const basePath = config.server.basePath;

// Static files
app.use(basePath, express.static(path.join(__dirname, 'public')));

// Routes with base path
app.use(`${basePath}/api/upload`, uploadRoutes);
app.use(`${basePath}/webhook`, webhookRoutes);

// Health check with base path
app.get(`${basePath}/health`, (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    basePath: basePath || '/',
    environment: config.server.env
  });
});

// Root redirect to base path (if base path is set)
if (basePath) {
  app.get('/', (req, res) => {
    res.redirect(basePath);
  });
}

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    error: config.server.env === 'development' ? err.message : 'Internal server error'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    requestedPath: req.originalUrl,
    availablePaths: [
      `${basePath}/`,
      `${basePath}/webhook`,
      `${basePath}/api/upload/*`,
      `${basePath}/health`
    ]
  });
});

// Start server
const port = config.server.port;
app.listen(port, () => {
  console.log(`🚀 Server running on port ${port}`);
  console.log(`📱 Web interface: http://localhost:${port}${basePath}`);
  console.log(`🔗 LINE Webhook: http://localhost:${port}${basePath}/webhook`);
  console.log(`🏥 Health check: http://localhost:${port}${basePath}/health`);
  console.log(`📁 Upload directory: ${uploadDir}`);
  console.log(`🛣️  Base path: ${basePath || '/'}`);
});
