"""
Mofy Agent Framework - 轻量级Agent框架
基于从0到1开发Agent框架的最佳实践实现
"""

import os
import sys
import time
import uuid
import json
import hashlib
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# 第三方依赖
try:
    from openai import OpenAI
    import redis
    from loguru import logger
    from dotenv import load_dotenv
except ImportError as e:
    print(f"请先安装依赖: pip install -r requirements.txt")
    print(f"缺少依赖: {e}")
    sys.exit(1)

# 加载环境变量
load_dotenv()

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class MofyConfig:
    """Mofy框架配置"""
    # LLM配置
    llm_provider: str = "openai"
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    openai_api_key: str = ""
    
    # 记忆配置
    short_term_memory_ttl: int = 3600
    enable_long_term_memory: bool = True
    redis_url: str = "redis://localhost:6379/0"
    
    # 工具配置
    tool_timeout: int = 3
    max_tool_retries: int = 2
    
    def __post_init__(self):
        """从环境变量加载配置"""
        self.llm_provider = os.getenv("LLM_PROVIDER", self.llm_provider)
        self.model_name = os.getenv("MODEL_NAME", self.model_name)
        self.temperature = float(os.getenv("TEMPERATURE", self.temperature))
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.redis_url = os.getenv("REDIS_URL", self.redis_url)
        self.tool_timeout = int(os.getenv("TOOL_TIMEOUT", self.tool_timeout))
        self.max_tool_retries = int(os.getenv("TOOL_RETRIES", self.max_tool_retries))

class LLMClient:
    """LLM客户端封装"""
    
    def __init__(self, config: MofyConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
        try:
            self.redis_client = redis.Redis.from_url(config.redis_url)
            self.redis_client.ping()  # 测试连接
        except:
            self.redis_client = None
            logger.warning("Redis连接失败，将不使用缓存")
    
    def invoke(self, prompt: str, cache_ttl: int = 3600) -> str:
        """调用LLM，支持缓存"""
        # 生成缓存键
        cache_key = f"llm_cache:{hashlib.md5(prompt.encode()).hexdigest()}"
        
        # 尝试从Redis获取缓存
        if self.redis_client:
            try:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"LLM缓存命中: {cache_key[:8]}")
                    return cached_result.decode()
            except:
                pass
        
        # 调用LLM
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature
            )
            result = response.choices[0].message.content
            
            # 存入缓存
            if self.redis_client:
                try:
                    self.redis_client.setex(cache_key, cache_ttl, result)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                raise ValueError("未找到JSON结构")
            return json.loads(response[json_start:json_end])
        except Exception as e:
            logger.error(f"解析失败，原始响应: {response}")
            return {"action": "error", "message": str(e)}

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, max_retries: int = 3):
        self.task_queue: List[Dict[str, Any]] = []
        self.max_retries = max_retries
        self.completed_tasks: List[Dict[str, Any]] = []
    
    def add_task(self, task_type: str, parameters: Dict[str, Any], priority: int = 5):
        """添加任务"""
        task = {
            "task_id": f"task_{len(self.task_queue) + 1}",
            "type": task_type,
            "params": parameters,
            "priority": priority,
            "status": TaskStatus.PENDING,
            "retries": 0,
            "created_at": time.time()
        }
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: x["priority"])
        logger.info(f"任务已添加: {task['task_id']}")
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """获取下一个任务"""
        for task in self.task_queue:
            if task["status"] == TaskStatus.PENDING:
                task["status"] = TaskStatus.EXECUTING
                return task
        return None
    
    def complete_task(self, task_id: str, result: Any, success: bool = True):
        """完成任务"""
        for task in self.task_queue:
            if task["task_id"] == task_id:
                task["status"] = TaskStatus.COMPLETED if success else TaskStatus.FAILED
                task["result"] = result
                task["completed_at"] = time.time()
                self.completed_tasks.append(task)
                return True
        return False

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, config: MofyConfig):
        self.config = config
        self.short_term: List[Dict[str, Any]] = []
        self.long_term: Dict[str, Any] = {}
        try:
            self.redis_client = redis.Redis.from_url(config.redis_url)
        except:
            self.redis_client = None
    
    def add_experience(self, session_id: str, content: str, is_structured: bool = False, key: str = None):
        """添加经验"""
        if is_structured and key:
            self.long_term[key] = {
                "content": content,
                "updated_at": time.time()
            }
        else:
            self.short_term.append({
                "session_id": session_id,
                "content": content,
                "timestamp": time.time()
            })
            self._clean_short_term()
    
    def get_relevant_memory(self, session_id: str, query: str) -> str:
        """获取相关记忆"""
        recent = [item for item in self.short_term 
                 if item["session_id"] == session_id][-5:]
        recent_dialog = "\n".join([item["content"] for item in recent])
        
        context = f"最近对话:\n{recent_dialog}"
        return context[:2000] if len(context) > 2000 else context
    
    def _clean_short_term(self):
        """清理过期记忆"""
        now = time.time()
        self.short_term = [
            item for item in self.short_term
            if now - item["timestamp"] < self.config.short_term_memory_ttl
        ]

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self, config: MofyConfig):
        self.config = config
        self.tools: Dict[str, Any] = {}
        self.schemas: Dict[str, Dict] = {}
        self.metrics: Dict[str, Dict] = {}
        self._init_builtin_tools()
    
    def register_tool(self, name: str, func: Any, schema: Dict):
        """注册工具"""
        self.tools[name] = func
        self.schemas[name] = schema
        self.metrics[name] = {"calls": 0, "success": 0, "failures": 0}
        logger.info(f"工具注册成功: {name}")
    
    def execute_tool(self, tool_name: str, params: str) -> str:
        """执行工具"""
        if tool_name not in self.tools:
            return f"工具不存在: {tool_name}"
        
        try:
            parsed_params = self._parse_parameters(tool_name, params)
            start_time = time.time()
            
            result = self.tools[tool_name](**parsed_params)
            exec_time = (time.time() - start_time) * 1000
            
            self.metrics[tool_name]["calls"] += 1
            self.metrics[tool_name]["success"] += 1
            
            return f"[{tool_name}执行成功] {result}"
            
        except Exception as e:
            self.metrics[tool_name]["calls"] += 1
            self.metrics[tool_name]["failures"] += 1
            logger.error(f"工具执行失败 {tool_name}: {str(e)}")
            return f"[{tool_name}执行失败] {str(e)}"
    
    def _parse_parameters(self, tool_name: str, params: str) -> Dict[str, Any]:
        """解析参数"""
        schema = self.schemas[tool_name]
        required_params = schema["parameters"].get("required", [])
        
        # 尝试JSON解析
        try:
            return json.loads(params)
        except:
            pass
        
        # 尝试键值对解析
        if "=" in params and "&" in params:
            import re
            parsed = dict(re.findall(r"(\w+)=([^&]+)", params))
            if all(p in parsed for p in required_params):
                return parsed
        
        # 单参数工具
        if len(required_params) == 1:
            return {required_params[0]: params.strip()}
        
        raise ValueError(f"无法解析参数格式: {params}")
    
    def _init_builtin_tools(self):
        """初始化内置工具"""
        # 计算器工具
        def calculator(expression: str) -> str:
            try:
                result = eval(expression)
                return f"计算结果: {result}"
            except Exception as e:
                return f"计算错误: {str(e)}"
        
        self.register_tool(
            "calculator",
            calculator,
            {
                "description": "执行数学计算",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "数学表达式"}
                    },
                    "required": ["expression"]
                }
            }
        )
        
        # 搜索工具
        def search(query: str) -> str:
            return f"搜索'{query}'的结果：这里应该是搜索结果内容"
        
        self.register_tool(
            "search",
            search,
            {
                "description": "搜索信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"}
                    },
                    "required": ["query"]
                }
            }
        )

def generate_docker_config():
    """生成Docker配置文件"""
    print("🐳 生成Docker开发环境配置...")
    
    # docker-compose.dev.yml
    compose_content = '''version: '3.8'

services:
  mofy-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: mofy-dev
    ports:
      - "8000:8000"
      - "5678:5678"
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
      - REDIS_HOST=redis-dev
      - REDIS_PORT=6379
      - LOG_LEVEL=DEBUG
    env_file:
      - .env
    volumes:
      - .:/app
      - ./logs:/app/logs
    depends_on:
      redis-dev:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - mofy-dev-network

  redis-dev:
    image: redis:7-alpine
    container_name: mofy-redis-dev
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-dev-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - mofy-dev-network

volumes:
  redis-dev-data:
    driver: local

networks:
  mofy-dev-network:
    driver: bridge
'''
    
    # Dockerfile.dev
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN pip install debugpy pytest pytest-html

COPY . .

RUN mkdir -p logs test_reports

EXPOSE 8000 5678

CMD ["python", "run.py"]
'''
    
    try:
        with open('docker-compose.dev.yml', 'w', encoding='utf-8') as f:
            f.write(compose_content)
        print("✅ docker-compose.dev.yml 创建成功")
        
        with open('Dockerfile.dev', 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        print("✅ Dockerfile.dev 创建成功")
        
        os.makedirs('logs', exist_ok=True)
        os.makedirs('test_reports', exist_ok=True)
        print("✅ 目录创建成功")
        
        print("\n🎉 Docker开发环境配置完成!")
        print("\n🚀 使用命令:")
        print("   docker-compose -f docker-compose.dev.yml up -d")
        print("   docker-compose -f docker-compose.dev.yml ps")
        print("   docker-compose -f docker-compose.dev.yml logs -f")
        print("   docker-compose -f docker-compose.dev.yml down")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False

def generate_wsl_docker_config():
    """生成WSL专用的Docker配置文件"""
    print("🐳 生成WSL专用Docker开发环境配置...")
    
    # WSL优化的docker-compose.wsl.yml
    compose_content = '''version: '3.8'

services:
  mofy-wsl:
    build:
      context: .
      dockerfile: Dockerfile.wsl
    container_name: mofy-wsl
    ports:
      - "8000:8000"
      - "5678:5678"
      - "9229:9229"  # Node.js调试端口（如果需要）
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
      - REDIS_HOST=redis-wsl
      - REDIS_PORT=6379
      - LOG_LEVEL=DEBUG
      - WSL_MODE=1
    env_file:
      - .env
    volumes:
      - /mnt/d/Workshop/ai4se/mofiy:/app  # WSL路径映射
      - /mnt/d/Workshop/ai4se/mofiy/logs:/app/logs
      - /mnt/d/Workshop/ai4se/mofiy/test_reports:/app/test_reports
    depends_on:
      redis-wsl:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - mofy-wsl-network
    command: >
      bash -c "pip install debugpy &&
               python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m run.py"

  redis-wsl:
    image: redis:7-alpine
    container_name: mofy-redis-wsl
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-wsl-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - mofy-wsl-network

  # 开发工具容器（可选）
  dev-tools:
    build:
      context: .
      dockerfile: Dockerfile.wsl
    container_name: mofy-dev-tools
    volumes:
      - /mnt/d/Workshop/ai4se/mofiy:/app
    networks:
      - mofy-wsl-network
    profiles:
      - tools
    command: tail -f /dev/null  # 保持容器运行

volumes:
  redis-wsl-data:
    driver: local

networks:
  mofy-wsl-network:
    driver: bridge
'''
    
    # WSL优化的Dockerfile.wsl
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖和WSL相关工具
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    make \\
    curl \\
    git \\
    vim \\
    htop \\
    net-tools \\
    iputils-ping \\
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 安装开发和调试工具
RUN pip install debugpy pytest pytest-html black flake8 mypy ipython jupyter

# 复制项目代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs test_reports .vscode

# 设置权限
RUN chmod +x run.py 2>/dev/null || true

EXPOSE 8000 5678 9229

# 默认启动命令
CMD ["python", "run.py"]
'''
    
    # WSL启动脚本
    wsl_script = '''#!/bin/bash
# WSL Docker开发环境启动脚本

echo "🐳 启动WSL Docker开发环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker Desktop"
    exit 1
fi

# 检查WSL路径
if [ ! -d "/mnt/d/Workshop/ai4se/mofiy" ]; then
    echo "❌ WSL路径不存在: /mnt/d/Workshop/ai4se/mofiy"
    echo "请确保Windows路径正确映射到WSL"
    exit 1
fi

# 启动服务
docker-compose -f docker-compose.wsl.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 显示服务状态
docker-compose -f docker-compose.wsl.yml ps

echo ""
echo "🎉 WSL Docker环境启动完成!"
echo ""
echo "🔧 服务信息:"
echo "   - 主应用: http://localhost:8000"
echo "   - 调试端口: localhost:5678"
echo "   - Redis: localhost:6379"
echo ""
echo "📝 调试命令:"
echo "   docker-compose -f docker-compose.wsl.yml logs -f mofy-wsl"
echo "   docker-compose -f docker-compose.wsl.yml exec mofy-wsl bash"
echo ""
echo "🛑 停止服务:"
echo "   docker-compose -f docker-compose.wsl.yml down"
'''
    
    # VS Code调试配置
    vscode_config = '''{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "WSL Docker Debug",
            "type": "python",
            "request": "attach",
            "port": 5678,
            "host": "localhost",
            "pathMappings": [
                {
                    "localRoot": "/mnt/d/Workshop/ai4se/mofiy",
                    "remoteRoot": "/app"
                }
            ],
            "justMyCode": false
        },
        {
            "name": "WSL Docker Test",
            "type": "python",
            "request": "attach",
            "port": 5678,
            "host": "localhost",
            "pathMappings": [
                {
                    "localRoot": "/mnt/d/Workshop/ai4se/mofiy",
                    "remoteRoot": "/app"
                }
            ],
            "args": ["-m", "pytest", "tests/", "-v"]
        }
    ]
}
'''
    
    try:
        # 创建WSL Docker配置文件
        with open('docker-compose.wsl.yml', 'w', encoding='utf-8') as f:
            f.write(compose_content)
        print("✅ docker-compose.wsl.yml 创建成功")
        
        with open('Dockerfile.wsl', 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        print("✅ Dockerfile.wsl 创建成功")
        
        # 创建WSL启动脚本
        with open('start_wsl_docker.sh', 'w', encoding='utf-8') as f:
            f.write(wsl_script)
        print("✅ start_wsl_docker.sh 创建成功")
        
        # 创建VS Code配置目录和文件
        os.makedirs('.vscode', exist_ok=True)
        with open('.vscode/launch.json', 'w', encoding='utf-8') as f:
            f.write(vscode_config)
        print("✅ .vscode/launch.json 创建成功")
        
        # 创建必要目录
        os.makedirs('logs', exist_ok=True)
        os.makedirs('test_reports', exist_ok=True)
        print("✅ 目录创建成功")
        
        # 设置脚本执行权限
        os.chmod('start_wsl_docker.sh', 0o755)
        
        print("\n🎉 WSL Docker开发环境配置完成!")
        print("\n🚀 WSL使用方法:")
        print("   1. 在WSL中运行: ./start_wsl_docker.sh")
        print("   2. 或者手动启动: docker-compose -f docker-compose.wsl.yml up -d")
        print("   3. 在VS Code中按F5选择'WSL Docker Debug'进行调试")
        print("\n🔧 WSL调试配置:")
        print("   - 主应用: http://localhost:8000")
        print("   - 调试端口: localhost:5678")
        print("   - Redis: localhost:6379")
        print("   - VS Code调试: 已配置路径映射")
        print("\n📝 常用命令:")
        print("   docker-compose -f docker-compose.wsl.yml logs -f")
        print("   docker-compose -f docker-compose.wsl.yml exec mofy-wsl bash")
        print("   docker-compose -f docker-compose.wsl.yml down")
        
        return True
        
    except Exception as e:
        print(f"❌ WSL配置创建失败: {e}")
        return False

class MofyAgent:
    """Mofy Agent主类"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.config = MofyConfig()
        self.llm_client = LLMClient(self.config)
        self.scheduler = TaskScheduler()
        self.memory = MemoryManager(self.config)
        self.tool_registry = ToolRegistry(self.config)
        self.last_active = time.time()
        
        logger.info(f"Mofy Agent初始化完成: {self.session_id}")
    
    def process_message(self, message: str) -> str:
        """处理用户消息"""
        try:
            self.last_active = time.time()
            self.memory.add_experience(self.session_id, f"用户: {message}")
            
            context = self.memory.get_relevant_memory(self.session_id, message)
            
            # 简化的意图分析
            if any(keyword in message.lower() for keyword in ["计算", "算", "+", "-", "*", "/"]):
                return self._handle_calculation(message)
            elif any(keyword in message.lower() for keyword in ["搜索", "查找", "查询"]):
                return self._handle_search(message)
            else:
                return self._handle_general_chat(message, context)
                
        except Exception as e:
            logger.error(f"消息处理失败: {str(e)}")
            return f"抱歉，处理过程中出现错误：{str(e)}"
    
    def _handle_calculation(self, message: str) -> str:
        """处理计算请求"""
        # 提取数学表达式
        import re
        pattern = r'[\d+\-*/(). ]+'
        matches = re.findall(pattern, message)
        if matches:
            expression = matches[0].strip()
            result = self.tool_registry.execute_tool("calculator", expression)
            self.memory.add_experience(self.session_id, f"助手: {result}")
            return result
        return "请提供要计算的数学表达式"
    
    def _handle_search(self, message: str) -> str:
        """处理搜索请求"""
        # 简单的关键词提取
        keywords = message.replace("搜索", "").replace("查找", "").replace("查询", "").strip()
        if keywords:
            result = self.tool_registry.execute_tool("search", keywords)
            self.memory.add_experience(self.session_id, f"助手: {result}")
            return result
        return "请告诉我您想搜索什么"
    
    def _handle_general_chat(self, message: str, context: str) -> str:
        """处理一般对话"""
        prompt = f"""你是一个智能助手。基于以下上下文回答用户问题。

上下文信息:
{context}

用户消息: {message}

请给出简洁、有用的回复:
"""
        
        try:
            response = self.llm_client.invoke(prompt)
            self.memory.add_experience(self.session_id, f"助手: {response}")
            return response
        except Exception as e:
            return f"抱歉，我暂时无法处理这个请求：{str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "session_id": self.session_id,
            "last_active": self.last_active,
            "pending_tasks": len([t for t in self.scheduler.task_queue if t["status"].value == "pending"]),
            "completed_tasks": len(self.scheduler.completed_tasks),
            "tool_metrics": self.tool_registry.metrics
        }

def main():
    """主函数 - 简单的交互示例"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--docker-setup":
            generate_docker_config()
            return
        elif sys.argv[1] == "--wsl-setup":
            generate_wsl_docker_config()
            return
    
    print("=== Mofy Agent Framework ===")
    print("轻量级Agent框架演示")
    print("输入 'quit' 退出，'status' 查看状态")
    print()
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: 未设置OPENAI_API_KEY环境变量")
        print("某些功能可能无法正常使用")
        print()
    
    agent = MofyAgent()
    
    while True:
        try:
            user_input = input("用户: ").strip()
            
            if user_input.lower() == 'quit':
                print("再见！")
                break
            
            if user_input.lower() == 'status':
                status = agent.get_status()
                print(f"Agent状态:")
                for key, value in status.items():
                    print(f"  {key}: {value}")
                continue
            
            if not user_input:
                continue
            
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