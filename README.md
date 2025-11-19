# Mofy Agent Framework

一个轻量级、高性能的Python Agent框架，基于从0到1开发Agent框架的最佳实践构建。

## 特性

- 🚀 **轻量级设计** - 核心依赖最小化，启动速度快
- 🧠 **智能调度** - 基于优先级的任务调度系统
- 💾 **分层记忆** - 短期/长期记忆分离，支持Redis持久化
- 🛠️ **工具系统** - 智能参数解析，支持并行执行
- 🔄 **反思机制** - 自动错误分析和自我改进
- ⚡ **高性能** - 多级缓存、异步执行、批处理优化
- 🌐 **多模型支持** - 支持OpenAI、硅基流动等多种LLM提供商
- 🐳 **Docker支持** - 完整的容器化开发和部署环境

## 快速开始

### 方式1: 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置你的API密钥

# 3. 运行示例
python examples/simple_agent.py
```

### 方式2: Docker调试（推荐）

```bash
# Windows用户
scripts\docker-start.bat prod

# Linux/Mac用户
chmod +x scripts/docker-start.sh
./scripts/docker-start.sh prod
```

## Docker调试指南

### 🐳 Docker服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   mofy-agent    │    │     Redis       │    │ Redis Commander │
│   (主应用)       │◄──►│   (记忆存储)     │    │   (管理界面)     │
│   :8000         │    │   :6379         │    │   :8081         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Jupyter Lab   │    │   mofy-test     │
│  (开发调试)      │    │   (测试服务)     │
│   :8888         │    │                 │
└─────────────────┘    └─────────────────┘
```

### 🚀 快速启动命令

```bash
# 生产环境（包含所有服务）
./scripts/docker-start.sh prod

# 开发环境（热重载+调试）
./scripts/docker-start.sh dev

# 运行测试
./scripts/docker-start.sh test

# 查看服务状态
docker-compose ps

# 查看日志
./scripts/docker-start.sh logs

# 停止所有服务
./scripts/docker-start.sh stop

# 清理所有资源
./scripts/docker-start.sh clean
```

### 🛠️ 开发环境特性

- **热重载**: 代码修改自动重启
- **远程调试**: 支持VS Code调试器连接
- **代码质量检查**: 集成flake8、black、isort
- **单元测试**: pytest + 覆盖率报告
- **性能分析**: memory_profiler + psutil

### 📊 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 主应用 | http://localhost:8000 | Mofy Agent Web界面 |
| Redis管理 | http://localhost:8081 | Redis Commander管理界面 |
| Jupyter Lab | http://localhost:8888 | 开发调试环境 |
| Redis | localhost:6379 | 记忆存储服务 |

### 🔧 环境配置

1. **复制环境配置**:
```bash
cp .env.docker .env
```

2. **编辑配置文件**:
```env
# 选择LLM提供商
LLM_PROVIDER=siliconflow
MODEL_NAME=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
SILICONFLOW_API_KEY=your_api_key_here

# 或使用OpenAI
# LLM_PROVIDER=openai
# MODEL_NAME=gpt-4o
# OPENAI_API_KEY=your_openai_api_key
```

### 🐛 调试配置

#### VS Code远程调试

创建 `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Docker Python Debug",
            "type": "python",
            "request": "attach",
            "port": 5678,
            "host": "localhost",
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ]
        }
    ]
}
```

#### 日志调试

```bash
# 查看实时日志
docker-compose logs -f mofy-agent

# 查看特定服务日志
docker-compose logs -f redis

# 查看所有服务日志
docker-compose logs -f
```

## LLM模型配置

### OpenAI模型（默认）
```env
LLM_PROVIDER=openai
MODEL_NAME=gpt-4o
OPENAI_API_KEY=your_openai_api_key
```

### 硅基流动模型
```env
LLM_PROVIDER=siliconflow
MODEL_NAME=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
SILICONFLOW_API_KEY=your_siliconflow_api_key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
```

#### 支持的硅基流动模型
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` - DeepSeek R1蒸馏版32B
- `Qwen/Qwen2.5-72B-Instruct` - 通义千问2.5 72B指令版
- `meta-llama/Llama-3.1-70B-Instruct` - Llama 3.1 70B指令版
- `01-ai/Yi-1.5-34B-Chat` - 零一万物34B对话版

#### 获取硅基流动API密钥
1. 访问 [硅基流动官网](https://cloud.siliconflow.cn/)
2. 注册并登录账户
3. 在控制台获取API密钥
4. 将密钥配置到环境变量中

## 核心架构