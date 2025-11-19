"""
Mofy Agent Framework - ReAct范式Agent示例
展示思考-行动-观察的循环模式
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import create_agent
from modules.tools.builtin import register_builtin_tools
from core.llm import llm_client

class ReActAgent:
    """ReAct范式的Agent"""
    
    def __init__(self, session_id: str = None):
        self.agent = create_agent(session_id)
        self.max_iterations = 5
    
    async def solve(self, problem: str) -> str:
        """使用ReAct模式解决问题"""
        print(f"🤔 问题: {problem}")
        print("=" * 50)
        
        context = ""
        for iteration in range(self.max_iterations):
            print(f"\n📍 步骤 {iteration + 1}:")
            
            # 思考阶段
            thought = await self._think(problem, context)
            print(f"💭 思考: {thought}")
            
            # 行动阶段
            action = await self._act(thought)
            print(f"🎬 行动: {action}")
            
            # 观察阶段
            observation = await self._observe(action)
            print(f"👀 观察: {observation}")
            
            # 更新上下文
            context += f"\n步骤{iteration + 1}:\n思考: {thought}\n行动: {action}\n观察: {observation}\n"
            
            # 检查是否完成
            if await self._is_complete(problem, observation):
                final_answer = await self._generate_final_answer(problem, context)
                print(f"\n✅ 最终答案: {final_answer}")
                return final_answer
        
        return "达到最大迭代次数，未能完全解决问题"
    
    async def _think(self, problem: str, context: str) -> str:
        """思考阶段"""
        prompt = f"""问题: {problem}
之前的步骤: {context}

请分析当前情况，决定下一步应该采取什么行动。思考过程应该简短明确。
输出格式: {{
    "thought": "你的思考内容",
    "next_action": "下一步行动描述"
}}
"""
        
        response = llm_client.invoke(prompt)
        parsed = llm_client.parse_response(response)
        return parsed.get("thought", "继续分析问题")
    
    async def _act(self, thought: str) -> str:
        """行动阶段"""
        prompt = f"""基于以下思考，选择合适的工具或直接回答:
思考: {thought}

可用工具:
- calculator: 数学计算
- search: 网络搜索  
- weather: 天气查询

输出格式: {{
    "action": "tool_call|direct_answer",
    "tool": "工具名称",
    "parameters": {{"参数": "值"}},
    "response": "直接回答内容"
}}
"""
        
        response = llm_client.invoke(prompt)
        parsed = llm_client.parse_response(response)
        
        if parsed.get("action") == "tool_call":
            tool_name = parsed.get("tool")
            parameters = parsed.get("parameters", {})
            
            # 执行工具
            from modules.tools import tool_registry
            params_str = str(parameters) if isinstance(parameters, dict) else parameters
            result = tool_registry.execute_tool(tool_name, params_str)
            return f"使用{tool_name}工具: {result}"
        else:
            return parsed.get("response", "直接回答")
    
    async def _observe(self, action_result: str) -> str:
        """观察阶段"""
        # 这里可以添加对行动结果的分析
        if "执行失败" in action_result:
            return "行动失败，需要调整策略"
        elif "计算结果" in action_result or "搜索结果" in action_result:
            return "行动成功，获得有用信息"
        else:
            return "行动完成"
    
    async def _is_complete(self, problem: str, observation: str) -> bool:
        """检查是否完成"""
        prompt = f"""问题: {problem}
最新观察: {observation}

问题是否已经完全解决？回答"是"或"否"。
"""
        
        response = llm_client.invoke(prompt)
        return "是" in response
    
    async def _generate_final_answer(self, problem: str, context: str) -> str:
        """生成最终答案"""
        prompt = f"""基于以下思考过程，为问题提供最终答案:
问题: {problem}
完整过程: {context}

请提供清晰、准确的最终答案。
"""
        
        return llm_client.invoke(prompt)

async def main():
    """主函数"""
    print("🤖 Mofy Agent Framework - ReAct范式示例")
    print("=" * 50)
    
    # 注册内置工具
    register_builtin_tools()
    
    # 创建ReAct Agent
    agent = ReActAgent("react_demo")
    
    # 示例问题
    problems = [
        "计算 123 + 456 * 789 的结果",
        "查询北京今天的天气情况",
        "搜索人工智能的最新发展"
    ]
    
    print("请选择要解决的问题:")
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem}")
    print("4. 自定义问题")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "4":
        problem = input("请输入您的问题: ").strip()
    elif choice in ["1", "2", "3"]:
        problem = problems[int(choice) - 1]
    else:
        print("无效选择，使用默认问题")
        problem = problems[0]
    
    # 解决问题
    await agent.solve(problem)

if __name__ == "__main__":
    asyncio.run(main())