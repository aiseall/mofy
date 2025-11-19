from typing import Dict, Any, List, Optional
import time
import json
import redis
from datetime import datetime
from loguru import logger
from ..core.config import config
from ..core.exceptions import StateError

class ConversationState:
    """对话状态管理"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.intent: str = None  # 用户意图
        self.steps: List[Dict] = []  # 对话步骤
        self.slots: Dict[str, Dict] = {}  # 槽位信息
        self.last_active: float = time.time()
        self.created_at: float = time.time()
    
    def update_slot(self, slot_name: str, value: Any, confidence: float = 1.0):
        """更新槽位信息，支持置信度管理"""
        self.slots[slot_name] = {
            "value": value,
            "confidence": confidence,
            "updated_at": time.time()
        }
        logger.debug(f"槽位更新: {slot_name} = {value} (置信度: {confidence})")
    
    def get_slot(self, slot_name: str) -> Optional[Dict[str, Any]]:
        """获取槽位信息"""
        return self.slots.get(slot_name)
    
    def is_complete(self, required_slots: List[str]) -> bool:
        """检查是否收集完所有必填槽位"""
        for slot in required_slots:
            slot_data = self.slots.get(slot)
            if not slot_data or slot_data["confidence"] < 0.8:
                return False
        return True
    
    def add_step(self, action: str, content: str, metadata: Dict[str, Any] = None):
        """添加对话步骤"""
        step = {
            "action": action,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.steps.append(step)
        self.last_active = time.time()
    
    def get_recent_steps(self, limit: int = 5) -> List[Dict]:
        """获取最近的对话步骤"""
        return self.steps[-limit:] if limit > 0 else self.steps
    
    def to_context(self) -> str:
        """转换为上下文字符串，控制长度"""
        context_parts = []
        
        context_parts.append(f"会话ID: {self.session_id}")
        
        if self.intent:
            context_parts.append(f"用户意图: {self.intent}")
        
        if self.slots:
            context_parts.append("已收集信息:")
            for slot, data in self.slots.items():
                context_parts.append(f"- {slot}: {data['value']} (可信度: {data['confidence']:.2f})")
        
        result = "\n".join(context_parts)
        
        # 控制上下文长度不超过500字符
        if len(result) > 500:
            result = result[:500] + "...[上下文已截断]"
        
        return result
    
    def clear_slots(self):
        """清空槽位信息"""
        self.slots.clear()
        logger.info("槽位信息已清空")
    
    def get_age(self) -> float:
        """获取会话年龄（秒）"""
        return time.time() - self.created_at
    
    def is_expired(self, max_age: int = 86400) -> bool:
        """检查会话是否过期"""
        return self.get_age() > max_age

class StateStore:
    """状态存储管理器"""
    
    def __init__(self, redis_url: str = None):
        try:
            self.redis_client = redis.Redis.from_url(redis_url or config.redis_url) if redis_url or config.redis_url else None
            self.prefix = "agent_state:"
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存存储: {e}")
            self.redis_client = None
            self.memory_store = {}
    
    def save_state(self, state: ConversationState, ttl: int = 86400):
        """保存状态"""
        try:
            state_data = {
                "intent": state.intent,
                "steps": json.dumps(state.steps),
                "slots": json.dumps(state.slots),
                "last_active": state.last_active,
                "created_at": state.created_at
            }
            
            if self.redis_client:
                key = self.prefix + state.session_id
                self.redis_client.hset(key, mapping=state_data)
                self.redis_client.expire(key, ttl)
            else:
                self.memory_store[state.session_id] = state_data
            
            logger.debug(f"状态已保存: {state.session_id}")
            
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
            raise StateError(f"保存状态失败: {e}")
    
    def load_state(self, session_id: str) -> ConversationState:
        """加载状态"""
        try:
            if self.redis_client:
                key = self.prefix + session_id
                data = self.redis_client.hgetall(key)
                if not data:
                    return ConversationState(session_id)
                
                return ConversationState(
                    session_id=session_id,
                    intent=data.get(b"intent", b"").decode(),
                    steps=json.loads(data.get(b"steps", b"[]")),
                    slots=json.loads(data.get(b"slots", b"{}")),
                    last_active=float(data.get(b"last_active", b"0").decode()),
                    created_at=float(data.get(b"created_at", b"0").decode())
                )
            else:
                data = self.memory_store.get(session_id)
                if not data:
                    return ConversationState(session_id)
                
                return ConversationState(
                    session_id=session_id,
                    intent=data.get("intent"),
                    steps=json.loads(data.get("steps", "[]")),
                    slots=json.loads(data.get("slots", "{}")),
                    last_active=data.get("last_active", 0),
                    created_at=data.get("created_at", 0)
                )
                
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return ConversationState(session_id)
    
    def delete_state(self, session_id: str) -> bool:
        """删除状态"""
        try:
            if self.redis_client:
                key = self.prefix + session_id
                self.redis_client.delete(key)
            else:
                if session_id in self.memory_store:
                    del self.memory_store[session_id]
            
            logger.info(f"状态已删除: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除状态失败: {e}")
            return False
    
    def cleanup_expired(self, max_age: int = 86400):
        """清理过期状态"""
        try:
            if self.redis_client:
                # Redis通过TTL自动清理，这里不需要额外操作
                pass
            else:
                current_time = time.time()
                expired_sessions = []
                
                for session_id, state_data in self.memory_store.items():
                    created_at = state_data.get("created_at", 0)
                    if current_time - created_at > max_age:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.memory_store[session_id]
                
                if expired_sessions:
                    logger.info(f"清理了{len(expired_sessions)}个过期会话")
                    
        except Exception as e:
            logger.error(f"清理过期状态失败: {e}")