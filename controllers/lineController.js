const RequestService = require('../services/request');
const GeminiService = require('../services/gemini');
const FileHelper = require('../utils/fileHelper');

class LineController {
  async handleWebhook(req, res) {
    try {
      console.log('🔔 Webhook received:', JSON.stringify(req.body, null, 2));
      
      const events = req.body.events || [];
      console.log(`📨 Processing ${events.length} events`);

      for (const event of events) {
        // ตรวจสอบ redelivery และ skip ถ้าเป็น redelivery
        if (event.deliveryContext?.isRedelivery) {
          console.log('⏭️ Skipping redelivery event:', event.webhookEventId);
          continue;
        }
        
        await this.processEvent(event);
      }

      res.status(200).json({ success: true, message: 'Events processed' });
    } catch (error) {
      console.error('❌ Webhook error:', error);
      // ส่ง status 200 กลับไปให้ LINE เพื่อไม่ให้ retry
      res.status(200).json({ success: false, error: error.message });
    }
  }

  async processEvent(event) {
    console.log('🎯 Processing event:', event.type, event.message?.type || 'no-message');
    
    if (event.type !== 'message') {
      console.log('⏭️ Skipping non-message event');
      return;
    }

    const { replyToken, message, source } = event;
    const userId = source.userId;

    try {
      // Show loading indicator
      if (userId) {
        try {
          await RequestService.showLoading(userId);
        } catch (loadingError) {
          console.log('⚠️ Loading indicator failed (not critical):', loadingError.message);
        }
      }

      switch (message.type) {
        case 'text':
          console.log('💬 Processing text message:', message.text);
          await this.handleTextMessage(replyToken, message, userId);
          break;
        case 'image':
        case 'video':
        case 'audio':
        case 'file':
          console.log('📎 Processing file message:', message.type);
          await this.handleFileMessage(replyToken, message, userId);
          break;
        default:
          console.log('❓ Processing unsupported message type:', message.type);
          await this.handleUnsupportedMessage(replyToken);
      }
    } catch (error) {
      console.error('❌ Event processing error:', error);
      if (replyToken) {
        try {
          const replyResult = await RequestService.reply(replyToken, {
            type: 'text',
            text: 'เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง'
          });
          
          if (replyResult === null) {
            console.log('⚠️ Reply skipped due to invalid/expired token');
          }
        } catch (replyError) {
          console.error('❌ Reply error:', replyError);
        }
      }
    }
  }

  async handleTextMessage(replyToken, message, userId) {
    const text = message.text.toLowerCase();

    if (text.includes('help') || text.includes('ช่วย')) {
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `🤖 สวัสดีครับ! ผมสามารถช่วยคุณได้ดังนี้:\n\n📎 วิเคราะห์ไฟล์: ส่งรูปภาพ, PDF, เสียง, วิดีโอ มาพร้อมบอกว่าต้องการให้ทำอะไร\n\n💬 สนทนาทั่วไป: ถามคำถามอะไรก็ได้\n\n🔍 คำสั่งพิเศษ: help, status\n\n✨ ตัวอย่าง:\n"วิเคราะห์รูปนี้หน่อย"\n"แปลข้อความในรูป"\n"สรุปเนื้อหา PDF"\n"แปลงเสียงเป็นข้อความ"`
      });
    } else if (text.includes('status')) {
      const uptime = Math.floor(process.uptime() / 60);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `✅ สถานะระบบ\n🚀 เซิร์ฟเวอร์: ทำงานปกติ\n🤖 AI: พร้อมใช้งาน\n⏱️ เวลาทำงาน: ${uptime} นาที\n📊 อัพเดต: ${new Date().toLocaleString('th-TH')}\n\n💡 ส่งไฟล์หรือข้อความมาได้เลยครับ!`
      });
    } else {
      // Process general text with Gemini
      try {
        const response = await GeminiService.generateContent(
          `คุณเป็น AI ผู้ช่วยที่เป็นมิตรและใจดี ตอบเป็นภาษาไทยแบบสนทนาธรรมชาติ ไม่เป็นทางการมากเกินไป:\n\nคำถาม: ${message.text}`
        );
        await RequestService.reply(replyToken, {
          type: 'text',
          text: response
        });
      } catch (error) {
        await RequestService.reply(replyToken, {
          type: 'text',
          text: 'ขออภัยครับ มีปัญหาในการประมวลผล กรุณาลองใหม่อีกครั้ง 🙏'
        });
      }
    }
  }

  async handleFileMessage(replyToken, message, userId) {
    try {
      // ส่งข้อความถามความต้องการก่อน
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `📎 ได้รับไฟล์ ${this.getFileTypeText(message.type)} แล้วครับ!\n\n🤔 คุณต้องการให้ผมทำอะไรกับไฟล์นี้ครับ?\n\n📋 ตัวอย่างที่ทำได้:\n• วิเคราะห์เนื้อหา\n• สรุปสาระสำคัญ\n• แปลข้อความ\n• อธิบายรายละเอียด\n• ตอบคำถามเกี่ยวกับไฟล์\n\n💬 บอกความต้องการมาได้เลยครับ หรือพิมพ์ "วิเคราะห์" เพื่อวิเคราะห์ทั่วไป`
      });

      // เก็บข้อมูลไฟล์ไว้ใน memory สำหรับการประมวลผลต่อไป
      // ในที่นี้เราจะเก็บ message ID ไว้
      global.pendingFiles = global.pendingFiles || {};
      global.pendingFiles[userId] = {
        messageId: message.id,
        type: message.type,
        timestamp: Date.now()
      };

    } catch (error) {
      console.error('File message error:', error);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: 'ขออภัยครับ ไม่สามารถรับไฟล์ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง 🙏'
      });
    }
  }

  getFileTypeText(type) {
    const types = {
      'image': 'รูปภาพ 🖼️',
      'video': 'วิดีโอ 🎥',
      'audio': 'ไฟล์เสียง 🎵',
      'file': 'เอกสาร 📄'
    };
    return types[type] || 'ไฟล์';
  }

  async processFileWithIntent(replyToken, userId, intent) {
    try {
      const pendingFile = global.pendingFiles?.[userId];
      
      if (!pendingFile) {
        const result = await RequestService.reply(replyToken, {
          type: 'text',
          text: '🤔 ไม่พบไฟล์ที่รอการประมวลผล กรุณาส่งไฟล์ใหม่อีกครั้งครับ'
        });
        if (result === null) console.log('⚠️ Reply skipped - token invalid');
        return;
      }

      // ตรวจสอบว่าไฟล์ไม่เก่าเกิน 10 นาที
      if (Date.now() - pendingFile.timestamp > 10 * 60 * 1000) {
        delete global.pendingFiles[userId];
        const result = await RequestService.reply(replyToken, {
          type: 'text',
          text: '⏰ ไฟล์หมดอายุแล้ว กรุณาส่งไฟล์ใหม่อีกครั้งครับ'
        });
        if (result === null) console.log('⚠️ Reply skipped - token invalid');
        return;
      }

      // แสดงสถานะกำลังประมวลผล
      const processingResult = await RequestService.reply(replyToken, {
        type: 'text',
        text: '⚙️ กำลังประมวลผลไฟล์ตามความต้องการของคุณ รอสักครู่นะครับ...'
      });
      
      if (processingResult === null) {
        console.log('⚠️ Processing message skipped - token invalid');
        return;
      }

      // ดาวน์โหลดไฟล์จาก LINE
      const response = await RequestService.getBinary(pendingFile.messageId);
      
      // บันทึกไฟล์ไว้ใน local
      const fileName = FileHelper.generateFileName(`line_${pendingFile.messageId}`, this.getFileExtension(pendingFile.type));
      const filePath = RequestService.saveFile(response.data, fileName);
      
      // สร้าง prompt ตามความต้องการ
      const prompt = this.createPromptFromIntent(intent, pendingFile.type);
      
      // ประมวลผลไฟล์ด้วย Gemini
      const aiResponse = await GeminiService.processLocalFile(filePath, prompt);
      
      // ใช้ push message แทน reply เพื่อหลีกเลี่ยงปัญหา replyToken
      await RequestService.push(userId, {
        type: 'text',
        text: `✨ ${aiResponse}\n\n🔄 หากต้องการวิเคราะห์แบบอื่น สามารถบอกความต้องการใหม่ได้เลยครับ`
      });
      
      // ลบไฟล์หลังจากประมวลผลเสร็จ
      setTimeout(() => {
        FileHelper.deleteFile(filePath);
      }, 5000);

      // ลบข้อมูลไฟล์ที่รอประมวลผล
      delete global.pendingFiles[userId];
      
    } catch (error) {
      console.error('File processing error:', error);
      try {
        const result = await RequestService.reply(replyToken, {
          type: 'text',
          text: `❌ ขออภัยครับ ไม่สามารถประมวลผลไฟล์ได้\n\n🔍 สาเหตุที่เป็นไปได้:\n• ไฟล์เสียหาย\n• รูปแบบไฟล์ไม่รองรับ\n• ไฟล์ขนาดใหญ่เกินไป\n\n💡 ลองส่งไฟล์ใหม่อีกครั้งครับ`
        });
        if (result === null) console.log('⚠️ Error reply skipped - token invalid');
      } catch (replyError) {
        console.error('❌ Error reply failed:', replyError);
      }
    }
  }

  createPromptFromIntent(intent, fileType) {
    const lowerIntent = intent.toLowerCase();
    
    // วิเคราะห์ความต้องการ
    if (lowerIntent.includes('แปล')) {
      return 'แปลข้อความทั้งหมดในไฟล์นี้เป็นภาษาไทย หากมีข้อความหลายภาษาให้แปลทั้งหมด';
    } else if (lowerIntent.includes('สรุป')) {
      return 'สรุปเนื้อหาสำคัญของไฟล์นี้ให้กระชับและเข้าใจง่าย';
    } else if (lowerIntent.includes('วิเคราะห์')) {
      return 'วิเคราะห์และอธิบายเนื้อหาของไฟล์นี้อย่างละเอียด';
    } else if (lowerIntent.includes('อ่าน') || lowerIntent.includes('ข้อความ')) {
      if (fileType === 'image') {
        return 'อ่านข้อความทั้งหมดที่มีในรูปภาพนี้ และจัดรูปแบบให้อ่านง่าย';
      } else {
        return 'อ่านและแสดงเนื้อหาทั้งหมดในไฟล์นี้';
      }
    } else if (lowerIntent.includes('เสียง') && fileType === 'audio') {
      return 'แปลงเสียงเป็นข้อความและสรุปเนื้อหาที่พูด';
    } else if (lowerIntent.includes('ตาราง') || lowerIntent.includes('ข้อมูล')) {
      return 'วิเคราะห์ตารางหรือข้อมูลในไฟล์นี้ และสรุปผลการวิเคราะห์';
    } else {
      // ความต้องการทั่วไป
      return `ต่อไปนี้คือความต้องการของผู้ใช้: "${intent}"\n\nกรุณาประมวลผลไฟล์นี้ตามความต้องการที่ระบุ หากไม่สามารถทำได้ให้อธิบายเหตุผลและแนะนำทางเลือกอื่น`;
    }
  }

  getFileExtension(type) {
    const extensions = {
      'image': '.jpg',
      'video': '.mp4',
      'audio': '.m4a',
      'file': '.pdf'
    };
    return extensions[type] || '.bin';
  }

  async handleTextMessage(replyToken, message, userId) {
    const text = message.text.toLowerCase();

    // ตรวจสอบว่าเป็นการตอบคำถามเกี่ยวกับไฟล์หรือไม่
    const pendingFile = global.pendingFiles?.[userId];
    if (pendingFile) {
      // มีไฟล์รอประมวลผล ให้ถือว่าเป็นคำสั่งสำหรับไฟล์
      await this.processFileWithIntent(replyToken, userId, message.text);
      return;
    }

    if (text.includes('help') || text.includes('ช่วย')) {
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `🤖 สวัสดีครับ! ผมสามารถช่วยคุณได้ดังนี้:\n\n📎 วิเคราะห์ไฟล์: ส่งรูปภาพ, PDF, เสียง, วิดีโอ มาพร้อมบอกว่าต้องการให้ทำอะไร\n\n💬 สนทนาทั่วไป: ถามคำถามอะไรก็ได้\n\n🔍 คำสั่งพิเศษ: help, status\n\n✨ ตัวอย่าง:\n"วิเคราะห์รูปนี้หน่อย"\n"แปลข้อความในรูป"\n"สรุปเนื้อหา PDF"\n"แปลงเสียงเป็นข้อความ"`
      });
    } else if (text.includes('status')) {
      const uptime = Math.floor(process.uptime() / 60);
      await RequestService.reply(replyToken, {
        type: 'text',
        text: `✅ สถานะระบบ\n🚀 เซิร์ฟเวอร์: ทำงานปกติ\n🤖 AI: พร้อมใช้งาน\n⏱️ เวลาทำงาน: ${uptime} นาที\n📊 อัพเดต: ${new Date().toLocaleString('th-TH')}\n\n💡 ส่งไฟล์หรือข้อความมาได้เลยครับ!`
      });
    } else {
      // Process general text with Gemini
      try {
        const response = await GeminiService.generateContent(
          `คุณเป็น AI ผู้ช่วยที่เป็นมิตรและใจดี ตอบเป็นภาษาไทยแบบสนทนาธรรมชาติ ไม่เป็นทางการมากเกินไป:\n\nคำถาม: ${message.text}`
        );
        await RequestService.reply(replyToken, {
          type: 'text',
          text: response
        });
      } catch (error) {
        await RequestService.reply(replyToken, {
          type: 'text',
          text: 'ขออภัยครับ มีปัญหาในการประมวลผล กรุณาลองใหม่อีกครั้ง 🙏'
        });
      }
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