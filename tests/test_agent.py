import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import MofyAgent
import unittest

class TestMofyAgent(unittest.TestCase):
    """Mofy Agent测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = MofyAgent()
    
    def test_agent_creation(self):
        """测试Agent创建"""
        self.assertIsNotNone(self.agent.session_id)
        self.assertIsNotNone(self.agent.llm_client)
        self.assertIsNotNone(self.agent.scheduler)
        self.assertIsNotNone(self.agent.memory)
        self.assertIsNotNone(self.agent.tool_registry)
    
    def test_simple_message(self):
        """测试简单消息处理"""
        response = self.agent.process_message("你好")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
    
    def test_calculation(self):
        """测试计算功能"""
        response = self.agent.process_message("帮我计算 2+3")
        self.assertIsInstance(response, str)
    
    def test_agent_status(self):
        """测试状态获取"""
        status = self.agent.get_status()
        self.assertIn("session_id", status)
        self.assertIn("pending_tasks", status)
        self.assertIn("completed_tasks", status)
        self.assertIn("tool_metrics", status)

if __name__ == "__main__":
    unittest.main()