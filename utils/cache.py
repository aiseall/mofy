"""
Mofy Agent Framework - 缓存管理
提供多级缓存功能
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict
import redis
from ..core.config import config

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.memory_cache: Dict[str, Dict] = {}
        self.redis_client = None
        
        if config.redis_url:
            try:
                self.redis_client = redis.Redis.from_url(config.redis_url)
                self.redis_client.ping()
            except Exception:
                print("Redis不可用，使用内存缓存")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            # 先从内存缓存获取
            if key in self.memory_cache:
                cache_item = self.memory_cache[key]
                if time.time() < cache_item["expires"]:
                    return cache_item["value"]
                else:
                    del self.memory_cache[key]
            
            # 再从Redis获取
            if self.redis_client:
                data = self.redis_client.get(f"cache:{key}")
                if data:
                    return json.loads(data)
            
            return None
            
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or config.cache_ttl
            
            # 设置内存缓存
            self.memory_cache[key] = {
                "value": value,
                "expires": time.time() + ttl
            }
            
            # 设置Redis缓存
            if self.redis_client:
                self.redis_client.setex(
                    f"cache:{key}", 
                    ttl, 
                    json.dumps(value, default=str)
                )
            
            return True
            
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            # 删除内存缓存
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # 删除Redis缓存
            if self.redis_client:
                self.redis_client.delete(f"cache:{key}")
            
            return True
            
        except Exception:
            return False
    
    def clear(self) -> bool:
        """清空所有缓存"""
        try:
            self.memory_cache.clear()
            
            if self.redis_client:
                # 清空所有以cache:开头的键
                keys = self.redis_client.keys("cache:*")
                if keys:
                    self.redis_client.delete(*keys)
            
            return True
            
        except Exception:
            return False
    
    def generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

# 全局缓存管理器实例
cache_manager = CacheManager()