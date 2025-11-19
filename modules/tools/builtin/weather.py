"""
Mofy Agent Framework - 天气工具
提供天气查询功能
"""

from ..base import BaseTool

class WeatherTool(BaseTool):
    """天气查询工具"""
    
    def __init__(self):
        super().__init__(
            name="weather",
            description="查询指定城市的天气信息",
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如 '北京'"
                    }
                },
                "required": ["city"]
            }
        )
    
    def execute(self, city: str) -> str:
        """查询天气"""
        try:
            # 模拟天气数据
            weather_data = {
                "北京": {"temp": "15°C", "condition": "晴朗", "humidity": "45%"},
                "上海": {"temp": "18°C", "condition": "多云", "humidity": "65%"},
                "广州": {"temp": "25°C", "condition": "小雨", "humidity": "80%"},
                "深圳": {"temp": "24°C", "condition": "阴天", "humidity": "75%"}
            }
            
            if city in weather_data:
                data = weather_data[city]
                return f"{city}天气: 温度{data['temp']}, {data['condition']}, 湿度{data['humidity']}"
            else:
                return f"抱歉，暂不支持查询{city}的天气信息"
                
        except Exception as e:
            return f"天气查询失败: {str(e)}"