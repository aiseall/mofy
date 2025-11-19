"""
Mofy Agent Framework - 工具基类
定义工具的标准接口和通用功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import json

class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行工具逻辑"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        required_params = self.parameters_schema.get("required", [])
        properties = self.parameters_schema.get("properties", {})
        
        # 检查必填参数
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"缺少必填参数: {param}")
        
        # 检查参数类型
        for param, value in parameters.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"参数 {param} 应为字符串类型")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"参数 {param} 应为数字类型")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"参数 {param} 应为布尔类型")
        
        return True
    
    def run_with_timeout(self, **kwargs) -> str:
        """带超时的工具执行"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"工具 {self.name} 执行超时")
        
        # 设置超时信号（仅在Unix系统上有效）
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)  # 5秒超时
            
            result = self.execute(**kwargs)
            
            signal.alarm(0)  # 取消超时
            return result
            
        except (ValueError, AttributeError):
            # Windows系统不支持信号，直接执行
            return self.execute(**kwargs)
        except TimeoutError:
            return f"工具 {self.name} 执行超时"
        finally:
            try:
                signal.alarm(0)  # 确保取消超时
            except:
                pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema
        }