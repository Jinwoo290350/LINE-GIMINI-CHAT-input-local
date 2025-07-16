const RequestService = require('../services/request');
const GeminiService = require('../services/gemini');
const FileHelper = require('../utils/fileHelper');

class LineController {
  async handleWebhook(req, res) {
    try {
      const events = req.body.events || [];

      for (const event of events) {
        await this.processEvent(event);
      }

      res.status(200).json({ success: true });
    } catch (error) {
      console.error('Webhook error:', error);
      res.status(500).json({ error: error.message });
    }
  }

  async processEvent(event) {
    if (event.type !== 'message') return;

    const { replyToken, message, source } = event;
    const userId = source.userId;

    try {
      // Show loading indicator
      await RequestService.showLoading(userId);

      switch (message.type) {
        case 'text':
          await this.handleTextMessage(replyToken, message, userId);
          break;
        case 'image':
        case 'video':
        case 'audio':
        case 'file':
          await this.handleFileMessage(replyToken, message, userId);
          break;
        default:
          await this.handleUnsupportedMessage(replyToken);
      }
    } catch (error) {
      console.error('Event processing error:', error);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: 'เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง'
      });
    }
  }

  async handleTextMessage(replyToken, message, userId) {
    const text = message.text.toLowerCase();

    if (text.includes('help') || text.includes('ช่วย')) {
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `🤖 LINE Bot ช่วยเหลือ\n\n📎 ส่งไฟล์: รูปภาพ, PDF, เสียง, วิดีโอ\n💬 ส่งข้อความ: สอบถามข้อมูลทั่วไป\n🔍 คำสั่ง: help, status, info\n\nพิมพ์ข้อความพร้อมส่งไฟล์เพื่อให้ AI วิเคราะห์ครับ!`
      });
    } else if (text.includes('status')) {
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `✅ สถานะระบบ: ปกติ\n🚀 เซิร์ฟเวอร์: ออนไลน์\n🤖 AI: พร้อมใช้งาน\n📊 อัพเดต: ${new Date().toLocaleString('th-TH')}`
      });
    } else {
      // Process general text with Gemini
      const response = await GeminiService.generateContent(message.text);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: response
      });
    }
  }

  async handleFileMessage(replyToken, message, userId) {
    try {
      // Download file from LINE
      const response = await RequestService.getBinary(message.id);
      
      // Generate unique filename
      const fileName = FileHelper.generateFileName(`line_${message.id}`, '.bin');
      const filePath = RequestService.saveFile(response.data, fileName);
      
      // Process file with Gemini
      const prompt = 'วิเคราะห์และอธิบายเนื้อหาของไฟล์นี้ให้ละเอียด';
      const aiResponse = await GeminiService.processLocalFile(filePath, prompt);
      
      // Get file info
      const fileInfo = FileHelper.getFileInfo(filePath);
      
      // Reply with analysis
      await RequestService.reply(replyToken, [
        {
          type: 'text',
          text: `📁 ไฟล์: ${fileInfo.name}\n📊 ขนาด: ${FileHelper.formatFileSize(fileInfo.size)}\n\n🔍 การวิเคราะห์:\n${aiResponse}`
        }
      ]);
      
      // Clean up file after processing
      setTimeout(() => {
        FileHelper.deleteFile(filePath);
      }, 5000);
      
    } catch (error) {
      console.error('File processing error:', error);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: 'ไม่สามารถประมวลผลไฟล์ได้ กรุณาตรวจสอบรูปแบบไฟล์และลองใหม่'
      });
    }
  }

  async handleUnsupportedMessage(replyToken) {
    await RequestService.reply(replyToken, {
      type: 'text',
      text: 'ขออภัย ยังไม่รองรับข้อความประเภทนี้ กรุณาส่งข้อความหรือไฟล์ (รูป, เสียง, วิดีโอ, PDF)'
    });
  }
}

module.exports = new LineController();
