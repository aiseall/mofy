"""
Mofy Agent Framework - LLM客户端封装
统一的大语言模型调用接口，支持OpenAI、硅基流动等多种Provider
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional
from openai import OpenAI
from .config import config
from .exceptions import LLMError
import redis
from loguru import logger

class LLMClient:
    """LLM客户端封装，支持多种Provider和缓存"""
    
    def __init__(self):
        self.client = self._init_client()
        self.redis_client = redis.Redis.from_url(config.redis_url)
    
    def _init_client(self):
        """根据配置初始化对应的LLM客户端"""
        if config.llm_provider == "openai":
            if not config.openai_api_key:
                raise LLMError("OpenAI API密钥未配置")
            return OpenAI(api_key=config.openai_api_key)
        
        elif config.llm_provider == "siliconflow":
            if not config.siliconflow_api_key:
                raise LLMError("硅基流动API密钥未配置")
            return OpenAI(
                api_key=config.siliconflow_api_key,
                base_url=config.siliconflow_base_url
            )
        
        else:
            raise LLMError(f"不支持的LLM提供商: {config.llm_provider}")
        
    def invoke(self, prompt: str, cache_ttl: int = 3600, **kwargs) -> str:
        """带缓存的LLM调用"""
        # 生成缓存键
        cache_key = f"llm_cache:{config.llm_provider}:{config.model_name}:{hashlib.md5(prompt.encode()).hexdigest()}"
        
        # 尝试从Redis获取缓存
        cached_result = self.redis_client.get(cache_key)
        if cached_result:
            logger.info(f"LLM缓存命中: {cache_key[:16]}")
            return cached_result.decode()
        
        # 缓存未命中，调用LLM
        try:
            response = self.client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                **kwargs
            )
            result = response.choices[0].message.content
            
            # 存入缓存
            self.redis_client.setex(cache_key, cache_ttl, result)
            logger.info(f"LLM调用成功: {config.llm_provider}/{config.model_name}")
            return result
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise LLMError(f"LLM调用失败: {str(e)}")
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应，处理格式错误"""
        try:
            # 提取JSON部分
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                raise ValueError("未找到JSON结构")
            return json.loads(response[json_start:json_end])
        except Exception as e:
            logger.error(f"解析失败，原始响应: {response}")
            return {"action": "error", "message": str(e)}
    
    def get_provider_info(self) -> Dict[str, str]:
        """获取当前Provider信息"""
        return {
            "provider": config.llm_provider,
            "model": config.model_name,
            "base_url": getattr(config, 'siliconflow_base_url', '') if config.llm_provider == "siliconflow" else "https://api.openai.com/v1"
        }

# 全局LLM客户端实例
llm_client = LLMClient()