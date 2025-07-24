"""
Pydantic Models สำหรับ LINE API
ใช้สำหรับ validation และ serialization ของข้อมูล LINE
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class LineUser(BaseModel):
    """ข้อมูลผู้ใช้ LINE"""
    type: Literal["user", "group", "room"] = "user"
    userId: Optional[str] = None
    groupId: Optional[str] = None
    roomId: Optional[str] = None


class LineMessage(BaseModel):
    """ข้อความจาก LINE"""
    id: str
    type: Literal["text", "image", "video", "audio", "file", "location", "sticker"]
    text: Optional[str] = None
    quoteToken: Optional[str] = None


class LineEvent(BaseModel):
    """Event จาก LINE Webhook"""
    type: Literal["message", "follow", "unfollow", "join", "leave", "memberJoined", "memberLeft", "postback", "beacon"]
    message: Optional[LineMessage] = None
    replyToken: Optional[str] = None
    source: LineUser
    timestamp: int
    mode: Literal["active", "standby"] = "active"
    webhookEventId: str
    deliveryContext: Optional[Dict[str, Any]] = None


class LineWebhookBody(BaseModel):
    """LINE Webhook Request Body"""
    destination: str
    events: List[LineEvent]


class LineReplyMessage(BaseModel):
    """ข้อความตอบกลับ LINE"""
    type: Literal["text", "image", "video", "audio", "file", "template", "imagemap", "flex"] = "text"
    text: Optional[str] = None
    quickReply: Optional[Dict[str, Any]] = None


class LinePushMessage(BaseModel):
    """ข้อความ Push ไป LINE"""
    to: str
    messages: List[LineReplyMessage]