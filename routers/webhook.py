"""
Router สำหรับ LINE Webhook - AI-Powered Context Analysis
จัดการการรับและประมวลผลข้อความจาก LINE + Smart Context Management
"""
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
from models.line_models import LineWebhookBody, LineEvent, LineReplyMessage
from models.ai_models import IntentAnalysis
from models.file_models import PendingFile
from services.line_service import line_service
from services.gemini_service import gemini_service
from services.file_service import file_service
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    จัดการ LINE Webhook
    รับและประมวลผลข้อความจาก LINE
    """
    try:
        # อ่าน request body
        body = await request.body()
        
        logger.info("🔔 Webhook received")
        
        # แปลง JSON เป็น Pydantic model
        webhook_data = LineWebhookBody.parse_raw(body)
        logger.info(f"📨 Processing {len(webhook_data.events)} events")
        
        # ประมวลผลแต่ละ event ใน background
        for event in webhook_data.events:
            # ข้าม redelivery events
            if event.deliveryContext and event.deliveryContext.get("isRedelivery"):
                logger.info(f"⏭️ Skipping redelivery event: {event.webhookEventId}")
                continue
            
            background_tasks.add_task(process_event, event)
        
        return JSONResponse(
            content={"success": True, "message": "Events queued for processing"},
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=200
        )


async def process_event(event: LineEvent):
    """
    ประมวลผล LINE Event
    """
    try:
        logger.info(f"🎯 Processing event: {event.type}")
        
        if event.type != "message" or not event.message:
            logger.info("⏭️ Skipping non-message event")
            return
        
        user_id = event.source.userId
        if not user_id:
            logger.warning("⚠️ No user ID found")
            return
        
        # แสดง loading indicator
        await line_service.show_loading(user_id)
        
        # ประมวลผลตามประเภทข้อความ
        if event.message.type == "text":
            await handle_text_message(event)
        elif event.message.type in ["image", "video", "audio", "file"]:
            await handle_file_message(event)
        else:
            await handle_unsupported_message(event)
            
    except Exception as e:
        logger.error(f"❌ Event processing error: {str(e)}")
        
        if event.replyToken:
            try:
                await line_service.reply_message(
                    event.replyToken,
                    [LineReplyMessage(
                        type="text",
                        text="เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง 🙏"
                    )]
                )
            except:
                logger.error("❌ Failed to send error message")


async def handle_text_message(event: LineEvent):
    """
    จัดการข้อความแบบข้อความ - ใช้ AI analysis แทน rule-based
    """
    user_id = event.source.userId
    text = event.message.text
    
    logger.info(f"💬 Text message from {user_id}: '{text}'")
    
    # เพิ่มข้อความผู้ใช้ในประวัติ
    file_service.add_conversation_message(user_id, "user", text)
    
    # ตรวจสอบไฟล์ที่รอประมวลผล
    pending_file = file_service.get_pending_file(user_id)
    if pending_file:
        logger.info("📎 Found pending file - processing with intent")
        await process_file_with_intent(event, pending_file, text)
        return
    
    # ตรวจสอบ context เดิม
    existing_context = file_service.get_conversation_context(user_id)
    
    if existing_context:
        logger.info(f"📋 Found existing context: {existing_context.file_type} file")
        
        # ใช้ AI วิเคราะห์ความเกี่ยวข้อง
        ai_analysis = await file_service.analyze_context_with_ai(user_id, text)
        
        logger.info(f"🤖 AI Analysis: Related={ai_analysis.is_related}, Confidence={ai_analysis.confidence:.2f}")
        logger.info(f"🤖 AI Reasoning: {ai_analysis.reasoning}")
        
        # อัพเดต context ด้วยผลการวิเคราะห์ของ AI
        existing_context.update_ai_analysis(ai_analysis.confidence, ai_analysis.reasoning)
        
        if not ai_analysis.should_keep_context:
            logger.info("🗑️ AI decided to clear context - message not related")
            file_service.clear_all_user_data(user_id)
            await handle_general_conversation(event)
            return
        
        # ถ้า AI ตัดสินใจว่าเกี่ยวข้อง
        logger.info("🔗 AI confirmed message is related - continuing context")
        
        # สร้าง PendingFile จาก context เดิม
        fake_pending = PendingFile(
            message_id="context_reuse",
            file_type=existing_context.file_type,
            user_id=user_id
        )
        
        await process_file_with_intent(event, fake_pending, text)
        return
    
    # จัดการคำสั่งพิเศษ
    text_lower = text.lower()
    if any(word in text_lower for word in ["help", "ช่วย"]):
        await send_help_message(event.replyToken)
        # เพิ่มในประวัติ
        file_service.add_conversation_message(user_id, "assistant", "ส่งข้อความช่วยเหลือ")
    elif "status" in text_lower:
        await send_status_message(event.replyToken)
        # เพิ่มในประวัติ
        file_service.add_conversation_message(user_id, "assistant", "แสดงสถานะระบบ")
    else:
        # สนทนาทั่วไปกับ AI
        await handle_general_conversation(event)


async def handle_file_message(event: LineEvent):
    """
    จัดการข้อความที่มีไฟล์
    """
    user_id = event.source.userId
    message_id = event.message.id
    file_type = event.message.type
    
    try:
        # ลบ context เดิม (หากมี) เมื่อมีไฟล์ใหม่
        existing_context = file_service.get_conversation_context(user_id)
        if existing_context:
            logger.info("🗑️ Removing old context - new file received")
            file_service.clear_all_user_data(user_id)
        
        # เพิ่มข้อความการอัพโหลดไฟล์ในประวัติ
        file_service.add_conversation_message(
            user_id, 
            "user", 
            f"ส่งไฟล์ {file_type}", 
            message_type="file_upload",
            file_reference=message_id
        )
        
        # เพิ่มไฟล์ที่รอการประมวลผล
        file_service.add_pending_file(user_id, message_id, file_type)
        
        # ส่งข้อความถามความต้องการ
        file_type_text = gemini_service.get_file_type_text(file_type)
        
        message_text = f"""📎 ได้รับ{file_type_text}แล้วครับ!

🤔 คุณต้องการให้ผมทำอะไรกับไฟล์นี้ครับ?

📋 ตัวอย่างที่ทำได้:
• วิเคราะห์เนื้อหา
• สรุปสาระสำคัญ
• แปลข้อความ
• อธิบายรายละเอียด
• ตอบคำถามเกี่ยวกับไฟล์

💬 บอกความต้องการมาได้เลยครับ หรือพิมพ์ "วิเคราะห์" เพื่อวิเคราะห์ทั่วไป

💡 **AI Context Awareness**: หลังจากประมวลผลแล้ว คุณสามารถถามคำถามเพิ่มเติมเกี่ยวกับไฟล์นี้ได้โดยไม่ต้องส่งใหม่!"""

        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(type="text", text=message_text)]
        )
        
        # เพิ่มข้อความของ AI ในประวัติ
        file_service.add_conversation_message(user_id, "assistant", "ถามความต้องการสำหรับไฟล์ที่ส่งมา")
        
    except Exception as e:
        logger.error(f"❌ File message error: {str(e)}")
        error_msg = "ขออภัยครับ ไม่สามารถรับไฟล์ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง 🙏"
        
        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(type="text", text=error_msg)]
        )
        
        file_service.add_conversation_message(user_id, "assistant", error_msg)


async def process_file_with_intent(event: LineEvent, pending_file, intent: str):
    """
    ประมวลผลไฟล์ตามความตั้งใจ - เก็บประวัติครบถ้วน + AI Analysis
    """
    user_id = event.source.userId
    
    try:
        # ตรวจสอบ context เดิม
        existing_context = file_service.get_conversation_context(user_id)
        current_intent = IntentAnalysis.analyze_intent(intent).intent_type
        
        # ใช้ AI วิเคราะห์ความเกี่ยวข้อง (สำหรับไฟล์ใหม่)
        if existing_context and pending_file.message_id != "context_reuse":
            ai_analysis = await file_service.analyze_context_with_ai(user_id, intent)
            
            if ai_analysis.should_keep_context:
                logger.info(f"🔗 AI confirmed new file relates to previous context")
                file_path = existing_context.file_path
                file_service.update_conversation_context(user_id, intent, ai_analysis.confidence)
            else:
                logger.info(f"📎 Processing new file - AI says different context")
                # ประมวลผลไฟล์ใหม่
                content = await line_service.get_message_content(pending_file.message_id)
                if not content:
                    raise Exception("ไม่สามารถดาวน์โหลดไฟล์ได้")
                
                base_filename = f"line_{pending_file.message_id}_{int(pending_file.timestamp.timestamp())}"
                file_path = await file_service.save_binary_content_with_extension(content, base_filename, pending_file.file_type)
        
        elif existing_context and pending_file.message_id == "context_reuse":
            # ใช้ไฟล์เดิม
            file_path = existing_context.file_path
            file_service.update_conversation_context(user_id, intent)
            
            await line_service.reply_message(
                event.replyToken,
                [LineReplyMessage(text="🔄 กำลังประมวลผลไฟล์เดิมตามคำสั่งใหม่... ระบบ AI จดจำไฟล์ของคุณแล้ว!")]
            )
        
        else:
            # ไฟล์ใหม่ - ไม่มี context เดิม
            content = await line_service.get_message_content(pending_file.message_id)
            if not content:
                raise Exception("ไม่สามารถดาวน์โหลดไฟล์ได้")
            
            base_filename = f"line_{pending_file.message_id}_{int(pending_file.timestamp.timestamp())}"
            file_path = await file_service.save_binary_content_with_extension(content, base_filename, pending_file.file_type)
            
            await line_service.reply_message(
                event.replyToken,
                [LineReplyMessage(text="⚙️ กำลังประมวลผลไฟล์ใหม่... AI จะจดจำไฟล์นี้เพื่อการสนทนาต่อเนื่อง")]
            )
        
        # เพิ่มข้อความการประมวลผลในประวัติ
        file_service.add_conversation_message(
            user_id, 
            "user", 
            intent, 
            message_type="file_analysis",
            file_reference=file_path
        )
        
        # สร้าง prompt และประมวลผล
        prompt = gemini_service.create_prompt_from_intent(intent, pending_file.file_type)
        ai_response = await gemini_service.process_file(file_path, prompt)
        
        if ai_response.success:
            # เพิ่มคำตอบของ AI ในประวัติ
            file_service.add_conversation_message(user_id, "assistant", ai_response.text)
            
            # สร้างข้อความตอบกลับพร้อมคำแนะนำ AI
            response_text = f"✨ {ai_response.text}"
            
            # เพิ่มคำแนะนำเกี่ยวกับ Context Awareness
            response_text += f"\n\n🤖 **AI Context Awareness**\n💡 คุณสามารถถามคำถามเพิ่มเติมเกี่ยวกับไฟล์นี้ได้โดยไม่ต้องส่งใหม่\n🔄 เช่น: \"แปลข้อความในไฟล์\" หรือ \"สรุปใหม่อีกครั้ง\"\n⏰ ระบบจะจดจำไฟล์นี้เป็นเวลา 15 นาที"
            
            # ส่งผลลัพธ์
            await line_service.push_message(
                user_id,
                [LineReplyMessage(type="text", text=response_text)]
            )
            
            # เพิ่ม/อัพเดต conversation context พร้อม AI summary
            if not existing_context:
                file_service.add_conversation_context(
                    user_id, file_path, pending_file.file_type, current_intent, ai_response.text
                )
                
                # สร้าง AI summary แบบ async
                await file_service.update_context_with_ai_summary(user_id)
        
        else:
            error_msg = f"❌ ขออภัยครับ ไม่สามารถประมวลผลไฟล์ได้\n\n{ai_response.error_message or 'เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ'}"
            file_service.add_conversation_message(user_id, "assistant", error_msg)
            
            await line_service.push_message(
                user_id,
                [LineReplyMessage(type="text", text=error_msg)]
            )
        
        # ลบข้อมูล pending file เสมอ
        file_service.remove_pending_file(user_id)
        
    except Exception as e:
        logger.error(f"❌ File processing error: {str(e)}")
        
        error_msg = f"""❌ ขออภัยครับ ไม่สามารถประมวลผลไฟล์ได้

🔍 สาเหตุที่เป็นไปได้:
• ไฟล์เสียหาย
• รูปแบบไฟล์ไม่รองรับ
• ไฟล์ขนาดใหญ่เกินไป
• ปัญหาการเชื่อมต่อ

💡 ลองส่งไฟล์ใหม่อีกครั้งครับ หรือลดขนาดไฟล์"""
        
        file_service.add_conversation_message(user_id, "assistant", error_msg)
        
        await line_service.push_message(
            user_id,
            [LineReplyMessage(type="text", text=error_msg)]
        )
        
        file_service.remove_pending_file(user_id)


async def handle_general_conversation(event: LineEvent):
    """
    จัดการการสนทนาทั่วไป - เพิ่มในประวัติ
    """
    user_id = event.source.userId
    text = event.message.text
    
    try:
        # ดึงประวัติการสนทนาเพื่อให้ AI มีบริบท
        conversation_history = file_service.get_conversation_history(user_id, limit=5)
        
        # สร้าง prompt ที่มีบริบทการสนทนา
        if conversation_history:
            context_text = "\n".join(conversation_history[-3:])  # ใช้ 3 ข้อความล่าสุด
            prompt = f"""คุณเป็น AI ผู้ช่วยที่เป็นมิตรและใจดี ตอบเป็นภาษาไทยแบบสนทนาธรรมชาติ

บริบทการสนทนาก่อนหน้า:
{context_text}

คำถามปัจจุบัน: {text}

กรุณาตอบโดยคำนึงถึงบริบทการสนทนาที่ผ่านมา แต่เน้นการตอบคำถามปัจจุบันเป็นหลัก"""
        else:
            prompt = f"""คุณเป็น AI ผู้ช่วยที่เป็นมิตรและใจดี ตอบเป็นภาษาไทยแบบสนทนาธรรมชาติ:

คำถาม: {text}"""
        
        ai_response = await gemini_service.generate_text(prompt)
        
        # เพิ่มคำตอบของ AI ในประวัติ
        file_service.add_conversation_message(user_id, "assistant", ai_response.text)
        
        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(type="text", text=ai_response.text)]
        )
        
    except Exception as e:
        logger.error(f"❌ Conversation error: {str(e)}")
        error_msg = "ขออภัยครับ มีปัญหาในการประมวลผล กรุณาลองใหม่อีกครั้ง 🙏"
        
        file_service.add_conversation_message(user_id, "assistant", error_msg)
        
        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(type="text", text=error_msg)]
        )


async def send_help_message(reply_token: str):
    """ส่งข้อความช่วยเหลือ - เวอร์ชันใหม่ที่เน้น AI Context"""
    help_text = """🤖 สวัสดีครับ! ผมเป็น AI Assistant ที่ขับเคลื่อนด้วย Google Gemini

✨ **ความสามารถหลัก:**
📎 **วิเคราะห์ไฟล์**: ส่งรูปภาพ, PDF, เสียง, วิดีโอ พร้อมบอกว่าต้องการให้ทำอะไร

🧠 **AI Context Awareness**: 
• จดจำไฟล์และบริบทการสนทนา
• ตอบคำถามเพิ่มเติมโดยไม่ต้องส่งไฟล์ใหม่
• วิเคราะห์ว่าคำถามเกี่ยวข้องกับไฟล์เดิมหรือไม่

💬 **สนทนาธรรมชาติ**: ถามคำถามอะไรก็ได้

🔍 **คำสั่งพิเศษ**: help, status

✨ **ตัวอย่างการใช้งาน:**
1. ส่งรูป + "วิเคราะห์เนื้อหา"
2. ถามต่อ: "แปลข้อความในรูป" (ไม่ต้องส่งรูปใหม่)
3. ถามต่อ: "สรุปสาระสำคัญ" (ใช้รูปเดิม)
4. เปลี่ยนหัวข้อ: "อากาศวันนี้เป็นไง" (AI จะลบไฟล์เดิม)

🎯 **จุดเด่น:**
• ใช้ AI วิเคราะห์บริบทแทนการจับคำ
• เก็บประวัติการสนทนาทั้งหมด
• ตัดสินใจอัจฉริยะว่าเมื่อไหร่ควรลบไฟล์
• รองรับไฟล์หลากหลายประเภท

⚠️ **หมายเหตุ**: ระบบจะจดจำบริบทเป็นเวลา 15 นาทีหลังจากไม่มีการใช้งาน"""

    await line_service.reply_message(
        reply_token,
        [LineReplyMessage(type="text", text=help_text)]
    )


async def send_status_message(reply_token: str):
    """ส่งข้อความสถานะระบบ - เพิ่มข้อมูล AI Context"""
    import psutil
    
    # ดึงข้อมูลระบบ
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # ดึงสถิติ AI Context Management
    stats = file_service.get_system_statistics()
    
    status_text = f"""✅ **สถานะระบบ AI Assistant**

🚀 **เซิร์ฟเวอร์**: ทำงานปกติ
🤖 **Gemini AI**: พร้อมใช้งาน  
🧠 **Context Management**: ใช้งานได้
💾 **หน่วยความจำ**: {memory.percent}%
🔧 **CPU**: {cpu_percent}%

📊 **สถิติ AI Context:**
🗣️ การสนทนาที่ใช้งาน: {stats.get('contexts', {}).get('active', 0)} บทสนทนา
📝 ประวัติการสนทนา: {stats.get('histories', {}).get('active', 0)} ประวัติ
📁 ไฟล์รอประมวลผล: {stats.get('pending_files', {}).get('active', 0)} ไฟล์
💾 ไฟล์ที่เก็บไว้: {stats.get('upload_files', {}).get('count', 0)} ไฟล์

⏰ **อัพเดต**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 **AI Features:**
• บริบทการสนทนาอัจฉริยะ
• วิเคราะห์ความเกี่ยวข้องด้วย AI
• จัดการไฟล์อัตโนมัติ
• สรุปการสนทนาด้วย AI

💡 ส่งไฟล์หรือข้อความมาได้เลยครับ!
🧹 ระบบจะลบไฟล์อัตโนมัติเมื่อ AI ตัดสินว่าไม่เกี่ยวข้องแล้ว"""

    await line_service.reply_message(
        reply_token,
        [LineReplyMessage(type="text", text=status_text)]
    )


async def handle_unsupported_message(event: LineEvent):
    """จัดการข้อความที่ไม่รองรับ"""
    user_id = event.source.userId
    unsupported_msg = "ขออภัย ยังไม่รองรับข้อความประเภทนี้ กรุณาส่งข้อความหรือไฟล์ (รูป, เสียง, วิดีโอ, PDF) ครับ"
    
    await line_service.reply_message(
        event.replyToken,
        [LineReplyMessage(type="text", text=unsupported_msg)]
    )
    
    # เพิ่มในประวัติ
    file_service.add_conversation_message(user_id, "assistant", unsupported_msg)


@router.get("/")
async def webhook_status():
    """
    ตรวจสอบสถานะ Webhook
    """
    return {
        "status": "LINE Webhook endpoint is ready",
        "ai_features": {
            "context_awareness": "enabled",
            "conversation_history": "enabled", 
            "ai_analysis": "enabled",
            "smart_file_management": "enabled"
        },
        "timestamp": datetime.now().isoformat()
    }