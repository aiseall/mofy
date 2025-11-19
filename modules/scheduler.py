"""
Mofy Agent Framework - 任务调度器
负责任务队列管理、优先级排序和执行调度
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import time
from loguru import logger

class TaskStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskScheduler:
    """任务调度器：Agent的大脑中枢"""
    
    def __init__(self, max_retries: int = 3):
        self.task_queue: List[Dict[str, Any]] = []
        self.max_retries = max_retries
        self.completed_tasks: List[Dict[str, Any]] = []
        
    def add_task(self, task_type: str, parameters: Dict[str, Any], priority: int = 5):
        """添加任务到队列，支持优先级排序"""
        task = {
            "task_id": f"task_{len(self.task_queue) + 1}",
            "type": task_type,
            "params": parameters,
            "priority": priority,
            "status": TaskStatus.PENDING,
            "retries": 0,
            "created_at": time.time()
        }
        self.task_queue.append(task)
        # 按优先级排序（1最高，10最低）
        self.task_queue.sort(key=lambda x: x["priority"])
        logger.info(f"任务已添加: {task['task_id']} (优先级: {priority})")
        
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """获取下一个待执行任务"""
        for task in self.task_queue:
            if task["status"] == TaskStatus.PENDING:
                task["status"] = TaskStatus.EXECUTING
                return task
        return None
    
    def complete_task(self, task_id: str, result: Any, success: bool = True):
        """标记任务完成"""
        for task in self.task_queue:
            if task["task_id"] == task_id:
                task["status"] = TaskStatus.COMPLETED if success else TaskStatus.FAILED
                task["result"] = result
                task["completed_at"] = time.time()
                self.completed_tasks.append(task)
                logger.info(f"任务完成: {task_id} (成功: {success})")
                return True
        return False
    
    def retry_task(self, task_id: str) -> bool:
        """重试失败的任务"""
        for task in self.task_queue:
            if task["task_id"] == task_id and task["status"] == TaskStatus.FAILED:
                if task["retries"] < self.max_retries:
                    task["status"] = TaskStatus.PENDING
                    task["retries"] += 1
                    logger.info(f"任务重试: {task_id} (第{task['retries']}次)")
                    return True
        return False