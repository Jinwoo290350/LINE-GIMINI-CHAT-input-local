"""
Router สำหรับ LINE Webhook - เวอร์ชันสุดท้าย
จัดการการรับและประมวลผลข้อความจาก LINE + Context Awareness ที่ชาญฉลาด
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
from services.content_analyzer import content_analyzer
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
    จัดการข้อความแบบข้อความ (เวอร์ชันสุดท้าย - แก้ไขแล้ว)
    """
    user_id = event.source.userId
    text = event.message.text
    
    logger.info(f"💬 Text message from {user_id}: '{text}'")
    
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
        
        # **KEY FIX: เพิ่มการตรวจสอบว่าควรลบ context หรือไม่**
        should_clear = content_analyzer.should_clear_context(text, existing_context)
        
        if should_clear:
            logger.info("🗑️ Clearing context - message not related to previous file")
            file_service.remove_conversation_context(user_id)
            # ประมวลผลเป็นการสนทนาทั่วไป
            await handle_general_conversation(event)
            return
        
        # ถ้าเกี่ยวข้องกับไฟล์เดิม
        logger.info("🔗 Message related to previous file - continuing context")
        
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
    elif "status" in text_lower:
        await send_status_message(event.replyToken)
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
            file_service.remove_conversation_context(user_id)
        
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

💬 บอกความต้องการมาได้เลยครับ หรือพิมพ์ "วิเคราะห์" เพื่อวิเคราะห์ทั่วไป"""

        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(type="text", text=message_text)]
        )
        
    except Exception as e:
        logger.error(f"❌ File message error: {str(e)}")
        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(
                type="text",
                text="ขออภัยครับ ไม่สามารถรับไฟล์ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง 🙏"
            )]
        )


async def process_file_with_intent(event: LineEvent, pending_file, intent: str):
    """
    ประมวลผลไฟล์ตามความตั้งใจของผู้ใช้ (ปรับปรุงแล้ว)
    """
    user_id = event.source.userId
    
    try:
        # ตรวจสอบ context เดิม
        existing_context = file_service.get_conversation_context(user_id)
        current_intent = IntentAnalysis.analyze_intent(intent).intent_type
        
        # ถ้ามี context เดิมและเป็นเรื่องเดียวกัน
        if existing_context and content_analyzer.is_related_to_previous(intent, existing_context):
            logger.info(f"🔗 Continuing previous conversation - reusing file: {existing_context.file_path}")
            
            # ใช้ไฟล์เดิม
            file_path = existing_context.file_path
            
            # อัพเดต context
            file_service.update_conversation_context(user_id, current_intent)
            
            # ส่งข้อความแจ้งว่ากำลังประมวลผล
            await line_service.reply_message(
                event.replyToken,
                [LineReplyMessage(
                    type="text",
                    text=f"🔄 กำลังประมวลผลไฟล์เดิมตามคำสั่งใหม่: {intent} รอสักครู่นะครับ..."
                )]
            )
            
        else:
            # ประมวลผลไฟล์ใหม่
            logger.info(f"📎 Processing new file for intent: {current_intent}")
            
            # ส่งข้อความแจ้งว่ากำลังประมวลผล
            await line_service.reply_message(
                event.replyToken,
                [LineReplyMessage(
                    type="text",
                    text="⚙️ กำลังประมวลผลไฟล์ตามความต้องการของคุณ รอสักครู่นะครับ..."
                )]
            )
            
            # ดาวน์โหลดไฟล์จาก LINE (เฉพาะไฟล์ใหม่)
            if pending_file.message_id != "context_reuse":
                content = await line_service.get_message_content(pending_file.message_id)
                if not content:
                    raise Exception("ไม่สามารถดาวน์โหลดไฟล์ได้")
                
                # บันทึกไฟล์
                filename = f"line_{pending_file.message_id}_{int(pending_file.timestamp.timestamp())}.bin"
                file_path = await file_service.save_binary_content(content, filename)
            else:
                # ใช้ไฟล์จาก existing context
                file_path = existing_context.file_path
        
        # สร้าง prompt ตามความตั้งใจ
        prompt = gemini_service.create_prompt_from_intent(intent, pending_file.file_type)
        
        # ประมวลผลด้วย AI
        ai_response = await gemini_service.process_file(file_path, prompt)
        
        if ai_response.success:
            # วิเคราะห์เนื้อหาที่ได้จาก AI เพื่อหา intent เพิ่มเติม
            content_analysis = content_analyzer.analyze_content(ai_response.text, pending_file.file_type)
            
            # สร้างข้อความตอบกลับพร้อมคำแนะนำ
            response_text = f"✨ {ai_response.text}"
            
            # เพิ่มคำแนะนำถ้ามี suggested actions
            if content_analysis.suggested_actions:
                suggestions = content_analysis.suggested_actions[:3]  # เอาแค่ 3 ตัวแรก
                response_text += f"\n\n💡 คำแนะนำเพิ่มเติม:\n"
                for i, suggestion in enumerate(suggestions, 1):
                    response_text += f"{i}. {suggestion}\n"
                response_text += "\n🔄 หากต้องการวิเคราะห์แบบอื่น สามารถบอกความต้องการใหม่ได้เลยครับ"
            
            # ส่งผลลัพธ์ด้วย push message
            await line_service.push_message(
                user_id,
                [LineReplyMessage(
                    type="text",
                    text=response_text
                )]
            )
            
            # เพิ่ม/อัพเดต conversation context
            if not existing_context:
                file_service.add_conversation_context(user_id, file_path, pending_file.file_type, current_intent, ai_response.text)
            
        else:
            await line_service.push_message(
                user_id,
                [LineReplyMessage(
                    type="text",
                    text=f"❌ ขออภัยครับ ไม่สามารถประมวลผลไฟล์ได้\n\n{ai_response.error_message or 'เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ'}"
                )]
            )
        
        # ตัดสินใจเรื่องการลบไฟล์
        should_keep = file_service.should_keep_file_for_user(user_id, current_intent)
        
        if not should_keep:
            # ลบไฟล์และข้อมูลที่รอประมวลผล
            file_service.delete_file(file_path)
            file_service.remove_conversation_context(user_id)
            logger.info(f"🗑️ File deleted immediately - no future use expected")
        else:
            logger.info(f"📁 File kept for potential future use")
        
        # ลบข้อมูล pending file เสมอ
        file_service.remove_pending_file(user_id)
        
    except Exception as e:
        logger.error(f"❌ File processing error: {str(e)}")
        
        await line_service.push_message(
            user_id,
            [LineReplyMessage(
                type="text",
                text=f"""❌ ขออภัยครับ ไม่สามารถประมวลผลไฟล์ได้

🔍 สาเหตุที่เป็นไปได้:
• ไฟล์เสียหาย
• รูปแบบไฟล์ไม่รองรับ
• ไฟล์ขนาดใหญ่เกินไป

💡 ลองส่งไฟล์ใหม่อีกครั้งครับ"""
            )]
        )
        
        file_service.remove_pending_file(user_id)


async def handle_general_conversation(event: LineEvent):
    """
    จัดการการสนทนาทั่วไป
    """
    try:
        prompt = f"""คุณเป็น AI ผู้ช่วยที่เป็นมิตรและใจดี ตอบเป็นภาษาไทยแบบสนทนาธรรมชาติ ไม่เป็นทางการมากเกินไป:

คำถาม: {event.message.text}"""
        
        ai_response = await gemini_service.generate_text(prompt)
        
        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(type="text", text=ai_response.text)]
        )
        
    except Exception as e:
        logger.error(f"❌ Conversation error: {str(e)}")
        await line_service.reply_message(
            event.replyToken,
            [LineReplyMessage(
                type="text",
                text="ขออภัยครับ มีปัญหาในการประมวลผล กรุณาลองใหม่อีกครั้ง 🙏"
            )]
        )


async def send_help_message(reply_token: str):
    """ส่งข้อความช่วยเหลือ"""
    help_text = """🤖 สวัสดีครับ! ผมสามารถช่วยคุณได้ดังนี้:

📎 วิเคราะห์ไฟล์: ส่งรูปภาพ, PDF, เสียง, วิดีโอ มาพร้อมบอกว่าต้องการให้ทำอะไร

💬 สนทนาทั่วไป: ถามคำถามอะไรก็ได้

🔍 คำสั่งพิเศษ: help, status

✨ ตัวอย่าง:
"วิเคราะห์รูปนี้หน่อย"
"แปลข้อความในรูป"
"สรุปเนื้อหา PDF"
"แปลงเสียงเป็นข้อความ"

🔄 ความพิเศษ: หลังจากส่งไฟล์และประมวลผลแล้ว คุณสามารถขอให้ประมวลผลเรื่องอื่นจากไฟล์เดิมได้โดยไม่ต้องส่งใหม่!

⚠️ หมายเหตุ: หากคุณถามคำถามที่ไม่เกี่ยวข้องกับไฟล์ ระบบจะลบไฟล์เดิมออกเพื่อประหยัดพื้นที่"""

    await line_service.reply_message(
        reply_token,
        [LineReplyMessage(type="text", text=help_text)]
    )


async def send_status_message(reply_token: str):
    """ส่งข้อความสถานะระบบ"""
    import psutil
    
    # ดึงข้อมูลระบบ
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # ดึงจำนวน active contexts
    active_contexts = len(file_service.conversation_contexts)
    
    status_text = f"""✅ สถานะระบบ

🚀 เซิร์ฟเวอร์: ทำงานปกติ
🤖 AI: พร้อมใช้งาน
💾 หน่วยความจำ: {memory.percent}%
🔧 CPU: {cpu_percent}%
🗣️ การสนทนาที่ใช้งาน: {active_contexts} บทสนทนา
📊 อัพเดต: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 ส่งไฟล์หรือข้อความมาได้เลยครับ!
🔄 ระบบจดจำไฟล์ที่คุณส่งมาเพื่อประมวลผลต่อเนื่อง
🧹 ระบบจะลบไฟล์เดิมเมื่อคุณถามคำถามที่ไม่เกี่ยวข้อง"""

    await line_service.reply_message(
        reply_token,
        [LineReplyMessage(type="text", text=status_text)]
    )


async def handle_unsupported_message(event: LineEvent):
    """จัดการข้อความที่ไม่รองรับ"""
    await line_service.reply_message(
        event.replyToken,
        [LineReplyMessage(
            type="text",
            text="ขออภัย ยังไม่รองรับข้อความประเภทนี้ กรุณาส่งข้อความหรือไฟล์ (รูป, เสียง, วิดีโอ, PDF) ครับ"
        )]
    )


@router.get("/")
async def webhook_status():
    """
    ตรวจสอบสถานะ Webhook
    """
    return {
        "status": "LINE Webhook endpoint is ready",
        "timestamp": datetime.now().isoformat()
    }