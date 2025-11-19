from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

class Message(BaseModel):
    """消息基类"""
    id: str
    type: MessageType
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class MessageBus:
    """消息总线，用于模块间通信"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[callable]] = {}
    
    def subscribe(self, event_type: str, callback: callable):
        """订阅事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def publish(self, event_type: str, data: Any):
        """发布事件"""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"事件处理失败: {e}")
    
    def create_message(self, message_type: MessageType, content: str, 
                      metadata: Dict[str, Any] = None) -> Message:
        """创建消息"""
        return Message(
            id=f"msg_{datetime.now().timestamp()}",
            type=message_type,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )