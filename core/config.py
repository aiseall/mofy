"""
Mofy Agent Framework - 配置管理模块
基于Pydantic的类型安全配置系统
"""

from pydantic import BaseSettings, Field, validator
import os
from dotenv import load_dotenv

load_dotenv()  # 加载.env文件

class MofyConfig(BaseSettings):
    """Mofy Agent框架核心配置"""
    # LLM配置
    llm_provider: str = Field("openai", env="LLM_PROVIDER")
    model_name: str = Field("gpt-4o", env="MODEL_NAME")
    temperature: float = Field(0.7, env="TEMPERATURE")
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    
    # 硅基流动配置
    siliconflow_api_key: str = Field("", env="SILICONFLOW_API_KEY")
    siliconflow_base_url: str = Field("https://api.siliconflow.cn/v1", env="SILICONFLOW_BASE_URL")

    # 记忆配置
    short_term_memory_ttl: int = Field(3600, env="SHORT_TERM_TTL")
    enable_long_term_memory: bool = Field(True, env="ENABLE_LONG_MEMORY")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # 工具配置
    tool_timeout: int = Field(3, env="TOOL_TIMEOUT")
    max_tool_retries: int = Field(2, env="TOOL_RETRIES")

    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/mofy.log", env="LOG_FILE")

    @validator("temperature")
    def temp_range(cls, v):
        """验证温度值在有效范围"""
        if not (0 <= v <= 2):
            raise ValueError("temperature必须在0-2之间")
        return v

    @validator("llm_provider")
    def validate_provider(cls, v):
        """验证LLM提供商合法性"""
        if v not in ["openai", "anthropic", "modelscope", "zhipu", "siliconflow"]:
            raise ValueError(f"不支持的LLM提供商: {v}")
        return v

    class Config:
        env_file = ".env"

# 全局配置实例
config = MofyConfig()