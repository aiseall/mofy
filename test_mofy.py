"""
Mofy Agent Framework 测试脚本
支持OpenAI和硅基流动模型测试
"""

import sys
import os
from mofy import MofyAgent, MofyConfig
from loguru import logger

def test_siliconflow_config():
    """测试硅基流动配置"""
    print("=== 硅基流动配置测试 ===")
    
    # 检查环境变量
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("❌ 硅基流动API密钥未配置")
        print("请设置环境变量: SILICONFLOW_API_KEY")
        return False
    
    # 临时设置配置
    original_provider = os.getenv("LLM_PROVIDER", "openai")
    original_model = os.getenv("MODEL_NAME", "gpt-4o")
    
    os.environ["LLM_PROVIDER"] = "siliconflow"
    os.environ["MODEL_NAME"] = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
    
    try:
        config = MofyConfig()
        print(f"✅ LLM提供商: {config.llm_provider}")
        print(f"✅ 模型名称: {config.model_name}")
        print(f"✅ API密钥: {'*' * 20}{config.siliconflow_api_key[-4:] if config.siliconflow_api_key else 'None'}")
        print(f"✅ Base URL: {config.siliconflow_base_url}")
        return True
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        return False
    finally:
        # 恢复原始配置
        os.environ["LLM_PROVIDER"] = original_provider
        os.environ["MODEL_NAME"] = original_model

def test_siliconflow_agent():
    """测试硅基流动Agent"""
    print("\n=== 硅基流动Agent测试 ===")
    
    # 设置环境变量
    os.environ["LLM_PROVIDER"] = "siliconflow"
    os.environ["MODEL_NAME"] = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
    
    try:
        # 创建Agent实例
        agent = MofyAgent()
        
        # 显示Provider信息
        provider_info = agent.llm_client.get_provider_info()
        print(f"当前Provider: {provider_info}")
        
        # 测试对话
        test_messages = [
            "你好，请简单介绍一下DeepSeek模型",
            "请用一句话说明什么是人工智能",
            "计算 15 * 8 等于多少？"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. 测试消息: {message}")
            try:
                response = agent.process_message(message)
                print(f"回复: {response}")
            except Exception as e:
                print(f"❌ 测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent创建或测试失败: {e}")
        return False

def test_openai_agent():
    """测试OpenAI Agent"""
    print("\n=== OpenAI Agent测试 ===")
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OpenAI API密钥未配置，跳过测试")
        return False
    
    # 设置环境变量
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["MODEL_NAME"] = "gpt-4o"
    
    try:
        agent = MofyAgent()
        provider_info = agent.llm_client.get_provider_info()
        print(f"当前Provider: {provider_info}")
        
        response = agent.process_message("你好，请简单介绍一下GPT-4")
        print(f"回复: {response}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI测试失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 基本功能测试 ===")
    
    # 使用默认配置创建Agent
    agent = MofyAgent()
    
    # 测试计算功能
    print("\n1. 测试计算功能:")
    response = agent.process_message("帮我计算 2+3*4")
    print(f"用户: 帮我计算 2+3*4")
    print(f"助手: {response}")
    
    # 测试搜索功能
    print("\n2. 测试搜索功能:")
    response = agent.process_message("搜索 Python")
    print(f"用户: 搜索 Python")
    print(f"助手: {response}")
    
    # 测试一般对话
    print("\n3. 测试一般对话:")
    response = agent.process_message("你好，请介绍一下自己")
    print(f"用户: 你好，请介绍一下自己")
    print(f"助手: {response}")
    
    # 显示状态
    print("\n4. Agent状态:")
    status = agent.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

def test_config():
    """测试配置"""
    print("\n=== 配置测试 ===")
    config = MofyConfig()
    print(f"LLM提供商: {config.llm_provider}")
    print(f"模型名称: {config.model_name}")
    print(f"温度: {config.temperature}")
    print(f"工具超时: {config.tool_timeout}秒")

def main():
    """主测试函数"""
    print("Mofy Agent Framework 综合测试")
    print("=" * 50)
    
    # 配置测试
    test_config()
    
    # 硅基流动测试
    siliconflow_ok = test_siliconflow_config()
    if siliconflow_ok:
        test_siliconflow_agent()
    
    # OpenAI测试
    test_openai_agent()
    
    # 基本功能测试
    test_basic_functionality()
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()