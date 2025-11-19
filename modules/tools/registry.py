"""
Mofy Agent Framework - 工具注册机制
管理工具的注册、调用和参数解析
"""

from typing import Dict, Callable, Any, List
import re
import json
import time
import asyncio
from loguru import logger
from contextlib import contextmanager
from ..core.config import config

class ToolRegistry:
    """工具注册和执行系统"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: Dict[str, Dict] = {}  # 工具参数schema
        self.metrics: Dict[str, Dict] = {}  # 工具调用指标
        
    def register_tool(self, name: str, func: Callable, schema: Dict):
        """注册工具并验证参数schema"""
        if "parameters" not in schema:
            raise ValueError(f"工具{name}缺少parameters定义")
        
        self.tools[name] = func
        self.schemas[name] = schema
        self.metrics[name] = {"calls": 0, "success": 0, "failures": 0, "total_time": 0}
        logger.info(f"✅ 工具注册成功: {name}")
    
    def execute_tool(self, tool_name: str, params: str) -> str:
        """执行工具调用，支持智能参数解析"""
        if tool_name not in self.tools:
            return f"❌ 工具不存在: {tool_name}"
        
        try:
            # 智能参数解析
            parsed_params = self._parse_parameters(tool_name, params)
            
            # 带超时的工具执行
            start_time = time.time()
            result = self._execute_with_timeout(tool_name, parsed_params)
            exec_time = (time.time() - start_time) * 1000
            
            # 记录调用指标
            self._record_metrics(tool_name, exec_time, success=True)
            return f"[{tool_name}执行成功] {result}"
            
        except Exception as e:
            self._record_metrics(tool_name, 0, success=False)
            logger.error(f"工具执行失败 {tool_name}: {str(e)}")
            return f"[{tool_name}执行失败] {str(e)}"
    
    async def batch_execute_tools(self, tasks: List[Dict]) -> List[str]:
        """并行执行多个工具任务"""
        async_tasks = []
        for task in tasks:
            tool_name = task["tool"]
            params = task["params"]
            async_tasks.append(
                asyncio.create_task(
                    asyncio.to_thread(
                        self._execute_with_timeout,
                        tool_name=tool_name,
                        params=self._parse_parameters(tool_name, params),
                        timeout=config.tool_timeout
                    )
                )
            )
        
        # 并行执行并收集结果
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # 处理结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(f"任务{i+1}失败: {str(result)}")
            else:
                final_results.append(f"任务{i+1}结果: {result}")
        
        return final_results
    
    def _parse_parameters(self, tool_name: str, params: str) -> Dict[str, Any]:
        """智能参数解析，支持多种格式"""
        schema = self.schemas[tool_name]
        required_params = schema["parameters"].get("required", [])
        
        # 尝试JSON解析（优先）
        try:
            return json.loads(params)
        except json.JSONDecodeError:
            pass
        
        # 尝试键值对解析
        if "=" in params and "&" in params:
            parsed = dict(re.findall(r"(\w+)=([^&]+)", params))
            if all(p in parsed for p in required_params):
                return parsed
        
        # 尝试纯文本解析（适合单参数工具）
        if len(required_params) == 1:
            return {required_params[0]: params.strip()}
        
        # 解析失败时返回友好提示
        raise ValueError(f"无法解析参数格式，请使用JSON或'key=value'格式")
    
    @contextmanager
    def _time_limit(self, seconds):
        """超时控制上下文管理器"""
        import signal
        
        def signal_handler(signum, frame):
            raise TimeoutError("工具执行超时")
        
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
    
    def _execute_with_timeout(self, tool_name: str, params: Dict, timeout: int = None) -> Any:
        """带超时的工具执行"""
        if timeout is None:
            timeout = config.tool_timeout
        
        try:
            with self._time_limit(timeout):
                return self.tools[tool_name](**params)
        except TimeoutError:
            raise TimeoutError(f"工具{tool_name}执行超时（{timeout}秒）")
    
    def _record_metrics(self, tool_name: str, exec_time: float, success: bool):
        """记录工具调用指标"""
        if tool_name not in self.metrics:
            return
        
        self.metrics[tool_name]["calls"] += 1
        if success:
            self.metrics[tool_name]["success"] += 1
        else:
            self.metrics[tool_name]["failures"] += 1
        self.metrics[tool_name]["total_time"] += exec_time
    
    def get_metrics(self, tool_name: str = None) -> Dict:
        """获取工具调用指标"""
        if tool_name:
            return self.metrics.get(tool_name, {})
        return self.metrics