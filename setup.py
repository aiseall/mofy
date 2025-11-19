"""
Mofy Agent Framework 安装脚本
"""

import subprocess
import sys
import os

def install_requirements():
    """安装依赖"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False
    return True

def create_docker_config():
    """创建Docker配置文件"""
    print("\n🐳 创建Docker开发环境配置...")
    
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
        print(f"❌ Docker配置创建失败: {e}")
        return False

def check_env():
    """检查环境配置"""
    print("\n检查环境配置...")
    
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ 已创建 .env 文件")
            print("⚠️  请编辑 .env 文件设置您的API密钥")
        else:
            print("⚠️  未找到 .env.example 文件")
    else:
        print("✅ .env 文件已存在")
    
    # 检查关键环境变量
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OPENAI_API_KEY 已设置")
    else:
        print("⚠️  OPENAI_API_KEY 未设置，某些功能可能无法使用")

def main():
    """主函数"""
    print("=== Mofy Agent Framework 安装程序 ===")
    
    # 检查是否需要创建Docker配置
    if len(sys.argv) > 1 and sys.argv[1] == "--docker":
        create_docker_config()
        return
    
    # 安装依赖
    if not install_requirements():
        return
    
    # 检查环境
    check_env()
    
    # 创建Docker配置
    create_docker_config()
    
    print("\n=== 安装完成 ===")
    print("运行以下命令启动Agent:")
    print("python mofy.py")
    print("\n或者运行测试:")
    print("python test_mofy.py")
    print("\n或者启动Docker开发环境:")
    print("docker-compose -f docker-compose.dev.yml up -d")

if __name__ == "__main__":
    main()