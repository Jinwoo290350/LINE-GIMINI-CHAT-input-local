"""
Debug Router สำหรับ AI Context Management
ใช้สำหรับ debug และ monitoring ระบบ AI context awareness
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
from services.file_service import file_service
from services.gemini_service import gemini_service
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/contexts")
async def get_all_contexts():
    """
    ดึงข้อมูล contexts ทั้งหมด (สำหรับ debug) - เวอร์ชัน AI Enhanced
    """
    try:
        contexts_data = []
        
        for user_id, context in file_service.conversation_contexts.items():
            contexts_data.append({
                "user_id": user_id,
                "file_path": context.file_path,
                "file_type": context.file_type,
                "original_intent": context.original_intent,
                "detected_intents": context.detected_intents,
                "interaction_count": context.interaction_count,
                "last_activity": context.last_activity.isoformat(),
                "should_keep_file": context.should_keep_file,
                "is_expired": context.is_expired,
                # AI-specific fields
                "ai_confidence": context.ai_confidence,
                "ai_reasoning": context.ai_reasoning,
                "conversation_summary": context.conversation_summary,
                "content_preview": context.processed_content[:200] + "..." if context.processed_content else None
            })
        
        return JSONResponse(content={
            "success": True,
            "contexts": contexts_data,
            "total": len(contexts_data),
            "ai_powered": True,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Debug contexts error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/context/{user_id}")
async def get_user_context(user_id: str):
    """
    ดึงข้อมูล context ของผู้ใช้คนใดคนหนึ่ง - เพิ่มข้อมูล AI และประวัติ
    """
    try:
        context = file_service.get_conversation_context(user_id)
        history = file_service.get_conversation_history_object(user_id)
        
        if not context and not history:
            return JSONResponse(content={
                "success": False,
                "message": "No context or history found for this user"
            })
        
        result = {
            "success": True,
            "user_id": user_id
        }
        
        # Context data
        if context:
            result["context"] = {
                "file_path": context.file_path,
                "file_type": context.file_type,
                "original_intent": context.original_intent,
                "detected_intents": context.detected_intents,
                "interaction_count": context.interaction_count,
                "last_activity": context.last_activity.isoformat(),
                "should_keep_file": context.should_keep_file,
                "is_expired": context.is_expired,
                # AI fields
                "ai_confidence": context.ai_confidence,
                "ai_reasoning": context.ai_reasoning,
                "conversation_summary": context.conversation_summary,
                "processed_content_preview": context.processed_content[:200] if context.processed_content else None
            }
        
        # History data
        if history:
            result["conversation_history"] = {
                "total_messages": len(history.messages),
                "created_at": history.created_at.isoformat(),
                "last_updated": history.last_updated.isoformat(),
                "is_expired": history.is_expired,
                "recent_messages": [
                    {
                        "timestamp": msg.timestamp.isoformat(),
                        "role": msg.role,
                        "message_type": msg.message_type,
                        "content_preview": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "file_reference": msg.file_reference
                    }
                    for msg in history.get_recent_messages(10)
                ]
            }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"❌ Debug user context error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.delete("/context/{user_id}")
async def clear_user_context(user_id: str):
    """
    ลบ context และประวัติของผู้ใช้ (สำหรับ debug)
    """
    try:
        context = file_service.get_conversation_context(user_id)
        history = file_service.get_conversation_history_object(user_id)
        
        if not context and not history:
            return JSONResponse(content={
                "success": False,
                "message": "No context or history found for this user"
            })
        
        # ลบข้อมูลทั้งหมด
        file_service.clear_all_user_data(user_id)
        
        return JSONResponse(content={
            "success": True,
            "message": f"All data cleared for user: {user_id}",
            "cleared": {
                "context": context is not None,
                "history": history is not None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Clear context error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.post("/cleanup/contexts")
async def force_cleanup_contexts():
    """
    บังคับทำความสะอาด contexts และประวัติที่หมดอายุ
    """
    try:
        # เก็บจำนวนก่อนทำความสะอาด
        before_contexts = len(file_service.conversation_contexts)
        before_histories = len(file_service.conversation_histories)
        
        file_service.cleanup_expired_contexts()
        
        # นับหลังทำความสะอาด
        after_contexts = len(file_service.conversation_contexts)
        after_histories = len(file_service.conversation_histories)
        
        cleaned_contexts = before_contexts - after_contexts
        cleaned_histories = before_histories - after_histories
        
        return JSONResponse(content={
            "success": True,
            "message": f"Cleaned up {cleaned_contexts} contexts and {cleaned_histories} histories",
            "contexts": {
                "before": before_contexts,
                "after": after_contexts,
                "cleaned": cleaned_contexts
            },
            "histories": {
                "before": before_histories,
                "after": after_histories,
                "cleaned": cleaned_histories
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Force cleanup error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/conversation-histories")
async def get_conversation_histories():
    """
    ดึงข้อมูลประวัติการสนทนาทั้งหมด
    """
    try:
        histories_data = []
        
        for user_id, history in file_service.conversation_histories.items():
            histories_data.append({
                "user_id": user_id,
                "total_messages": len(history.messages),
                "created_at": history.created_at.isoformat(),
                "last_updated": history.last_updated.isoformat(),
                "is_expired": history.is_expired,
                "message_types": {
                    "text": len([m for m in history.messages if m.message_type == "text"]),
                    "file_upload": len([m for m in history.messages if m.message_type == "file_upload"]),
                    "file_analysis": len([m for m in history.messages if m.message_type == "file_analysis"])
                },
                "role_distribution": {
                    "user": len([m for m in history.messages if m.role == "user"]),
                    "assistant": len([m for m in history.messages if m.role == "assistant"])
                },
                "recent_activity": [
                    {
                        "timestamp": msg.timestamp.isoformat(),
                        "role": msg.role,
                        "type": msg.message_type,
                        "content_preview": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    }
                    for msg in history.get_recent_messages(5)
                ]
            })
        
        return JSONResponse(content={
            "success": True,
            "histories": histories_data,
            "total": len(histories_data),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Get conversation histories error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/pending-files")
async def get_pending_files():
    """
    ดูไฟล์ที่รอการประมวลผล
    """
    try:
        pending_data = []
        
        for user_id, pending_file in file_service.pending_files.items():
            pending_data.append({
                "user_id": user_id,
                "message_id": pending_file.message_id,
                "file_type": pending_file.file_type,
                "timestamp": pending_file.timestamp.isoformat(),
                "is_expired": pending_file.is_expired,
                "age_seconds": (datetime.now() - pending_file.timestamp).total_seconds()
            })
        
        return JSONResponse(content={
            "success": True,
            "pending_files": pending_data,
            "total": len(pending_data),
            "active": len([p for p in pending_data if not p["is_expired"]]),
            "expired": len([p for p in pending_data if p["is_expired"]])
        })
        
    except Exception as e:
        logger.error(f"❌ Get pending files error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.post("/analyze-intent")
async def analyze_intent_debug(text: str):
    """
    ทดสอบการวิเคราะห์ intent ด้วย AI
    """
    try:
        # ใช้ AI วิเคราะห์ context (จำลอง conversation history)
        fake_history = [
            "ผู้ใช้: ส่งรูปภาพ",
            "AI: ได้รับรูปภาพแล้ว",
            "ผู้ใช้: วิเคราะห์รูปนี้",
            "AI: รูปนี้เป็นเมนูอาหารไทย..."
        ]
        
        # วิเคราะห์ด้วย AI
        analysis = await gemini_service.analyze_context_relevance(
            current_prompt=text,
            conversation_history=fake_history,
            file_context="ไฟล์: image - เมนูอาหารไทยที่มีหลายจาน..."
        )
        
        # วิเคราะห์ด้วย IntentAnalysis (rule-based)
        from models.ai_models import IntentAnalysis
        intent_analysis = IntentAnalysis.analyze_intent(text)
        
        return JSONResponse(content={
            "success": True,
            "input_text": text,
            "ai_analysis": {
                "is_related": analysis.get("is_related", False),
                "confidence": analysis.get("confidence", 0.0),
                "reasoning": analysis.get("reasoning", ""),
                "action": analysis.get("action", ""),
                "related_aspects": analysis.get("related_aspects", [])
            },
            "rule_based_analysis": {
                "intent_type": intent_analysis.intent_type,
                "confidence": intent_analysis.confidence
            },
            "comparison": {
                "ai_vs_rules": "AI analysis provides context awareness, rules provide intent classification",
                "recommendation": "Use AI for context decisions, rules for intent parsing"
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Analyze intent error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.post("/test-ai-context")
async def test_ai_context_analysis(
    current_prompt: str,
    conversation_history: list = None,
    file_context: str = None
):
    """
    ทดสอบ AI context analysis แบบกำหนดเอง
    """
    try:
        if conversation_history is None:
            conversation_history = []
        
        analysis = await gemini_service.analyze_context_relevance(
            current_prompt=current_prompt,
            conversation_history=conversation_history,
            file_context=file_context
        )
        
        return JSONResponse(content={
            "success": True,
            "input": {
                "current_prompt": current_prompt,
                "conversation_history": conversation_history,
                "file_context": file_context
            },
            "ai_analysis": analysis,
            "recommendation": {
                "should_keep_context": analysis.get("is_related", False) and analysis.get("confidence", 0) > 0.6,
                "confidence_level": "high" if analysis.get("confidence", 0) > 0.8 else "medium" if analysis.get("confidence", 0) > 0.5 else "low"
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Test AI context error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/system-stats")
async def get_system_stats():
    """
    ดูสถิติระบบโดยรวม - เวอร์ชัน AI Enhanced
    """
    try:
        import psutil
        
        # ข้อมูลระบบ
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # ข้อมูล AI contexts
        stats = file_service.get_system_statistics()
        
        # วิเคราะห์ AI confidence scores
        confidence_scores = [ctx.ai_confidence for ctx in file_service.conversation_contexts.values()]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # วิเคราะห์ประเภทไฟล์ที่ใช้งาน
        file_types = {}
        for ctx in file_service.conversation_contexts.values():
            file_types[ctx.file_type] = file_types.get(ctx.file_type, 0) + 1
        
        # วิเคราะห์ intents ที่พบ
        all_intents = []
        for ctx in file_service.conversation_contexts.values():
            all_intents.extend(ctx.detected_intents)
        
        intent_counts = {}
        for intent in all_intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # ข้อมูลไฟล์ในโฟลเดอร์ uploads
        upload_files = list(Path(file_service.upload_dir).glob("*"))
        upload_files_count = len([f for f in upload_files if f.is_file() and f.name != '.gitkeep'])
        
        return JSONResponse(content={
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "ai_context_stats": stats,
            "ai_analysis": {
                "average_confidence": round(avg_confidence, 2),
                "high_confidence_contexts": len([c for c in confidence_scores if c > 0.8]),
                "medium_confidence_contexts": len([c for c in confidence_scores if 0.5 < c <= 0.8]),
                "low_confidence_contexts": len([c for c in confidence_scores if c <= 0.5])
            },
            "content_analysis": {
                "popular_file_types": file_types,
                "detected_intents": intent_counts,
                "total_unique_intents": len(intent_counts)
            },
            "storage": {
                "upload_files_count": upload_files_count,
                "upload_directory": str(file_service.upload_dir)
            },
            "features": {
                "ai_context_awareness": "enabled",
                "conversation_history": "enabled",
                "smart_file_management": "enabled",
                "ai_intent_analysis": "enabled"
            }
        })
        
    except Exception as e:
        logger.error(f"❌ System stats error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.post("/simulate-conversation")
async def simulate_conversation(
    user_id: str = "test_user",
    messages: list = None
):
    """
    จำลองการสนทนาเพื่อทดสอบระบบ AI Context
    """
    try:
        if messages is None:
            messages = [
                {"role": "user", "content": "ส่งรูปภาพ", "type": "file_upload"},
                {"role": "assistant", "content": "ได้รับรูปภาพแล้ว"},
                {"role": "user", "content": "วิเคราะห์รูปนี้", "type": "file_analysis"},
                {"role": "assistant", "content": "รูปนี้เป็นเมนูอาหารไทย..."}
            ]
        
        # ลบข้อมูลเดิม
        file_service.clear_all_user_data(user_id)
        
        # เพิ่มข้อความทีละข้อความ
        for msg in messages:
            file_service.add_conversation_message(
                user_id=user_id,
                role=msg["role"],
                content=msg["content"],
                message_type=msg.get("type", "text")
            )
        
        # สร้าง fake context
        if any(msg.get("type") == "file_upload" for msg in messages):
            file_service.add_conversation_context(
                user_id=user_id,
                file_path="/fake/path/test_image.jpg",
                file_type="image",
                intent="analyze",
                ai_response="รูปนี้เป็นเมนูอาหารไทย มีหลายจาน..."
            )
        
        # ทดสอบ AI analysis กับข้อความใหม่
        test_prompts = [
            "แปลข้อความในรูป",  # ควรเกี่ยวข้อง
            "อากาศวันนี้เป็นไง",  # ไม่ควรเกี่ยวข้อง
            "สรุปเมนูในรูป"  # ควรเกี่ยวข้อง
        ]
        
        test_results = []
        for prompt in test_prompts:
            analysis = await file_service.analyze_context_with_ai(user_id, prompt)
            test_results.append({
                "prompt": prompt,
                "is_related": analysis.is_related,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "action": analysis.action
            })
        
        return JSONResponse(content={
            "success": True,
            "simulation": {
                "user_id": user_id,
                "messages_added": len(messages),
                "context_created": True
            },
            "ai_analysis_tests": test_results,
            "current_state": {
                "context_exists": file_service.get_conversation_context(user_id) is not None,
                "history_messages": len(file_service.get_conversation_history(user_id)),
                "ai_confidence": file_service.get_conversation_context(user_id).ai_confidence if file_service.get_conversation_context(user_id) else None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Simulate conversation error: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@router.get("/")
async def debug_index():
    """
    Debug endpoints รายการ - เวอร์ชัน AI Enhanced
    """
    return {
        "message": "Debug API for AI Context Management",
        "ai_features": {
            "context_awareness": "enabled",
            "conversation_history": "enabled",
            "ai_analysis": "enabled",
            "smart_file_management": "enabled"
        },
        "endpoints": {
            "GET /debug/contexts": "ดู AI contexts ทั้งหมด",
            "GET /debug/context/{user_id}": "ดู context + history ของผู้ใช้",
            "DELETE /debug/context/{user_id}": "ลบ context + history ของผู้ใช้",
            "POST /debug/cleanup/contexts": "บังคับ cleanup contexts",
            "GET /debug/conversation-histories": "ดูประวัติการสนทนาทั้งหมด",
            "GET /debug/pending-files": "ดูไฟล์ที่รอประมวลผล",
            "POST /debug/analyze-intent": "ทดสอบ AI intent analysis",
            "POST /debug/test-ai-context": "ทดสอบ AI context analysis",
            "GET /debug/system-stats": "ดูสถิติระบบ + AI metrics",
            "POST /debug/simulate-conversation": "จำลองการสนทนาเพื่อทดสอบ AI"
        },
        "ai_capabilities": {
            "context_analysis": "AI วิเคราะห์ความเกี่ยวข้องของข้อความ",
            "conversation_memory": "จดจำประวัติการสนทนาทั้งหมด",
            "smart_cleanup": "ลบไฟล์อัตโนมัติเมื่อ AI ตัดสินว่าไม่เกี่ยวข้อง",
            "confidence_scoring": "ให้คะแนนความมั่นใจในการตัดสินใจ",
            "reasoning_explanation": "อธิบายเหตุผลการตัดสินใจ"
        }
    }