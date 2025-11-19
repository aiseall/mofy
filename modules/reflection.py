from typing import List, Dict, Any
import json
import re
from loguru import logger
from ..core.llm import LLMClient
from ..core.exceptions import MofyException

class ReflectionEngine:
    """反思引擎，让Agent从错误中学习"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.error_patterns = {
            "参数错误": r"缺少必选参数|类型错误|格式错误|参数验证失败",
            "工具失败": r"API超时|权限不足|服务不可用|连接失败",
            "逻辑错误": r"结论矛盾|步骤缺失|计算错误|逻辑不一致",
            "解析错误": r"解析失败|格式错误|JSON解析|无法解析"
        }
    
    def analyze_failure(self, task_history: List[str]) -> Dict[str, str]:
        """分析任务失败原因"""
        try:
            # 构建反思提示词
            prompt = f"""分析以下任务执行历史，指出失败类型和具体原因:
{chr(10).join(task_history[-5:])}  # 最近5步历史

失败类型只能是:参数错误/工具失败/逻辑错误/解析错误/未知错误
输出格式:{{"type":"错误类型","reason":"具体原因","suggestion":"改进建议"}}

请严格按照JSON格式输出，不要添加任何额外内容。"""

            response = self.llm.invoke(prompt)
            
            # 尝试解析JSON响应
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                return self._default_error("反思结果解析失败")
            
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
            
            # 验证输出格式
            if "type" not in result:
                return self._default_error("反思结果缺少type字段")
            
            # 验证错误类型
            valid_types = ["参数错误", "工具失败", "逻辑错误", "解析错误", "未知错误"]
            if result["type"] not in valid_types:
                result["type"] = "未知错误"
            
            logger.info(f"反思分析完成: {result['type']} - {result['reason']}")
            return result
            
        except Exception as e:
            logger.error(f"反思分析失败: {e}")
            return self._default_error(f"反思分析异常: {str(e)}")
    
    def _default_error(self, message: str) -> Dict[str, str]:
        """返回默认错误信息"""
        return {
            "type": "未知错误",
            "reason": message,
            "suggestion": "检查提示词模板和LLM响应格式"
        }
    
    def detect_loop(self, history: List[Dict], max_repeats: int = 3) -> bool:
        """检测工具调用循环"""
        if len(history) < max_repeats * 2:
            return False
        
        # 提取最近的工具调用序列
        recent_actions = []
        for item in history[-max_repeats*2:]:
            if "action" in item:
                recent_actions.append(item["action"])
        
        # 检查是否有重复模式
        for i in range(len(recent_actions) - max_repeats):
            pattern = recent_actions[i:i+max_repeats]
            next_pattern = recent_actions[i+max_repeats:i+max_repeats*2]
            if pattern == next_pattern:
                logger.warning(f"检测到循环模式: {pattern}")
                return True
        
        return False
    
    def get_improvement_suggestion(self, error_type: str, context: Dict[str, Any]) -> str:
        """根据错误类型获取改进建议"""
        suggestions = {
            "参数错误": "请检查工具调用参数的格式和完整性，确保所有必填参数都已提供",
            "工具失败": "请检查网络连接和API密钥，或尝试使用备用工具",
            "逻辑错误": "请重新审视任务步骤，确保逻辑链条完整且正确",
            "解析错误": "请检查LLM输出格式，确保返回有效的JSON格式"
        }
        
        base_suggestion = suggestions.get(error_type, "请检查任务执行的各个环节")
        
        # 根据上下文添加具体建议
        if "tool_name" in context:
            base_suggestion += f"，特别关注{context['tool_name']}工具的使用"
        
        return base_suggestion
    
    def should_retry(self, error_analysis: Dict[str, str], retry_count: int) -> bool:
        """判断是否应该重试"""
        if retry_count >= 3:
            return False
        
        error_type = error_analysis.get("type", "")
        
        # 某些错误类型不值得重试
        no_retry_types = ["参数错误", "解析错误"]
        if error_type in no_retry_types:
            return False
        
        return True