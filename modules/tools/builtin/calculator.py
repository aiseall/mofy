"""
Mofy Agent Framework - 计算器工具
提供基本的数学计算功能
"""

from ..base import BaseTool

class CalculatorTool(BaseTool):
    """计算器工具"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算，支持加减乘除等基本运算",
            parameters_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，如 '2+3*4'"
                    }
                },
                "required": ["expression"]
            }
        )
    
    def execute(self, expression: str) -> str:
        """执行数学计算"""
        try:
            # 安全的数学表达式计算
            allowed_chars = set("0123456789+-*/().() ")
            if not all(c in allowed_chars for c in expression):
                return "错误：表达式包含非法字符"
            
            # 使用eval计算（在生产环境中应使用更安全的方法）
            result = eval(expression)
            return f"计算结果: {result}"
            
        except Exception as e:
            return f"计算错误: {str(e)}"