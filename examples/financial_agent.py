"""
Mofy Agent Framework - 金融分析Agent示例
展示专业领域Agent的实现
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import create_agent
from modules.tools.builtin import register_builtin_tools
from modules.tools.base import BaseTool

class StockAnalysisTool(BaseTool):
    """股票分析工具"""
    
    def __init__(self):
        super().__init__(
            name="stock_analysis",
            description="分析股票的基本面和技术面",
            parameters_schema={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "股票代码，如 '000001'"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "分析类型: 'basic'基本面, 'technical'技术面, 'all'综合分析"
                    }
                },
                "required": ["stock_code"]
            }
        )
    
    def execute(self, stock_code: str, analysis_type: str = "all") -> str:
        """执行股票分析"""
        try:
            # 模拟股票数据
            stock_data = {
                "000001": {"name": "平安银行", "price": 12.50, "pe": 5.8, "pb": 0.6},
                "000002": {"name": "万科A", "price": 18.30, "pe": 8.2, "pb": 1.1},
                "600036": {"name": "招商银行", "price": 35.80, "pe": 6.5, "pb": 0.8}
            }
            
            if stock_code not in stock_data:
                return f"未找到股票代码 {stock_code} 的数据"
            
            data = stock_data[stock_code]
            
            if analysis_type == "basic":
                return f"{data['name']}({stock_code}) 基本面分析:\n- 当前价格: ¥{data['price']}\n- 市盈率: {data['pe']}\n- 市净率: {data['pb']}\n- 评估: 估值合理，可考虑持有"
            
            elif analysis_type == "technical":
                return f"{data['name']}({stock_code}) 技术面分析:\n- 短期趋势: 震荡上行\n- 支撑位: ¥{data['price']*0.95:.2f}\n- 阻力位: ¥{data['price']*1.1:.2f}\n- 建议: 短线可逢低关注"
            
            else:  # all
                return f"""{data['name']}({stock_code}) 综合分析:

📊 基本面:
- 当前价格: ¥{data['price']}
- 市盈率: {data['pe']} (较低)
- 市净率: {data['pb']} (较低)

📈 技术面:
- 短期趋势: 震荡上行
- 支撑位: ¥{data['price']*0.95:.2f}
- 阻力位: ¥{data['price']*1.1:.2f}

💡 投资建议:
基本面良好，估值偏低，技术面处于上升趋势，建议中长期持有，短期可逢低加仓。

⚠️ 风险提示:
股市有风险，投资需谨慎。以上分析仅供参考，不构成投资建议。
"""
                
        except Exception as e:
            return f"股票分析失败: {str(e)}"

class RiskAssessmentTool(BaseTool):
    """风险评估工具"""
    
    def __init__(self):
        super().__init__(
            name="risk_assessment",
            description="评估投资组合的风险水平",
            parameters_schema={
                "type": "object",
                "properties": {
                    "portfolio": {
                        "type": "string",
                        "description": "投资组合，格式: '股票代码1:比例1,股票代码2:比例2'"
                    }
                },
                "required": ["portfolio"]
            }
        )
    
    def execute(self, portfolio: str) -> str:
        """执行风险评估"""
        try:
            # 解析投资组合
            stocks = {}
            for item in portfolio.split(","):
                if ":" in item:
                    code, ratio = item.split(":")
                    stocks[code.strip()] = float(ratio.strip())
            
            # 模拟风险评估
            total_risk = 0
            analysis = []
            
            for code, ratio in stocks.items():
                # 模拟不同股票的风险等级
                risk_levels = {
                    "000001": 3,  # 银行股，低风险
                    "000002": 4,  # 地产股，中风险
                    "600036": 3,  # 银行股，低风险
                }
                
                risk = risk_levels.get(code, 5)  # 默认中高风险
                weighted_risk = risk * ratio / 100
                total_risk += weighted_risk
                
                analysis.append(f"股票{code}: 风险等级{risk}/10, 权重{ratio}%")
            
            # 风险评级
            if total_risk < 2:
                risk_level = "低风险"
                suggestion = "适合保守型投资者"
            elif total_risk < 4:
                risk_level = "中等风险"
                suggestion = "适合稳健型投资者"
            else:
                risk_level = "高风险"
                suggestion = "适合激进型投资者"
            
            return f"""投资组合风险评估:

📊 组合构成:
{chr(10).join(analysis)}

🎯 综合风险评分: {total_risk:.2f}/10
📈 风险等级: {risk_level}
💡 建议: {suggestion}

🔍 风险分散建议:
- 当前组合{'较为集中' if len(stocks) < 3 else '相对分散'}
- 建议持有3-5只不同行业的股票以分散风险
- 定期调整仓位，保持风险平衡
"""
            
        except Exception as e:
            return f"风险评估失败: {str(e)}"

class FinancialAgent:
    """金融分析Agent"""
    
    def __init__(self, session_id: str = None):
        self.agent = create_agent(session_id)
        
        # 注册金融专用工具
        from modules.tools import tool_registry
        tool_registry.register_tool(StockAnalysisTool())
        tool_registry.register_tool(RiskAssessmentTool())
    
    async def analyze_stock(self, stock_code: str, analysis_type: str = "all") -> str:
        """分析股票"""
        message = f"请分析股票{stock_code}的{analysis_type}情况"
        return await self.agent.process_message(message)
    
    async def assess_portfolio_risk(self, portfolio: str) -> str:
        """评估投资组合风险"""
        message = f"请评估投资组合{portfolio}的风险水平"
        return await self.agent.process_message(message)
    
    async def get_investment_advice(self, user_profile: str) -> str:
        """获取投资建议"""
        message = f"根据用户画像{user_profile}，提供投资建议"
        return await self.agent.process_message(message)

async def main():
    """主函数"""
    print("🏦 Mofy Agent Framework - 金融分析Agent示例")
    print("=" * 50)
    
    # 注册基础工具
    register_builtin_tools()
    
    # 创建金融Agent
    agent = FinancialAgent("financial_demo")
    
    while True:
        print("\n请选择服务:")
        print("1. 股票分析")
        print("2. 投资组合风险评估")
        print("3. 投资建议")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "4":
            print("感谢使用金融分析服务！")
            break
        
        try:
            if choice == "1":
                stock_code = input("请输入股票代码: ").strip()
                print("分析类型: basic(基本面), technical(技术面), all(综合)")
                analysis_type = input("请输入分析类型 (默认all): ").strip() or "all"
                
                print("\n分析中...")
                result = await agent.analyze_stock(stock_code, analysis_type)
                print(f"\