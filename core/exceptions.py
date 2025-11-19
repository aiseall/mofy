"""
Mofy Agent Framework - 异常体系
定义框架中的各类异常
"""

class MofyException(Exception):
    """Mofy框架基础异常类"""
    pass

class ConfigError(MofyException):
    """配置错误"""
    pass

class LLMError(MofyException):
    """LLM调用错误"""
    pass

class ToolError(MofyException):
    """工具执行错误"""
    pass

class MemoryError(MofyException):
    """记忆系统错误"""
    pass

class SchedulerError(MofyException):
    """任务调度错误"""
    pass

class ReflectionError(MofyException):
    """反思机制错误"""
    pass

class StateError(MofyException):
    """状态管理错误"""
    pass

class TimeoutError(MofyException):
    """超时错误"""
    pass

class ToolExecutionError(MofyException):
    """工具执行异常"""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"工具 {tool_name} 执行失败: {message}")