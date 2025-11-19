"""
Mofy Agent Framework - 参数解析工具
提供智能参数解析功能
"""

import json
import re
from typing import Dict, Any, Union

class ParameterParser:
    """参数解析器"""
    
    @staticmethod
    def parse_parameters(params_str: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """智能参数解析"""
        required_params = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # 方法1: 尝试JSON解析
        try:
            result = json.loads(params_str)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        # 方法2: 尝试键值对解析
        if "=" in params_str and ("&" in params_str or "," in params_str):
            # 支持 "key=value&key2=value2" 或 "key=value,key2=value2" 格式
            separator = "&" if "&" in params_str else ","
            pairs = params_str.split(separator)
            result = {}
            
            for pair in pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    result[key.strip()] = value.strip()
            
            if result and all(param in result for param in required_params):
                return result
        
        # 方法3: 尝试自然语言解析（适用于单参数）
        if len(required_params) == 1:
            param_name = required_params[0]
            param_type = properties.get(param_name, {}).get("type", "string")
            
            if param_type == "number":
                # 尝试提取数字
                numbers = re.findall(r"-?\d+\.?\d*", params_str)
                if numbers:
                    return {param_name: float(numbers[0])}
            
            elif param_type == "boolean":
                # 尝试提取布尔值
                if any(word in params_str.lower() for word in ["是", "真", "true", "yes"]):
                    return {param_name: True}
                elif any(word in params_str.lower() for word in ["否", "假", "false", "no"]):
                    return {param_name: False}
            
            # 默认返回字符串
            return {param_name: params_str.strip()}
        
        # 方法4: 尝试从schema推断参数
        return ParameterParser._infer_from_schema(params_str, schema)
    
    @staticmethod
    def _infer_from_schema(params_str: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """从schema推断参数"""
        properties = schema.get("properties", {})
        result = {}
        
        # 简单的关键词匹配
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            description = param_info.get("description", "").lower()
            
            if param_type == "string":
                # 检查描述中的关键词
                if "城市" in description and any(city in params_str for city in ["北京", "上海", "广州", "深圳"]):
                    for city in ["北京", "上海", "广州", "深圳"]:
                        if city in params_str:
                            result[param_name] = city
                            break
                
                elif "查询" in description or "搜索" in description:
                    result[param_name] = params_str.strip()
                
                elif "表达式" in description or "计算" in description:
                    # 提取数学表达式
                    math_expr = re.search(r"[\d+\-*/().]+", params_str)
                    if math_expr:
                        result[param_name] = math_expr.group()
        
        return result
    
    @staticmethod
    def validate_parameters(params: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, str]:
        """验证参数"""
        required_params = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # 检查必填参数
        for param in required_params:
            if param not in params:
                return False, f"缺少必填参数: {param}"
        
        # 检查参数类型
        for param, value in params.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False, f"参数 {param} 应为字符串类型"
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False, f"参数 {param} 应为数字类型"
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False, f"参数 {param} 应为布尔类型"
        
        return True, ""

def parse_json_safely(text: str) -> Dict[str, Any]:
    """安全解析JSON"""
    try:
        # 提取JSON部分
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start == -1 or json_end == -1:
            return {}
        
        json_str = text[json_start:json_end]
        return json.loads(json_str)
    except:
        return {}

def parse_key_value_pairs(text: str) -> Dict[str, str]:
    """解析键值对字符串"""
    pattern = r"(\w+)=([^&]+)"
    matches = re.findall(pattern, text)
    return dict(matches)

def extract_code_blocks(text: str, language: str = None) -> list:
    """提取代码块"""
    if language:
        pattern = f"```{language}\n(.*?)\n```"
    else:
        pattern = r"```(?:\w+)?\n(.*?)\n```"
    
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def clean_text(text: str) -> str:
    """清理文本，移除多余空白"""
    # 移除多余的空白行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # 移除行首尾空白
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix