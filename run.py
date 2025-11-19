#!/usr/bin/env python3
"""
Mofy Agent Framework 启动脚本
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_docker():
    """创建Docker配置文件"""
    print("🐳 创建Docker开发环境配置...")
    
    # docker-compose.dev.yml
    docker_compose = '''version: '3.8'

services:
  # 开发环境主应用
  mofy-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: mofy-dev
    ports:
      - "8000:8000"
      - "5678:5678"  # 调试端口
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
      - REDIS_HOST=redis-dev
      - REDIS_PORT=6379
      - LOG_LEVEL=DEBUG
    env_file:
      - .env
    volumes:
      - .:/app  # 代码热重载
      - ./logs:/app/logs
    depends_on:
      redis-dev:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - mofy-dev-network
    command: >
      bash -c "pip install debugpy &&
               python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m run.py"

  # Redis缓存服务
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

  # 测试服务
  test:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: mofy-test
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
      - REDIS_HOST=redis-dev
      - REDIS_PORT=6379
    env_file:
      - .env
    volumes:
      - .:/app
      - ./test_reports:/app/test_reports
    depends_on:
      - redis-dev
    profiles:
      - testing
    command: >
      bash -c "pytest test_mofy.py -v --tb=short --html=test_reports/report.html"

volumes:
  redis-dev-data:
    driver: local

networks:
  mofy-dev-network:
    driver: bridge
'''

    # Dockerfile.dev
    dockerfile = '''FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 安装开发工具
RUN pip install debugpy pytest pytest-html

# 复制项目代码
COPY . .

# 创建日志目录
RUN mkdir -p logs test_reports

EXPOSE 8000 5678

CMD ["python", "run.py"]
'''

    # 创建文件
    files = [
        ('docker-compose.dev.yml', docker_compose),
        ('Dockerfile.dev', dockerfile)
    ]
    
    success_count = 0
    for filename, content in files:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 创建文件: {filename}")
            success_count += 1
        except Exception as e:
            print(f"❌ 创建文件失败 {filename}: {e}")
    
    # 创建目录
    dirs = ['logs', 'test_reports']
    for dir_name in dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
            print(f"✅ 创建目录: {dir_name}")
        except Exception as e:
            print(f"❌ 创建目录失败 {dir_name}: {e}")
    
    if success_count == len(files):
        print("\\n🎉 Docker配置创建完成!")
        print("\\n🚀 使用方法:")
        print("   1. 启动开发环境: docker-compose -f docker-compose.dev.yml up -d")
        print("   2. 查看服务状态: docker-compose -f docker-compose.dev.yml ps")
        print("   3. 查看日志: docker-compose -f docker-compose.dev.yml logs -f")
        print("   4. 停止服务: docker-compose -f docker-compose.dev.yml down")
        print("   5. 运行测试: docker-compose -f docker-compose.dev.yml --profile testing up test")
        print("\\n🔧 调试配置:")
        print("   - 主应用: http://localhost:8000")
        print("   - 调试端口: localhost:5678 (VS Code可连接)")
        print("   - Redis: localhost:6379")
    else:
        print("\\n⚠️ 部分文件创建失败，请检查错误信息")

def main():
    parser = argparse.ArgumentParser(description="Mofy Agent Framework")
    parser.add_argument("--example", choices=["simple", "react", "financial"], 
                       default="simple", help="运行示例类型")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--docker-setup", action="store_true", help="设置Docker开发环境")
    
    args = parser.parse_args()
    
    if args.docker_setup:
        setup_docker()
        return
    
    if args.test:
        print("运行测试...")
        os.system(f"python -m pytest tests/ -v")
        return
    
    if args.example == "simple":
        from examples.simple_agent import main as simple_main
        simple_main()
    elif args.example == "react":
        print("ReAct示例待实现")
    elif args.example == "financial":
        print("金融分析示例待实现")

if __name__ == "__main__":
    main()