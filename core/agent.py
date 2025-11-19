from typing import Dict, Any, List, Optional
import time
import uuid
from loguru import logger
from .config import config
from .llm import LLMClient
from ..modules.scheduler import TaskScheduler
from ..modules.memory import MemoryManager
from ..modules.tools.registry import ToolRegistry
from ..modules.reflection import ReflectionEngine

class MofyAgent:
    """Mofy Agent基类：智能体核心实现"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.llm_client = LLMClient()
        self.scheduler = TaskScheduler()
        self.memory = MemoryManager()
        self.tool_registry = ToolRegistry()
        self.reflection_engine = ReflectionEngine(self.llm_client)
        self.last_active = time.time()
        
        # 初始化内置工具
        self._init_builtin_tools()
        
        logger.info(f"Mofy Agent初始化完成: {self.session_id}")
    
    def process_message(self, message: str) -> str:
        """处理用户消息的主要入口"""
        try:
            # 更新活跃时间
            self.last_active = time.time()
            
            # 保存用户消息到记忆
            self.memory.add_experience(self.session_id, f"用户: {message}")
            
            # 获取相关记忆作为上下文
            context = self.memory.get_relevant_memory(self.session_id, message)
            
            # 分析用户意图并规划任务
            task_plan = self._analyze_intent(message, context)
            
            # 执行任务计划
            result = self._execute_task_plan(task_plan)
            
            # 保存助手回复到记忆
            self.memory.add_experience(self.session_id, f"助手: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"消息处理失败: {str(e)}")
            return f"抱歉，处理过程中出现错误：{str(e)}"
    
    def _analyze_intent(self, message: str, context: str) -> Dict[str, Any]:
        """分析用户意图并生成任务计划"""
        prompt = f"""基于以下上下文分析用户意图，生成任务执行计划:

上下文信息:
{context}

用户消息: {message}

请分析用户意图并返回JSON格式的任务计划:
{{
    "intent": "用户意图描述",
    "tasks": [
        {{
            "type": "任务类型",
            "tool": "工具名称",
            "parameters": {{"param": "value"}},
            "priority": 1-10
        }}
    ]
}}
"""
        
        response = self.llm_client.invoke(prompt)
        plan = self.llm_client.parse_response(response)
        
        # 验证并修正计划
        if "tasks" not in plan:
            plan["tasks"] = []
        
        return plan
    
    def _execute_task_plan(self, task_plan: Dict[str, Any]) -> str:
        """执行任务计划"""
        if not task_plan.get("tasks"):
            return "我理解了您的需求，但没有找到合适的工具来处理。"
        
        # 添加任务到调度器
        for task in task_plan["tasks"]:
            self.scheduler.add_task(
                task_type=task.get("type", "unknown"),
                parameters=task.get("parameters", {}),
                priority=task.get("priority", 5)
            )
        
        # 执行任务
        results = []
        task_history = []
        
        while True:
            task = self.scheduler.get_next_task()
            if not task:
                break
            
            # 执行具体任务
            if "tool" in task_plan:
                tool_name = task_plan["tool"]
                params_str = str(task["params"])
                result = self.tool_registry.execute_tool(tool_name, params_str)
            else:
                result = "任务执行完成"
            
            results.append(result)
            task_history.append(f"任务: {task['type']}, 结果: {result}")
            
            # 标记任务完成
            self.scheduler.complete_task(task["task_id"], result)
        
        # 生成最终回复
        if results:
            final_prompt = f"""基于以下任务执行结果，生成自然语言回复:

任务执行历史:
{chr(10).join(task_history)}

请生成简洁、有用的回复:
"""
            response = self.llm_client.invoke(final_prompt)
            return response
        else:
            return "任务执行完成，但没有产生具体结果。"
    
    def _init_builtin_tools(self):
        """初始化内置工具"""
        # 示例：计算器工具
        def calculator(expression: str) -> str:
            """简单计算器"""
            try:
                result = eval(expression)
                return f"计算结果: {result}"
            except Exception as e:
                return f"计算错误: {str(e)}"
        
        self.tool_registry.register_tool(
            "calculator",
            calculator,
            {
                "description": "执行数学计算",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '2+3*4'"
                        }
                    },
                    "required": ["expression"]
                }
            }
        )
        
        # 示例：搜索工具
        def search(query: str) -> str:
            """模拟搜索工具"""
            return f"搜索'{query}'的结果：这里应该是搜索结果内容"
        
        self.tool_registry.register_tool(
            "search",
            search,
            {
                "description": "搜索信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        }
                    },
                    "required": ["query"]
                }
            }
        )
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态信息"""
        return {
            "session_id": self.session_id,
            "last_active": self.last_active,
            "pending_tasks": len([t for t in self.scheduler.task_queue if t["status"].value == "pending"]),
            "completed_tasks": len(self.scheduler.completed_tasks),
            "tool_metrics": self.tool_registry.get_metrics()
        }