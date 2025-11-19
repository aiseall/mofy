"""
Mofy Agent Framework - 简单对话Agent示例
展示基本的Agent使用方法，支持OpenAI和硅基流动模型
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import MofyAgent
from core.config import config
from loguru import logger

def setup_siliconflow():
    """设置硅基流动配置"""
    if os.getenv("SILICONFLOW_API_KEY"):
        config.llm_provider = "siliconflow"
        config.model_name = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
        config.siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY")
        config.siliconflow_base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        logger.info(f"使用硅基流动模型: {config.model_name}")
        return True
    return False

def main():
    """简单Agent示例程序"""
    logger.info("启动Mofy Agent示例程序")
    
    # 尝试设置硅基流动
    use_siliconflow = setup_siliconflow()
    
    # 创建Agent实例
    agent = MofyAgent()
    
    # 显示当前配置
    provider_info = agent.llm_client.get_provider_info()
    print(f"=== Mofy Agent 简单示例 ===")
    print(f"当前使用: {provider_info['provider']} - {provider_info['model']}")
    if use_siliconflow:
        print("模型提供商: 硅基流动")
    print("输入 'quit' 退出程序")
    print("输入 'status' 查看Agent状态")
    print()
    
    while True:
        try:
            user_input = input("用户: ").strip()
            
            if user_input.lower() == 'quit':
                print("再见！")
                break
            
            if user_input.lower() == 'status':
                status = agent.get_status()
                print(f"Agent状态: {status}")
                continue
            
            if not user_input:
                continue
            
            # 处理用户消息
            response = agent.process_message(user_input)
            print(f"助手: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            logger.error(f"程序错误: {str(e)}")
            print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()