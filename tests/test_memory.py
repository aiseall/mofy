import sys
import os
import time
import unittest

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.memory import MemoryManager

class TestMemoryManager(unittest.TestCase):
    """记忆管理器测试"""
    
    def setUp(self):
        self.session_id = "test_session"
        self.memory = MemoryManager(self.session_id)
    
    def test_add_short_term_memory(self):
        """测试添加短期记忆"""
        self.memory.add_experience("测试内容")
        self.assertEqual(len(self.memory.short_term), 1)
        self.assertEqual(self.memory.short_term[0]["content"], "测试内容")
    
    def test_add_long_term_memory(self):
        """测试添加长期记忆"""
        self.memory.add_experience("结构化知识", is_structured=True, key="test_key")
        result = self.memory.get_long_term("test_key")
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "结构化知识")
    
    def test_short_term_expiration(self):
        """测试短期记忆过期"""
        # 添加一个短期记忆，TTL设为1秒
        self.memory.short_term_ttl = 1
        self.memory.add_experience("即将过期的内容")
        
        # 等待过期
        time.sleep(2)
        self.memory._clean_short_term()
        
        # 验证已清理
        self.assertEqual(len(self.memory.short_term), 0)
    
    def test_search_long_term(self):
        """测试搜索长期记忆"""
        # 添加多个长期记忆
        self.memory.add_experience("Python编程语言", is_structured=True, key="python")
        self.memory.add_experience("Java编程语言", is_structured=True, key="java")
        
        # 搜索包含"编程"的记忆
        results = self.memory.search_long_term("编程")
        self.assertGreaterEqual(len(results), 2)
    
    def test_get_relevant_memory(self):
        """测试获取相关记忆"""
        # 添加短期记忆
        self.memory.add_experience("用户询问天气")
        
        # 添加长期记忆
        self.memory.add_experience("北京今天晴天", is_structured=True, key="beijing_weather")
        
        # 获取相关记忆
        context = self.memory.get_relevant_memory("天气")
        self.assertIn("天气", context)

if __name__ == "__main__":
    unittest.main()