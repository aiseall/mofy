"""
Mofy Agent Framework - 记忆管理模块
实现短期记忆、长期记忆和分层存储策略
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import redis
from loguru import logger
from ..core.config import config
from ..core.exceptions import MemoryError

class MemoryManager:
    """记忆管理器，支持多级存储"""
    
    def __init__(self):
        self.short_term: List[Dict[str, Any]] = []  # 内存中的短期记忆
        self.long_term: Dict[str, Any] = {}         # 长期记忆
        self.redis_client = None
        
        if config.redis_url:
            try:
                self.redis_client = redis.Redis.from_url(config.redis_url)
                self.redis_client.ping()
            except Exception as e:
                raise MemoryError(f"Redis连接失败: {str(e)}")
    
    def add_experience(self, session_id: str, content: str, is_structured: bool = False, key: str = None):
        """添加经验到记忆系统"""
        try:
            if is_structured and key:
                # 结构化知识存入长期记忆
                self.long_term[key] = {
                    "content": content,
                    "session_id": session_id,
                    "updated_at": datetime.now().isoformat()
                }
                
                # 如果启用Redis，也存入Redis
                if self.redis_client:
                    redis_key = f"long_term:{key}"
                    self.redis_client.hset(redis_key, mapping={
                        "content": content,
                        "session_id": session_id,
                        "updated_at": datetime.now().isoformat()
                    })
            else:
                # 对话内容存入短期记忆
                experience = {
                    "session_id": session_id,
                    "content": content,
                    "timestamp": datetime.now().timestamp()
                }
                self.short_term.append(experience)
                
                # 如果启用Redis，也存入Redis
                if self.redis_client:
                    redis_key = f"short_term:{session_id}"
                    self.redis_client.lpush(redis_key, json.dumps(experience))
                    self.redis_client.expire(redis_key, config.short_term_memory_ttl)
                
                # 清理过期短期记忆
                self._clean_short_term()
                
        except Exception as e:
            raise MemoryError(f"添加记忆失败: {str(e)}")
    
    def get_short_term(self, session_id: str, limit: int = 10) -> str:
        """获取短期记忆"""
        try:
            # 从内存获取
            memories = [m for m in self.short_term if m["session_id"] == session_id]
            memories = sorted(memories, key=lambda x: x["timestamp"], reverse=True)[:limit]
            
            # 如果内存中没有且启用Redis，从Redis获取
            if not memories and self.redis_client:
                redis_key = f"short_term:{session_id}"
                cached_data = self.redis_client.lrange(redis_key, 0, limit - 1)
                memories = [json.loads(data) for data in cached_data]
            
            return "\n".join([f"- {m['content']}" for m in memories])
            
        except Exception as e:
            raise MemoryError(f"获取短期记忆失败: {str(e)}")
    
    def get_long_term(self, key: str) -> Optional[Dict[str, Any]]:
        """获取长期记忆"""
        try:
            # 先从内存获取
            if key in self.long_term:
                return self.long_term[key]
            
            # 如果内存中没有且启用Redis，从Redis获取
            if self.redis_client:
                redis_key = f"long_term:{key}"
                data = self.redis_client.hgetall(redis_key)
                if data:
                    return {
                        "content": data.get(b"content", b"").decode(),
                        "session_id": data.get(b"session_id", b"").decode(),
                        "updated_at": data.get(b"updated_at", b"").decode()
                    }
            
            return None
            
        except Exception as e:
            raise MemoryError(f"获取长期记忆失败: {str(e)}")
    
    def get_relevant_memory(self, session_id: str, query: str) -> str:
        """获取与查询相关的记忆片段"""
        try:
            # L1: 短期记忆
            recent_dialog = self.get_short_term(session_id, limit=5)
            
            # L2: 长期记忆（简单关键词匹配）
            relevant_long_term = []
            for key, data in self.long_term.items():
                if any(word in data["content"].lower() for word in query.lower().split() if len(word) > 2):
                    relevant_long_term.append(f"- {key}: {data['content']}")
            
            # 拼接上下文，控制长度
            context_parts = []
            if recent_dialog:
                context_parts.append(f"最近对话:\n{recent_dialog}")
            
            if relevant_long_term:
                context_parts.append(f"相关记忆:\n" + "\n".join(relevant_long_term[:3]))
            
            context = "\n\n".join(context_parts)
            
            # 确保上下文不超过2000字符
            return context[:2000] if len(context) > 2000 else context
            
        except Exception as e:
            raise MemoryError(f"获取相关记忆失败: {str(e)}")
    
    def _clean_short_term(self):
        """清理过期短期记忆"""
        now = datetime.now().timestamp()
        self.short_term = [
            item for item in self.short_term
            if now - item["timestamp"] < config.short_term_memory_ttl
        ]
    
    def clear_session(self, session_id: str):
        """清理指定会话的记忆"""
        self.short_term = [m for m in self.short_term if m["session_id"] != session_id]
        
        if self.redis_client:
            # 清理Redis中的相关数据
            self.redis_client.delete(f"short_term:{session_id}")

# 全局记忆管理器实例
memory_manager = MemoryManager()